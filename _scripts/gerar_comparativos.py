"""Gera as páginas "X ou Y" (/comparativos/<a>-ou-<b>/) e o índice /comparativos/.

Os pares ficam em _scripts/comparativos.json. Tudo o que aparece na página sai do
catálogo (/produtos.json): o script não dá veredito de "melhor" e não inventa dados.
Rode depois de mudar os pares ou o catálogo:

    python3 _scripts/gerar_comparativos.py
    python3 _scripts/gerar_produtos.py   # links "Compare com" nas páginas de produto
    python3 _scripts/menu.py
    python3 _scripts/seo.py
"""
import json
import shutil

from gerar_produtos import (CATALOGO, LOJAS, PASSOS, PERIODO, TEXTURA, TIPOS, data_curta, esc, juntar, link_loja,
                            milhar, reais, sem_acento)
from pagina_base import RAIZ, pagina

PARES = RAIZ / "_scripts" / "comparativos.json"
DESTINO = RAIZ / "comparativos"

CSS = """
.cp-tabela-rolagem{overflow-x:auto;margin:16px 0}
.cp-tabela{width:100%;border-collapse:collapse;font-size:.94rem;table-layout:fixed}
.cp-tabela td,.cp-tabela th{overflow-wrap:anywhere}
.cp-tabela th,.cp-tabela td{padding:10px 12px;border-bottom:1px solid var(--linha);text-align:left;vertical-align:top}
.cp-tabela thead th{font-family:var(--fonte-display);font-size:1.05rem;font-weight:500}
.cp-tabela tbody th{font-weight:600;color:var(--suave);width:28%}
.cp-btns{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:16px 0}
.cp-btn{display:flex;align-items:center;justify-content:center;text-align:center;min-height:48px;padding:8px 16px;border-radius:999px;background:var(--rosa);color:#fff;font-weight:600;text-decoration:none}
@media(prefers-color-scheme:dark){.cp-btn{color:#28131b}}
html[data-tema=claro] .cp-btn{color:#fff}html[data-tema=escuro] .cp-btn{color:#28131b}
@media(max-width:560px){.cp-btns{grid-template-columns:1fr}.cp-tabela{font-size:.84rem}.cp-tabela th,.cp-tabela td{padding:8px 6px}.cp-tabela tbody th{width:30%}}
"""


def slug(a, b):
    return f"{a}-ou-{b}"


def pares():
    return json.loads(PARES.read_text(encoding="utf-8"))["pares"]


def tipos_txt(p):
    t = [TIPOS.get(x, (x, None))[0] for x in p.get("tipos", [])]
    return ", ".join(t) or "—"


def quando(p):
    per = [x for x in ("manha", "noite") if x in p.get("periodo", [])]
    return {("manha",): "Manhã", ("noite",): "Noite", ("manha", "noite"): "Manhã e noite"}.get(tuple(per), "—")


def nota(p):
    if p.get("avaliacao") and p.get("num_avaliacoes"):
        return f'{str(p["avaliacao"]).replace(".", ",")} de 5 ({milhar(p["num_avaliacoes"])} avaliações na {LOJAS.get(p.get("plataforma"), "loja")})'
    return "—"


def base_ativo(a):
    """'niacinamida 10%' -> 'niacinamida', para achar o que os dois têm em comum."""
    return sem_acento(" ".join(w for w in a.split() if not any(c.isdigit() for c in w))).strip()


