"""Gera /blog/feed.xml (RSS 2.0) a partir do que já está publicado no blog.

    python -I _scripts/gerar_feed.py

Rode depois de publicar ou alterar um post. Idempotente: sem mudança no blog, o arquivo sai igual.

De onde vem cada dado (nada é inventado):
- a lista e a ordem dos posts: os cartões <a class="artigo"> de blog/index.html, de cima para baixo;
- o resumo: o <p> do cartão;
- o título: o <h2> do cartão;
- a data: "datePublished" do JSON-LD do post; se faltar, "dateModified"; se faltar, o primeiro
  <time datetime>. Post sem nenhuma data interrompe o script;
- a imagem: a og:image do post.

O RSS pede data com hora. Os posts só têm o dia, então a hora sai como 00:00 GMT.
Só usa a biblioteca padrão.
"""
import html
import re
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SITE = "https://produtoskincare.com.br"
FEED = RAIZ / "blog/feed.xml"
TITULO = "Blog Produto Skincare"
DESCRICAO = "Artigos sobre skincare: tipos de pele, ativos, protetor solar, notícias e mitos explicados."

CARTAO = re.compile(r'<a class="artigo" href="(/blog/[^"]+/)">(.*?)</a>', re.S)


def texto(trecho):
    """Tira as tags e desfaz as entidades; devolve texto puro."""
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", trecho))).strip()


def data_do_post(pagina, url):
    for padrao in (r'"datePublished":\s*"(\d{4}-\d{2}-\d{2})', r'"dateModified":\s*"(\d{4}-\d{2}-\d{2})',
                   r'<time datetime="(\d{4}-\d{2}-\d{2})'):
        m = re.search(padrao, pagina)
        if m:
            return datetime.strptime(m.group(1), "%Y-%m-%d").replace(tzinfo=timezone.utc)
    raise SystemExit(f"post sem data: {url}")


def main():
    indice = (RAIZ / "blog/index.html").read_text(encoding="utf-8-sig")
    itens = []
    for url, miolo in CARTAO.findall(indice):
        arq = RAIZ / url.strip("/") / "index.html"
        if not arq.exists():
            raise SystemExit(f"cartão aponta para página que não existe: {url}")
        pagina = arq.read_text(encoding="utf-8-sig")
        h2 = re.search(r"<h2[^>]*>(.*?)</h2>", miolo, re.S)
        p = re.search(r"<p[^>]*>(.*?)</p>", miolo, re.S)
        if not h2:
            raise SystemExit(f"cartão sem <h2>: {url}")
        og = re.search(r'<meta property="og:image" content="([^"]+)"', pagina)
        itens.append({"url": SITE + url, "titulo": texto(h2.group(1)), "resumo": texto(p.group(1)) if p else "",
                      "data": data_do_post(pagina, url), "imagem": og.group(1) if og else ""})
    if not itens:
        raise SystemExit("nenhum cartão de post encontrado em blog/index.html")

    esc = lambda s: html.escape(s, quote=False)
    linhas = ['<?xml version="1.0" encoding="UTF-8"?>',
              '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:media="http://search.yahoo.com/mrss/">',
              "<channel>",
              f"<title>{esc(TITULO)}</title>",
              f"<link>{SITE}/blog/</link>",
              f"<description>{esc(DESCRICAO)}</description>",
              "<language>pt-BR</language>",
              f'<atom:link href="{SITE}/blog/feed.xml" rel="self" type="application/rss+xml"/>',
              f"<lastBuildDate>{format_datetime(max(i['data'] for i in itens), usegmt=True)}</lastBuildDate>"]
    for i in itens:
        linhas += ["<item>",
                   f"<title>{esc(i['titulo'])}</title>",
                   f"<link>{i['url']}</link>",
                   f'<guid isPermaLink="true">{i["url"]}</guid>',
                   f"<pubDate>{format_datetime(i['data'], usegmt=True)}</pubDate>"]
        if i["resumo"]:
            linhas.append(f"<description>{esc(i['resumo'])}</description>")
        if i["imagem"]:
            linhas.append(f'<media:content url="{html.escape(i["imagem"])}" medium="image"/>')
        linhas.append("</item>")
    linhas += ["</channel>", "</rss>"]
    FEED.write_bytes(("\n".join(linhas) + "\n").encode("utf-8"))
    print(f"{len(itens)} posts em {FEED.relative_to(RAIZ).as_posix()}")


if __name__ == "__main__":
    main()
