"""Gera o Atlas dos Ativos em /ativos/ (índice interativo dos 88 ativos).

Uso:  python -I _scripts/gerar_atlas.py        (precisa do Node no PATH)
Depois: python -I _scripts/prontidao.py

Não inventa dado: tudo sai de fontes que já estão no repositório.
  - ferramentas/ativos/index.html  -> base ATIVOS do guia (objetivos, pele, irritação,
                                      nível, turno, concentração, gestação, sol, receita)
                                      e o mapa de fichas (GUIA_ATIVOS_CONFIG.fichas)
  - ingredientes/ingredientes.json -> nível de evidência avaliado (só os ativos com ficha
                                      de estudos; os outros saem "ainda não avaliada")
  - regras-ativos.js               -> classe de combinação de cada ativo (verificador)
  - ativos/*/ e ingredientes/*/    -> data da última revisão de cada ficha (<time>)
  - _scripts/atlas.json            -> nomes e resumos dos cartões, vocabulário da busca,
                                      temas do mapa da pele
  - _scripts/potencia-ativos.json  -> potência (suave a potente) e a frase da ficha que a sustenta.
                                      Evidência só entra se a URL está em ingredientes.json.

Escreve:
  - ativos/atlas-dados.js  (window.ATLAS, lido por ativos/atlas.js)
  - ativos/index.html      (só o trecho entre <!-- atlas:inicio --> e <!-- atlas:fim -->,
                            mais o link do CSS e os scripts; o resto da página fica como está)
"""
import html
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
GUIA = RAIZ / "ferramentas" / "ativos" / "index.html"
REGRAS = RAIZ / "regras-ativos.js"
INDICE = RAIZ / "ativos" / "index.html"
DADOS = RAIZ / "ativos" / "atlas-dados.js"
CFG = RAIZ / "_scripts" / "atlas.json"
POTENCIA = RAIZ / "_scripts" / "potencia-ativos.json"
SEM_FICHA = "sem ficha com fontes ainda"
EV_ROTULO = {"forte": "evidência forte", "moderada": "evidência moderada", "emergente": "evidência emergente"}

NODE = r"""
const fs = require('fs');
const g = fs.readFileSync(process.argv[1], 'utf8').replace(/\r\n/g, '\n');
const a = g.indexOf('var ATIVOS = [');
const b = g.indexOf('\n  ];', a);
if (a < 0 || b < 0) { console.error('ATIVOS não encontrado no guia'); process.exit(2); }
const ATIVOS = eval(g.slice(a + 'var ATIVOS = '.length, b + 4));
const R = require(process.argv[2]);
const out = ATIVOS.map(function (x) {
  var classes = [];
  if (x.cat === 'Filtros solares') classes = ['filtro'];
  else R.detectar(x.n + ', ' + x.inci).forEach(function (d) { if (classes.indexOf(d.classe) < 0) classes.push(d.classe); });
  x.classes = classes;
  return x;
});
process.stdout.write(JSON.stringify({ ativos: out, versaoRegras: R.VERSAO }));
"""

OBJETIVOS = {
    "acne": "Acne e cravos", "oleosidade": "Oleosidade e poros", "manchas": "Manchas e melasma",
    "rugas": "Rugas e firmeza", "textura": "Textura e falta de viço", "hidratacao": "Desidratação",
    "barreira": "Ressecamento e barreira danificada", "sensibilidade": "Sensibilidade e vermelhidão",
    "olheiras": "Olheiras e inchaço", "protecao": "Proteção solar",
}
PELES = {"oleosa": "oleosa", "mista": "mista", "normal": "normal", "seca": "seca", "sensivel": "sensível"}
EVID = {"forte": 3, "moderada": 2, "emergente": 1}
IRRITA = {0: "baixa", 1: "moderada", 2: "alta"}
NIVEL = {1: "iniciante", 2: "intermediário", 3: "avançado"}
POT_ROTULO = {1: "suave", 2: "moderada", 3: "alta", 4: "potente"}
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto",
         "setembro", "outubro", "novembro", "dezembro"]
