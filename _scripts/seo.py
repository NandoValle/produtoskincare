"""SEO de todas as páginas: canonical, Open Graph com imagem, hreflang, JSON-LD,
script de estatística e sitemap.xml.

Idempotente: o bloco gerado fica entre <!-- seo:inicio --> e <!-- seo:fim -->
e é refeito a cada execução. Rode depois de criar ou mudar páginas:

    python3 _scripts/seo.py

Requer Pillow (pip install pillow) para gerar as imagens de compartilhamento.
"""
import hashlib
import html
import json
import re
import subprocess
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

RAIZ = Path(__file__).resolve().parent.parent
SITE = "https://produtoskincare.com.br"
MARCA = "Produto Skincare"
HOJE = date.today().isoformat()
IGNORAR = {"_arquivo", "_scripts", "_servidor", ".git", "fotos", "fonts", "img", "icones"}
MESES = {m: i + 1 for i, m in enumerate(["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
                                          "agosto", "setembro", "outubro", "novembro", "dezembro"])}
ROTULOS = {"blog": "Blog", "ingredientes": "Ingredientes", "condicoes": "Condições", "pele": "Tipos de pele",
           "ferramentas": "Ferramentas", "achados": "Achados", "provador": "Provador", "sobre": "Sobre",
           "privacidade": "Privacidade", "pergunte": "Pergunte à IA", "mais-vendidos": "Mais vendidos",
           "rotina-de-skincare": "Rotina de skincare", "fortskin": "FortSkin", "en": "English", "es": "Español",
           "contato": "Contato", "produtos": "Produtos", "comparativos": "Comparativos", "combina": "Posso usar junto?"}
# Páginas com versão em outro idioma (hreflang). Os guias traduzidos ficam em _scripts/traducoes.json.
TRADUCOES = [{"pt-BR": "/", "en": "/en/", "es": "/es/"}] + [
    g for g in json.loads((RAIZ / "_scripts" / "traducoes.json").read_text(encoding="utf-8"))["grupos"]]
SECOES_ARTIGO = ("blog/", "en/blog/", "es/blog/", "ingredientes/", "condicoes/", "pele/", "rotina-de-skincare/")


class Leitor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = self.h1 = ""
        self.meta = {}
        self.ld = False
        self._em = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("title", "h1") and not getattr(self, tag):
            self._em = tag
        if tag == "br" and self._em:
            setattr(self, self._em, getattr(self, self._em) + " ")
        if tag == "meta":
            chave = a.get("name") or a.get("property")
            if chave and "content" in a:
                self.meta.setdefault(chave, a["content"])
        if tag == "script" and a.get("type") == "application/ld+json":
            self.ld = True

    def handle_endtag(self, tag):
        if tag == self._em:
            self._em = None

    def handle_data(self, data):
        if self._em:
            setattr(self, self._em, (getattr(self, self._em) + data))


def limpar(t):
    return re.sub(r"\s+", " ", html.unescape(t or "")).strip()


def sem_marca(t):
    return re.sub(r"\s*[|—–-]\s*(Blog )?Produto Skincare\s*$", "", t).strip() or t


def caminho_url(arq: Path):
    rel = arq.relative_to(RAIZ).as_posix()
    return "/" if rel == "index.html" else "/" + rel[: -len("index.html")]


def data_rotulada(rotulo, texto):
    """Data depois de 'Publicado em' / 'Atualizado em', nos dois formatos usados no site:
    '<time datetime="AAAA-MM-DD">4 de novembro de 2026</time>' (vale o atributo) ou
    texto puro '4 de novembro de 2026'."""
    m = re.search(rotulo + r'\s*<time datetime="(\d{4}-\d{2}-\d{2})"', texto)
    if m:
        return m.group(1)
    m = re.search(rotulo + r" (\d{1,2}) de (\w+) de (\d{4})", texto)
    if m and m.group(2).lower() in MESES:
        return f"{m.group(3)}-{MESES[m.group(2).lower()]:02d}-{int(m.group(1)):02d}"
    return None


def data_publicacao(texto):
    return data_rotulada("Publicado em", texto)


def data_atualizacao(texto):
    return data_rotulada("Atualizado em", texto)


