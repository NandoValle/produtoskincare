"""Põe um vídeo curto no topo de um post do blog, no lugar da imagem de capa.

O vídeo roda sem som, em repetição, e tem um botão para pausar. A imagem de capa do post
continua sendo usada: vira o pôster do vídeo (aparece enquanto ele carrega e fica parada para
quem pede menos movimento no sistema) e segue nos cards do blog e na prévia de compartilhamento.

Uso:
  python3 _scripts/capa_video.py <slug> --video baixado.mp4 --descricao "o que o vídeo mostra"

Grava blog/<slug>/capa.mp4 (H.264, até 1280 px de largura, sem áudio, faststart) e troca, em
blog/<slug>/index.html, o <figure class="capa-artigo"> da imagem pelo do vídeo. Pode rodar de novo
para trocar o vídeo ou a descrição.
"""
import argparse
import html
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

CSS = (".capa-video{position:relative}"
       ".capa-artigo video{display:block;width:100%;height:auto;aspect-ratio:16/9;object-fit:cover;"
       "border-radius:var(--raio);background:var(--rosa-claro)}"
       ".capa-pausa{position:absolute;right:12px;bottom:12px;width:40px;height:40px;border-radius:50%;"
       "border:0;background:rgba(26,22,20,.6);color:#fff;font:600 .8rem/1 var(--fonte-corpo);cursor:pointer}"
       ".capa-pausa:focus-visible{outline:3px solid #fff;outline-offset:2px}\n")

SCRIPT = """<script>
(function(){var f=document.querySelector('.capa-video');if(!f)return;var v=f.querySelector('video'),b=f.querySelector('.capa-pausa');
function marcar(){var p=v.paused;b.textContent=p?'\\u25B6':'\\u275A\\u275A';b.setAttribute('aria-label',p?'Reproduzir vídeo':'Pausar vídeo');}
if(window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches){v.removeAttribute('autoplay');v.pause();}
b.addEventListener('click',function(){if(v.paused){v.play();}else{v.pause();}});
v.addEventListener('play',marcar);v.addEventListener('pause',marcar);marcar();})();
</script>"""


def sair(msg):
    raise SystemExit(f"ERRO: {msg}")


def info(arq):
    s = json.loads(subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams",
                                   "-show_format", str(arq)], capture_output=True, text=True, check=True).stdout)
    v = next((x for x in s["streams"] if x.get("codec_type") == "video"), None)
    if not v:
        sair(f"{arq} não tem faixa de vídeo")
    return int(v["width"]), int(v["height"]), float(s["format"].get("duration") or 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slug")
    ap.add_argument("--video", required=True)
    ap.add_argument("--descricao", required=True, help="o que o vídeo mostra (vira o aria-label)")
    ap.add_argument("--forcar", action="store_true", help="aceita vídeo que não seja 16:9")
    a = ap.parse_args()
    if not shutil.which("ffmpeg"):
        sair("ffmpeg não encontrado no PATH")

    pasta = RAIZ / "blog" / a.slug
    pagina = pasta / "index.html"
    if not pagina.exists():
        sair(f"o post blog/{a.slug}/ não existe")
    w, h, dur = info(a.video)
    if abs(w / h - 16 / 9) > 0.03 and not a.forcar:
        sair(f"o vídeo tem {w}x{h}; a capa é 16:9 (use --forcar para aceitar e cortar as bordas)")

    with tempfile.TemporaryDirectory() as tmp:
        saida = Path(tmp) / "capa.mp4"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", a.video, "-map", "0:v:0", "-an",
                        "-vf", "scale='min(1280,iw)':-2,format=yuv420p", "-c:v", "libx264", "-preset", "slow",
                        "-crf", "26", "-profile:v", "high", "-movflags", "+faststart", "-map_metadata", "-1",
                        str(saida)], check=True)
        shutil.move(str(saida), pasta / "capa.mp4")

    t = pagina.read_text(encoding="utf-8")
    desc = html.escape(a.descricao, quote=True)
    m = re.search(r'<figure class="capa-artigo">(<img [^>]*>)</figure>', t)
    if m:
        img = m.group(1)
        poster = re.search(r'src="([^"]+)"', img).group(1)
        fig = (f'<figure class="capa-artigo capa-video">'
               f'<video autoplay muted loop playsinline preload="auto" poster="{poster}" width="1600" height="900" '
               f'aria-label="Vídeo ilustrativo: {desc}"><source src="capa.mp4" type="video/mp4">{img}</video>'
               f'<button type="button" class="capa-pausa" aria-label="Pausar vídeo"></button></figure>\n{SCRIPT}')
        t = t.replace(m.group(0), fig, 1)
        if "</style>" not in t:
            sair("o post não tem <style> para o CSS do vídeo")
        t = t.replace("</style>", CSS + "</style>", 1)
    elif 'class="capa-artigo capa-video"' in t:
        t = re.sub(r'aria-label="Vídeo ilustrativo: [^"]*"', f'aria-label="Vídeo ilustrativo: {desc}"', t, count=1)
    else:
        sair("não achei a imagem de capa (<figure class=\"capa-artigo\"><img ...></figure>) no post")
    pagina.write_text(t, encoding="utf-8")

    w2, h2, d2 = info(pasta / "capa.mp4")
    mb = (pasta / "capa.mp4").stat().st_size / 1e6
    print(f"blog/{a.slug}/capa.mp4  {w2}x{h2}  {d2:.1f} s  {mb:.2f} MB")
    if mb > 4:
        print("AVISO: passou de 4 MB; ele baixa sozinho ao abrir a página. Considere um clipe mais curto.")


if __name__ == "__main__":
    main()