# Fora do leitor de rótulo, como no verificador: ácido cítrico costuma ser só ajuste de pH.
ROTULO_FORA = {"citric acid"}


def norm(s):
    s = unicodedata.normalize("NFD", str(s))
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn").lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def esc(s):
    return html.escape(str(s), quote=True)


def data_longa(iso):
    a, m, d = iso.split("-")
    return "%d de %s de %s" % (int(d), MESES[int(m) - 1], a)


def gest_ficha(pagina):
    """Frase da ficha curta (<b>Gestação:</b>). Vazio nas fichas de ingredientes."""
    m = re.search(r"<b>Gestação:</b>\s*([^<]+)", pagina)
    if not m:
        return ""
    t = norm(m.group(1))
    if "evitar" in t:
        return "evitar"
    if "compativel" in t:
        return "compativel"
    if "consulte" in t or "confirme" in t:
        return "consultar"
    return ""


def carregar():
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    potencia = json.loads(POTENCIA.read_text(encoding="utf-8"))
    pot_ativos = potencia.get("ativos") or {}
    r = subprocess.run(["node", "-e", NODE, str(GUIA), str(REGRAS)], capture_output=True)
    if r.returncode != 0:
        sys.exit("node falhou: " + r.stderr.decode("utf-8", "replace"))
    bruto = json.loads(r.stdout.decode("utf-8"))
    guia = GUIA.read_text(encoding="utf-8-sig")
    fichas = json.loads(re.search(r"GUIA_ATIVOS_CONFIG\.fichas = (\{.*?\});", guia).group(1))
    evid = {e["url"]: e for e in json.loads((RAIZ / "ingredientes" / "ingredientes.json").read_text(encoding="utf-8"))}
    cat_id = {c["titulo"]: c["id"] for c in cfg["categorias"]}
    extra = cfg.get("rotulo_extra", {})
    ativos = []
    for x in bruto["ativos"]:
        i = x["id"]
        url = fichas[i]
        pagina = (RAIZ / url.strip("/") / "index.html").read_text(encoding="utf-8-sig")
        m = re.search(r'<time datetime="(\d{4}-\d{2}-\d{2})"', pagina)
        if len(x["classes"]) > 1:
            print("AVISO: %s caiu em mais de uma classe do verificador: %s (fica a primeira)" % (i, x["classes"]))
        e = evid.get(url)
        if e and not url.startswith("/ingredientes/"):
            sys.exit("evidência só pode vir de ficha com fontes: " + i)
        if url.startswith("/ingredientes/") and not e:
            sys.exit("ficha de ingredientes sem evidência em ingredientes.json: " + url)
        gf = gest_ficha(pagina)
        gest = gf or x.get("gest") or ""
        if gf and x.get("gest") and gf != x.get("gest"):
            print("AVISO gestação %s: guia=%s ficha=%s (fica a ficha)" % (i, x.get("gest"), gf))
        pot = pot_ativos.get(i)
        if not pot or pot.get("n") not in POT_ROTULO or not pot.get("nota"):
            sys.exit("potência ausente ou inválida em _scripts/potencia-ativos.json: " + i)
        termos = [norm(p) for p in x["inci"].split("·")]
        termos += [norm(cfg["nomes"][i]), norm(re.sub(r"\(.*?\)", "", x["n"]))]
        termos += [norm(t) for t in extra.get(i, [])]
        rot = []
        for t in termos:
            if len(t) >= 5 and t not in ROTULO_FORA and t not in rot:
                rot.append(t)
        ativos.append({
            "id": i, "n": x["n"], "nome": cfg["nomes"][i], "resumo": cfg["resumos"][i], "inci": x["inci"],
            "cat": x["cat"], "catId": cat_id[x["cat"]], "c": x["c"], "pele": x.get("pele") or [],
            "irrita": x["irrita"], "nivel": x["nivel"], "pot": pot["n"], "potNota": pot["nota"],
            "turno": x["turno"], "conc": x["conc"],
            "gest": gest, "sol": bool(x.get("sol")), "rx": bool(x.get("rx")),
            "d": x["d"], "dica": x.get("dica", ""), "url": url, "rev": m.group(1) if m else "",
            "ev": e["evidencia"] if e else "", "evm": e["evidencia_motivo"] if e else "",
            "classe": cfg.get("classes", {}).get(i) or (x["classes"][0] if x["classes"] else ""), "rot": rot,
        })
    return cfg, ativos, bruto["versaoRegras"]


