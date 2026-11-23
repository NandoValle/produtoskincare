# -*- coding: utf-8 -*-
"""Cruza o catálogo com os dados abertos da ANVISA (cosméticos regularizados).

Fonte oficial (verificada em 20/11/2026):
  https://dados.anvisa.gov.br/dados/CONSULTAS/PRODUTOS/TA_CONSULTA_COSMETICOS.CSV
  (índice em https://dados.anvisa.gov.br/dados/CONSULTAS/ — atualizado quase todo dia;
  o portal de APIs fica em https://api.anvisa.gov.br/)

O que faz:
  1. baixa o CSV uma vez e guarda em _scripts/anvisa/ (pasta com _ não é publicada);
  2. compara os produtos do catálogo (produtos.json) com NO_PRODUTO/NO_RAZAO_SOCIAL_EMPRESA;
  3. escreve anvisa-cosmeticos.json na raiz (publicado) — só os produtos do catálogo,
     com o processo/situação quando há correspondência e a data da conferência.

Limite honesto: "não encontrado" NÃO prova irregularidade (a base é de produtos
regularizados/notificados pela ANVISA; importados vendidos só em marketplace podem
não estar nela, e nomes comerciais mudam). A página mostra o link oficial para a
pessoa conferir por conta própria.

Uso:
    python _scripts/anvisa_cosmeticos.py            # baixa (se preciso) e escreve
    python _scripts/anvisa_cosmeticos.py --check    # só mostra os matches
"""
import csv
import io
import json
import re
import sys
import unicodedata
import urllib.request
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path

URL_CSV = "https://dados.anvisa.gov.br/dados/CONSULTAS/PRODUTOS/TA_CONSULTA_COSMETICOS.CSV"
CACHE = Path(__file__).resolve().parent / "anvisa" / "TA_CONSULTA_COSMETICOS.CSV"
RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "anvisa-cosmeticos.json"
ARQ_PRODUTOS = RAIZ / "produtos.json"

LIMIAR = 0.65  # similaridade mínima (tokens) para aceitar correspondência

# Tokens genéricos que não identificam produto nem marca (evita "CREAMY"~"CREAM",
# "PROTETOR SOLAR" como nome e "SKINCARE" dentro da razão social de qualquer um).
GENERICOS = {
    "skincare", "skin", "care", "cosmeticos", "cosmetica", "derm", "lab",
    "laboratorio", "farmaceutica", "ind", "industria", "com", "comercio",
    "ltda", "epp", "brasil", "beauty", "produtos", "grupo", "global",
    "international", "corp", "inc", "co", "cia", "sa", "the", "of", "and",
    # palavras de categoria: ajudam a descrever, não a identificar
    "protetor", "solar", "limpeza", "facial", "hidratante", "creme", "serum",
    "locacao", "locao", "sabonete", "espuma", "oleo", "fps", "acid", "acido",
    "solution", "water", "aqua", "extract", "complex", "system",
}


def codigos(txt):
    """Códigos de produto tipo VC-10, NC-10, RN-0,3, AH-2, B5 — muito discriminantes.
    FPS fica de fora: "FPS 60" é categoria, não identifica produto."""
    t = norm(txt)
    achados = set(re.findall(r"(?<![a-z0-9])[a-z]{1,3}[- ]\d{1,3}(?![0-9])", t))
    achados |= set(re.findall(r"(?<![a-z0-9])[a-z]\d(?![0-9])", t))
    return {c for c in achados if not c.startswith("fps")}


