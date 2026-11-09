"""Gera uma página por produto do catálogo (/produtos/<id>/) e o índice /produtos/.

Fonte única: /produtos.json. Rode depois de mudar o catálogo ou os preços:

    python3 _scripts/gerar_produtos.py
    python3 _scripts/seo.py

Histórico de preço: a cada execução, o preço atual (preco + preco_em) de cada
produto entra em /produtos/historico-precos.json, se aquela data ainda não
estiver lá. Assim o histórico cresce sozinho conforme os preços são atualizados.

O script NÃO inventa a lista de ingredientes (INCI): a página manda conferir no
anúncio ou na embalagem e oferece o verificador de ingredientes.
"""
import json
import re
import shutil
import unicodedata
from pathlib import Path
from urllib.parse import quote

from pagina_base import RAIZ, esc, pagina


def comparativos_de(pid):
    """Comparativos (/comparativos/) que incluem o produto, lidos de _scripts/comparativos.json."""
    pares = json.loads((RAIZ / "_scripts" / "comparativos.json").read_text(encoding="utf-8"))["pares"]
    return [(f"/comparativos/{a}-ou-{b}/", b if a == pid else a) for a, b in pares if pid in (a, b)]

CATALOGO = RAIZ / "produtos.json"
FICHAS = RAIZ / "ingredientes" / "ingredientes.json"
DESTINO = RAIZ / "produtos"
HISTORICO = DESTINO / "historico-precos.json"

LOJAS = {"amazon": "Amazon", "shopee": "Shopee", "mercadolivre": "Mercado Livre", "tiktok": "TikTok Shop"}
PASSOS = {"limpeza": "Limpeza", "tratamento": "Tratamento (sérum)", "hidratacao": "Hidratante", "protetor": "Protetor solar"}
ORDEM_PASSOS = ["limpeza", "tratamento", "hidratacao", "protetor"]
TIPOS = {"oleosa": ("Pele oleosa", "/pele/oleosa/"), "seca": ("Pele seca", "/pele/seca/"), "mista": ("Pele mista", "/pele/mista/"),
         "normal": ("Pele normal", "/pele/normal/"), "sensivel": ("Pele sensível", None), "todos": ("Todos os tipos", None)}
CONC = {"acne": ("Acne", "/condicoes/acne/"), "poros": ("Poros aparentes", None), "manchas": ("Manchas e tom irregular", None),
        "idade": ("Sinais de idade", None), "desidratacao": ("Desidratação", "/condicoes/desidratacao/")}
PERIODO = {"manha": "manhã", "noite": "noite"}
TEXTURA = {"serum": "sérum", "gel": "gel", "creme": "creme"}
SELOS = {"forte": "Evidência forte", "moderada": "Evidência moderada", "emergente": "Evidência emergente"}
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]


def sem_acento(t):
    return "".join(c for c in unicodedata.normalize("NFD", str(t).lower()) if unicodedata.category(c) != "Mn")


def data_br(iso):
    a, m, d = iso.split("-")
    return f"{int(d)} de {MESES[int(m) - 1]} de {a}"


def data_curta(iso):
    a, m, d = iso.split("-")
    return f"{d}/{m}/{a}"


def reais(v):
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def milhar(n):
    return f"{n:,}".replace(",", ".")


def link_loja(p):
    loja = LOJAS.get(p.get("plataforma"), "loja")
    busca = "/search?" in p["link"] or "/s?" in p["link"]
    return ("Buscar na " if busca else "Ver na ") + loja


def ficha_do_ativo(ativo, fichas):
    a = sem_acento(re.sub(r"[\d,.%]+", "", ativo)).strip()
    for f in fichas:
        if sem_acento(f["nome"]) == a or f["slug"].replace("-", " ") == a.replace("-", " "):
            return f
    return None