def barra(n, total, rotulo, classe="", vazia=False):
    segs = "".join('<i class="on"></i>' if k < n else "<i></i>" for k in range(total))
    cls = ((" " + classe) if classe else "") + (" vazia" if vazia else "")
    return '<span class="at-barra%s" aria-hidden="true">%s</span><span class="at-valor">%s</span>' % (cls, segs, esc(rotulo))


def cartao(a, ordem):
    if a["ev"]:
        ev = barra(EVID[a["ev"]], 3, EV_ROTULO[a["ev"]], "ev")
    else:
        ev = barra(0, 3, SEM_FICHA, "ev", vazia=True)
    selos = []
    if a["rx"]:
        selos.append('<span class="at-selo rx">Receita médica</span>')
    if a["gest"] == "evitar":
        selos.append('<span class="at-selo">Evitar na gestação</span>')
    if a["sol"]:
        selos.append('<span class="at-selo">Exige protetor solar</span>')
    if a["ev"]:
        selos.append('<span class="at-selo ok">Ficha com estudos e fontes</span>')
    return (
        '<li class="at-card" id="a-%(id)s" data-id="%(id)s" data-ordem="%(ordem)d">'
        '<h3><a href="%(url)s">%(nome)s</a></h3>'
        '<p class="at-inci">%(inci)s</p>'
        '<p class="at-resumo">%(resumo)s</p>'
        '<dl class="at-medidores">'
        '<div><dt>Evidência</dt><dd>%(ev)s</dd></div>'
        '<div><dt>Potência</dt><dd>%(pot)s</dd></div>'
        '<div><dt>Irritação</dt><dd>%(ir)s</dd></div>'
        '</dl>'
        '%(selos)s'
        '<p class="at-acoes"><button type="button" class="at-bt" data-passaporte="%(id)s">Passaporte</button>'
        '<button type="button" class="at-bt" data-comparar="%(id)s" aria-pressed="false">Comparar</button></p>'
        '</li>'
    ) % {
        "id": a["id"], "ordem": ordem, "url": a["url"], "nome": esc(a["nome"]), "inci": esc(a["inci"]),
        "resumo": a["resumo"], "ev": ev,
        "pot": barra(a["pot"], 4, POT_ROTULO[a["pot"]], "po"),
        "ir": barra(a["irrita"] + 1, 3, IRRITA[a["irrita"]], "ir"),
        "selos": ('<p class="at-selos">%s</p>' % "".join(selos)) if selos else "",
    }