# ---------- imagem de compartilhamento (1200x630) ----------
FUNDO = Image.open(RAIZ / "img/skincare-editorial.jpg").convert("RGB")
F_TITULO = RAIZ / "fonts/cormorant-500.ttf"
F_CORPO = RAIZ / "fonts/manrope-600.ttf"


def quebrar(draw, texto, fonte, largura):
    linhas, atual = [], ""
    for palavra in texto.split():
        teste = (atual + " " + palavra).strip()
        if draw.textlength(teste, font=fonte) <= largura:
            atual = teste
        else:
            if atual:
                linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas


def gerar_og(titulo, secao, destino: Path):
    img = Image.new("RGB", (1200, 630), (247, 248, 247))
    img.paste(ImageOps.fit(FUNDO, (460, 630), method=Image.LANCZOS), (740, 0))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, 14, 630), fill=(155, 64, 91))
    pequeno = ImageFont.truetype(str(F_CORPO), 26)
    d.text((72, 64), (secao or MARCA).upper(), font=pequeno, fill=(55, 93, 78))
    tamanho = 76
    while tamanho > 40:
        fonte = ImageFont.truetype(str(F_TITULO), tamanho)
        linhas = quebrar(d, titulo, fonte, 600)
        if len(linhas) <= 4:
            break
        tamanho -= 6
    linhas = linhas[:4]
    y = 140
    for linha in linhas:
        d.text((72, y), linha, font=fonte, fill=(37, 43, 42))
        y += int(tamanho * 1.08)
    d.text((72, 540), "produtoskincare.com.br", font=pequeno, fill=(155, 64, 91))
    destino.parent.mkdir(parents=True, exist_ok=True)
    img.save(destino, "JPEG", quality=78, optimize=True, progressive=True)


ARQ_CACHE_OG = RAIZ / "_scripts/og-cache.json"
CACHE_OG = json.loads(ARQ_CACHE_OG.read_text()) if ARQ_CACHE_OG.exists() else {}


def nome_og(url):
    base = url.strip("/").replace("/", "-") or "inicio"
    return f"img/og/{base}.jpg"


# ---------- dados de produto (schema.org/Product) nas páginas /produtos/<id>/ ----------
_CATALOGO = None
LOJAS_LD = {"amazon": "Amazon", "shopee": "Shopee", "mercadolivre": "Mercado Livre", "tiktok": "TikTok Shop"}


def produto_do_catalogo(rel):
    """Devolve o item do produtos.json se a página for /produtos/<id>/; senão None."""
    global _CATALOGO
    partes = [p for p in rel.split("/") if p]
    if len(partes) != 2 or partes[0] != "produtos":
        return None
    if _CATALOGO is None:
        try:
            _CATALOGO = {p["id"]: p for p in json.loads((RAIZ / "produtos.json").read_text(encoding="utf-8"))["produtos"]}
        except Exception:
            _CATALOGO = {}
    return _CATALOGO.get(partes[1])


def json_ld_produto(p, url, imagem):
    # Só preço, loja e data do catálogo. A nota da loja NÃO entra como aggregateRating:
    # é avaliação de outro site, e as regras do Google pedem avaliações coletadas aqui.
    oferta = {"@type": "Offer", "price": f"{p['preco']:.2f}", "priceCurrency": "BRL",
              "seller": {"@type": "Organization", "name": LOJAS_LD.get(p.get("plataforma"), "Loja")}}
    # Link para a página do produto entra; link para uma busca da loja, não.
    if not re.search(r"/search|/s\?|lista\.mercadolivre", p.get("link", "")):
        oferta["url"] = p["link"]
    frases = [f for f in re.split(r"(?<=[.!?])\s+", p.get("porque", "")) if f.strip() and "★" not in f]
    item = {"@context": "https://schema.org", "@type": "Product", "name": p["nome"],
            "description": " ".join(frases), "image": imagem, "url": f"{SITE}{url}", "offers": oferta}
    if p.get("marca"):
        item["brand"] = {"@type": "Brand", "name": p["marca"]}
    return item


