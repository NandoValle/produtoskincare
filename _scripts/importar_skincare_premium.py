"""Monta skincare-premium-amazon.json a partir do texto copiado da categoria
Beleza Premium › Skincare Premium da Amazon Brasil (Ctrl+A, Ctrl+C na página de resultados).

    python3 -I _scripts/importar_skincare_premium.py texto-da-pagina.txt [AAAA-MM-DD]

O texto copiado NÃO vai para o repositório: ele traz nome e CEP de quem estava logado.
O texto não traz o código do produto (ASIN). Para ter link direto ao anúncio, preencha
"asin" no JSON; sem ele o botão leva a uma busca pelo nome, e a página diz isso.
"imagem" é o código da foto do anúncio (o trecho depois de /images/I/ no endereço da imagem na Amazon).
Rodar de novo preserva ASIN e imagem já preenchidos (casados por nome + preço cheio).
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "skincare-premium-amazon.json"
TAG = "produtoskincare0f-20"
NODE = "24070135011"

# (marca, termos que a identificam no nome do anúncio). Linhas de produto só entram
# quando outro anúncio da mesma lista traz a marca escrita junto (ex.: "Dermage Photoage").
MARCAS = [
    ("La Roche-Posay", ("la roche-posay", "la roche posay")), ("Mantecorp", ("mantecorp", "episol")),
    ("NeoStrata", ("neostrata", "minesol")), ("Dermage", ("dermage", "photoage", "improve c", "secatriz", "bruma aox")),
    ("Eucerin", ("eucerin",)), ("ISDIN", ("isdin", "acniben")), ("Bioderma", ("bioderma",)), ("Darrow", ("darrow",)),
    ("Avène", ("avène", "avene")), ("CeraVe", ("cerave",)), ("Cetaphil", ("cetaphil",)), ("Vichy", ("vichy",)),
    ("Caudalie", ("caudalie",)), ("Lancôme", ("lancôme", "lancome")), ("Nuxe", ("nuxe",)), ("Clarins", ("clarins",)),
    ("Clinique", ("clinique",)), ("Anna Pegova", ("anna pegova",)), ("medicube", ("medicube",)),
    ("KIKO Milano", ("kiko milano",)), ("CARE Natural Beauty", ("care natural beauty", "skindrops")),
    ("Kohll Beauty", ("kohll",)), ("Shiseido", ("shiseido",)), ("SkinCeuticals", ("skinceuticals",)),
    ("Estée Lauder", ("estée lauder",)), ("Weleda", ("weleda",)), ("Korres", ("korres",)), ("Adcos", ("adcos",)),
    ("Profuse", ("profuse",)), ("Etat Pur", ("etat pur",)), ("Alastin", ("alastin",)), ("ROUND LAB", ("round lab",)),
    ("SKIN1004", ("skin1004",)), ("Steralys", ("steralys",)),
]
# Ordem importa: o primeiro grupo que casar define a categoria.
CATEGORIAS = [
    ("Outros", ("cílios", "lipstick", "teint ", "eau de toilette", "chá ", "shampoo", "capilar", "desodorante")),
    ("Protetor solar", ("protetor sol", "fps", "fotoprotetor", "anthelios")),
    ("Máscara", ("máscara",)),
    ("Limpeza", ("limpeza", "sabonete", "demaquilante", "micelar", "cleanser", "moussant", "esfoliante", "limpador",
                 "mousse nettoyante")),
    ("Sérum", ("sérum", "serum", "soro ")),
    ("Hidratante e tratamento", ("hidratante", "creme", "loção", "gel", "baume", "pomada", "óleo", "clareador",
                                 "água termal", "bruma", "balm", "water", "epidrat", "solução",
                                 "rejuvenescedor")),
]


def num(s):
    return float(s.replace(".", "").replace(",", "."))


def marca_de(nome):
    n = nome.lower()
    for marca, termos in MARCAS:
        if any(t in n for t in termos):
            return marca
    return "Outras marcas"


def categoria_de(nome):
    n = nome.lower() + " "
    for cat, termos in CATEGORIAS:
        if any(t in n for t in termos):
            return cat
    return "Outros"


def ler(caminho):
    linhas = [l.strip().replace("​", "") for l in Path(caminho).read_text(encoding="utf-8").split("\n")]
    fim = next(i for i, l in enumerate(linhas) if re.match(r"Mostrando \d+ resultados", l))
    total = int(re.search(r"\d+", linhas[fim]).group(0))
    # Cada produto abre com o nome duas vezes (a primeira pode vir cortada com "...").
    inicios, i = [], 0
    while i < fim - 1:
        a = linhas[i]
        if a:
            j = i + 1
            if re.match(r"^\+\d+ cores? adiciona", linhas[j]):
                j += 1
            b = linhas[j]
            if (a == b and re.search(r"R\$\d", " ".join(linhas[j + 1:j + 8]))) or (
                    a.endswith("...") and b.startswith(a[:-3].rstrip()[:40])):
                inicios.append(j)
                i = j + 1
                continue
        i += 1
    produtos = []
    for k, j in enumerate(inicios):
        bloco = linhas[j + 1:(inicios[k + 1] - 1 if k + 1 < len(inicios) else fim)]
        nome = re.sub(r"\s+", " ", linhas[j])
        p = {"nome": nome, "marca": marca_de(nome), "categoria": categoria_de(nome), "asin": None}
        for l in bloco:
            m = re.match(r"^(\d,\d)\1 de 5 estrelas \(([^)]+)\)", l)
            if m and "avaliacao" not in p:
                p["avaliacao"], p["reviews"] = num(m.group(1)), m.group(2)
            m = re.match(r"^(Preço, página do produto)?R\$([\d.]+,\d\d)(.*)$", l)
            if m and "preco" not in p:
                p["preco"] = num(m.group(2))
                de = re.search(r"De: R\$ ?([\d.]+,\d\d)", m.group(3)) or (
                    not m.group(1) and re.match(r"^ R\$([\d.]+,\d\d)$", m.group(3)))
                if de:
                    p["preco_de"] = num(de.group(1))
        if "preco" in p:
            produtos.append(p)
    return produtos, total


def main():
    produtos, total = ler(sys.argv[1])
    data = sys.argv[2] if len(sys.argv) > 2 else date.today().isoformat()
    if SAIDA.exists():
        antigos = {(p["nome"], p.get("preco_de")): (p.get("asin"), p.get("imagem"))
                   for p in json.loads(SAIDA.read_text(encoding="utf-8"))["produtos"]}
        for p in produtos:
            p["asin"], p["imagem"] = antigos.get((p["nome"], p.get("preco_de")), (None, None))
    dados = {"atualizado_em": data, "tag_afiliado": TAG, "node": NODE,
             "fonte": "Amazon.com.br — Beleza Premium › Skincare Premium, ordem \"Em destaque\"",
             "total_na_amazon": total, "total": len(produtos), "produtos": produtos}
    SAIDA.write_text(json.dumps(dados, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(produtos)} produtos (a Amazon mostrava {total}) em {SAIDA.name}")


if __name__ == "__main__":
    main()
