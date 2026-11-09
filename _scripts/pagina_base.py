"""Casca comum das páginas no estilo dos artigos (classe .ig).

Lê o CSS e o rodapé do artigo-modelo para que as páginas novas fiquem iguais
ao resto do site. Uso:

    from pagina_base import pagina
    html = pagina(titulo=..., descricao=..., caminho="/contato/", trilha=[("/", "Início"), (None, "Contato")],
                  corpo="<article>...</article>")
"""
import html as _html
import re
from pathlib import Path

from menu import bloco as menu_superior

RAIZ = Path(__file__).resolve().parent.parent
MODELO = RAIZ / "blog" / "protetor-solar-pele-oleosa" / "index.html"
SITE = "https://produtoskincare.com.br"


def _pecas():
    t = MODELO.read_text(encoding="utf-8")
    css = re.search(r"<style>(.*?)</style>", t, re.S).group(1)
    rodape = re.search(r'(<footer class="ps-rodape">.*?</footer>)', t, re.S).group(1)
    return css, rodape


def esc(t):
    return _html.escape(str(t or ""), quote=True)


def pagina(titulo, descricao, caminho, trilha, corpo, css_extra="", scripts="", larga=False,
           aviso="Conteúdo informativo, não substitui consulta com dermatologista.", body_attrs=""):
    css, rodape = _pecas()
    rodape = rodape.replace(f'<a href="{caminho}">', f'<a href="{caminho}" aria-current="page">', 1)
    itens = []
    for href, nome in trilha:
        if href:
            itens.append(f'<li><a href="{esc(href)}">{esc(nome)}</a></li>')
        else:
            itens.append(f'<li aria-current="page">{esc(nome)}</li>')
    classe = "ig ig-larga" if larga else "ig"
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(titulo)} | Produto Skincare</title>
<meta name="description" content="{esc(descricao)}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{SITE}{esc(caminho)}">
<link rel="stylesheet" href="/premium.css">
<style>{css}{css_extra}
</style>
<!-- seo:inicio -->
<!-- seo:fim -->
</head>
<body{(' ' + body_attrs) if body_attrs else ''}>
<a class="skip-link" href="#conteudo">Pular para o conteúdo</a>
{menu_superior(caminho)}<main class="{classe}" id="conteudo">
<header class="ig-top">
<a class="ig-marca" href="/">Produto <span>Skincare</span></a>
<nav class="ig-trilha" aria-label="Trilha">
<ol>
{chr(10).join(itens)}
</ol>
</nav>
</header>
{corpo}
<footer class="ig-foot">
<p>{esc(aviso)}</p>
<p><a href="/privacidade/">Privacidade</a> · <a href="/sobre/">Sobre o Produto Skincare</a></p>
</footer>
</main>
{rodape}
{scripts}
</body>
</html>
"""