SVG = """<svg class="at-pele" viewBox="0 0 560 380" role="img" aria-labelledby="at-pele-t at-pele-d">
<title id="at-pele-t">Corte ilustrado da pele em camadas</title>
<desc id="at-pele-d">De cima para baixo: radiação solar, superfície (camada córnea), barreira, base da epiderme com melanócitos e derme com fibras de colágeno. Um poro com glândula sebácea atravessa as camadas.</desc>
<g class="at-zona" data-tema="sol"><rect class="at-hit" x="0" y="0" width="560" height="70"/>
<circle class="at-sol" cx="486" cy="6" r="30"/>
<path class="at-raio" d="M440 30l-34 34M470 44l-22 26M500 46l-10 24M418 14l-44 30"/>
<text x="16" y="42">Radiação solar</text></g>
<g class="at-zona" data-tema="superficie"><rect class="at-hit" x="0" y="70" width="560" height="30"/>
<rect class="at-fx c1" x="0" y="70" width="560" height="30"/>
<path class="at-tr" d="M8 80h40M60 78h52M124 81h34M170 79h60M242 81h44M298 78h50M410 80h46M468 79h60M20 91h58M92 90h40M146 92h62M222 90h38M274 92h64M420 91h52M486 90h44"/>
<text x="16" y="89">Superfície</text></g>
<g class="at-zona" data-tema="barreira"><rect class="at-hit" x="0" y="100" width="560" height="56"/>
<rect class="at-fx c2" x="0" y="100" width="560" height="56"/>
<path class="at-tr" d="M0 118h356M404 118h156M0 137h356M404 137h156M60 100v18M150 100v18M240 100v18M330 100v18M450 100v18M520 100v18M30 118v19M110 118v19M200 118v19M290 118v19M430 118v19M500 118v19M70 137v19M160 137v19M250 137v19M336 137v19M460 137v19M530 137v19"/>
<text x="16" y="133">Barreira e hidratação</text></g>
<g class="at-zona" data-tema="pigmentacao"><rect class="at-hit" x="0" y="156" width="560" height="52"/>
<path class="at-fx c3" d="M0 156h560v38c-24 0-28 16-52 16s-28-16-52-16-28 16-52 16-28-16-52-16-28 16-52 16-28-16-52-16-28 16-52 16-28-16-52-16-28 16-52 16-28-16-40-16z"/>
<g class="at-mel"><circle cx="46" cy="190" r="5"/><circle cx="150" cy="190" r="5"/><circle cx="254" cy="190" r="5"/><circle cx="462" cy="190" r="5"/><circle cx="530" cy="184" r="5"/>
<path d="M46 185v-9M40 187l-7-6M52 187l7-6M150 185v-9M144 187l-7-6M156 187l7-6M254 185v-9M248 187l-7-6M260 187l7-6M462 185v-9M456 187l-7-6M468 187l7-6"/></g>
<text x="16" y="174">Pigmentação</text></g>
<g class="at-zona" data-tema="derme"><rect class="at-hit" x="0" y="208" width="560" height="172"/>
<path class="at-col" d="M0 250c40-18 80 18 120 0s80-18 120 0 80 18 120 0M0 290c50 16 90-16 140 0s90 16 140 0 70-14 96-6M0 330c40-16 80 16 120 0s80-16 120 0 80 16 120 0 80-16 200-4M420 300c40-14 70 12 140 2M440 258c36 10 70-10 120 0"/>
<text x="16" y="362">Firmeza (derme)</text></g>
<g class="at-zona" data-tema="poros"><rect class="at-hit" x="352" y="70" width="56" height="230"/>
<path class="at-fol" d="M366 70c2 70-6 150 8 214 3 12 15 12 18 0 14-64 4-144 8-214z"/>
<path class="at-pelo" d="M383 286c-3-90 6-170-2-262"/>
<path class="at-gl" d="M398 200c20-18 46-12 50 10s-14 40-34 34c-14-4-18-16-18-28z"/>
<text x="420" y="270">Poros e oleosidade</text></g>
</svg>"""


def secao_mapa(cfg, ativos):
    cats = [c["titulo"] for c in cfg["categorias"]]
    botoes, paineis = [], []
    for t in cfg["temas"]:
        rel = [a for a in ativos if any(o in a["c"] for o in t["objetivos"])]
        por_cat = {}
        for a in rel:
            por_cat[a["cat"]] = por_cat.get(a["cat"], 0) + 1
        grupos = sorted(por_cat.items(), key=lambda kv: (-kv[1], cats.index(kv[0])))[:4]
        lista = ", ".join("%s (%d)" % (esc(k), v) for k, v in grupos)
        botoes.append('<button type="button" class="at-chip" data-tema="%s" aria-pressed="false">%s</button>' % (t["id"], esc(t["titulo"])))
        paineis.append(
            '<div class="at-tema" id="tema-%s" data-tema="%s" data-objetivos="%s">'
            '<h3>%s</h3><p>%s</p>'
            '<p class="ig-nota">%d ativos do atlas têm este objetivo. Grupos mais frequentes: %s.</p>'
            '<p class="at-acoes"><button type="button" class="at-bt cheio" data-ver-tema="%s">Ver os %d ativos</button></p>'
            '</div>' % (t["id"], t["id"], ",".join(t["objetivos"]), esc(t["titulo"]), esc(t["texto"]),
                        len(rel), lista, t["id"], len(rel)))
    return (
        '<section class="at-mapa" aria-labelledby="mapa-da-pele">'
        '<h2 id="mapa-da-pele">Mapa da pele</h2>'
        '<p>Escolha uma área para ver o que acontece ali e quais grupos de ativos costumam ser usados para aquele objetivo.</p>'
        '<div class="at-mapa-grade"><figure>%s'
        '<figcaption class="ig-nota">Ilustração educativa e fora de escala. Não representa até onde cada produto penetra.</figcaption></figure>'
        '<div class="at-mapa-lado"><p class="at-temas" hidden>%s</p>%s</div></div>'
        '</section>' % (SVG, "".join(botoes), "".join(paineis)))


