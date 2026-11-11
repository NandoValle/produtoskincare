"""Vídeo "a notícia em 1 minuto" de um post do blog: quadros nas cores do site + narração.

Entrada:
  _roteiros/<slug>.txt            roteiro da narração (o texto falado, depois das 2 linhas de cabeçalho)
  _roteiros/<slug>.quadros.json   etiqueta e quadros: {"etiqueta": "...", "quadros": [
                                    {"inicio": "primeiras palavras faladas", "titulo": "...", "texto": "..."}]}
                                  O último quadro sai com o título em rosa ("Leia o artigo completo").
  --audio    narração em MP3 (ex.: ElevenLabs)
  --palavras transcrição com o tempo de cada palavra (JSON com "words": [{"text","start","end"}])

Saída, em blog/<slug>/:
  video.mp4      720x1280, H.264 + AAC, faststart
  poster.jpg     o primeiro quadro
  legendas.vtt   legendas sincronizadas pelos tempos das palavras

Cada quadro entra quando a narração chega às palavras de "inicio" e fica até o próximo.
Uso: python3 _scripts/video_noticia.py <slug> --audio narracao.mp3 --palavras words.json
"""
import argparse
import json
import re
import shutil
import subprocess
import tempfile
import unicodedata
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

RAIZ = Path(__file__).resolve().parent.parent
L, A = 720, 1280
MARGEM = 64
FUNDO = (248, 244, 241)
TINTA = (26, 22, 20)
SUAVE = (107, 96, 88)
RODAPE = (122, 110, 101)
ROSA = (180, 84, 106)
ROSA_CLARO = (251, 233, 237)
TRILHO = (228, 221, 217)


def fonte(candidatas, tamanho):
    for c in candidatas:
        p = Path(c)
        if p.exists():
            return ImageFont.truetype(str(p), tamanho)
    raise SystemExit(f"nenhuma fonte encontrada entre: {candidatas}")


SERIFA = ["/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
          "C:/Windows/Fonts/times.ttf", str(RAIZ / "fonts/cormorant-500.ttf")]
SANS = ["/usr/share/fonts/opentype/inter/Inter-Regular.otf", "C:/Windows/Fonts/segoeui.ttf",
        str(RAIZ / "fonts/manrope-400.ttf")]
SANS_FORTE = ["/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", "C:/Windows/Fonts/seguisb.ttf",
              str(RAIZ / "fonts/manrope-600.ttf")]


def fundo():
    """Creme com duas manchas rosadas desfocadas (alto à direita, baixo à esquerda)."""
    y, x = np.mgrid[0:A, 0:L].astype(np.float32)
    img = np.ones((A, L, 3), np.float32) * np.array(FUNDO, np.float32)
    for cx, cy, r, forca in ((640, 120, 300, 0.55), (30, 1230, 280, 0.35)):
        peso = np.exp(-(((x - cx) ** 2 + (y - cy) ** 2) / (r ** 2))) * forca
        img = img * (1 - peso[..., None]) + np.array((238, 212, 217), np.float32) * peso[..., None]
    return Image.fromarray(img.clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2))


def quebrar(d, texto, f, largura):
    linhas, atual = [], ""
    for p in texto.split():
        teste = (atual + " " + p).strip()
        if d.textlength(teste, font=f) <= largura or not atual:
            atual = teste
        else:
            linhas.append(atual)
            atual = p
    if atual:
        linhas.append(atual)
    return linhas


def equilibrar(d, texto, f, largura):
    """Mesmo número de linhas da quebra simples, mas com linhas de tamanho parecido (sem palavra sozinha)."""
    linhas = quebrar(d, texto, f, largura)
    if len(linhas) < 2:
        return linhas
    lo, hi = largura // 3, largura
    while lo < hi:
        meio = (lo + hi) // 2
        if len(quebrar(d, texto, f, meio)) <= len(linhas):
            hi = meio
        else:
            lo = meio + 1
    return quebrar(d, texto, f, lo)


def quadro(base, etiqueta, titulo, texto, i, n, destaque):
    img = base.copy()
    d = ImageDraw.Draw(img)
    # marca
    f_marca = fonte(SERIFA, 30)
    d.text((MARGEM, 76), "Produto ", font=f_marca, fill=TINTA)
    d.text((MARGEM + d.textlength("Produto ", font=f_marca), 76), "Skincare", font=f_marca, fill=ROSA)
    # etiqueta
    f_tag = fonte(SANS_FORTE, 19)
    w = d.textlength(etiqueta, font=f_tag)
    d.rounded_rectangle((MARGEM, 128, MARGEM + w + 36, 164), radius=18, fill=ROSA_CLARO)
    d.text((MARGEM + 18, 133), etiqueta, font=f_tag, fill=ROSA)
    # título e texto, centrados na altura
    largura = L - 2 * MARGEM
    tam = 66
    while True:
        f_tit = fonte(SERIFA, tam)
        l_tit = equilibrar(d, titulo, f_tit, largura)
        if len(l_tit) <= 4 or tam <= 44:
            break
        tam -= 4
    f_txt = fonte(SANS, 29)
    l_txt = equilibrar(d, texto, f_txt, largura) if texto else []
    alt_tit, alt_txt = int(tam * 1.2), 44
    bloco = 4 + 44 + alt_tit * len(l_tit) + (28 + alt_txt * len(l_txt) if l_txt else 0)
    y = max(240, 650 - bloco // 2)
    d.rectangle((MARGEM, y, MARGEM + 64, y + 4), fill=ROSA)
    y += 4 + 44
    for linha in l_tit:
        d.text((MARGEM, y), linha, font=f_tit, fill=ROSA if destaque else TINTA)
        y += alt_tit
    y += 28
    for linha in l_txt:
        d.text((MARGEM, y), linha, font=f_txt, fill=SUAVE)
        y += alt_txt
    # rodapé e progresso
    d.text((MARGEM, 1140), "produtoskincare.com.br/blog", font=fonte(SANS, 21), fill=RODAPE)
    vao = 10
    seg = (L - 2 * MARGEM - vao * (n - 1)) / n
    for k in range(n):
        x0 = MARGEM + k * (seg + vao)
        d.rectangle((round(x0), 1195, round(x0 + seg), 1199), fill=ROSA if k <= i else TRILHO)
    return img


def normal(p):
    p = unicodedata.normalize("NFKD", p.lower())
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in p if not unicodedata.combining(c)))


