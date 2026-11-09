"""Põe a capa (foto 16:9) num post do blog.

Uso (na raiz do site):
    python -I _scripts/capa_post.py --slug <slug> --img <original.png> --alt "descrição da imagem"
    python -I _scripts/seo.py          # depois, para o JSON-LD do artigo apontar para a capa

O que faz:
  1. Recorta a imagem no centro para 16:9.
  2. Gera img/blog/<slug>-3840.webp (mestre 4K), -1600.webp, -800.webp e -og.jpg (1200x675).
     O 3840 sai do 4x-UltraSharp quando o ampliador local existe (ver AMPLIADOR abaixo);
     sem ele, cai para Lanczos e avisa.
  3. No blog/<slug>/index.html: CSS .capa-artigo, <figure class="capa-artigo"> logo abaixo da
     linha "Publicado em" e og:image apontando para o -og.jpg.
  4. No blog/index.html: <img class="capa"> no cartão do post. Só o 1º cartão da lista
     fica com fetchpriority="high"; os outros ficam com loading="lazy".

Rodar de novo com o mesmo slug substitui a capa (os arquivos e o HTML).
Prompts e estilo das capas: _roteiros/capas.txt.
"""
import argparse
import html
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
SITE = "https://produtoskincare.com.br"

# Ampliador local (PC do Fernando): python do ComfyUI + script do 4x-UltraSharp.
# Pode ser trocado pelas variáveis CAPA_PY e CAPA_UPSCALE.
AMPLIADOR_PY = os.environ.get("CAPA_PY", r"E:\DoC\ComfyUI\venv\Scripts\python.exe")
AMPLIADOR = os.environ.get("CAPA_UPSCALE", r"E:\Xiaomimimo\originais-chatgpt\upscale_8k.py")

TAMANHOS = ((3840, 84), (1600, 84), (800, 82))  # (largura, qualidade WebP)
SIZES = "(max-width: 736px) calc(100vw - 36px), 700px"
CSS_CAPA = (".capa-artigo{margin:22px 0 28px}.capa-artigo img{display:block;width:100%;height:auto;"
            "aspect-ratio:16/9;object-fit:cover;border-radius:var(--raio);background:var(--rosa-claro)}")


def recorte_16x9(im: Image.Image) -> Image.Image:
    w, h = im.size
    if w * 9 > h * 16:          # larga demais: corta as laterais
        nw = round(h * 16 / 9)
        x = (w - nw) // 2
        return im.crop((x, 0, x + nw, h))
    nh = round(w * 9 / 16)       # alta demais: corta em cima e embaixo
    y = (h - nh) // 2
    return im.crop((0, y, w, y + nh))


def mestre_4k(im: Image.Image) -> tuple[Image.Image, str]:
    if Path(AMPLIADOR_PY).exists() and Path(AMPLIADOR).exists():
        with tempfile.TemporaryDirectory() as tmp:
            ent, sai = Path(tmp) / "ent.png", Path(tmp) / "sai.png"
            im.save(ent)
            r = subprocess.run([AMPLIADOR_PY, AMPLIADOR, str(ent), str(sai), "3840", "2160"],
                               capture_output=True, text=True)
            if r.returncode == 0 and sai.exists():
                return Image.open(sai).convert("RGB").copy(), "4x-UltraSharp"
            print("AVISO: o ampliador falhou, usando Lanczos.\n" + r.stderr[-800:], file=sys.stderr)
    else:
        print("AVISO: ampliador local não encontrado, usando Lanczos.", file=sys.stderr)
    return im.resize((3840, 2160), Image.LANCZOS), "Lanczos"


