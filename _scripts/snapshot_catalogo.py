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

O que conta como mudança de fórmula: só duas listas INCI registradas, com fonte e data,
que diferem em pelo menos um ingrediente. A primeira lista de um produto é o ponto de
partida, e mudar o campo "ativos" do catálogo é edição do site (tipo "catalogo").

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
    """Lista INCI -> nomes normalizados, na ordem do rótulo (vírgula dentro de nome, como 1,2-HEXANEDIOL, não separa)."""
    t = re.sub(r"(\d),(\d)", "\\1\x01\\2", str(texto or "").replace("\n", " "))
    nomes = []
    for parte in re.split(r"[,;]", t):
        nome = re.sub(r"\s+", " ", parte.replace("\x01", ",")).strip(" .*").upper()
        if len(nome) >= 2 and nome not in nomes:
            nomes.append(nome)
    return nomes


def chave_inci(nome):
    return re.sub(r"[^A-Z0-9]", "", nome)


def diferenca_inci(antes, depois):
    """(saiu, entrou): ingredientes que estão só em uma das duas listas. Ordem e pontuação não contam."""
    a, b = ingredientes(antes), ingredientes(depois)
    ka, kb = {chave_inci(n) for n in a}, {chave_inci(n) for n in b}
    return [n for n in a if chave_inci(n) not in kb], [n for n in b if chave_inci(n) not in ka]


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
    # Ativos são a curadoria do site (campo "ativos" de produtos.json). Mudar esse campo é edição
    # do catálogo, não mudança do produto: nunca vira "reformulação".
    if sorted(e.get("ativos") or []) != sorted(novo.get("ativos") or []):
        itens.append({
            "em": hoje, "produto_id": pid, "produto": nome, "tipo": "catalogo",
            "de": e.get("ativos"), "para": novo.get("ativos"),
            "leitura": "ativos destacados no catálogo atualizados (edição do site, não mudança do produto)",
        })
    # Fórmula: só há mudança quando existem DUAS listas INCI registradas e elas diferem.
    # A primeira lista registrada de um produto é o ponto de partida, não uma alteração.
    if e.get("inci") and novo.get("inci") and e.get("inci") != novo.get("inci"):
        saiu, entrou = diferenca_inci(e["inci"], novo["inci"])
        if saiu or entrou:
            partes = []
            if saiu:
                partes.append("só na lista anterior: " + ", ".join(saiu))
            if entrou:
                partes.append("só na lista nova: " + ", ".join(entrou))
            itens.append({
                "em": hoje, "produto_id": pid, "produto": nome, "tipo": "formula",
                "de": e.get("inci"), "para": novo.get("inci"),
                "saiu": saiu, "entrou": entrou,
                "de_fonte": e.get("inci_fonte"), "de_em": e.get("inci_em"),
                "para_fonte": novo.get("inci_fonte"), "para_em": novo.get("inci_em"),
                "leitura": "lista de ingredientes diferente entre dois registros — " + "; ".join(partes),
            })
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
        "não muda e o volume cai), formula (duas listas INCI registradas e diferentes), "
        "catalogo (o site mudou os ativos que destaca; não é mudança do produto).", "itens": [],
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