def achar_inicio(palavras, frase, a_partir):
    alvo = [normal(p) for p in frase.split() if normal(p)]
    chaves = [normal(w["text"]) for w in palavras]
    for k in range(a_partir, len(chaves) - len(alvo) + 1):
        if chaves[k:k + len(alvo)] == alvo:
            return k
    raise SystemExit(f"não achei na narração o início de quadro: {frase!r}")


def tempo_vtt(s):
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}"


def legendas(palavras):
    """Cues por frase ou trecho entre vírgulas; trechos curtos se juntam e os longos se dividem por igual."""
    trechos, atual = [], []
    for w in palavras:
        atual.append(w)
        if w["text"][-1] in ".?!…,:;":
            trechos.append(atual)
            atual = []
    if atual:
        trechos.append(atual)
    texto = lambda ws: " ".join(x["text"] for x in ws)
    juntos = []
    for tr in trechos:
        if juntos and juntos[-1][-1]["text"][-1] not in ".?!…" and len(texto(juntos[-1] + tr)) <= 44:
            juntos[-1] = juntos[-1] + tr
        else:
            juntos.append(tr)
    cues = []
    for tr in juntos:
        partes = -(-len(texto(tr)) // 64)
        if partes <= 1:
            cues.append(tr)
            continue
        alvo, atual = len(texto(tr)) / partes, []
        for w in tr:
            atual.append(w)
            if len(texto(atual)) >= alvo:
                cues.append(atual)
                atual = []
        if atual:
            if len(texto(atual)) < 14 and cues:
                cues[-1] = cues[-1] + atual
            else:
                cues.append(atual)
    linhas = ["WEBVTT", ""]
    for n, c in enumerate(cues, 1):
        texto = " ".join(x["text"] for x in c)
        if len(texto) > 36:  # duas linhas equilibradas
            ps, melhor = texto.split(), None
            for k in range(1, len(ps)):
                a, b = " ".join(ps[:k]), " ".join(ps[k:])
                custo = max(len(a), len(b))
                if melhor is None or custo < melhor[0]:
                    melhor = (custo, a + "\n" + b)
            texto = melhor[1]
        linhas += [str(n), f"{tempo_vtt(c[0]['start'])} --> {tempo_vtt(c[-1]['end'])}", texto, ""]
    return "\n".join(linhas)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slug")
    ap.add_argument("--audio", required=True)
    ap.add_argument("--palavras", required=True)
    args = ap.parse_args()
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg não encontrado no PATH")

    cfg = json.loads((RAIZ / "_roteiros" / f"{args.slug}.quadros.json").read_text(encoding="utf-8"))
    palavras = [w for w in json.loads(Path(args.palavras).read_text(encoding="utf-8"))["words"]
                if w.get("type", "word") == "word"]
    destino = RAIZ / "blog" / args.slug
    if not (destino / "index.html").exists():
        raise SystemExit(f"o post blog/{args.slug}/ não existe")
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                args.audio], capture_output=True, text=True, check=True).stdout)

    quadros = cfg["quadros"]
    inicios, k = [], 0
    for q in quadros:
        k = achar_inicio(palavras, q["inicio"], k)
        inicios.append(0.0 if not inicios else palavras[k]["start"] - 0.15)
    fins = inicios[1:] + [dur + 0.6]

    base = fundo()
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        lista = []
        for i, q in enumerate(quadros):
            img = quadro(base, cfg["etiqueta"], q["titulo"], q.get("texto", ""), i, len(quadros),
                         i == len(quadros) - 1)
            png = tmp / f"q{i:02d}.png"
            img.save(png)
            if i == 0:
                img.convert("RGB").save(destino / "poster.jpg", "JPEG", quality=85, optimize=True, progressive=True)
            lista += [f"file '{png.as_posix()}'", f"duration {fins[i] - inicios[i]:.3f}"]
        lista.append(f"file '{(tmp / f'q{len(quadros) - 1:02d}.png').as_posix()}'")
        (tmp / "lista.txt").write_text("\n".join(lista) + "\n")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(tmp / "lista.txt"),
                        "-i", args.audio, "-map", "0:v", "-map", "1:a",
                        "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-preset", "slow", "-crf", "24",
                        "-tune", "stillimage", "-c:a", "aac", "-b:a", "96k", "-ac", "1",
                        "-af", "apad=pad_dur=0.6", "-t", f"{dur + 0.6:.2f}",
                        "-movflags", "+faststart", "-map_metadata", "-1", str(destino / "video.mp4")], check=True)
    (destino / "legendas.vtt").write_text(legendas(palavras) + "\n", encoding="utf-8")
    total = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                  str(destino / "video.mp4")], capture_output=True, text=True, check=True).stdout)
    mb = (destino / "video.mp4").stat().st_size / 1e6
    print(f"blog/{args.slug}/video.mp4  {total:.1f} s  {mb:.2f} MB  ({len(quadros)} quadros)")
    print(f"duração para o VideoObject: PT{round(total)}S")


if __name__ == "__main__":
    main()