def atualizar_historico(produtos):
    hist = {}
    if HISTORICO.exists():
        hist = json.loads(HISTORICO.read_text(encoding="utf-8"))
    for p in produtos:
        pontos = hist.setdefault(p["id"], [])
        if not any(x["em"] == p["preco_em"] for x in pontos):
            pontos.append({"em": p["preco_em"], "preco": p["preco"], "loja": p.get("plataforma", "")})
        pontos.sort(key=lambda x: x["em"])
    HISTORICO.write_text(json.dumps(hist, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return hist


def juntar(itens):
    itens = [i for i in itens if i]
    return itens[0] if len(itens) == 1 else ", ".join(itens[:-1]) + " e " + itens[-1]


def perguntas_produto(p):
    """Perguntas frequentes montadas só com os dados do catálogo (nada é inventado)."""
    loja = LOJAS.get(p.get("plataforma"), "loja")
    passo = PASSOS.get(p["passo"], p["passo"]).lower()
    periodo = " e ".join(PERIODO.get(x, x) for x in p.get("periodo", []))
    quando = {("manha",): "de manhã", ("noite",): "à noite", ("manha", "noite"): "de manhã e à noite"}.get(
        tuple(x for x in ("manha", "noite") if x in p.get("periodo", [])), f"de {periodo}")
    tipos = [TIPOS.get(t, (t, None))[0].lower() for t in p.get("tipos", []) if t != "todos"]
    evitar = [TIPOS.get(t, (t, None))[0].lower() for t in p.get("evitar", [])]
    nome = p["nome"]
    faq = []
    if tipos or "todos" in p.get("tipos", []):
        r = (f"No nosso catálogo, ele aparece para {juntar(tipos)}" if tipos else "No nosso catálogo, ele aparece para todos os tipos de pele")
        r += " (também marcado como opção para todos os tipos)." if tipos and "todos" in p.get("tipos", []) else "."
        if evitar:
            r += f" Talvez não seja a melhor escolha para {juntar(evitar)}."
        r += " Se não sabe seu tipo de pele, o quiz do provador ajuda a descobrir."
        faq.append((f"Para que tipo de pele é o {nome}?", r))
    if periodo:
        faq.append((f"Uso o {nome} de manhã ou à noite?",
                    f"Ele entra na rotina no passo “{passo}”, {quando}."))
    if p.get("ativos"):
        faq.append((f"Quais são os ativos em destaque do {nome}?",
                    f"Os ativos destacados no anúncio são {juntar(p['ativos'])}. A lista completa de ingredientes (INCI) "
                    "está na embalagem e no anúncio, e pode mudar entre lotes e versões."))
    faq.append((f"Quanto custa o {nome}?",
                f"Na última conferência, em {data_curta(p['preco_em'])}, custava {reais(p['preco'])} na {loja}. "
                "O preço muda com frequência: vale o mostrado na loja na hora da compra."))
    faq.append(("Posso usar junto com os outros produtos da minha rotina?",
                "Depende dos ativos de cada produto. Cole a lista de ingredientes no verificador de ingredientes do site "
                "para checar combinações. Em caso de irritação persistente, procure um dermatologista."))
    return faq


def bloco_faq(faq):
    itens = "".join(f"<details class=\"pd-faq\"><summary>{esc(q)}</summary><p>{esc(r)}</p></details>" for q, r in faq)
    ld = {"@context": "https://schema.org", "@type": "FAQPage",
          "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": r}} for q, r in faq]}
    ld_txt = json.dumps(ld, ensure_ascii=False).replace("</", "<\\/")
    return (f'<section aria-labelledby="faq"><h2 id="faq">Perguntas frequentes</h2>{itens}'
            f'<script type="application/ld+json">{ld_txt}</script></section>')


CSS = """
.pd-faq{border:1px solid var(--linha);border-radius:var(--raio-md);background:var(--papel);margin:8px 0;padding:0 16px}
.pd-faq summary{cursor:pointer;font-weight:600;min-height:48px;display:flex;align-items:center;padding:10px 0}
.pd-faq p{margin:0 0 14px}
.pd-topo{display:flex;flex-wrap:wrap;gap:6px 10px;align-items:center}
.pd-tag{display:inline-block;font-size:.76rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;padding:4px 12px;border-radius:999px;background:var(--papel-2);color:var(--tinta)}
.pd-tag.refil{background:var(--verde-claro);color:var(--verde)}
.pd-compra{display:flex;flex-direction:column;gap:10px}
.pd-preco{font-family:var(--fonte-display);font-size:2.2rem;line-height:1;margin:0}
.pd-btns{display:flex;flex-wrap:wrap;gap:8px}
.pd-btn{display:inline-flex;align-items:center;justify-content:center;min-height:48px;padding:0 22px;border-radius:999px;background:var(--rosa);color:#fff;font-weight:600;text-decoration:none}
.pd-btn.sec{background:transparent;color:var(--tinta);border:1px solid var(--linha-2)}
@media(prefers-color-scheme:dark){.pd-btn:not(.sec){color:#28131b}}
html[data-tema=claro] .pd-btn:not(.sec){color:#fff}html[data-tema=escuro] .pd-btn:not(.sec){color:#28131b}
.pd-lista{list-style:none;padding:0;margin:0;display:flex;flex-wrap:wrap;gap:8px}
.pd-lista li{margin:0}
.pd-lista span,.pd-lista a{display:inline-flex;align-items:center;min-height:36px;padding:4px 12px;border:1px solid var(--linha-2);border-radius:999px;font-size:.92rem;text-decoration:none;color:var(--tinta)}
.pd-lista a:hover{border-color:var(--rosa)}
.pd-ativos{list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:8px}
.pd-ativos li{margin:0;padding:12px 14px;border:1px solid var(--linha);border-radius:var(--raio-md);background:var(--papel)}
.pd-ativos .ig-selo{margin:0 0 0 8px;vertical-align:middle}
.pd-grupo{margin-top:8px}
"""


