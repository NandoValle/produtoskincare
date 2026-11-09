"""Perguntas frequentes nos guias do blog, com o bloco FAQPage (JSON-LD) para buscadores.

As perguntas e respostas ficam em _scripts/faq_blog.json, uma lista por artigo. O bloco
gerado fica entre <!-- faq:inicio --> e <!-- faq:fim -->, antes de "Leia também" (ou das
fontes) e é refeito a cada execução:

    python3 _scripts/faq_blog.py
"""
import html
import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DADOS = Path(__file__).with_name("faq_blog.json")
INICIO, FIM = "<!-- faq:inicio -->", "<!-- faq:fim -->"
BLOCO_RE = re.compile(r"\n?" + re.escape(INICIO) + r".*?" + re.escape(FIM) + r"\n?", re.S)


def bloco(perguntas):
    esc = lambda t: html.escape(t, quote=True)  # noqa: E731
    itens = "".join(f'<details class="ps-faq"><summary>{esc(q)}</summary><p>{esc(r)}</p></details>\n'
                    for q, r in perguntas)
    ld = {"@context": "https://schema.org", "@type": "FAQPage",
          "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": r}}
                         for q, r in perguntas]}
    ld_txt = json.dumps(ld, ensure_ascii=False).replace("</", "<\\/")
    return (f'{INICIO}\n<section class="ps-faq-bloco" aria-labelledby="faq">\n<h2 id="faq">Perguntas frequentes</h2>\n'
            f'{itens}<script type="application/ld+json">{ld_txt}</script>\n</section>\n{FIM}\n')


def ancora(texto):
    """Posição antes de "Leia também"; se não houver, antes das fontes; se não, antes de </main>."""
    m = re.search(r'<h2 id="relacionados"', texto)
    if m:
        abre = texto.rfind("<section", 0, m.start())
        fecha = texto.rfind("</section>", 0, m.start())
        return abre if abre > fecha else m.start()
    for padrao in (r'<section class="ig-fontes"', r"</main>"):
        m = re.search(padrao, texto)
        if m:
            return m.start()
    raise ValueError("sem lugar para as perguntas")


def main():
    dados = json.loads(DADOS.read_text(encoding="utf-8"))
    mudou = 0
    for slug, perguntas in dados.items():
        if slug.startswith("_"):
            continue
        p = RAIZ / "blog" / slug / "index.html"
        antes = p.read_text(encoding="utf-8")
        texto = BLOCO_RE.sub("\n", antes, count=1)
        pos = ancora(texto)
        depois = texto[:pos] + bloco(perguntas) + texto[pos:]
        if depois != antes:
            p.write_text(depois, encoding="utf-8")
            mudou += 1
    print(f"perguntas frequentes atualizadas em {mudou} artigos")


if __name__ == "__main__":
    main()
