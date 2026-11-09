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
import sys
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

# Explicit local import also works with the documented python -I invocation.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from schema_site import montar_schema, json_script

from PIL import Image, ImageDraw, ImageFont, ImageOps

RAIZ = Path(__file__).resolve().parent.parent
SITE = "https://produtoskincare.com.br"
MARCA = "Produto Skincare"
HOJE = date.today().isoformat()
IGNORAR = {"_arquivo", "_scripts", "_servidor", ".git", "fotos", "fonts", "img", "icones"}
ROTULOS = {"blog": "Blog", "ingredientes": "Ingredientes", "condicoes": "Condições", "pele": "Tipos de pele",
           "ferramentas": "Ferramentas", "achados": "Achados", "provador": "Provador", "sobre": "Sobre",
           "privacidade": "Privacidade", "pergunte": "Pergunte à IA", "mais-vendidos": "Mais vendidos",
           "rotina-de-skincare": "Rotina de skincare", "fortskin": "FortSkin", "en": "English", "es": "Español",
           "contato": "Contato", "produtos": "Produtos", "comparativos": "Comparativos", "combina": "Posso usar junto?"}
# Páginas com versão em outro idioma (hreflang). Os guias traduzidos ficam em _scripts/traducoes.json.
TRADUCOES = [{"pt-BR": "/", "en": "/en/", "es": "/es/"}] + [
    g for g in json.loads((RAIZ / "_scripts" / "traducoes.json").read_text(encoding="utf-8"))["grupos"]]
SECOES_ARTIGO = ("blog/", "en/blog/", "es/blog/", "ingredientes/", "en/ingredients/", "es/ingredientes/", "condicoes/", "pele/", "rotina-de-skincare/")


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

    ld = montar_schema(RAIZ, SITE, MARCA, url, info, texto, artigo)
    tags.append('<script type="application/ld+json">' + json_script(ld) + "</script>")
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