def pagina_produto(p, fichas, hist, todos):
    loja = LOJAS.get(p.get("plataforma"), "loja")
    passo = PASSOS.get(p["passo"], p["passo"])
    refil = "refil" in sem_acento(p["nome"])
    tags = [f'<span class="pd-tag">{esc(passo)}</span>']
    if refil:
        tags.append('<span class="pd-tag refil">Refil</span>')
    meta = " · ".join(x for x in [p.get("marca"), TEXTURA.get(p.get("textura"), p.get("textura")), p.get("origem")] if x)

    tipos = []
    for t in p.get("tipos", []):
        nome, url = TIPOS.get(t, (t, None))
        tipos.append(f'<li><a href="{url}">{esc(nome)}</a></li>' if url else f"<li><span>{esc(nome)}</span></li>")
    conc = []
    for c in p.get("conc", []):
        nome, url = CONC.get(c, (c, None))
        conc.append(f'<li><a href="{url}">{esc(nome)}</a></li>' if url else f"<li><span>{esc(nome)}</span></li>")
    evitar = [TIPOS.get(t, (t, None))[0].lower() for t in p.get("evitar", [])]
    periodo = " e ".join(PERIODO.get(x, x) for x in p.get("periodo", []))

    ativos = []
    for a in p.get("ativos", []):
        f = ficha_do_ativo(a, fichas)
        if f:
            selo = SELOS.get(f.get("evidencia"), "")
            cls = f.get("evidencia", "")
            ativos.append(f'<li><a href="{esc(f["url"])}">{esc(a)}</a>' +
                          (f'<span class="ig-selo {esc(cls)}">{esc(selo)}</span>' if selo else "") +
                          f'<br><span class="ig-nota">{esc(f.get("resumo", ""))}</span></li>')
        else:
            ativos.append(f"<li>{esc(a)}</li>")

    pontos = hist.get(p["id"], [])
    if len(pontos) >= 2:
        linhas = "".join(f"<tr><td>{data_curta(x['em'])}</td><td>{reais(x['preco'])}</td><td>{esc(LOJAS.get(x.get('loja'), x.get('loja', '')))}</td></tr>" for x in reversed(pontos))
        historico = f'<table class="ig-tabela"><caption>Preços conferidos</caption><thead><tr><th>Data</th><th>Preço</th><th>Loja</th></tr></thead><tbody>{linhas}</tbody></table>'
    else:
        historico = f'<p>Primeiro preço registrado: {reais(p["preco"])} em {data_curta(p["preco_em"])}. O histórico aparece aqui conforme o preço é conferido de novo.</p>'

    parecidos = [q for q in todos if q["id"] != p["id"] and q["passo"] == p["passo"] and
                 (q.get("grupo") == p.get("grupo") or set(q.get("tipos", [])) & set(p.get("tipos", [])) - {"todos"})]
    parecidos.sort(key=lambda q: (q.get("grupo") != p.get("grupo"), q["preco"]))
    alt = "".join(f'<li><a href="/produtos/{esc(q["id"])}/">{esc(q["nome"])}</a> <span class="ig-nota">{reais(q["preco"])} em {data_curta(q["preco_em"])}</span></li>' for q in parecidos[:4])

    avaliacao = ""
    if p.get("avaliacao") and p.get("num_avaliacoes"):
        avaliacao = (f'<p class="ig-nota">Nota {str(p["avaliacao"]).replace(".", ",")} de 5 em {milhar(p["num_avaliacoes"])} avaliações na {esc(loja)}, '
                     f'conferida em {data_curta(p["preco_em"])}. A nota é de quem comprou na loja, não uma avaliação do site.</p>')

    nomes = {q["id"]: q["nome"] for q in todos}
    compare = "".join(f'<li><a href="{url}">Compare com {esc(nomes.get(outro, outro))}</a></li>'
                      for url, outro in comparativos_de(p["id"]))
    evitar_txt = f"<li><b>Talvez não seja para:</b> {esc(', '.join(evitar))}.</li>" if evitar else ""
    corpo = f"""<article>
<div class="ig-cab">
<div class="pd-topo">{''.join(tags)}</div>
<h1>{esc(p['nome'])}</h1>
<p class="ig-meta">{esc(meta)} · Atualizado em <time datetime="{p['preco_em']}">{data_br(p['preco_em'])}</time></p>
<p class="ig-lede">{esc(p.get('porque', ''))}</p>
</div>
<div class="ig-caixa pd-compra">
<p class="ig-rotulo">Preço conferido</p>
<p class="pd-preco">{reais(p['preco'])}</p>
<p class="ig-nota">Na {esc(loja)}, em {data_curta(p['preco_em'])}. Preço muda: vale o mostrado na loja na hora da compra.</p>
<div class="pd-btns">
<a class="pd-btn" href="{esc(p['link'])}" target="_blank" rel="sponsored noopener" data-produto="{esc(p['nome'])}">{esc(link_loja(p))} ↗</a>
<a class="pd-btn sec" href="/ferramentas/reposicao/?produto={esc(quote(p['nome']))}">Lembrete de reposição</a>
<a class="pd-btn sec" href="/ferramentas/comparar/">Comparar</a>
</div>
<p class="ig-nota">Link de afiliado: se você comprar por ele, posso receber comissão, sem custo extra. Confira vendedor, tamanho e condições no anúncio.</p>
</div>
<div class="ig-caixa ig-resumo">
<p class="ig-rotulo">Em poucas palavras</p>
<ul>
<li><b>Passo da rotina:</b> {esc(passo.lower())}{(', de ' + esc(periodo)) if periodo else ''}.</li>
{evitar_txt}
</ul>
</div>
<section aria-labelledby="para-quem">
<h2 id="para-quem">Para quem faz mais sentido</h2>
<ul class="pd-lista">{''.join(tipos)}</ul>
{('<p class="pd-grupo">Costuma ser escolhido para:</p><ul class="pd-lista">' + ''.join(conc) + '</ul>') if conc else ''}
<p class="ig-nota">Não sabe seu tipo de pele? Faça o <a href="/provador/">quiz do provador</a>.</p>
</section>
<section aria-labelledby="ativos">
<h2 id="ativos">Ativos em destaque</h2>
{('<ul class="pd-ativos">' + ''.join(ativos) + '</ul>') if ativos else '<p>O anúncio não destaca um ativo principal.</p>'}
<p class="ig-nota">O selo de evidência avalia o ativo em geral, não esta fórmula. <a href="/sobre/">Como classificamos</a>.</p>
</section>
<section aria-labelledby="inci">
<h2 id="inci">Lista completa de ingredientes</h2>
<p>A lista completa (INCI) está na embalagem e no anúncio, e pode mudar entre lotes e versões. Não copiamos a lista aqui para não mostrar uma versão desatualizada.</p>
<p>Copie a lista do anúncio, ou fotografe o rótulo, e cole no <a href="/ferramentas/ingredientes/">verificador de ingredientes</a> para checar combinações com o resto da sua rotina.</p>
</section>
<section aria-labelledby="historico">
<h2 id="historico">Histórico de preço</h2>
{historico}
{avaliacao}
</section>
{bloco_faq(perguntas_produto(p))}
{('<section aria-labelledby="alternativas"><h2 id="alternativas">Alternativas do catálogo</h2><ul>' + alt + '</ul></section>') if alt else ''}
<section aria-labelledby="relacionados">
<h2 id="relacionados">Leia também</h2>
<ul class="ig-rel">
{compare}<li><a href="/produtos/">Todos os produtos</a></li>
<li><a href="/rotina-de-skincare/">Rotina passo a passo</a></li>
<li><a href="/blog/ordem-dos-produtos-skincare/">Ordem dos produtos</a></li>
</ul>
</section>
</article>"""
    descricao = f"{p['nome']}: para quem é, ativos em destaque, preço conferido em {data_curta(p['preco_em'])} e alternativas. {p.get('porque', '')}"[:300]
    return pagina(p["nome"], descricao, f"/produtos/{p['id']}/",
                  [("/", "Início"), ("/produtos/", "Produtos"), (None, p["nome"])], corpo, css_extra=CSS)