def melhor_match(nome_produto, nome, empresa, marca):
    """Score entre o NOME do produto do catálogo e o NO_PRODUTO da linha ANVISA.

    Portões: (1) a marca precisa aparecer na linha, OU o nome do produto é
    subconjunto de tokens do nome da ANVISA (fabricantes do grupo aparecem com
    outra razão social — COSMED × MANTECORP); (2) precisa haver conteúdo em
    comum além da marca (token identificador ou código de produto). O bônus de
    contenção (nome inteiro dentro do outro) desempata variantes parecidas
    ("gel de limpeza" × "espuma de limpeza").
    """
    a = norm(nome_produto)
    b = norm(nome)
    if not a or not b:
        return 0.0

    def toks(s):
        return {t for t in s.split() if len(t) >= 3 and t not in GENERICOS}

    tokens_a, tokens_b = toks(a), toks(b)
    marca_t = {t for t in norm(marca).split() if len(t) >= 4 and t not in GENERICOS}
    texto_linha = (b + " " + norm(empresa)).split()
    tem_marca = any(t in texto_linha for t in marca_t) or any(
        len(w) >= 6 and SequenceMatcher(None, t, w).ratio() >= 0.9
        for t in marca_t for w in texto_linha)

    menor, maior = (tokens_a, tokens_b) if len(tokens_a) <= len(tokens_b) else (tokens_b, tokens_a)
    subconjunto = len(menor) >= 2 and menor <= maior and any(len(t) >= 5 for t in menor)

    if marca_t and not tem_marca and not subconjunto:
        return 0.0

    # conteúdo em comum além da marca; se o nome do produto for só
    # marca + categoria ("CETAPHIL CREME HIDRATANTE"), a marca presente no
    # NOME da linha já conta como conteúdo.
    extra_a = {t for t in tokens_a if t not in marca_t}
    if extra_a:
        comum = bool(extra_a & tokens_b) or bool(codigos(a) & codigos(b))
    else:
        comum = bool(marca_t & tokens_b) or bool(codigos(a) & codigos(b))
    if not comum:
        return 0.0

    contencao = (a in b or b in a) and min(len(a), len(b)) >= 12
    # Similaridade por tokens: nomes ANVISA reordenam ("AZELAIC ACID 10
    # PRINCIPIA" × "Principia…") e a comparação de strings castiga o certo.
    inter = tokens_a & tokens_b
    score = (2.0 * len(inter) / (len(tokens_a) + len(tokens_b))) if (tokens_a and tokens_b) else 0.0
    if contencao:
        score += 0.15
    if codigos(a) & codigos(b):
        score = max(score, 0.8)
    return min(score, 0.99)


