"""Prontidão para agentes e buscadores (WebMCP, SEO, GEO, AEO), página por página.

Idempotente, como seo.py e menu.py. Rode POR ÚLTIMO, depois de qualquer gerador:

    python3 _scripts/prontidao.py

O que ele garante em cada página (a página inicial fica de fora: é feita à mão):

1. WebMCP no <head>: meta do Origin Trial (copiada da página inicial; o token vale só para esta
   origem), /webmcp-polyfill.js e /webmcp.js. Os geradores gerar_*.py reescrevem a página inteira
   e não conhecem essas linhas; este passo as devolve.
2. Nota de fallback em <noscript>, quando a página não tem nenhuma.
3. Perguntas abertas: os blocos <details class="pd-faq|ps-faq"> viram título <h3> com a resposta
   visível logo abaixo. O texto e o FAQPage (JSON-LD) dos geradores não mudam.
4. Bloco "Perguntas frequentes" com as perguntas de _scripts/perguntas.json, entre
   <!-- perguntas:inicio --> e <!-- perguntas:fim -->, com FAQPage quando a página ainda não tem.
   Cada resposta resume o que a própria página já diz. Ao mudar uma página, revise as dela.
5. Linha de atualização e referências, entre <!-- nota-pagina:inicio --> e <!-- nota-pagina:fim -->:
   a data vem do <lastmod> do sitemap.xml; as referências só entram onde a página tem menos de
   duas fontes ou links externos.
6. <title> com até 65 caracteres (tira o sufixo " | Produto Skincare" ou usa TITULOS abaixo) e
   meta description com até 180 (corta na última frase inteira).

Só usa a biblioteca padrão. Não inventa conteúdo: o que não está em perguntas.json não aparece.
"""
import html
import json
import re
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DADOS = Path(__file__).with_name("perguntas.json")
ORIGEM = "https://produtoskincare.com.br"
SUFIXO = " | Produto Skincare"
P_INI, P_FIM = "<!-- perguntas:inicio -->", "<!-- perguntas:fim -->"
N_INI, N_FIM = "<!-- nota-pagina:inicio -->", "<!-- nota-pagina:fim -->"
P_RE = re.compile(r"\n?" + re.escape(P_INI) + r".*?" + re.escape(P_FIM) + r"\n?", re.S)
N_RE = re.compile(r"\n?" + re.escape(N_INI) + r".*?" + re.escape(N_FIM) + r"\n?", re.S)

# Páginas que ficam sem a linha de referências (não são conteúdo de skincare do site).
SEM_REFERENCIAS = {"/contato/", "/privacidade/", "/termos/", "/fortskin/"}
# Páginas que não recebem nem perguntas nem nota: /fortskin/ é uma experiência de tela cheia que
# trava a rolagem, então o bloco ficaria escondido do visitante (e FAQ escondida é má prática).
SEM_BLOCOS = {"/fortskin/"}
# Páginas em que o <main> é redesenhado por JavaScript: os blocos entram depois do </main>.
MAIN_DINAMICO = re.compile(r'<main[^>]*\bid="(?:grade|stage)"')

# As duas referências já usadas e conferidas na página inicial.
REF_ANVISA = "https://www.gov.br/anvisa/pt-br/assuntos/cosmeticos"
REF_SBD = "https://www.sbd.org.br/encontre-um-dermatologista/"
TEXTOS = {
    "pt": {"h2": "Perguntas frequentes", "data": "Página atualizada em {}.",
           "refs": ('Conteúdo informativo, não é diagnóstico. Regras de cosméticos no Brasil: '
                    '<a href="{a}" rel="noopener">Anvisa</a>. Para diagnóstico e tratamento: '
                    '<a href="{s}" rel="noopener">encontre um dermatologista pela SBD</a>.'),
           "fallback": ("Sem JavaScript, as ferramentas para assistentes não rodam, e nada se perde: os guias, "
                        "o catálogo de produtos e as rotinas seguem abertos como HTML comum. Esse é o caminho manual."),
           "meses": "janeiro fevereiro março abril maio junho julho agosto setembro outubro novembro dezembro".split(),
           "fmt": "{d} de {m} de {a}"},
    "en": {"h2": "Frequently asked questions", "data": "Page updated on {}.",
           "refs": ('For information only, not a diagnosis. Cosmetics rules in Brazil: '
                    '<a href="{a}" rel="noopener">Anvisa</a>. For diagnosis and treatment: '
                    '<a href="{s}" rel="noopener">find a dermatologist through the Brazilian Society of Dermatology</a>.'),
           "fallback": ("Without JavaScript the assistant tools do not run and nothing is lost: the guides, the product "
                        "catalogue and the routines stay open as plain HTML. That is the manual fallback."),
           "meses": "January February March April May June July August September October November December".split(),
           "fmt": "{d} {m} {a}"},
    "es": {"h2": "Preguntas frecuentes", "data": "Página actualizada el {}.",
           "refs": ('Contenido informativo, no es un diagnóstico. Normas de cosméticos en Brasil: '
                    '<a href="{a}" rel="noopener">Anvisa</a>. Para diagnóstico y tratamiento: '
                    '<a href="{s}" rel="noopener">busca un dermatólogo en la Sociedad Brasileña de Dermatología</a>.'),
           "fallback": ("Sin JavaScript las herramientas para asistentes no funcionan y no se pierde nada: las guías, el "
                        "catálogo y las rutinas siguen abiertos como HTML común. Ese es el fallback manual."),
           "meses": "enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre".split(),
           "fmt": "{d} de {m} de {a}"},
}