# Filtro do índice: mesmas faixas de preço do provador (teto por produto).
FAIXAS_FILTRO = [("qualquer", "Sem limite"), ("50", "Até R$ 50"), ("100", "Até R$ 100"), ("200", "Até R$ 200")]
TIPOS_FILTRO = [("", "Todos"), ("oleosa", "Pele oleosa"), ("seca", "Pele seca"), ("mista", "Pele mista"),
                ("normal", "Pele normal"), ("sensivel", "Pele sensível")]

CSS_INDICE = """
.ig [hidden]{display:none!important}
.ig .ig-grade{padding:0;margin:0}
.ig .pf-status{margin:0}
.ig-card h3{font-size:1.25rem;margin:0}
.pf-filtros{display:grid;grid-template-columns:1fr;gap:12px;padding:16px;border:1px solid var(--linha);border-radius:var(--raio);background:var(--papel)}
.pf-campo{display:flex;flex-direction:column;gap:6px;min-width:0}
.pf-campo label{font-size:.78rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--suave)}
.pf-campo input,.pf-campo select{font:inherit;font-size:16px;width:100%;min-height:48px;padding:10px 14px;border:1px solid var(--linha-2);border-radius:var(--raio-md);background:var(--fundo);color:var(--tinta)}
.pf-campo input:focus-visible,.pf-campo select:focus-visible{outline:2px solid var(--rosa);outline-offset:1px}
.pf-status{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:8px;margin:0;font-size:.92rem;color:var(--suave)}
.pf-limpar{font:inherit;font-size:.92rem;min-height:44px;padding:0 16px;border:1px solid var(--linha-2);border-radius:999px;background:transparent;color:var(--tinta);cursor:pointer}
.pf-limpar:hover{border-color:var(--rosa)}
.pf-vazio{text-align:center}
.pf-vazio p{margin:0 0 12px}
.pf-vazio .pf-limpar{margin-top:4px}
@media(min-width:700px){.pf-filtros{grid-template-columns:1.4fr 1fr 1fr}.pf-status{grid-column:1/-1}}
"""