def corpo(cfg, ativos):
    hoje = max(a["rev"] for a in ativos)
    n = len(ativos)
    n_ev = sum(1 for a in ativos if a["ev"])
    sug = "".join('<button type="button" class="at-chip" data-q="%s">%s</button>' % (esc(s), esc(s)) for s in cfg["sugestoes"])
    nome = {a["id"]: a["nome"] for a in ativos}
    comps = "".join(
        '<li><button type="button" class="at-bt" data-comparacao="%s">%s</button></li>' % (",".join(c["ids"]), esc(c["titulo"]))
        for c in cfg["comparacoes"])
    partes = []
    partes.append(
        '<header class="at-hero">'
        '<p class="at-olho">Fichas de ativos</p>'
        '<h1>Fichas de princípios ativos de skincare</h1>'
        '<p class="ig-meta">Por Equipe Produto Skincare · Atualizado em <time datetime="%s">%s</time></p>'
        '<p class="ig-lede">%d ativos em %d categorias, cada um com uma página curta: o que é, para que serve, para quem, como usar, cuidados, combinações e gestação. '
        'Busque por um objetivo ou pelo nome do ativo. Os %d que já têm <a href="/ingredientes/">ficha com estudos e fontes</a> mostram o nível de evidência; '
        'nos outros %d o cartão diz “%s”, sem inventar uma nota.</p>'
        '<form class="at-busca" id="at-busca" role="search" hidden>'
        '<label for="at-q">Qual preocupação ou ativo você quer ver?</label>'
        '<div class="at-busca-linha"><input id="at-q" name="q" type="search" autocomplete="off" enterkeyhint="search" '
        'placeholder="melasma, acne, poros, pele sensível, gestação ou o nome de um ativo">'
        '<button type="submit" class="at-bt cheio">Buscar</button></div>'
        '<p class="at-sugestoes"><span>Experimente:</span> %s</p>'
        '</form>'
        '</header>' % (hoje, data_longa(hoje), n, len(cfg["categorias"]), n_ev, n - n_ev, SEM_FICHA, sug))
    chips_cat = "".join(
        '<button type="button" class="at-chip" data-cat="%s" aria-pressed="false">%s</button>' % (c["id"], esc(c["titulo"]))
        for c in cfg["categorias"])
    partes.append(
        '<section class="at-painel" id="at-painel" aria-label="Filtros e ordem" hidden>'
        '<div class="at-filtros" role="group" aria-labelledby="at-filtros-t">'
        '<p class="at-filtros-rotulo" id="at-filtros-t">Filtros</p>'
        '<button type="button" class="at-chip" data-filtro="gest" aria-pressed="false">Seguro na gestação</button>'
        '<button type="button" class="at-chip" data-filtro="semrx" aria-pressed="false">Sem receita</button>'
        '<button type="button" class="at-chip" data-filtro="sensivel" aria-pressed="false">Pele sensível</button>'
        '<button type="button" class="at-chip" data-filtro="evid" aria-pressed="false">Com ficha e fontes</button>'
        '<button type="button" class="at-chip" data-filtro="iniciante" aria-pressed="false">Para iniciantes</button>'
        '<button type="button" class="at-chip" data-filtro="manha" aria-pressed="false">Uso de manhã</button>'
        '</div>'
        '<div class="at-filtros" role="group" aria-labelledby="at-cats-t">'
        '<p class="at-filtros-rotulo" id="at-cats-t">Categorias</p>'
        '%s</div>'
        '<p class="at-ordem"><label for="at-ordem">Ordenar por</label> <select id="at-ordem">'
        '<option value="padrao">Evidência primeiro</option><option value="encaixe">Melhor encaixe</option>'
        '<option value="irrita">Menor irritação</option><option value="az">Nome (A a Z)</option></select>'
        '<button type="button" class="at-link" id="at-limpar" hidden>Limpar tudo</button></p>'
        '<p class="at-contagem" id="at-contagem" role="status" aria-live="polite"></p>'
        '<p class="ig-nota at-aviso-gest" id="at-aviso-gest" hidden>“Seguro na gestação” reúne só quem a ficha diz que costuma ser considerado compatível. Confirme com seu médico. Quem a ficha manda evitar, ou só consultar, fica de fora.</p>'
        '</section>' % chips_cat)
    partes.append(
        '<div class="at-extra">'
        '<details class="at-rotulo" id="at-rotulo" hidden><summary>Tenho a lista de ingredientes do rótulo</summary>'
        '<label for="at-inci">Cole aqui a lista de ingredientes (INCI)</label>'
        '<textarea id="at-inci" rows="4" placeholder="Aqua, Niacinamide, Glycerin, Zinc PCA, …"></textarea>'
        '<p class="at-acoes"><button type="button" class="at-bt cheio" id="at-ler">Identificar ativos</button></p>'
        '<p class="ig-nota">A lista, sozinha, não mostra a concentração de cada ingrediente e não comprova eficácia nem segurança da fórmula. '
        'O texto colado não sai do seu navegador.</p>'
        '</details>'
        '<noscript><p class="ig-nota">Sem JavaScript, a busca, os filtros e o comparador não funcionam. A lista completa dos %d ativos segue abaixo, por categoria.</p></noscript>'
        '<p class="ig-nota">Quer uma sugestão pelo seu objetivo e tipo de pele, com rotina de manhã e de noite? Use o <a href="/ferramentas/ativos/">guia de princípios ativos</a>.</p>'
        '</div>' % n)
    extra = partes.pop()
    partes.append(
        '<section class="at-resultados" id="at-resultados" aria-labelledby="at-res-t" hidden>'
        '<h2 id="at-res-t" tabindex="-1">Resultado</h2>'
        '<p class="ig-nota" id="at-res-nota" hidden></p>'
        '<ol class="at-grade" id="at-res-lista"></ol>'
        '<div class="ig-caixa" id="at-res-vazio" hidden></div>'
        '</section>')
    partes.append(extra)
    partes.append(secao_mapa(cfg, ativos))
    partes.append(
        '<section class="at-prontas" id="at-prontas" aria-labelledby="comparacoes" hidden>'
        '<h2 id="comparacoes">Comparações prontas</h2>'
        '<p>Três dúvidas comuns, lado a lado. Você também pode montar a sua: toque em “Comparar” em até três cartões.</p>'
        '<ul class="at-prontas-lista">%s</ul></section>' % comps)
    partes.append('<div id="at-categorias">')
    ordem = 0
    for c in cfg["categorias"]:
        itens = [a for a in ativos if a["catId"] == c["id"]]
        cards = []
        for a in itens:
            cards.append(cartao(a, ordem))
            ordem += 1
        partes.append('<section class="at-cat" aria-labelledby="%s"><h2 id="%s">%s <span class="at-n">%d</span></h2><ul class="at-grade">\n%s\n</ul></section>'
                      % (c["id"], c["id"], esc(c["titulo"]), len(itens), "\n".join(cards)))
    partes.append('</div>')
    partes.append(
        '<section aria-labelledby="como-ler">'
        '<h2 id="como-ler">Como ler estas fichas</h2>'
        '<ul>'
        '<li><b>Evidência</b>: forte, moderada ou emergente, só nos %d ativos que já têm ficha com estudos e fontes. Nos outros aparece “%s”: o site ainda não publicou essa ficha. Não é uma nota, e não quer dizer que o ativo não funciona.</li>'
        '<li><b>Potência</b>: suave, moderada, alta ou potente, conforme a força de ação que a ficha descreve. Não é uma dose nem uma nota de evidência. Em filtros solares, a barra mede a força do filtro, não a de um tratamento.</li>'
        '<li><b>Irritação</b>: baixa, moderada ou alta, conforme a chance de arder, descamar ou avermelhar no começo do uso.</li>'
        '</ul>'
        '<p>Irritação, objetivos, concentração e gestação vêm da mesma base do <a href="/ferramentas/ativos/">guia de princípios ativos</a>, conferida com a frase de gestação de cada ficha. A potência fica nos dados da página, com a frase da ficha que sustenta cada número. As fichas sem fontes resumem orientações de uso comuns em dermatologia cosmética e não citam estudos. Concentrações são faixas usuais em cosméticos; os limites legais mudam de país para país e com o tempo. Ativos marcados como <b>receita médica</b> são medicamentos e só devem ser usados com prescrição.</p>'
        '<p>As combinações do passaporte e do comparador saem das regras do <a href="/ferramentas/ingredientes/">verificador de ingredientes</a>. Quando não há regra cadastrada para um par, a página diz que não sabe. Para montar a rotina inteira, veja a <a href="/rotina-de-skincare/">rotina de skincare passo a passo</a>.</p>'
        '</section>' % (n_ev, SEM_FICHA))
    return "\n".join(partes)