# Títulos que continuam longos mesmo sem o sufixo. Mesma informação, menos palavras.
TITULOS = {
    "/en/blog/myth-rule-sunblock-100/": 'Myth vs rule: no "sunblock" or "100% protection" on labels',
    "/es/blog/mito-regla-ardencia/": "Mito × regla: el escozor no indica que el producto funciona",
    "/es/blog/mito-regla-sunblock-100/": "Mito × regla: ni «sunblock» ni «100% de protección»",
    "/ferramentas/prateleira/": "Minha prateleira: o que combina entre os produtos que você tem",
    "/blog/mito-x-regra-ardencia-nao-e-eficacia/": "Mito x regra: ardência não é sinal de que o produto funciona",
    "/blog/mito-x-regra-sunblock-100/": "Mito x regra: “sunblock” e “100% de proteção” não existem",
    "/comparativos/cerave-gel-limpeza-ou-lrp-effaclar-gel/": "CeraVe Gel de Limpeza ou La Roche-Posay Effaclar Gel?",
    "/comparativos/isdin-fusion-water-sem-cor-ou-skin-aqua-moisture-milk/": "ISDIN Fusion Water Sem Cor ou Skin Aqua Super Moisture Milk?",
    "/comparativos/neutrogena-hydro-boost-ou-garnier-uniform-matte/": "Neutrogena Hydro Boost ou Garnier Uniform & Matte Toque Seco?",
    "/comparativos/neutrogena-sun-fresh-fps70-ou-isdin-fusion-water-sem-cor/": "Neutrogena Sun Fresh FPS 70 ou ISDIN Fusion Water Sem Cor?",
    "/comparativos/principia-niacinamida-ou-ordinary-niacinamide/": "Principia Niacinamida NC-10 ou The Ordinary Niacinamide 10%?",
    "/comparativos/principia-rn03-ou-loreal-revitalift-noturno/": "Principia RN-0,3 Retinol ou L'Oréal Revitalift Sérum Noturno?",
}


def paginas():
    for p in sorted(RAIZ.rglob("index.html")):
        partes = p.relative_to(RAIZ).parts
        if any(x.startswith(("_", ".")) for x in partes):
            continue
        rel = "/" + "/".join(partes[:-1]) + "/"
        yield rel.replace("//", "/"), p


def idioma(t):
    m = re.search(r'<html[^>]*\blang="([a-zA-Z]{2})', t)
    cod = (m.group(1).lower() if m else "pt")
    return cod if cod in TEXTOS else "pt"


def datas_do_sitemap():
    sm = (RAIZ / "sitemap.xml").read_text(encoding="utf-8")
    return {loc.replace(ORIGEM, ""): mod[:10]
            for loc, mod in re.findall(r"<loc>([^<]+)</loc>\s*<lastmod>([^<]+)</lastmod>", sm)}


def bloco_webmcp():
    home = (RAIZ / "index.html").read_text(encoding="utf-8")
    m = re.search(r'(<!-- WebMCP Origin Trial[^\n]*-->\n)?<meta http-equiv="origin-trial"[^\n]*>\n', home)
    if not m:
        raise SystemExit("a página inicial perdeu a meta do Origin Trial; não dá para copiar")
    return m.group(0)


