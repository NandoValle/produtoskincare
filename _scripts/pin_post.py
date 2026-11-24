"""Gera a versão vertical (1000x1500, 2:3) da capa de cada post do blog, para o Pinterest.

Uso (na raiz do site):
    python -I _scripts/pin_post.py              # todos os posts que têm capa
    python -I _scripts/pin_post.py --slug <slug>

O que faz:
  1. Recorta o centro da capa 16:9 (img/blog/<slug>-3840.webp ou -1600.webp) para o topo do pin.
  2. Embaixo, um painel creme com a etiqueta do post, o título e o endereço do blog.
  3. Grava img/pin/<slug>.jpg.
  4. No blog/<slug>/index.html, logo abaixo da capa, põe o link "Salvar no Pinterest",
     que abre o Pinterest já com este pin, o endereço e o título do post.

Rodar de novo refaz a imagem e o link. Post sem capa é pulado (a capa vem do capa_post.py).
"""
import argparse
import html
import re
import urllib.parse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parent.parent
SITE = "https://produtoskincare.com.br"
W, H, FOTO = 1000, 1500, 900          # pin 2:3; a foto ocupa os 900 px de cima
M = 64                                # margem lateral do painel
COR = {"fundo": "#F7F2EC", "tinta": "#17120E", "suave": "#5A4C41", "ouro": "#755728", "ouro_claro": "#F1E7D6"}
DISPLAY = RAIZ / "fonts" / "cormorant-500.ttf"
CORPO = RAIZ / "fonts" / "manrope-600.ttf"
LNUM = ["lnum"]                       # algarismos alinhados: no Cormorant o "1" antigo parece "I"

INICIO, FIM = "<!-- pin:inicio -->", "<!-- pin:fim -->"
BLOCO_RE = re.compile(r"\n?" + re.escape(INICIO) + r".*?" + re.escape(FIM), re.S)
CSS_PIN = ".pin-salvar{margin:-14px 0 24px;font-size:.88rem}.pin-salvar a{color:var(--suave)}"


def fonte(caminho, tamanho):
    return ImageFont.truetype(str(caminho), tamanho, layout_engine=ImageFont.Layout.RAQM)


def quebrar(draw, texto, f, largura, features=None):
    linhas, atual = [], ""
    for palavra in texto.split():
        tentativa = f"{atual} {palavra}".strip()
        if draw.textlength(tentativa, font=f, features=features) <= largura or not atual:
            atual = tentativa
        else:
            linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas


def recorte(im, largura, altura):
    """Recorta o centro na proporção pedida e redimensiona."""
    w, h = im.size
    if w * altura > h * largura:
        nw = round(h * largura / altura)
        x = (w - nw) // 2
        im = im.crop((x, 0, x + nw, h))
    else:
        nh = round(w * altura / largura)
        y = (h - nh) // 2
        im = im.crop((0, y, w, y + nh))
    return im.resize((largura, altura), Image.LANCZOS)


def desenhar(capa, titulo, etiqueta):
    pin = Image.new("RGB", (W, H), COR["fundo"])
    pin.paste(recorte(capa.convert("RGB"), W, FOTO), (0, 0))
    d = ImageDraw.Draw(pin)
    y = FOTO + 52

    if etiqueta:
        f = fonte(CORPO, 26)
        txt = etiqueta.upper()
        larg = d.textlength(txt, font=f) + 44
        d.rounded_rectangle((M, y, M + larg, y + 50), radius=25, fill=COR["ouro_claro"])
        d.text((M + 22, y + 25), txt, font=f, fill=COR["ouro"], anchor="lm")
        y += 78

    # Título: o maior corpo que cabe no espaço entre a etiqueta e o endereço.
    limite = H - 150 - y
    for tam in range(78, 37, -2):
        f = fonte(DISPLAY, tam)
        linhas = quebrar(d, titulo, f, W - 2 * M, LNUM)
        passo = round(tam * 1.08)
        if len(linhas) * passo <= limite:
            break
    for linha in linhas:
        d.text((M, y), linha, font=f, fill=COR["tinta"], features=LNUM)
        y += passo

    # Endereço
    f = fonte(CORPO, 30)
    d.rounded_rectangle((M, H - 118, W - M, H - 46), radius=36, fill=COR["ouro"])
    d.text((W // 2, H - 82), "produtoskincare.com.br/blog", font=f, fill="#ffffff", anchor="mm")
    return pin


def dados_do_post(slug):
    pagina = (RAIZ / "blog" / slug / "index.html").read_text(encoding="utf-8")
    m = re.search(r"<h1[^>]*>(.*?)</h1>", pagina, re.S)
    titulo = html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else slug
    indice = (RAIZ / "blog" / "index.html").read_text(encoding="utf-8")
    # A etiqueta fica dentro do cartão do post, depois do link.
    m = re.search(r'<a class="artigo" href="/blog/' + re.escape(slug) + r'/">(.*?)</a>', indice, re.S)
    tag = re.search(r'<span class="tag">([^<]*)</span>', m.group(1)) if m else None
    etiqueta = html.unescape(tag.group(1)).split("·")[0].strip() if tag else ""
    return titulo, etiqueta


def link_no_post(slug, titulo):
    caminho = RAIZ / "blog" / slug / "index.html"
    t = caminho.read_text(encoding="utf-8")
    t = BLOCO_RE.sub("", t)
    q = urllib.parse.urlencode({"url": f"{SITE}/blog/{slug}/", "media": f"{SITE}/img/pin/{slug}.jpg", "description": titulo})
    bloco = (f'\n{INICIO}<p class="pin-salvar"><a href="https://www.pinterest.com/pin/create/button/?{html.escape(q)}" '
             f'target="_blank" rel="noopener" data-pin-do="none">Salvar no Pinterest</a></p>{FIM}')
    m = re.search(r'<figure class="capa-artigo">.*?</figure>', t, re.S)
    if not m:
        return False
    t = t[:m.end()] + bloco + t[m.end():]
    if ".pin-salvar{" not in t:
        t = t.replace(".capa-artigo{", CSS_PIN + ".capa-artigo{", 1)
    caminho.write_text(t, encoding="utf-8")
    return True


def gerar(slug):
    capa = next((p for p in (RAIZ / "img" / "blog" / f"{slug}-{n}.webp" for n in (3840, 1600)) if p.exists()), None)
    if not capa:
        print(f"pulei (sem capa): {slug}")
        return False
    titulo, etiqueta = dados_do_post(slug)
    destino = RAIZ / "img" / "pin" / f"{slug}.jpg"
    destino.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(capa) as im:
        desenhar(im, titulo, etiqueta).save(destino, "JPEG", quality=88, optimize=True, progressive=True)
    ligado = link_no_post(slug, titulo)
    print(f"{slug}: img/pin/{slug}.jpg" + ("" if ligado else " (sem link: post sem <figure class=\"capa-artigo\">)"))
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--slug")
    a = ap.parse_args()
    slugs = [a.slug] if a.slug else sorted(p.parent.name for p in (RAIZ / "blog").glob("*/index.html"))
    feitos = sum(gerar(s) for s in slugs)
    print(f"{feitos} pin(s) gerado(s)")


if __name__ == "__main__":
    main()
