"""Série Mito x regra: página da série e numeração dos episódios.

Uso (na raiz do site):
    python -I _scripts/gerar_serie_mito.py
    python -I _scripts/seo.py
    python -I _scripts/prontidao.py

O que faz:
  1. Gera /mito-x-regra/ com a lista numerada dos episódios (EPISODIOS, do mais antigo
     para o mais novo) e a explicação do formato fixo da série.
  2. Em cada episódio, troca o selo "Série Mito x regra" por um selo com o número
     ("Série Mito x regra · nº 02"), ligado à página da série, e põe no fim do texto a
     navegação entre o episódio anterior e o próximo.

Episódio novo: publicar o post como os outros (capa, pin, cartão no blog/index.html),
acrescentar o slug no FIM de EPISODIOS e rodar este script. A pauta e o formato estão em
_roteiros/mito-x-regra.txt.
"""
import html
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # para rodar com "python -I"

from pagina_base import RAIZ, esc, pagina

# Do mais antigo para o mais novo. A posição na lista é o número do episódio.
EPISODIOS = [
    "mito-x-regra-ardencia-nao-e-eficacia",
    "mito-x-regra-sunblock-100",
    "mito-x-regra-resistente-agua",
]

CAMINHO = "/mito-x-regra/"
SELO_RE = re.compile(r'<p class="mr-selo-serie">.*?</p>', re.S)
NAV_INI, NAV_FIM = "<!-- serie:inicio -->", "<!-- serie:fim -->"
NAV_RE = re.compile(r"\n?" + re.escape(NAV_INI) + r".*?" + re.escape(NAV_FIM), re.S)
CSS_NAV = (".mr-selo-serie a{color:inherit;text-decoration:none}.mr-selo-serie a:hover{text-decoration:underline}"
           ".mr-nav{display:flex;flex-wrap:wrap;gap:12px;justify-content:space-between;margin:30px 0 0;padding-top:18px;"
           "border-top:1px solid var(--linha);font-size:.92rem}.mr-nav span{color:var(--suave)}")

CSS_PAGINA = """
.ig .mr-lista,.ig .mr-formato{list-style:none;padding:0;margin:0}
.mr-lista{display:grid;gap:18px}
.mr-ep{display:grid;grid-template-columns:200px 1fr;gap:18px;align-items:center;padding:16px;border:1px solid var(--linha);border-radius:var(--raio-md);background:var(--papel);text-decoration:none;color:var(--tinta)}
.mr-ep:hover{border-color:var(--rosa)}
.mr-ep img{width:100%;height:auto;aspect-ratio:16/9;object-fit:cover;border-radius:var(--raio);background:var(--rosa-claro)}
.mr-num{font-size:.8rem;letter-spacing:.08em;text-transform:uppercase;color:var(--rosa);font-weight:600;margin:0}
.mr-ep h3{font-size:1.35rem;line-height:1.25;margin:4px 0 6px}
.mr-ep p{margin:0}
.mr-par{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:10px;font-size:.92rem}
.mr-par p{padding:10px 12px;border-radius:var(--raio);background:var(--papel-2)}
.mr-par strong{display:block;font-size:.74rem;letter-spacing:.08em;text-transform:uppercase;color:var(--suave)}
.mr-formato{display:grid;gap:10px;padding:0;list-style:none}
.mr-formato li{padding:12px 14px;border-left:3px solid var(--rosa);background:var(--papel)}
@media(max-width:620px){.mr-ep{grid-template-columns:1fr}.mr-par{grid-template-columns:1fr}}
"""


def maiuscula(t):
    """Primeira letra em maiúscula, mesmo quando o título abre com aspas."""
    m = re.search(r"[^\W\d_]", t)
    return t[:m.start()] + t[m.start()].upper() + t[m.start() + 1:] if m else t


def numero(i):
    return f"{i:02d}"


def ler(slug):
    t = (RAIZ / "blog" / slug / "index.html").read_text(encoding="utf-8")
    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", t, re.S)
    titulo = html.unescape(re.sub(r"<[^>]+>", "", h1.group(1))).strip()
    frases = [html.unescape(re.sub(r"<[^>]+>", "", f)).strip()
              for f in re.findall(r'<p class="mr-frase">(.*?)</p>', t, re.S)]
    capa = re.search(r'<figure class="capa-artigo"><img[^>]*\balt="([^"]*)"', t)
    return {
        "slug": slug,
        "titulo": titulo,
        "curto": re.sub(r"^Mito x regra:\s*", "", titulo),
        "mito": frases[0] if frases else "",
        "regra": frases[1] if len(frases) > 1 else "",
        "alt": html.unescape(capa.group(1)) if capa else "",
        "tem_capa": (RAIZ / "img" / "blog" / f"{slug}-800.webp").exists(),
    }