def norm(txt):
    """Minúsculas, sem acento, sem pontuação, espaços colapsados.
    Também iguala grafias pt/en de ativos (azelaico×azelaic), que aparecem
    nas duas línguas entre fabricantes diferentes."""
    t = unicodedata.normalize("NFD", str(txt or ""))
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = t.lower()
    t = re.sub(r"[^a-z0-9]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    for de, para in SINONIMOS.items():
        t = re.sub(rf"\b{de}\b", para, t)
    return t


SINONIMOS = {
    "azelaico": "azelaic", "hialuronico": "hyaluronic", "hialuronica": "hyaluronic",
    "salicilico": "salicylic", "glicolico": "glycolic", "mandelico": "mandelic",
    "tranexamico": "tranexamic", "ferulico": "ferulic", "retinoico": "retinoic",
    "ascorbico": "ascorbic", "pantenol": "panthenol", "niacinamida": "niacinamide",
    "ceramida": "ceramide", "ceramidas": "ceramide", "benzoila": "benzoyl",
    "peroxido": "peroxide",
}


def baixar():
    if CACHE.exists() and CACHE.stat().st_size > 1_000_000:
        print("cache local:", CACHE)
        return
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    print("baixando CSV da ANVISA (~225 MB)…")
    req = urllib.request.Request(URL_CSV, headers={"User-Agent": "produtoskincare-snapshot/1.0"})
    with urllib.request.urlopen(req, timeout=600) as resp, open(CACHE, "wb") as f:
        while True:
            bloco = resp.read(1 << 20)
            if not bloco:
                break
            f.write(bloco)
    print("gravado:", CACHE, CACHE.stat().st_size, "bytes")


def ler_csv():
    bruto = CACHE.read_bytes()
    for cod in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            texto = bruto.decode(cod)
            break
        except UnicodeDecodeError:
            continue
    else:
        texto = bruto.decode("latin-1")
    leitor = csv.DictReader(io.StringIO(texto), delimiter=";")
    total = 0
    # Índice token → linhas; o matching final só varre as candidatas do índice.
    indice = {}
    linhas = []
    for linha in leitor:
        total += 1
        i = len(linhas)
        linhas.append(linha)
        for tok in set(norm(linha.get("NO_PRODUTO")).split() + norm(linha.get("NO_RAZAO_SOCIAL_EMPRESA")).split()):
            if len(tok) >= 4:
                indice.setdefault(tok, []).append(i)
    print(f"CSV lido: {total} linhas (encoding: {cod}, tokens: {len(indice)})")
    return linhas, indice


def candidatos(alvo, linhas, indice):
    """Índices das linhas que compartilham ao menos um token longo com o alvo."""
    toks = {t for t in norm(alvo).split() if len(t) >= 4}
    ids = set()
    for t in toks:
        ids.update(indice.get(t, ()))
    # guarda: se nada casou por token, devolve vazio (não varremos o CSV inteiro)
    return [linhas[i] for i in sorted(ids)]


def main():
    so_check = "--check" in sys.argv
    hoje = date.today().isoformat()

    produtos = json.loads(ARQ_PRODUTOS.read_text(encoding="utf-8"))["produtos"]
    baixar()
    linhas, indice = ler_csv()

    saida = []
    for p in produtos:
        alvo = f"{p.get('nome', '')} {p.get('marca', '')}"
        melhor, linha_melhor, desempate = 0.0, None, 0.0
        for ln in candidatos(alvo, linhas, indice):
            s = melhor_match(p.get("nome"), ln.get("NO_PRODUTO"), ln.get("NO_RAZAO_SOCIAL_EMPRESA"), p.get("marca"))
            d = SequenceMatcher(None, norm(p.get("nome")), norm(ln.get("NO_PRODUTO"))).ratio()
            if s > melhor or (s == melhor and d > desempate):
                melhor, linha_melhor, desempate = s, ln, d
        item = {
            "id": p["id"], "nome": p.get("nome"), "marca": p.get("marca"),
            "plataforma": p.get("plataforma"),
            "conferido_em": hoje,
        }
        if melhor >= LIMIAR and linha_melhor is not None:
            item["registro"] = {
                "encontrado": True,
                "confianca": "forte" if melhor >= 0.85 else "provavel",
                "similaridade": round(melhor, 2),
                "nome_anvisa": linha_melhor.get("NO_PRODUTO"),
                "empresa": linha_melhor.get("NO_RAZAO_SOCIAL_EMPRESA"),
                "nu_processo": linha_melhor.get("NU_PROCESSO"),
                "situacao": linha_melhor.get("ST_SITUACAO_PRODUTO"),
                "tipo_peticao": linha_melhor.get("DS_TIPO_PETICAO"),
                "nu_registro": linha_melhor.get("NU_REGISTRO"),
                "atualizado_em": linha_melhor.get("DT_ATUALIZACAO"),
            }
            print(f"  MATCH {p['id']} [{item['registro']['confianca']}]: {melhor:.2f} → {linha_melhor.get('NO_PRODUTO')}")
        else:
            item["registro"] = {"encontrado": False, "similaridade": round(melhor, 2)}
            print(f"  sem match {p['id']} (melhor similaridade {melhor:.2f})")
        saida.append(item)

    doc = {
        "verificado_em": hoje,
        "fonte_url": URL_CSV,
        "fonte_nota": ("Dados abertos da ANVISA — cosméticos regularizados/notificados. "
                       "'Não encontrado' não prova irregularidade: confira no portal oficial "
                       "https://consultas.anvisa.gov.br/"),
        "produtos": saida,
    }
    if not so_check:
        SAIDA.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print("gravado:", SAIDA)
    else:
        print("(--check: nada gravado)")


if __name__ == "__main__":
    main()
