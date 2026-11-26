"""Vídeo vertical "a notícia em 1 minuto" (1080x1920), uma frase do roteiro por tela.

É o visual dos vídeos dos posts "pele tem sexo" e "Ozempic face": marca e "BLOG · A NOTÍCIA EM 1 MINUTO"
no alto, etiqueta, a frase que está sendo narrada em Cormorant, rodapé com o aviso e uma barra de
progresso que anda com o tempo.

Entrada:
  _roteiros/<slug>.txt   roteiro (o texto falado começa depois das 2 linhas de cabeçalho)
  --audio                a narração (mp3, wav, m4a...), lendo o roteiro do jeito que está escrito
  --etiqueta             texto da etiqueta, ex.: "Saúde · Notícia"

A troca de frase é achada nas pausas do próprio áudio (ffmpeg silencedetect): entre as pausas, fica
a sequência que melhor bate com o tamanho de cada frase. Não precisa de transcrição.

Saída, em blog/<slug>/: video.mp4 (H.264 + AAC, faststart), poster.jpg e legendas.vtt (uma frase por legenda).
Com --nome e --descricao, também põe o vídeo na página (como no post do Ozempic): o CSS .video-wrap, o JSON-LD
VideoObject e a seção "Assista: a notícia em 1 minuto" logo depois do card de resumo, com a narração em texto.
Rodar de novo atualiza esses três blocos em vez de duplicar.

Em post que não é notícia (guia, mito x regra), passar --formato "o guia em 1 minuto": troca a faixa do alto
do vídeo e o título da seção na página.

Uso: python3 _scripts/video_noticia_frases.py <slug> --audio narracao.mp3 --etiqueta "Mercado · Notícia" \\
         --nome "Título: a notícia em 1 minuto" --descricao "Resumo narrado de ..."
"""
import argparse
import datetime
import html
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

RAIZ = Path(__file__).resolve().parent.parent
L, A = 1080, 1920
M = 78                       # margem lateral
LARG = L - 2 * M             # largura útil do texto
FUNDO = (249, 245, 239)
TINTA = (26, 22, 20)
SUAVE = (107, 96, 88)
RODAPE = (122, 110, 101)
ROSA = (180, 84, 106)
ROSA_CLARO = (251, 233, 237)
TRILHO = (228, 221, 217)
BARRA_Y, BARRA_H = 1833, 6
CENTRO_Y = 992               # centro vertical do bloco da frase

SERIFA = RAIZ / "fonts/cormorant-500.ttf"
SANS = RAIZ / "fonts/manrope-400.ttf"
SANS_FORTE = RAIZ / "fonts/manrope-600.ttf"


def fonte(caminho, tamanho):
    return ImageFont.truetype(str(caminho), tamanho)


def fundo():
    """Creme com uma névoa rosada no alto à direita e um tom quente embaixo à esquerda."""
    y, x = np.mgrid[0:A, 0:L].astype(np.float32)
    img = np.ones((A, L, 3), np.float32) * np.array(FUNDO, np.float32)
    for cx, cy, r, forca, cor in ((980, 150, 520, 0.6, (238, 212, 217)),
                                  (40, 1860, 480, 0.4, (240, 226, 214))):
        peso = np.exp(-(((x - cx) ** 2 + (y - cy) ** 2) / (r ** 2))) * forca
        img = img * (1 - peso[..., None]) + np.array(cor, np.float32) * peso[..., None]
    return Image.fromarray(img.clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3))


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


def base_comum(base, etiqueta, formato="a notícia em 1 minuto"):
    """Tudo o que não muda entre as telas: marca, etiqueta, traço, rodapé e o trilho da barra."""
    img = base.copy()
    d = ImageDraw.Draw(img, "RGBA")
    f_marca = fonte(SERIFA, 46)
    d.text((M, 135), "Produto ", font=f_marca, fill=TINTA, anchor="ls")
    d.text((M + d.textlength("Produto ", font=f_marca), 135), "Skincare", font=f_marca, fill=ROSA, anchor="ls")
    d.text((M, 175), "BLOG  ·  " + formato.upper(), font=fonte(SANS, 28), fill=SUAVE, anchor="ls")
    f_tag = fonte(SANS_FORTE, 28)
    w = d.textlength(etiqueta, font=f_tag)
    d.rounded_rectangle((M, 212, M + w + 50, 270), radius=29, fill=ROSA_CLARO + (120,))
    d.text((M + 25, 252), etiqueta, font=f_tag, fill=ROSA, anchor="ls")
    d.rectangle((M, 326, M + 120, 331), fill=ROSA)
    d.text((M, 1772), "produtoskincare.com.br", font=fonte(SANS, 30), fill=RODAPE, anchor="ls")
    d.text((M, 1811), "Conteúdo informativo. Não substitui avaliação médica.", font=fonte(SANS, 26),
           fill=RODAPE, anchor="ls")
    d.rectangle((M, BARRA_Y, L - M, BARRA_Y + BARRA_H - 1), fill=TRILHO)
    return img