def passo_webmcp(t, origin_trial, lang):
    if '<meta name="author"' not in t:
        t = t.replace("</head>", '<meta name="author" content="Equipe Produto Skincare">\n</head>', 1)
    if 'http-equiv="origin-trial"' not in t:
        t = t.replace("</head>", origin_trial + "</head>", 1)
    if 'src="/webmcp.js"' not in t:
        t = t.replace("</head>", '<script src="/webmcp.js" defer></script>\n</head>', 1)
    if 'src="/webmcp-polyfill.js"' not in t:
        t = t.replace('<script src="/webmcp.js" defer></script>',
                      '<script src="/webmcp-polyfill.js" defer></script>\n<script src="/webmcp.js" defer></script>', 1)
    # O scanner só reconhece o caminho manual em <noscript> ou em elemento interativo.
    if not re.search(r'<noscript>\s*<p class="[^"]*\bfallback\b', t) and "</main>" in t:
        t = t.replace("</main>", f'</main>\n<noscript><p class="fallback">{TEXTOS[lang]["fallback"]}</p></noscript>', 1)
    return t


def passo_faq_aberto(t):
    t = re.sub(r'<details class="(pd-faq|ps-faq)"><summary>(.*?)</summary>(.*?)</details>',
               r'<div class="\1"><h3 class="pq">\2</h3>\3</div>', t, flags=re.S)
    # <details> sem classe cuja chamada é uma pergunta (página de mercado, escrita à mão).
    return re.sub(r'<details><summary>([^<]*\?)</summary>(\s*<p>.*?)</details>',
                  r'<div class="ps-faq"><h3 class="pq">\1</h3>\2</div>', t, flags=re.S)


def inserir(t, pos, bloco):
    """Insere o bloco sempre do mesmo jeito, para a segunda execução não mexer em nada."""
    antes, depois = t[:pos], t[pos:]
    if not antes.endswith("\n"):
        bloco = "\n" + bloco
    if depois.startswith("\n"):
        bloco = bloco.rstrip("\n")
    return antes + bloco + depois


def data_do_git(p):
    """Para página fora do sitemap: a data do último commit do arquivo."""
    try:
        r = subprocess.run(["git", "log", "-1", "--format=%cs", "--", str(p.relative_to(RAIZ))],
                           cwd=RAIZ, capture_output=True, text=True, timeout=20)
        d = r.stdout.strip()
        return d if re.fullmatch(r"\d{4}-\d{2}-\d{2}", d) else None
    except Exception:
        return None


def passo_h1(t):
    """H1 único com menos de 8 caracteres ("Acne") recebe o texto do <title>, se o título começa por ele."""
    hs = re.findall(r"<h1[^>]*>(.*?)</h1>", t, re.S)
    mt = re.search(r"<title>(.*?)</title>", t, re.S)
    if len(hs) != 1 or not mt or "<" in hs[0]:
        return t
    h1 = html.unescape(hs[0].strip())
    titulo = html.unescape(mt.group(1).strip())
    if titulo.endswith(SUFIXO):
        titulo = titulo[: -len(SUFIXO)]
    if len(h1) >= 8 or len(titulo) < 8 or not titulo.lower().startswith(h1.lower()):
        return t
    return re.sub(r"(<h1[^>]*>).*?(</h1>)",
                  lambda m: m.group(1) + html.escape(titulo, quote=False) + m.group(2), t, count=1, flags=re.S)


def ancora(t):
    """Onde entram os blocos: antes da nota de fallback do <main> (a nota fica só em <noscript>,
    para o visitante com JavaScript não ver texto técnico); se não houver, antes de </main>;
    em página com <main> redesenhado por JavaScript, depois de </main>."""
    fim = t.find("</main>")
    if fim < 0:
        return None
    if MAIN_DINAMICO.search(t):
        return fim + len("</main>")
    m = re.search(r'<p class="fallback" id="fallback-manual">|<noscript><p class="fallback"', t)
    if m and m.start() < fim:
        return m.start()
    return fim


def bloco_perguntas(pares, lang, com_schema):
    esc = lambda x: html.escape(x, quote=False)  # noqa: E731
    itens = "".join(f"<h3>{esc(q)}</h3>\n<p>{esc(r)}</p>\n" for q, r in pares)
    ld = ""
    if com_schema:
        dados = {"@context": "https://schema.org", "@type": "FAQPage",
                 "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": r}}
                                for q, r in pares]}
        ld = '<script type="application/ld+json">' + json.dumps(dados, ensure_ascii=False).replace("</", "<\\/") + "</script>\n"
    return (f'{P_INI}\n<section class="ps-perguntas" aria-labelledby="perguntas-pagina">\n'
            f'<h2 id="perguntas-pagina">{TEXTOS[lang]["h2"]}</h2>\n{itens}{ld}</section>\n{P_FIM}\n')