JS_INDICE = """<script>
(function () {
  var busca = document.getElementById("pf-busca"), tipo = document.getElementById("pf-tipo"), preco = document.getElementById("pf-preco");
  var cards = [].slice.call(document.querySelectorAll("[data-pf-nome]"));
  var secoes = [].slice.call(document.querySelectorAll("[data-pf-secao]"));
  var contagem = document.getElementById("pf-contagem"), vazio = document.getElementById("pf-vazio");
  var limpar = [].slice.call(document.querySelectorAll("[data-pf-limpar]"));
  function norm(t) { return (t || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim(); }
  function cabe(li) {
    var termo = norm(busca.value), t = tipo.value, teto = preco.value;
    if (termo && li.getAttribute("data-pf-nome").indexOf(termo) < 0) return false;
    if (t) {
      var tipos = li.getAttribute("data-pf-tipos").split(" ");
      // "Todos os tipos" vale para oleosa, seca, mista e normal; pele sensível só quando o catálogo diz.
      if (tipos.indexOf(t) < 0 && !(t !== "sensivel" && tipos.indexOf("todos") >= 0)) return false;
    }
    if (teto !== "qualquer" && !(parseFloat(li.getAttribute("data-pf-preco")) <= parseFloat(teto))) return false;
    return true;
  }
  function aplicar() {
    var n = 0;
    cards.forEach(function (li) { var ok = cabe(li); li.hidden = !ok; if (ok) n++; });
    secoes.forEach(function (s) { s.hidden = !s.querySelector("[data-pf-nome]:not([hidden])"); });
    var filtrando = busca.value.trim() || tipo.value || preco.value !== "qualquer";
    contagem.textContent = filtrando ? n + " de " + cards.length + " produtos" : cards.length + " produtos";
    limpar[0].hidden = !filtrando;
    vazio.hidden = n > 0;
  }
  [busca, tipo, preco].forEach(function (el) { el.addEventListener("input", aplicar); el.addEventListener("change", aplicar); });
  limpar.forEach(function (b) { b.addEventListener("click", function () { busca.value = ""; tipo.value = ""; preco.value = "qualquer"; aplicar(); busca.focus(); }); });
  document.getElementById("pf-form").addEventListener("submit", function (e) { e.preventDefault(); });
  document.getElementById("pf-form").hidden = false;
  aplicar();
})();
</script>"""