def gerar_arquivos(slug: str, origem: Path, mestre_dir: Path | None) -> str:
    im = recorte_16x9(Image.open(origem).convert("RGB"))
    big, metodo = mestre_4k(im)
    if mestre_dir:  # cópia sem perdas do 4K, fora do site
        mestre_dir.mkdir(parents=True, exist_ok=True)
        big.save(mestre_dir / f"{slug}-3840.png", optimize=True)
    pasta = RAIZ / "img/blog"
    pasta.mkdir(parents=True, exist_ok=True)
    for largura, q in TAMANHOS:
        alvo = big if largura == 3840 else big.resize((largura, largura * 9 // 16), Image.LANCZOS)
        alvo.save(pasta / f"{slug}-{largura}.webp", "WEBP", quality=q, method=6)
    big.resize((1200, 675), Image.LANCZOS).save(pasta / f"{slug}-og.jpg", "JPEG", quality=85,
                                                 optimize=True, progressive=True)
    return metodo


def tag_img(slug: str, alt: str, classe: str, prioridade: str) -> str:
    base = f"/img/blog/{slug}"
    srcset = ", ".join(f"{base}-{l}.webp {l}w" for l in (800, 1600, 3840))
    cls = f' class="{classe}"' if classe else ""
    return (f'<img{cls} src="{base}-1600.webp" srcset="{srcset}" sizes="{SIZES}" width="1600" '
            f'height="900" alt="{html.escape(alt, quote=True)}" {prioridade} decoding="async">')


def trocar_meta(texto: str, prop: str, valor: str) -> str:
    padrao = rf'<meta property="{re.escape(prop)}" content="[^"]*">'
    novo = f'<meta property="{prop}" content="{html.escape(valor, quote=True)}">'
    if re.search(padrao, texto):
        return re.sub(padrao, lambda m: novo, texto, count=1)
    return texto.replace("<!-- seo:inicio -->\n", f"<!-- seo:inicio -->\n{novo}\n", 1)


def patch_post(slug: str, alt: str) -> None:
    arq = RAIZ / "blog" / slug / "index.html"
    texto = arq.read_text(encoding="utf-8")
    if ".capa-artigo{" not in texto:
        texto = texto.replace("</style>", CSS_CAPA + "\n</style>", 1)
    img = tag_img(slug, alt, "", 'fetchpriority="high"')
    figura = f'<figure class="capa-artigo">{img}</figure>'
    if '<figure class="capa-artigo">' in texto:
        texto = re.sub(r'<figure class="capa-artigo">.*?</figure>', lambda m: figura, texto, count=1, flags=re.S)
    else:
        m = re.search(r"<h1[^>]*>.*?</h1>\s*(?:<p class=\"ig-meta\">.*?</p>\s*)?(?:<p class=\"sub\">.*?</p>)?",
                      texto, flags=re.S)
        if not m:
            sys.exit(f"ERRO: não achei o <h1> em {arq}")
        texto = texto[:m.end()] + "\n" + figura + texto[m.end():]
    texto = trocar_meta(texto, "og:image", f"{SITE}/img/blog/{slug}-og.jpg")
    texto = trocar_meta(texto, "og:image:width", "1200")
    texto = trocar_meta(texto, "og:image:height", "675")
    texto = trocar_meta(texto, "og:image:alt", alt)
    arq.write_text(texto, encoding="utf-8", newline="\n")


def patch_indice(slug: str, alt: str) -> None:
    arq = RAIZ / "blog/index.html"
    texto = arq.read_text(encoding="utf-8")
    abre = f'<a class="artigo" href="/blog/{slug}/">'
    if abre not in texto:
        print(f"AVISO: o cartão de /blog/{slug}/ não está em blog/index.html", file=sys.stderr)
        return
    ini = texto.index(abre) + len(abre)
    resto = texto[ini:]
    resto = re.sub(r'^\n<img class="capa"[^>]*>', "", resto, count=1)
    texto = texto[:ini] + "\n" + tag_img(slug, alt, "capa", 'loading="lazy"') + resto
    # Só a primeira capa da lista carrega com prioridade.
    contador = iter(range(10_000))

    def prioridade(m: re.Match) -> str:
        tag = re.sub(r'\s(?:fetchpriority="high"|loading="lazy")', "", m.group(0))
        extra = 'fetchpriority="high"' if next(contador) == 0 else 'loading="lazy"'
        return tag.replace(' decoding="async"', f' {extra} decoding="async"')

    texto = re.sub(r'<img class="capa"[^>]*>', prioridade, texto)
    arq.write_text(texto, encoding="utf-8", newline="\n")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--slug", required=True)
    ap.add_argument("--img", required=True, type=Path)
    ap.add_argument("--alt", required=True)
    ap.add_argument("--mestre", type=Path, help="pasta para guardar o 4K em PNG (backup, fora do site)")
    a = ap.parse_args()
    if not (RAIZ / "blog" / a.slug / "index.html").exists():
        sys.exit(f"ERRO: blog/{a.slug}/index.html não existe")
    metodo = gerar_arquivos(a.slug, a.img, a.mestre)
    patch_post(a.slug, a.alt)
    patch_indice(a.slug, a.alt)
    tamanhos = ", ".join(f"{p.name} {p.stat().st_size // 1024} KB"
                         for p in sorted((RAIZ / "img/blog").glob(f"{a.slug}-*")))
    print(f"{a.slug}: mestre por {metodo}; {tamanhos}")


if __name__ == "__main__":
    main()