def resumo(a, b):
    linhas = []
    if a["preco"] != b["preco"]:
        barato, caro = (a, b) if a["preco"] < b["preco"] else (b, a)
        dif = caro["preco"] - barato["preco"]
        linhas.append(f"Na conferência de preços, o {barato['nome']} custava {reais(dif)} a menos que o {caro['nome']}. "
                      "Compare também o tamanho da embalagem no anúncio, que muda o preço por ml.")
    else:
        linhas.append("Os dois tinham o mesmo preço na última conferência.")
    ba, bb = {base_ativo(x): x for x in a.get("ativos", [])}, {base_ativo(x): x for x in b.get("ativos", [])}
    # Em comum: só o nome do ativo, sem a concentração (um anúncio pode citar "retinol 0,3%" e o outro só "retinol").
    comuns = [" ".join(w for w in ba[k].split() if not any(c.isdigit() for c in w)) for k in ba if k in bb]
    so_a = [ba[k] for k in ba if k not in bb]
    so_b = [bb[k] for k in bb if k not in ba]
    if comuns:
        linhas.append(f"Ativos em comum, segundo os anúncios: {juntar(comuns)}.")
    if so_a:
        linhas.append(f"Só o {a['nome']} destaca {juntar(so_a)}.")
    if so_b:
        linhas.append(f"Só o {b['nome']} destaca {juntar(so_b)}.")
    ta, tb = set(a.get("tipos", [])) - {"todos"}, set(b.get("tipos", [])) - {"todos"}
    if ta != tb and ta and tb:
        extra_a = [TIPOS.get(x, (x, None))[0].lower() for x in sorted(ta - tb)]
        extra_b = [TIPOS.get(x, (x, None))[0].lower() for x in sorted(tb - ta)]
        if extra_a:
            linhas.append(f"No catálogo, só o {a['nome']} aparece para {juntar(extra_a)}.")
        if extra_b:
            linhas.append(f"No catálogo, só o {b['nome']} aparece para {juntar(extra_b)}.")
    if a.get("textura") != b.get("textura") and a.get("textura") and b.get("textura"):
        linhas.append(f"Textura: {TEXTURA.get(a['textura'], a['textura'])} no {a['nome']} e "
                      f"{TEXTURA.get(b['textura'], b['textura'])} no {b['nome']}.")
    return linhas


def pagina_par(a, b):
    titulo = f"{a['nome']} ou {b['nome']}?"
    linhas = [
        ("Preço conferido", lambda p: f"{reais(p['preco'])} em {data_curta(p['preco_em'])}"),
        ("Loja", lambda p: LOJAS.get(p.get("plataforma"), "—")),
        ("Passo da rotina", lambda p: PASSOS.get(p["passo"], p["passo"])),
        ("Quando usar", quando),
        ("Textura", lambda p: TEXTURA.get(p.get("textura"), p.get("textura") or "—")),
        ("Tipos de pele no catálogo", tipos_txt),
        ("Talvez não seja para", lambda p: ", ".join(TIPOS.get(x, (x, None))[0] for x in p.get("evitar", [])) or "—"),
        ("Ativos em destaque", lambda p: ", ".join(p.get("ativos", [])) or "—"),
        ("Marca e origem", lambda p: " · ".join(x for x in [p.get("marca"), p.get("origem")] if x) or "—"),
        ("Nota de quem comprou", nota),
    ]
    corpo_tabela = "".join(f"<tr><th scope=\"row\">{esc(r)}</th><td>{esc(f(a))}</td><td>{esc(f(b))}</td></tr>" for r, f in linhas)
    tabela = (f'<div class="cp-tabela-rolagem"><table class="cp-tabela"><caption class="ig-rotulo">Lado a lado</caption>'
              f'<thead><tr><td></td><th scope="col"><a href="/produtos/{esc(a["id"])}/">{esc(a["nome"])}</a></th>'
              f'<th scope="col"><a href="/produtos/{esc(b["id"])}/">{esc(b["nome"])}</a></th></tr></thead>'
              f"<tbody>{corpo_tabela}</tbody></table></div>")
    resumo_html = "".join(f"<li>{esc(x)}</li>" for x in resumo(a, b))
    btns = "".join(f'<a class="cp-btn" href="{esc(p["link"])}" target="_blank" rel="sponsored noopener" '
                   f'data-produto="{esc(p["nome"])}">{esc(link_loja(p))}: {esc(p["marca"])} ↗</a>' for p in (a, b))
    datas = sorted({a["preco_em"], b["preco_em"]})
    corpo = f"""<article>
<div class="ig-cab">
<h1>{esc(titulo)}</h1>
<p class="ig-meta">Comparativo com dados do catálogo · Preços conferidos em <time datetime="{datas[-1]}">{data_curta(datas[-1])}</time></p>
<p class="ig-lede">Os dois são opções de {esc(PASSOS.get(a['passo'], a['passo']).lower())} no nosso catálogo. Esta página põe lado a lado o que sabemos de cada um, sem eleger um vencedor: a escolha depende da sua pele e do seu orçamento.</p>
</div>
<div class="ig-caixa ig-resumo">
<p class="ig-rotulo">O que muda entre os dois</p>
<ul>{resumo_html}</ul>
</div>
{tabela}
<p class="ig-nota">"Ativos em destaque" são os que o anúncio destaca, não a fórmula completa. A lista de ingredientes (INCI) está na embalagem e no anúncio; cole as duas no <a href="/ferramentas/ingredientes/">verificador de ingredientes</a> para checar combinações com a sua rotina.</p>
<div class="cp-btns">{btns}</div>
<p class="ig-nota">Links de afiliado: se você comprar por eles, posso receber comissão, sem custo extra. O preço muda: vale o mostrado na loja na hora da compra.</p>
<section aria-labelledby="relacionados">
<h2 id="relacionados">Leia também</h2>
<ul class="ig-rel">
<li><a href="/produtos/{esc(a['id'])}/">{esc(a['nome'])}</a></li>
<li><a href="/produtos/{esc(b['id'])}/">{esc(b['nome'])}</a></li>
<li><a href="/comparativos/">Outros comparativos</a></li>
<li><a href="/ferramentas/comparar/">Comparar outros produtos</a></li>
<li><a href="/provador/">Quiz do tipo de pele</a></li>
</ul>
</section>
</article>"""
    descricao = (f"{a['nome']} ou {b['nome']}: preço conferido, ativos em destaque, textura e tipos de pele lado a lado, "
                 "com dados do catálogo.")[:300]
    return pagina(titulo, descricao, f"/comparativos/{slug(a['id'], b['id'])}/",
                  [("/", "Início"), ("/comparativos/", "Comparativos"), (None, f"{a['marca']} ou {b['marca']}")],
                  corpo, css_extra=CSS)