def main():
    cfg, ativos, versao = carregar()
    dados = {
        "regras": versao,
        "objetivos": OBJETIVOS, "peles": PELES,
        "vocabulario": {k: {i: sorted({norm(t) for t in ts}) for i, ts in v.items()} for k, v in cfg["vocabulario"].items()},
        "temas": [{"id": t["id"], "titulo": t["titulo"], "objetivos": t["objetivos"]} for t in cfg["temas"]],
        "ativos": [{k: v for k, v in a.items() if k != "resumo"} for a in ativos],
    }
    DADOS.write_text("/* Gerado por _scripts/gerar_atlas.py. Não edite à mão. */\nwindow.ATLAS = "
                     + json.dumps(dados, ensure_ascii=False, separators=(",", ":")) + ";\n",
                     encoding="utf-8", newline="\n")

    t = INDICE.read_text(encoding="utf-8")
    novo = "<!-- atlas:inicio -->\n<article class=\"at\">\n" + corpo(cfg, ativos) + "\n</article>\n<!-- atlas:fim -->"
    if "<!-- atlas:inicio -->" in t:
        t = re.sub(r"<!-- atlas:inicio -->.*?<!-- atlas:fim -->", lambda m: novo, t, count=1, flags=re.S)
    else:
        a, b = t.index("<article>"), t.index("</article>") + len("</article>")
        t = t[:a] + novo + t[b:]
    t = t.replace('<main class="ig ig-larga" id="conteudo">', '<main class="ig ig-larga atlas" id="conteudo">')
    if "/ativos/atlas.css" not in t:
        t = t.replace('<link rel="stylesheet" href="/premium.css">',
                      '<link rel="stylesheet" href="/premium.css">\n<link rel="stylesheet" href="/ativos/atlas.css">', 1)
    if "/ativos/atlas.js" not in t:
        t = t.replace("</body>",
                      '<script src="/regras-ativos.js" defer></script>\n<script src="/ativos/atlas-dados.js" defer></script>\n'
                      '<script src="/ativos/atlas.js" defer></script>\n</body>', 1)
    INDICE.write_text(t, encoding="utf-8", newline="\n")
    sem = [a["id"] for a in ativos if not a["classe"]]
    print("Atlas: %d ativos, %d com evidência avaliada, %d sem classe no verificador (regras v%s)."
          % (len(ativos), sum(1 for a in ativos if a["ev"]), len(sem), versao))


if __name__ == "__main__":
    main()