def pagina_indice(produtos):
    grupos = []
    for passo in ORDEM_PASSOS:
        itens = sorted((p for p in produtos if p["passo"] == passo), key=lambda p: p["preco"])
        if not itens:
            continue
        cards = "".join(
            f'<li data-pf-nome="{esc(sem_acento(" ".join([p["nome"], p.get("marca", "")] + p.get("ativos", []))))}" '
            f'data-pf-tipos="{esc(" ".join(p.get("tipos", [])))}" data-pf-preco="{p["preco"]}">'
            f'<a class="ig-card" href="/produtos/{esc(p["id"])}/"><h3>{esc(p["nome"])}</h3>'
            f'<p>{esc(p.get("marca", ""))} · {reais(p["preco"])} em {data_curta(p["preco_em"])}</p></a></li>' for p in itens)
        grupos.append(f'<section data-pf-secao aria-labelledby="g-{passo}"><h2 id="g-{passo}">{esc(PASSOS[passo])}</h2><ul class="ig-grade">{cards}</ul></section>')
    tipos = "".join(f'<option value="{v}">{esc(r)}</option>' for v, r in TIPOS_FILTRO)
    faixas = "".join(f'<option value="{v}">{esc(r)}</option>' for v, r in FAIXAS_FILTRO)
    filtros = f"""<form class="pf-filtros" id="pf-form" role="search" aria-label="Buscar e filtrar produtos" hidden>
<div class="pf-campo"><label for="pf-busca">Buscar</label><input id="pf-busca" type="search" placeholder="Nome, marca ou ativo" autocomplete="off" enterkeyhint="search"></div>
<div class="pf-campo"><label for="pf-tipo">Tipo de pele</label><select id="pf-tipo">{tipos}</select></div>
<div class="pf-campo"><label for="pf-preco">Preço por produto</label><select id="pf-preco">{faixas}</select></div>
<p class="pf-status"><span id="pf-contagem" aria-live="polite">{len(produtos)} produtos</span><button type="button" class="pf-limpar" data-pf-limpar hidden>Limpar filtros</button></p>
</form>
<div class="ig-caixa pf-vazio" id="pf-vazio" hidden>
<p><strong>Nenhum produto com esses filtros.</strong></p>
<p class="ig-nota">Tente outro nome, outro tipo de pele ou uma faixa de preço maior.</p>
<button type="button" class="pf-limpar" data-pf-limpar>Limpar filtros</button>
</div>"""
    corpo = f"""<article>
<div class="ig-cab">
<h1>Produtos do catálogo</h1>
<p class="ig-lede">Cada produto tem uma página com o passo da rotina, o tipo de pele indicado, os ativos em destaque com o nível de evidência, o preço conferido com data e alternativas. Em dúvida entre dois parecidos? Veja os <a href="/comparativos/">comparativos</a>.</p>
</div>
{filtros}
{''.join(grupos)}
<p class="ig-nota">Contém links de afiliado. Veja <a href="/sobre/">como escolhemos os produtos</a>.</p>
</article>"""
    return pagina("Produtos de skincare: preço, ativos e para quem é",
                  "Catálogo de produtos de skincare com página para cada um: tipo de pele, ativos com nível de evidência, preço conferido com data e alternativas.",
                  "/produtos/", [("/", "Início"), (None, "Produtos")], corpo, css_extra=CSS_INDICE, scripts=JS_INDICE, larga=True)


def main():
    produtos = json.loads(CATALOGO.read_text(encoding="utf-8-sig"))["produtos"]
    fichas = json.loads(FICHAS.read_text(encoding="utf-8-sig"))
    DESTINO.mkdir(exist_ok=True)
    hist = atualizar_historico(produtos)
    ids = {p["id"] for p in produtos}
    for pasta in DESTINO.iterdir():
        if pasta.is_dir() and pasta.name not in ids:
            shutil.rmtree(pasta)  # produto saiu do catálogo
    for p in produtos:
        d = DESTINO / p["id"]
        d.mkdir(exist_ok=True)
        (d / "index.html").write_text(pagina_produto(p, fichas, hist, produtos), encoding="utf-8")
    (DESTINO / "index.html").write_text(pagina_indice(produtos), encoding="utf-8")
    print(f"{len(produtos)} páginas de produto geradas em /produtos/")


if __name__ == "__main__":
    main()