def pagina_da_serie(eps):
    cartoes = []
    for i, e in reversed(list(enumerate(eps, 1))):          # mais novo em cima
        img = (f'<img src="/img/blog/{e["slug"]}-800.webp" width="800" height="450" alt="{esc(e["alt"])}" '
               f'loading="lazy" decoding="async">') if e["tem_capa"] else "<span></span>"
        par = ""
        if e["mito"] and e["regra"]:
            par = (f'<div class="mr-par"><p><strong>O mito</strong>{esc(e["mito"])}</p>'
                   f'<p><strong>A regra</strong>{esc(e["regra"])}</p></div>')
        cartoes.append(
            f'<li><a class="mr-ep" href="/blog/{e["slug"]}/">{img}<div>'
            f'<p class="mr-num">Episódio nº {numero(i)}</p><h3>{esc(maiuscula(e["curto"]))}</h3>{par}'
            f'</div></a></li>')
    n = len(eps)
    corpo = f"""<article>
<h1>Mito x regra</h1>
<p class="ig-lede">Uma frase que todo mundo repete sobre skincare, colocada ao lado do que a regra da Anvisa e os estudos dizem de fato. Um episódio por semana, sempre no mesmo formato.</p>

<section>
<h2>Episódios</h2>
<p>{n} episódios publicados, do mais novo para o mais antigo.</p>
<ol class="mr-lista" reversed>
{chr(10).join(cartoes)}
</ol>
</section>

<section>
<h2>Como cada episódio funciona</h2>
<ul class="mr-formato">
<li><strong>O mito:</strong> a frase como ela circula, entre aspas, sem caricatura.</li>
<li><strong>A regra:</strong> o que diz a norma da Anvisa ou o estudo, com o número da resolução ou a referência para conferir.</li>
<li><strong>Na prática:</strong> o que muda no seu dia a dia, em poucos passos.</li>
</ul>
<p>Os textos são escritos com IA a partir das fontes citadas em cada episódio e ainda não são revisados por dermatologista. <a href="/sobre/#quem-escreve">Veja quem escreve</a>.</p>
</section>

<section>
<h2>Para acompanhar</h2>
<p>Os episódios novos entram no <a href="/blog/">blog</a> e no <a href="/blog/feed.xml">feed RSS</a>. Tem um mito que você quer ver aqui? <a href="/contato/">Sugira pelo contato</a>.</p>
</section>
</article>"""
    destino = RAIZ / "mito-x-regra" / "index.html"
    destino.parent.mkdir(exist_ok=True)
    destino.write_text(pagina(
        titulo="Mito x regra: a série que confere frases de skincare",
        descricao="Série semanal do Produto Skincare: uma frase comum sobre skincare ao lado do que a regra da Anvisa e os estudos dizem. Veja todos os episódios.",
        caminho=CAMINHO,
        trilha=[("/", "Início"), ("/blog/", "Blog"), (None, "Mito x regra")],
        corpo=corpo, css_extra=CSS_PAGINA), encoding="utf-8")


def marcar_episodio(i, eps):
    e = eps[i - 1]
    caminho = RAIZ / "blog" / e["slug"] / "index.html"
    t = caminho.read_text(encoding="utf-8")
    selo = f'<p class="mr-selo-serie"><a href="{CAMINHO}">Série Mito x regra · nº {numero(i)}</a></p>'
    t, n = SELO_RE.subn(selo, t, count=1)
    if not n:
        print(f"aviso: {e['slug']} sem selo da série (mr-selo-serie)")
    t = NAV_RE.sub("", t)
    ant = eps[i - 2] if i > 1 else None
    prox = eps[i] if i < len(eps) else None
    lado_a = (f'<a href="/blog/{ant["slug"]}/">← nº {numero(i - 1)}: {esc(ant["curto"])}</a>' if ant
              else "<span>Este é o primeiro episódio</span>")
    lado_b = (f'<a href="/blog/{prox["slug"]}/">nº {numero(i + 1)}: {esc(prox["curto"])} →</a>' if prox
              else f'<a href="{CAMINHO}">Todos os episódios da série →</a>')
    nav = (f'\n{NAV_INI}<nav class="mr-nav" aria-label="Episódios da série Mito x regra">{lado_a}{lado_b}</nav>{NAV_FIM}')
    marca = "<!-- perguntas:inicio -->"
    pos = t.find(marca)
    if pos < 0:
        pos = t.rfind("</main>")
    # antes da linha de créditos que fecha o texto, se ela estiver logo acima das perguntas
    t = t[:pos].rstrip("\n") + nav + "\n" + t[pos:]
    if ".mr-nav{" not in t:
        t = t.replace("</style>", CSS_NAV + "\n</style>", 1)
    caminho.write_text(t, encoding="utf-8")


def main():
    eps = [ler(s) for s in EPISODIOS]
    pagina_da_serie(eps)
    for i in range(1, len(eps) + 1):
        marcar_episodio(i, eps)
    print(f"série Mito x regra: página {CAMINHO} e {len(eps)} episódios numerados")


if __name__ == "__main__":
    main()