def pagina_indice(itens):
    cards = "".join(f'<li><a class="ig-card" href="/comparativos/{esc(slug(a["id"], b["id"]))}/"><h3>{esc(a["nome"])} ou {esc(b["nome"])}</h3>'
                    f'<p>{esc(PASSOS.get(a["passo"], a["passo"]))} · {reais(a["preco"])} e {reais(b["preco"])}</p></a></li>' for a, b in itens)
    corpo = f"""<article>
<div class="ig-cab">
<h1>Comparativos: qual dos dois?</h1>
<p class="ig-lede">Produtos parecidos do catálogo, lado a lado: preço conferido, ativos em destaque, textura e tipos de pele. Para comparar outros, use a <a href="/ferramentas/comparar/">ferramenta de comparar</a>.</p>
</div>
<ul class="ig-grade">{cards}</ul>
<p class="ig-nota">Contém links de afiliado. Veja <a href="/sobre/">como escolhemos os produtos</a>.</p>
</article>"""
    return pagina("Comparativos de produtos de skincare: qual dos dois?",
                  "Produtos de skincare parecidos lado a lado: preço conferido, ativos em destaque, textura e tipos de pele, com dados do catálogo.",
                  "/comparativos/", [("/", "Início"), (None, "Comparativos")], corpo, larga=True)


def main():
    produtos = {p["id"]: p for p in json.loads(CATALOGO.read_text(encoding="utf-8-sig"))["produtos"]}
    itens = []
    for a, b in pares():
        if a not in produtos or b not in produtos:
            print(f"pulei {a} ou {b}: produto fora do catálogo")
            continue
        if produtos[a]["passo"] != produtos[b]["passo"]:
            print(f"pulei {a} ou {b}: passos diferentes")
            continue
        itens.append((produtos[a], produtos[b]))
    DESTINO.mkdir(exist_ok=True)
    validos = {slug(a["id"], b["id"]) for a, b in itens}
    for pasta in DESTINO.iterdir():
        if pasta.is_dir() and pasta.name not in validos:
            shutil.rmtree(pasta)
    for a, b in itens:
        d = DESTINO / slug(a["id"], b["id"])
        d.mkdir(exist_ok=True)
        (d / "index.html").write_text(pagina_par(a, b), encoding="utf-8")
    (DESTINO / "index.html").write_text(pagina_indice(itens), encoding="utf-8")
    print(f"{len(itens)} comparativos gerados em /comparativos/")


if __name__ == "__main__":
    main()
