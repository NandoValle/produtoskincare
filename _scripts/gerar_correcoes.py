"""Gera /correcoes/: o registro público do que foi corrigido no site, a partir de _scripts/correcoes.json.

Processo (o mesmo que a página descreve):
1. O erro chega pelo /contato/ ou aparece numa conferência interna.
2. Confere-se na fonte (anúncio da loja, rótulo, estudo citado).
3. Corrige-se a página e acrescenta-se uma entrada em correcoes.json: o que estava, o que ficou, a data.
4. Rode:

    python -I _scripts/gerar_correcoes.py
    python -I _scripts/seo.py
    python -I _scripts/prontidao.py
"""
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pagina_base import RAIZ, esc, pagina

DADOS = RAIZ / "_scripts" / "correcoes.json"
DESTINO = RAIZ / "correcoes"

CSS = """
.cr-lista{list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:12px}
.cr-lista li{margin:0;padding:16px 18px;border:1px solid var(--linha);border-radius:var(--raio);background:var(--papel)}
.cr-lista time{font-weight:600}
.cr-lista dl{margin:8px 0 0;display:grid;grid-template-columns:max-content 1fr;gap:4px 12px}
.cr-lista dt{color:var(--suave)}.cr-lista dd{margin:0}
.cr-vazio{padding:16px 18px;border:1.5px dashed var(--linha-2,var(--linha));border-radius:var(--raio)}
"""


def br(iso):
    return date.fromisoformat(iso).strftime("%d/%m/%Y")


def entrada(c):
    return (f'<li><time datetime="{esc(c["data"])}">Corrigido em {br(c["data"])}</time> · '
            f'<a href="{esc(c["pagina"])}">{esc(c["pagina"])}</a>'
            f'<dl><dt>Estava</dt><dd>{esc(c["estava"])}</dd><dt>Ficou</dt><dd>{esc(c["ficou"])}</dd>'
            f'<dt>Origem</dt><dd>{esc(c["origem"])}</dd></dl></li>')


def main():
    d = json.loads(DADOS.read_text(encoding="utf-8"))
    itens = sorted(d["correcoes"], key=lambda c: c["data"], reverse=True)
    for c in itens:
        date.fromisoformat(c["data"])
        if not c["pagina"].startswith("/") or not all(c.get(k) for k in ("estava", "ficou", "origem")):
            raise SystemExit(f"entrada incompleta em correcoes.json: {c}")
    if itens:
        registro = '<ul class="cr-lista">\n' + "\n".join(entrada(c) for c in itens) + "\n</ul>"
    else:
        registro = (f'<p class="cr-vazio">Nenhuma correção registrada desde {br(d["inicio"])}, quando este registro começou. '
                    "Correções feitas antes dessa data não estão listadas aqui.</p>")
    corpo = f"""<article>
<div class="ig-cab">
<h1>Correções</h1>
<p class="ig-lede">Quando o site erra um preço, uma concentração ou uma afirmação sobre um ativo, a correção fica registrada aqui, com a data, o que estava escrito e o que passou a valer.</p>
</div>
<section aria-labelledby="registro">
<h2 id="registro">Registro</h2>
{registro}
</section>
<section aria-labelledby="como">
<h2 id="como">Como uma correção acontece</h2>
<ol>
<li>O erro chega por um aviso de leitor, pela página de <a href="/contato/">contato</a>, ou aparece numa conferência interna.</li>
<li>A informação é conferida na fonte: o anúncio da loja, o rótulo do produto ou o estudo citado.</li>
<li>A página é corrigida e ganha uma nota visível, "Corrigido em" com a data, junto do trecho alterado.</li>
<li>A correção entra neste registro, com o que estava e o que ficou.</li>
</ol>
</section>
<section aria-labelledby="entra">
<h2 id="entra">O que entra e o que não entra</h2>
<p>Entra o que mudava o sentido da página: preço, tamanho de frasco, concentração, dose, afirmação sobre o que um ativo faz e link que levava ao produto errado.</p>
<p>Não entra erro de digitação nem a atualização de rotina dos preços. Preço muda todo dia nas lojas, e por isso cada um aparece com a data em que foi conferido; a explicação está em <a href="/sobre/">Sobre</a>.</p>
</section>
<section aria-labelledby="avisar">
<h2 id="avisar">Viu um erro?</h2>
<p>Avise pela página de <a href="/contato/">contato</a>, com o endereço da página e o trecho.</p>
</section>
</article>"""
    DESTINO.mkdir(exist_ok=True)
    (DESTINO / "index.html").write_text(pagina(
        titulo="Correções: o que o site errou e corrigiu",
        descricao="Registro público das correções do Produto Skincare: a data, o que estava escrito e o que passou a valer, e como avisar um erro.",
        caminho="/correcoes/", trilha=[("/", "Início"), (None, "Correções")], corpo=corpo, css_extra=CSS,
        aviso="Conteúdo informativo, não substitui consulta com dermatologista."), encoding="utf-8")
    print(f"/correcoes/ gerada com {len(itens)} correção(ões)")


if __name__ == "__main__":
    main()