def passo_perguntas(t, pares, lang):
    t = P_RE.sub("\n", t, count=1)
    if not pares:
        return t
    pos = ancora(t)
    if pos is None:
        return t
    return inserir(t, pos, bloco_perguntas(pares, lang, com_schema='"FAQPage"' not in t))


def data_por_extenso(iso, lang):
    a, m, d = iso.split("-")
    tx = TEXTOS[lang]
    return tx["fmt"].format(d=int(d), m=tx["meses"][int(m) - 1], a=a)


def passo_nota(t, rel, lang, lastmod):
    t = N_RE.sub("\n", t, count=1)
    tx = TEXTOS[lang]
    partes = []
    tem_data = re.search(r"<time[^>]*\bdatetime=|article:(?:published|modified)_time", t)
    if not tem_data and lastmod:
        partes.append(tx["data"].format(f'<time datetime="{lastmod}">{data_por_extenso(lastmod, lang)}</time>'))
    corpo = re.sub(r"<(script|template)\b.*?</\1>", "", t[t.find("<body"):], flags=re.S)
    externos = len(re.findall(r'<a\b[^>]*\bhref="https?://(?!(?:www\.)?produtoskincare\.com\.br)', corpo))
    citacoes = len(re.findall(r"<(?:cite|blockquote|q)[\s>]", corpo))
    if externos + citacoes < 2 and rel not in SEM_REFERENCIAS:
        partes.append(tx["refs"].format(a=REF_ANVISA, s=REF_SBD))
    if not partes:
        return t
    bloco = f'{N_INI}\n<p class="ps-nota-pagina">{" ".join(partes)}</p>\n{N_FIM}\n'
    fim_perguntas = t.find(P_FIM)
    pos = fim_perguntas + len(P_FIM) if fim_perguntas >= 0 else ancora(t)
    if pos is None:
        return t
    return inserir(t, pos, bloco)


def passo_titulo(t, rel):
    m = re.search(r"<title>(.*?)</title>", t, re.S)
    if not m:
        return t
    atual = html.unescape(m.group(1).strip())
    novo = atual
    if len(novo) > 65 and novo.endswith(SUFIXO):
        novo = novo[: -len(SUFIXO)]
    if len(novo) > 65 and rel in TITULOS:
        novo = TITULOS[rel]
    if novo == atual:
        return t
    return t[: m.start(1)] + html.escape(novo, quote=False) + t[m.end(1):]


def passo_descricao(t):
    m = re.search(r'<meta name="description" content="([^"]*)"', t)
    if not m:
        return t
    atual = html.unescape(m.group(1).strip())
    if len(atual) <= 180:
        return t
    corte = atual[:180]
    fim = max(corte.rfind(". "), corte.rfind("? "), corte.rfind("! "))
    if fim >= 69:
        novo = corte[: fim + 1]
    else:
        novo = corte[:179].rsplit(" ", 1)[0].rstrip(" ,;:") + "…"
    return t[: m.start(1)] + html.escape(novo, quote=True) + t[m.end(1):]


def main():
    dados = {k: v for k, v in json.loads(DADOS.read_text(encoding="utf-8")).items() if not k.startswith("_")}
    datas = datas_do_sitemap()
    origin_trial = bloco_webmcp()
    mudou, sem_pagina = 0, set(dados)
    for rel, p in paginas():
        if rel == "/":
            continue
        sem_pagina.discard(rel)
        antes = p.read_bytes().decode("utf-8")
        t = antes.replace("\r\n", "\n")
        lang = idioma(t)
        t = passo_webmcp(t, origin_trial, lang)
        t = passo_faq_aberto(t)
        if rel in SEM_BLOCOS:  # só tira blocos antigos, se houver
            t = N_RE.sub("\n", P_RE.sub("\n", t, count=1), count=1)
        else:
            t = passo_perguntas(t, dados.get(rel), lang)
            t = passo_nota(t, rel, lang, datas.get(rel) or data_do_git(p))
        t = passo_h1(t)
        t = passo_titulo(t, rel)
        t = passo_descricao(t)
        if t != antes.replace("\r\n", "\n"):
            p.write_bytes(t.encode("utf-8"))
            mudou += 1
    print(f"prontidão: {mudou} página(s) atualizada(s)")
    for rel in sorted(sem_pagina):
        print(f"  aviso: perguntas.json cita {rel}, que não existe")


if __name__ == "__main__":
    main()