# ---------- bloco de SEO ----------
def montar_bloco(arq, url, info, texto):
    titulo_doc = limpar(info.title)
    og_title = limpar(info.meta.get("og:title")) or sem_marca(titulo_doc)
    descricao = limpar(info.meta.get("description"))
    og_desc = limpar(info.meta.get("og:description")) or descricao
    rel = url.lstrip("/")
    idioma = "en_US" if rel.startswith("en/") else "es_ES" if rel.startswith("es/") else "pt_BR"
    artigo = rel.startswith(SECOES_ARTIGO) and rel.count("/") >= (1 if rel.startswith("rotina-de-skincare/") else 2)
    secao = ROTULOS.get(rel.split("/")[0], MARCA) if rel else MARCA
    titulo_img = sem_marca(limpar(info.h1) or og_title)

    # Se a página define a própria og:image (ex.: capa do post), ela vale; senão geramos uma.
    propria = limpar(info.meta.get("og:image"))
    if propria and "/img/og/" not in propria:
        og_url = propria
        og_w = limpar(info.meta.get("og:image:width")) or "1200"
        og_h = limpar(info.meta.get("og:image:height")) or "630"
        og_alt = limpar(info.meta.get("og:image:alt")) or titulo_img
    else:
        og_path = nome_og(url)
        chave = hashlib.sha1((titulo_img + "|" + secao).encode()).hexdigest()[:10]
        destino = RAIZ / og_path
        if not destino.exists() or CACHE_OG.get(og_path) != chave:
            gerar_og(titulo_img, secao if secao != MARCA else "", destino)
            CACHE_OG[og_path] = chave
        og_url, og_w, og_h, og_alt = f"{SITE}/{og_path}", "1200", "630", titulo_img

    tags = []
    if 'rel="canonical"' not in texto:
        tags.append(f'<link rel="canonical" href="{SITE}{url}">')
    grupo = next((g for g in TRADUCOES if url in g.values()), None)
    if grupo:
        for lang, u in list(grupo.items()) + [("x-default", grupo["pt-BR"])]:
            tags.append(f'<link rel="alternate" hreflang="{lang}" href="{SITE}{u}">')
    e = lambda t: html.escape(t, quote=True)
    tags += [
        f'<meta property="og:type" content="{"article" if artigo else "website"}">',
        f'<meta property="og:title" content="{e(og_title)}">',
        f'<meta property="og:description" content="{e(og_desc)}">' if og_desc else "",
        f'<meta property="og:url" content="{SITE}{url}">',
        f'<meta property="og:site_name" content="{MARCA}">',
        f'<meta property="og:locale" content="{idioma}">',
        f'<meta property="og:image" content="{e(og_url)}">',
        f'<meta property="og:image:width" content="{og_w}">',
        f'<meta property="og:image:height" content="{og_h}">',
        f'<meta property="og:image:alt" content="{e(og_alt)}">',
        '<meta name="twitter:card" content="summary_large_image">',
    ]

    ld = []
    if url == "/":
        # WebPage com autor e data: a data vem da linha visível "Atualizado em <time datetime=...>".
        pagina = {"@type": "WebPage", "@id": SITE + "/#pagina", "url": SITE + "/", "name": titulo_doc,
                  "isPartOf": {"@id": SITE + "/#site"}, "inLanguage": "pt-BR",
                  "author": {"@type": "Organization", "name": "Equipe " + MARCA, "url": SITE + "/sobre/"},
                  "publisher": {"@id": SITE + "/#org"}}
        mod = data_atualizacao(texto)
        if mod:
            pagina["dateModified"] = mod
        ld.append({"@context": "https://schema.org", "@graph": [
            {"@type": "WebSite", "@id": SITE + "/#site", "url": SITE + "/", "name": MARCA, "inLanguage": "pt-BR"},
            {"@type": "Organization", "@id": SITE + "/#org", "name": MARCA, "url": SITE + "/",
             "logo": SITE + "/icones/icon-512.svg"},
            pagina]})
    else:
        itens = [{"@type": "ListItem", "position": 1, "name": "Início", "item": SITE + "/"}]
        partes = [p for p in url.strip("/").split("/") if p]
        acumulado = ""
        for i, parte in enumerate(partes):
            acumulado += parte + "/"
            ultimo = i == len(partes) - 1
            nome = sem_marca(limpar(info.h1) or og_title) if ultimo else ROTULOS.get(parte, parte)
            if not ultimo and not (RAIZ / acumulado / "index.html").exists():
                continue
            itens.append({"@type": "ListItem", "position": len(itens) + 1, "name": nome, "item": f"{SITE}/{acumulado}"})
        ld.append({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": itens})
        produto = produto_do_catalogo(rel)
        if produto:
            ld.append(json_ld_produto(produto, url, og_url))
        if artigo:
            pub = data_publicacao(texto)
            mod = data_atualizacao(texto) or pub
            art = {"@context": "https://schema.org", "@type": "Article", "headline": sem_marca(limpar(info.h1) or og_title)[:110],
                   "description": descricao, "image": og_url, "inLanguage": "pt-BR",
                   "mainEntityOfPage": f"{SITE}{url}",
                   "author": {"@type": "Organization", "name": "Equipe " + MARCA, "url": SITE + "/sobre/"},
                   "publisher": {"@type": "Organization", "name": MARCA, "url": SITE + "/"}}
            if pub:
                art["datePublished"] = pub
            if mod:
                art["dateModified"] = mod
            ld.append(art)
    for bloco in ld:
        tags.append('<script type="application/ld+json">' + json.dumps(bloco, ensure_ascii=False) + "</script>")
    tags.append('<script src="/analytics.js" defer></script>')
    tags.append('<script src="/canais.js" defer></script>')
    return "<!-- seo:inicio -->\n" + "\n".join(t for t in tags if t) + "\n<!-- seo:fim -->\n"


def processar(arq: Path):
    texto = arq.read_text(encoding="utf-8")
    info = Leitor()
    info.feed(texto)  # lê antes de tirar o bloco antigo, para manter og:title/og:description já definidos
    texto = re.sub(r"<!-- seo:inicio -->.*?<!-- seo:fim -->\n?", "", texto, flags=re.S)
    url = caminho_url(arq)
    bloco = montar_bloco(arq, url, info, texto)
    # remove OG/Twitter antigos e linhas em branco que sobraram; o bloco novo os substitui
    texto = re.sub(r'[ \t]*<meta (property="og:[^"]+"|name="twitter:[^"]+")[^>]*>\n?', "", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    if "</head>" not in texto:
        raise SystemExit(f"sem </head>: {arq}")
    texto = texto.replace("</head>", bloco + "</head>", 1)
    arq.write_text(texto, encoding="utf-8")
    robots = info.meta.get("robots", "")
    return url, "noindex" not in robots


def lastmod_antigos():
    p = RAIZ / "sitemap.xml"
    if not p.exists():
        return {}
    s = p.read_text(encoding="utf-8")
    return dict(re.findall(r"<loc>([^<]+)</loc>\s*<lastmod>([^<]+)</lastmod>", s))


def mudou_desde_main(arq: Path):
    try:
        r = subprocess.run(["git", "diff", "--quiet", "origin/main", "--", str(arq.relative_to(RAIZ))], cwd=RAIZ)
        novo = subprocess.run(["git", "cat-file", "-e", "origin/main:" + arq.relative_to(RAIZ).as_posix()],
                              cwd=RAIZ, capture_output=True).returncode != 0
        return r.returncode != 0 or novo
    except Exception:
        return True


def main():
    paginas = sorted((p for p in RAIZ.rglob("index.html")
                      if not (set(p.relative_to(RAIZ).parts[:-1]) & IGNORAR)), key=caminho_url)
    antigos = lastmod_antigos()
    urls = []
    for arq in paginas:
        url, indexar = processar(arq)
        if indexar:
            loc = SITE + url
            urls.append((loc, HOJE if mudou_desde_main(arq) else antigos.get(loc, HOJE), url))
    prioridade = lambda u: "1.0" if u == "/" else "0.9" if u in ("/provador/", "/pergunte/") else "0.8" if u.count("/") <= 2 else "0.7"
    linhas = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, mod, url in urls:
        linhas += ["  <url>", f"    <loc>{loc}</loc>", f"    <lastmod>{mod}</lastmod>",
                   f"    <priority>{prioridade(url)}</priority>", "  </url>"]
    linhas.append("</urlset>")
    (RAIZ / "sitemap.xml").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    ARQ_CACHE_OG.write_text(json.dumps(CACHE_OG, indent=1, sort_keys=True) + "\n")
    print(f"{len(paginas)} páginas processadas, {len(urls)} no sitemap")


if __name__ == "__main__":
    main()