def tela(comum, frase):
    img = comum.copy()
    d = ImageDraw.Draw(img)
    tam = 78
    while True:
        f = fonte(SERIFA, tam)
        linhas = quebrar(d, frase, f, LARG)
        if len(linhas) <= 7 or tam <= 58:
            break
        tam -= 4
    passo = round(tam * 1.27)
    # baseline da 1ª linha: bloco centrado em CENTRO_Y (o desenho da letra fica ~0,30 em acima da baseline do meio)
    y = CENTRO_Y - (len(linhas) - 1) * passo / 2 + round(tam * 0.30)
    for linha in linhas:
        d.text((M, round(y)), linha, font=f, fill=TINTA, anchor="ls")
        y += passo
    return img


def frases_do_roteiro(slug):
    texto = (RAIZ / "_roteiros" / f"{slug}.txt").read_text(encoding="utf-8").split("\n", 2)[2]
    texto = " ".join(texto.split())
    # quebra depois de . ? ! quando a próxima palavra começa com maiúscula (as reticências seguidas de
    # minúscula, como em "pessoas... e agora", ficam na mesma frase)
    return [f.strip() for f in re.split(r'(?<=[.?!])\s+(?=["“(]?[A-ZÁÉÍÓÚÂÊÔÃÕÀÇ0-9])', texto) if f.strip()]


def duracao(arq):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                 str(arq)], capture_output=True, text=True, check=True).stdout)


def silencios(audio, minimo=0.15):
    saida = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(audio), "-af",
                            f"silencedetect=noise=-35dB:d={minimo}", "-f", "null", "-"],
                           capture_output=True, text=True).stderr
    ini = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", saida)]
    fim = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", saida)]
    return list(zip(ini, fim))


def alinhar(frases, audio):
    """Devolve (início, fim) de cada frase. Escolhe, entre as pausas, a sequência mais próxima do tempo
    esperado pelo número de letras de cada frase (programação dinâmica)."""
    total = duracao(audio)
    pausas = silencios(audio)
    fala_ini, fala_fim = 0.0, total
    if pausas and pausas[0][0] < 0.05:
        fala_ini = pausas.pop(0)[1]
    if pausas and pausas[-1][1] > total - 0.05:
        fala_fim = pausas.pop()[0]
    n = len(frases)
    if n == 1:
        return [(fala_ini, fala_fim)], total
    if len(pausas) < n - 1:
        raise SystemExit(f"o áudio tem {len(pausas)} pausas e o roteiro precisa de {n - 1}: confira o áudio")
    letras = np.cumsum([len(f) for f in frases])
    esperado = [fala_ini + (fala_fim - fala_ini) * letras[j] / letras[-1] for j in range(n - 1)]
    meio = [(a + b) / 2 for a, b in pausas]
    dur = [b - a for a, b in pausas]
    INF = float("inf")
    # custo[j][k]: melhor custo pondo a fronteira j na pausa k
    custo = [[INF] * len(pausas) for _ in range(n - 1)]
    volta = [[-1] * len(pausas) for _ in range(n - 1)]
    for j in range(n - 1):
        for k in range(len(pausas)):
            local = ((meio[k] - esperado[j]) / 2.0) ** 2 - 2.0 * dur[k]
            if j == 0:
                custo[j][k] = local
            else:
                melhor = min(range(k), key=lambda q: custo[j - 1][q], default=None)
                if melhor is not None and custo[j - 1][melhor] < INF:
                    custo[j][k] = custo[j - 1][melhor] + local
                    volta[j][k] = melhor
    k = min(range(len(pausas)), key=lambda q: custo[n - 2][q])
    escolha = []
    for j in range(n - 2, -1, -1):
        escolha.append(k)
        k = volta[j][k]
    escolha.reverse()
    tempos, ini = [], fala_ini
    for k in escolha:
        tempos.append((ini, pausas[k][0]))
        ini = pausas[k][1]
    tempos.append((ini, fala_fim))
    return tempos, total


