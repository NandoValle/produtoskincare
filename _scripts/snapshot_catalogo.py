# -*- coding: utf-8 -*-
"""Snapshot versionado do catálogo: preço, volume, ativos e INCI, tudo datado.

Por que isto existe: dado temporal não se recupera retroativamente. Cada preço,
tamanho e lista de ingredientes registrado hoje é o "extrato bancário" do
cosmético amanhã — é o que detecta reformulação silenciosa e shrinkflation
(mesmo preço, volume menor). Começamos em 19/11/2026; os dados vêm de:

  - produtos.json                          (preço, data do preço, loja, ativos)
  - _scripts/precos/dados/tamanhos.json    (volume + fonte do volume)
  - _scripts/precos/dados/incis.json       (opcional: INCI por produto, com fonte)

Uso:
    python _scripts/snapshot_catalogo.py            # registra mudanças e escreve
    python _scripts/snapshot_catalogo.py --check    # só mostra o que mudaria

Saídas (publicadas no site):
    produtos/snapshots.json    histórico completo, por produto, datado
    produtos/mudancas.json     mudanças detectadas (preço / volume / fórmula)

Para registrar o INCI de um produto (uma vez por versão da fórmula), crie ou
atualize _scripts/precos/dados/incis.json:

    { "<produto-id>": { "texto": "AQUA, GLYCERIN, ...", "fonte": "embalagem",
                        "em": "2026-11-19" } }

Rode este script depois de cada atualização de produtos.json. É idempotente:
sem mudança desde o último snapshot, nada é acrescentado.
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ARQ_SNAPSHOTS = RAIZ / "produtos" / "snapshots.json"
ARQ_MUDANCAS = RAIZ / "produtos" / "mudancas.json"
ARQ_PRODUTOS = RAIZ / "produtos.json"
ARQ_TAMANHOS = RAIZ / "_scripts" / "precos" / "dados" / "tamanhos.json"
ARQ_INCIS = RAIZ / "_scripts" / "precos" / "dados" / "incis.json"

INSTRUCOES = (
    "Histórico datado de preço, volume e fórmula (INCI) por produto. "
    "Cada entrada é o estado conhecido na data 'em'. "
    "Volume vem de tamanhos.json (nunca estimado); INCI só entra quando alguém "
    "registra a lista da embalagem ou de fonte oficial, com a fonte anotada. "
    "Mudanças entre entradas viram produtos/mudancas.json (preço, volume, fórmula)."
)


def carregar_json(caminho, padrao):
    if not caminho.exists():
        return padrao
    return json.loads(caminho.read_text(encoding="utf-8"))


def estado_de(produto, tamanhos, incis):
    pid = produto["id"]
    tam = tamanhos.get(pid, {})
    inci = incis.get(pid, {})
    return {
        "nome": produto.get("nome", pid),
        "marca": produto.get("marca", ""),
        "preco": produto.get("preco"),
        "preco_em": produto.get("preco_em"),
        "loja": produto.get("plataforma"),
        "volume_ml": tam.get("size_ml"),
        "volume_g": tam.get("size_g"),
        "volume_fonte": tam.get("fonte"),
        "ativos": sorted(produto.get("ativos", [])),
        "inci": inci.get("texto"),
        "inci_fonte": inci.get("fonte"),
        "inci_em": inci.get("em"),
    }


def mesma_leitura(a, b, chaves):
    return all(a.get(c) == b.get(c) for c in chaves)


def preco_por_ml(e):
    ml = e.get("volume_ml")
    if ml and e.get("preco") is not None:
        return round(e["preco"] / ml, 2)
    g = e.get("volume_g")
    if g and e.get("preco") is not None:
        return round(e["preco"] / g, 2)
    return None


def ingredientes(texto):
    """Lista INCI em itens, na ordem da embalagem. Separa em ', ' (vírgula seguida de espaço),
    para não partir nomes como 1,2-HEXANEDIOL."""
    if not texto:
        return []
    bruto = re.split(r",\s+|;\s*|\s[•·]\s", str(texto).replace("\n", " "))
    return [re.sub(r"\s+", " ", i).strip(" .") for i in bruto if i.strip(" .")]


def diff_inci(antes, depois):
    """Compara duas listas INCI ingrediente a ingrediente, sem diferenciar maiúsculas e espaços.
    Sem lista anterior não há mudança: é o primeiro registro."""
    vazio = {"mudou": False, "entraram": [], "sairam": [], "reordenou": False}
    if not antes:
        return vazio
    a, b = ingredientes(antes), ingredientes(depois)
    ka, kb = [i.upper() for i in a], [i.upper() for i in b]
    if ka == kb:
        return vazio
    entraram = [i for i, k in zip(b, kb) if k not in ka]
    sairam = [i for i, k in zip(a, ka) if k not in kb]
    comuns_a = [k for k in ka if k in kb]
    comuns_b = [k for k in kb if k in ka]
    return {"mudou": True, "entraram": entraram, "sairam": sairam, "reordenou": comuns_a != comuns_b}


def mudancas_de(velho, novo, hoje):
    """Compara o último snapshot com o estado atual; devolve itens de mudanca."""
    itens = []
    pid = novo["id"]
    nome = novo["nome"]
    e = velho["estado"]

    if not mesma_leitura(e, novo, ["preco"]):
        itens.append({
            "em": hoje, "produto_id": pid, "produto": nome, "tipo": "preco",
            "de": e.get("preco"), "para": novo.get("preco"),
            "leitura": f"preço mudou de R$ {e.get('preco')} para R$ {novo.get('preco')}",
        })
    if not mesma_leitura(e, novo, ["volume_ml", "volume_g"]):
        mesmo_preco = mesma_leitura(e, novo, ["preco"])
        vol_v = e.get("volume_ml") or e.get("volume_g")
        vol_n = novo.get("volume_ml") or novo.get("volume_g")
        if mesmo_preco and vol_n is not None and vol_v is not None and vol_n < vol_v:
            pm_v, pm_n = preco_por_ml(e), preco_por_ml(novo)
            leitura = (f"shrinkflation: mesmo preço, volume menor ({vol_v} → {vol_n})"
                       + (f" — preço por ml subiu de R$ {pm_v} para R$ {pm_n}" if pm_v and pm_n else ""))
        else:
            leitura = f"volume mudou: {vol_v} → {vol_n}"
        itens.append({
            "em": hoje, "produto_id": pid, "produto": nome, "tipo": "volume",
            "de": vol_v, "para": vol_n, "leitura": leitura,
        })
    ativos_mudaram = sorted(e.get("ativos") or []) != sorted(novo.get("ativos") or [])
    d = diff_inci(e.get("inci"), novo.get("inci"))
    # Primeiro registro da lista (não havia versão anterior) não é reformulação: não há com o que comparar.
    if ativos_mudaram or d["mudou"]:
        detalhe = []
        if ativos_mudaram:
            detalhe.append(f"ativos: {e.get('ativos')} → {novo.get('ativos')}")
        if d["entraram"]:
            detalhe.append("entraram: " + ", ".join(d["entraram"]))
        if d["sairam"]:
            detalhe.append("saíram: " + ", ".join(d["sairam"]))
        if d["mudou"] and d["reordenou"]:
            detalhe.append("a ordem dos ingredientes mudou" if (d["entraram"] or d["sairam"])
                           else "mesmos ingredientes, em outra ordem")
        if d["mudou"] and novo.get("inci") is None:
            detalhe.append("a lista registrada foi retirada")
        item = {
            "em": hoje, "produto_id": pid, "produto": nome, "tipo": "formula",
            "de": e.get("inci") or e.get("ativos"), "para": novo.get("inci") or novo.get("ativos"),
            "leitura": "fórmula mudou — " + "; ".join(detalhe),
        }
        if d["mudou"]:
            item.update({"entraram": d["entraram"], "sairam": d["sairam"], "reordenou": d["reordenou"],
                         "fonte_de": e.get("inci_fonte"), "fonte_para": novo.get("inci_fonte")})
        itens.append(item)
    return itens


def main():
    so_check = "--check" in sys.argv
    hoje = date.today().isoformat()

    produtos = carregar_json(ARQ_PRODUTOS, {}).get("produtos", [])
    tamanhos = carregar_json(ARQ_TAMANHOS, {}).get("produtos", {})
    incis = carregar_json(ARQ_INCIS, {})
    snapshots = carregar_json(ARQ_SNAPSHOTS, {
        "versao": "1.0", "iniciado_em": hoje, "_instrucoes": INSTRUCOES, "produtos": {},
    })
    mudancas = carregar_json(ARQ_MUDANCAS, {
        "gerado_em": hoje, "_sobre": "Mudanças detectadas entre snapshots de "
        "produtos/snapshots.json. Tipos: preco, volume (shrinkflation quando o preço "
        "não muda e o volume cai), formula (ativos ou INCI; com os ingredientes que entraram e saíram).", "itens": [],
    })

    novos_itens = []
    acrescentados = []
    for p in produtos:
        estado = estado_de(p, tamanhos, incis)
        estado["id"] = p["id"]
        linha = snapshots["produtos"].setdefault(p["id"], [])
        if not linha:
            entrada = {"em": hoje, **{k: v for k, v in estado.items() if k != "id"}}
            linha.append(entrada)
            acrescentados.append(p["id"])
            continue
        ultimo = linha[-1]
        # Nome e marca são metadados do registro (não mudam a leitura de mudanças).
        for e in linha:
            e.setdefault("nome", estado["nome"])
            e.setdefault("marca", estado["marca"])
        if mesma_leitura(ultimo, estado, ["preco", "preco_em", "loja", "volume_ml", "volume_g",
                                          "ativos", "inci", "inci_fonte"]):
            continue
        novos_itens.extend(mudancas_de({"estado": ultimo}, estado, hoje))
        entrada = {"em": hoje, **{k: v for k, v in estado.items() if k != "id"}}
        linha.append(entrada)
        acrescentados.append(p["id"])

    print(f"data: {hoje} · produtos: {len(produtos)} · snapshots existentes: "
          f"{sum(len(v) for v in snapshots['produtos'].values())}")
    if acrescentados:
        print("snapshot novo para:", ", ".join(acrescentados))
    for it in novos_itens:
        print(f"  [{it['tipo']}] {it['produto']}: {it['leitura']}")
    if not acrescentados:
        print("sem mudança desde o último snapshot — nada a registrar.")

    if so_check:
        print("(--check: nada gravado)")
        return

    if novos_itens:
        mudancas["itens"].extend(novos_itens)
    mudancas["gerado_em"] = hoje
    snapshots.setdefault("_instrucoes", INSTRUCOES)
    ARQ_SNAPSHOTS.write_text(json.dumps(snapshots, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    ARQ_MUDANCAS.write_text(json.dumps(mudancas, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("gravado:", ARQ_SNAPSHOTS.relative_to(RAIZ), "e", ARQ_MUDANCAS.relative_to(RAIZ))


if __name__ == "__main__":
    main()
