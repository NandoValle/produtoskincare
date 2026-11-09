"""Menu superior completo (o mesmo da página inicial) em todas as páginas em português.

Idempotente: o bloco gerado fica entre <!-- menu:inicio --> e <!-- menu:fim -->,
logo depois do <body> (e do link "Pular para o conteúdo", se houver), e é refeito
a cada execução. Rode depois de criar ou mudar páginas:

    python3 _scripts/menu.py

Para mudar os itens do menu, edite PRINCIPAL e MAIS abaixo e rode de novo.
A página inicial e /mercado-skincare-brasil/ já têm o menu escrito à mão e ficam de fora,
assim como /en/ e /es/ (outro idioma) e /fortskin/ (página de outra marca).
"""
import html
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
IGNORAR_PASTAS = {"_arquivo", "_scripts", "_servidor", "_roteiros", ".git", "fotos", "fonts", "img", "icones",
                  "en", "es", "fortskin", "node_modules"}
IGNORAR_PAGINAS = {"index.html", "mercado-skincare-brasil/index.html"}

# (link, texto, seções que marcam o item como atual)
PRINCIPAL = [
    ("/provador/", "Provador", ("provador",)),
    ("/#tipos", "Tipos", ("pele",)),
    ("/rotina-de-skincare/", "Rotina", ("rotina-de-skincare", "rotinas")),
    ("/blog/", "Blog", ("blog",)),
    ("/achados/", "Achados", ("achados", "mais-vendidos", "produtos")),
]
MAIS = [
    ("/condicoes/", "Condições", ("condicoes",)),
    ("/ingredientes/", "Ingredientes", ("ingredientes",)),
    ("/ciencia/", "Ciência", ("ciencia",)),
    ("/ferramentas/ativos/", "Guia de ativos", ()),
    ("/ferramentas/ingredientes/", "Ferramentas", ("ferramentas",)),
    ("/queridinhos-do-skincare/", "Queridinhos", ("queridinhos-do-skincare",)),
    ("/pergunte/", "Pergunte à IA", ("pergunte",)),
]

INICIO, FIM = "<!-- menu:inicio -->", "<!-- menu:fim -->"
BLOCO_RE = re.compile(r"\n?" + re.escape(INICIO) + r".*?" + re.escape(FIM) + r"\n?", re.S)


def _link(href, texto, atual):
    cur = ' aria-current="page"' if atual else ""
    return f'<a href="{href}"{cur}>{html.escape(texto)}</a>'


def bloco(caminho, recuo=False):
    """caminho: '/blog/retinol-como-comecar/'. recuo: o <body> da página já tem margem lateral."""
    secao = caminho.strip("/").split("/")[0]
    exato = lambda href: href == caminho  # noqa: E731

    # A página exata recebe aria-current="page"; o item da seção atual ganha data-secao.
    def item(href, texto, secoes):
        a = _link(href, texto, exato(href))
        if secao in secoes and not exato(href):
            a = a.replace("<a ", '<a data-secao="atual" ', 1)
        return a

    principal = "".join(item(*i) for i in PRINCIPAL)
    mais_aberto = any(secao in s for _, _, s in MAIS)
    mais = "".join(f"<li>{item(*i)}</li>" for i in MAIS)
    classe_mais = ' data-secao="atual"' if mais_aberto else ""
    return (
        f"{INICIO}\n"
        f'<div class="ps-shell ps-topo{" ps-topo-recuo" if recuo else ""}">\n'
        '<header class="ps-header">\n'
        '<a href="/" class="ps-brand"><span class="ps-monogram" aria-hidden="true">PS</span>'
        "<span>Produto <b>Skincare</b></span></a>\n"
        '<button class="ps-menu" type="button" aria-controls="site-navigation" aria-expanded="false" hidden>'
        '<span>Menu</span><span class="ps-menu-lines" aria-hidden="true"></span></button>\n'
        '<div class="ps-navigation" id="site-navigation"><nav class="ps-nav" aria-label="Navegação principal">'
        f'{principal}<details class="ps-mais"><summary class="ps-mais-btn"{classe_mais}>Mais</summary>'
        f'<ul class="ps-mais-panel" id="menu-mais">{mais}</ul></details></nav>\n'
        '<nav class="ps-langs" aria-label="Idioma"><a href="/" lang="pt-BR" aria-label="PT - Português" '
        'aria-current="true">PT</a><a href="/en/" lang="en" aria-label="EN - English">EN</a>'
        '<a href="/es/" lang="es" aria-label="ES - Español">ES</a></nav></div>\n'
        "</header>\n"
        "</div>\n"
        '<script src="/premium.js" defer></script>\n'
        f"{FIM}\n"
    )


def paginas():
    for p in sorted(RAIZ.rglob("index.html")):
        rel = p.relative_to(RAIZ)
        if rel.parts[0] in IGNORAR_PASTAS or str(rel) in IGNORAR_PAGINAS:
            continue
        yield p, "/" + str(rel.parent).replace("\\", "/").strip(".") + "/"


def aplicar(texto, caminho):
    texto = BLOCO_RE.sub("\n", texto, count=1)
    # Página que já carrega o premium.js no <head> não precisa da tag de novo.
    corpo_css = re.search(r"\bbody\{[^}]*\}", texto)
    recuo = bool(corpo_css and re.search(r"padding:\s*0\s+\d", corpo_css.group(0)))
    b = bloco(caminho, recuo)
    if re.search(r'<script[^>]+src="/premium\.js"', texto):
        b = b.replace('<script src="/premium.js" defer></script>\n', "")
    m = re.search(r"<body[^>]*>\n?", texto)
    if not m:
        raise ValueError("sem <body>")
    pos = m.end()
    pulo = re.match(r'[ \t]*<a class="skip-link"[^>]*>.*?</a>\n?', texto[pos:])
    if pulo:
        pos += pulo.end()
    return texto[:pos] + b + texto[pos:]


def main():
    mudou = 0
    for p, caminho in paginas():
        antes = p.read_text(encoding="utf-8")
        if "premium.css" not in antes:
            print(f"pulei (sem premium.css): {caminho}")
            continue
        depois = aplicar(antes, caminho.replace("//", "/"))
        if depois != antes:
            p.write_text(depois, encoding="utf-8")
            mudou += 1
    print(f"menu atualizado em {mudou} páginas")


if __name__ == "__main__":
    main()