CSS_VIDEO = (".video-wrap{margin:28px 0}.video-wrap h2{margin-top:0}.video-wrap video{display:block;margin:0 auto;"
             "width:auto;max-width:100%;max-height:70vh;height:auto;aspect-ratio:9/16;border-radius:var(--raio);"
             "background:#faf7f2;border:1px solid var(--linha)}.video-wrap details{margin-top:14px}"
             ".video-wrap summary{cursor:pointer;color:var(--rosa);font-weight:600}.video-wrap details p{margin:.6em 0}")


def atualizar_pagina(slug, nome, descricao, segundos, formato="a notícia em 1 minuto"):
    """Põe (ou atualiza) o CSS, o JSON-LD VideoObject e a seção do vídeo na página do post."""
    pagina = RAIZ / "blog" / slug / "index.html"
    h = pagina.read_text(encoding="utf-8")
    if ".video-wrap{" not in h:
        h = h.replace("</style>", CSS_VIDEO + "\n</style>", 1)
    url = f"https://produtoskincare.com.br/blog/{slug}/"
    dados = {"@context": "https://schema.org", "@type": "VideoObject", "name": nome, "description": descricao,
             "thumbnailUrl": url + "poster.jpg", "uploadDate": datetime.date.today().isoformat(),
             "contentUrl": url + "video.mp4", "duration": f"PT{round(segundos)}S", "inLanguage": "pt-BR"}
    bloco_ld = f'<script type="application/ld+json">{json.dumps(dados, ensure_ascii=False)}</script>'
    ld_antigo = re.compile(r'<script type="application/ld\+json">\{"@context": "https://schema.org", '
                           r'"@type": "VideoObject".*?</script>')
    if ld_antigo.search(h):
        h = ld_antigo.sub(lambda _: bloco_ld, h, count=1)
    else:
        h = h.replace("<!-- seo:inicio -->", bloco_ld + "\n<!-- seo:inicio -->", 1)
    paragrafos = [" ".join(p.split()) for p in
                  (RAIZ / "_roteiros" / f"{slug}.txt").read_text(encoding="utf-8").split("\n", 2)[2].split("\n\n")]
    narracao = "".join(f"<p>{html.escape(p, quote=False)}</p>" for p in paragrafos if p)
    secao = ('<section class="video-wrap" aria-labelledby="assista">\n'
             f'<h2 id="assista">Assista: {formato}</h2>\n'
             '<video controls preload="metadata" playsinline poster="poster.jpg" width="1080" height="1920">\n'
             '<source src="video.mp4" type="video/mp4">\n'
             '<track kind="captions" src="legendas.vtt" srclang="pt-BR" label="Português" default>\n'
             'Seu navegador não reproduz vídeo. Leia a narração abaixo.\n'
             '</video>\n'
             f'<details><summary>Ler a narração</summary>{narracao}</details>\n'
             '</section>')
    secao_antiga = re.compile(r'<section class="video-wrap".*?</section>', re.S)
    if secao_antiga.search(h):
        h = secao_antiga.sub(lambda _: secao, h, count=1)
    else:
        resumo = (re.search(r'<div class="card aviso">\s*<strong>Resumo:</strong>.*?</div>\n', h, re.S)
                  or re.search(r'<div class="ig-caixa ig-resumo">.*?</div>\n', h, re.S))
        if not resumo:
            raise SystemExit(f"não achei o card de resumo em blog/{slug}/index.html para pôr o vídeo depois dele")
        h = h[:resumo.end()] + "\n" + secao + "\n" + h[resumo.end():]
    pagina.write_text(h, encoding="utf-8")


def tempo_vtt(s):
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slug")
    ap.add_argument("--audio", required=True)
    ap.add_argument("--etiqueta", default="Notícia")
    ap.add_argument("--formato", default="a notícia em 1 minuto",
                    help='nome do formato, no alto do vídeo e no título da seção (em guia: "o guia em 1 minuto")')
    ap.add_argument("--saida", help="pasta de saída (padrão: blog/<slug>/); com ela, a página não é alterada")
    ap.add_argument("--nome", help="nome do vídeo no JSON-LD (com --descricao, põe o vídeo na página)")
    ap.add_argument("--descricao", help="descrição do vídeo no JSON-LD")
    args = ap.parse_args()
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg não encontrado no PATH")
    destino = Path(args.saida) if args.saida else RAIZ / "blog" / args.slug
    if not args.saida and not (destino / "index.html").exists():
        raise SystemExit(f"o post blog/{args.slug}/ não existe")
    destino.mkdir(parents=True, exist_ok=True)

    frases = frases_do_roteiro(args.slug)
    tempos, dur_audio = alinhar(frases, args.audio)
    fim_video = dur_audio + 0.6
    trocas = [0.0] + [max(0.0, t[0] - 0.15) for t in tempos[1:]]
    duracoes = [b - a for a, b in zip(trocas, trocas[1:] + [fim_video])]

    base = fundo()
    comum = base_comum(base, args.etiqueta, args.formato)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        lista = []
        for i, frase in enumerate(frases):
            png = tmp / f"t{i:02d}.png"
            tela(comum, frase).save(png)
            if i == 0:
                Image.open(png).convert("RGB").save(destino / "poster.jpg", "JPEG", quality=88, optimize=True,
                                                    progressive=True)
            lista += [f"file '{png.as_posix()}'", f"duration {duracoes[i]:.3f}"]
        lista.append(f"file '{(tmp / f't{len(frases) - 1:02d}.png').as_posix()}'")
        (tmp / "lista.txt").write_text("\n".join(lista) + "\n")
        # barra rosa que anda com o tempo, e um pedaço do fundo para escondê-la antes da margem
        Image.new("RGB", (LARG, BARRA_H), ROSA).save(tmp / "barra.png")
        base.crop((0, BARRA_Y, M, BARRA_Y + BARRA_H)).save(tmp / "mascara.png")
        filtro = (f"[0:v]fps=30[f];[f][1:v]overlay=x='{M}-{LARG}+{LARG}*min(t/{fim_video:.3f}\\,1)':y={BARRA_Y}"
                  f":eval=frame[b];[b][2:v]overlay=0:{BARRA_Y},format=yuv420p[v]")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(tmp / "lista.txt"),
                        "-loop", "1", "-i", str(tmp / "barra.png"), "-loop", "1", "-i", str(tmp / "mascara.png"),
                        "-i", str(args.audio), "-filter_complex", filtro, "-map", "[v]", "-map", "3:a",
                        "-c:v", "libx264", "-preset", "slow", "-crf", "26", "-tune", "stillimage",
                        "-c:a", "aac", "-b:a", "128k", "-ac", "1", "-af", "apad=pad_dur=0.6",
                        "-t", f"{fim_video:.2f}", "-movflags", "+faststart", "-map_metadata", "-1",
                        str(destino / "video.mp4")], check=True)

    vtt = ["WEBVTT", ""]
    for n, (frase, (a, b)) in enumerate(zip(frases, tempos), 1):
        vtt += [str(n), f"{tempo_vtt(a)} --> {tempo_vtt(b)}", frase, ""]
    (destino / "legendas.vtt").write_text("\n".join(vtt), encoding="utf-8")

    total = duracao(destino / "video.mp4")
    mb = (destino / "video.mp4").stat().st_size / 1e6
    for frase, (a, b) in zip(frases, tempos):
        print(f"  {a:6.2f}-{b:6.2f}  {frase[:70]}")
    print(f"{destino / 'video.mp4'}  {total:.1f} s  {mb:.2f} MB  ({len(frases)} frases)")
    print(f"duração para o VideoObject: PT{round(total)}S")
    if args.nome and args.descricao and not args.saida:
        atualizar_pagina(args.slug, args.nome, args.descricao, total, args.formato)
        print(f"blog/{args.slug}/index.html: CSS, VideoObject e seção do vídeo em dia")


if __name__ == "__main__":
    main()
