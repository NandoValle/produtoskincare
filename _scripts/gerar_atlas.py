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
process.stdout.write(JSON.stringify({ ativos: out, versaoRegras: R.VERSAO, combinacoes: R.COMBINACOES, classes: R.CLASSES }));
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
    enriquecer(ativos)
    return cfg, ativos, bruto["versaoRegras"], bruto.get("combinacoes") or [], bruto.get("classes") or {}


# Nome no catálogo (produtos.json) -> id do atlas. Ordem: o prefixo mais longo ganha.
# "zinco 1%" não entra: o catálogo não diz se é PCA.
MAPA_CATALOGO = [
    ("pca de zinco", "zinco-pca"),
    ("acido hialuronico", "hialuronico"),
    ("acido azelaico", "azelaico"),
    ("acido ferulico", "ferulico"),
    ("alfa bisabolol", "bisabolol"),
    ("madecassoside", "centella"),
    ("niacinamida", "niacinamida"),
    ("ceramidas", "ceramidas"),
    ("glicerina", "glicerina"),
    ("pantenol", "pantenol"),
    ("thiamidol", "tiamidol"),
    ("tiamidol", "tiamidol"),
    ("vitamina e", "vitamina-e"),
    ("vitamina c", "vitc-pura"),
    ("retinol", "retinol"),
]


def id_catalogo(rotulo):
    n = norm(rotulo)
    melhor = ("", "")
    for prefixo, iid in MAPA_CATALOGO:
        if n == prefixo or n.startswith(prefixo + " "):
            if len(prefixo) > len(melhor[0]):
                melhor = (prefixo, iid)
    return melhor[1]


def conc_catalogo(rotulo):
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*%", rotulo)
    return m.group(0).replace(".", ",") if m else ""


def reais(valor):
    return ("R$ %.2f" % valor).replace(".", ",")


def data_curta(iso):
    a, m, d = iso.split("-")
    return "%s/%s/%s" % (d, m, a)


def enriquecer(ativos):
    por_id = {a["id"]: a for a in ativos}
    for a in ativos:
        a["produtos"] = []
        a["prazo"] = []
        a["ciencia"] = None
    historia = json.loads((RAIZ / "produtos" / "historico-precos.json").read_text(encoding="utf-8"))
    cat = json.loads((RAIZ / "produtos.json").read_text(encoding="utf-8"))["produtos"]
    for p in cat:
        if not isinstance(p.get("preco"), (int, float)):
            continue
        pontos = historia.get(p["id"]) or [{"em": p.get("preco_em") or "", "preco": p["preco"], "loja": p.get("plataforma") or ""}]
        pontos = [x for x in pontos if isinstance(x.get("preco"), (int, float))]
        if not pontos:
            continue
        vistos = set()
        for rotulo in p.get("ativos") or []:
            iid = id_catalogo(rotulo)
            if not iid or iid in vistos or iid not in por_id:
                continue
            vistos.add(iid)
            pagina = "/produtos/%s/" % p["id"]
            href = pagina if (RAIZ / "produtos" / p["id"] / "index.html").exists() else p.get("link") or pagina
            por_id[iid]["produtos"].append({
                "id": p["id"], "nome": p["nome"], "marca": p.get("marca") or "",
                "href": href, "externo": not href.startswith("/"),
                "como": rotulo, "conc": conc_catalogo(rotulo),
                "historia": [{"em": x.get("em") or "", "preco": x["preco"], "loja": x.get("loja") or ""} for x in pontos],
            })
    prazos = json.loads((RAIZ / "_scripts" / "linha-do-tempo.json").read_text(encoding="utf-8"))
    ciencia = json.loads((RAIZ / "_scripts" / "ciencia-recente.json").read_text(encoding="utf-8"))
    for iid, itens in (prazos.get("ativos") or {}).items():
        if iid not in por_id:
            sys.exit("linha do tempo sem ativo: " + iid)
        por_id[iid]["prazo"] = itens
    for iid, info in (ciencia.get("ativos") or {}).items():
        if iid not in por_id:
            sys.exit("ciência recente sem ativo: " + iid)
        por_id[iid]["ciencia"] = info
    return prazos.get("nota") or "", ciencia.get("nota") or ""


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
    ciencia = ""
    if a.get("ciencia") and a["ciencia"].get("texto"):
        info = a["ciencia"]
        selo = ""
        if info.get("selo"):
            ano = (" · %s" % info["ano"]) if info.get("ano") else ""
            selo = '<span class="at-selo novo">%s%s</span> ' % (esc(info["selo"]), ano)
        elif info.get("ano"):
            selo = '<span class="at-selo">Desde %s</span> ' % info["ano"]
        ciencia = '<p class="at-ciencia">%s%s</p>' % (selo, esc(info["texto"]))
    prazo = ""
    if a.get("prazo"):
        itens = "".join("<li><b>%s:</b> %s a %s. %s</li>" % (esc(OBJETIVOS.get(x["objetivo"], x["objetivo"])), esc(x["de"]), esc(x["ate"]), esc(x["texto"])) for x in a["prazo"])
        prazo = '<ul class="at-prazo"><li class="at-prazo-t">Quando costuma dar sinal</li>%s</ul>' % itens
    onde = ""
    if a.get("produtos"):
        lis = []
        for p in a["produtos"]:
            extra = []
            if p["conc"]:
                extra.append(esc(p["conc"]) + " no catálogo")
            elif p["como"]:
                extra.append(esc(p["como"]))
            ultimo = p["historia"][-1]
            extra.append(reais(ultimo["preco"]) + (" em " + data_curta(ultimo["em"]) if ultimo["em"] else ""))
            rel = ' rel="sponsored noopener"' if p["externo"] else ""
            alvo = ' target="_blank"' if p["externo"] else ""
            hist = ""
            if len(p["historia"]) > 1:
                hist = " <small>Histórico: %s.</small>" % "; ".join(
                    "%s %s" % (data_curta(h["em"]) if h["em"] else "sem data", reais(h["preco"])) for h in p["historia"])
            lis.append('<li><a href="%s"%s%s>%s</a> <small>%s.</small>%s</li>' % (
                esc(p["href"]), alvo, rel, esc(p["nome"]), " · ".join(extra), hist))
        onde = '<div class="at-onde"><p class="at-onde-t">Onde tem no catálogo</p><ul>%s</ul></div>' % "".join(lis)
    stories = '<p class="at-stories"><a href="/img/stories/%s.png">Card para stories</a></p>' % a["id"]
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
        '%(ciencia)s%(prazo)s%(onde)s%(stories)s'
        '%(selos)s'
        '<p class="at-acoes"><button type="button" class="at-bt" data-passaporte="%(id)s">Passaporte</button>'
        '<button type="button" class="at-bt" data-comparar="%(id)s" aria-pressed="false">Comparar</button></p>'
        '</li>'
    ) % {
        "id": a["id"], "ordem": ordem, "url": a["url"], "nome": esc(a["nome"]), "inci": esc(a["inci"]),
        "resumo": a["resumo"], "ev": ev,
        "pot": barra(a["pot"], 4, POT_ROTULO[a["pot"]], "po"),
        "ir": barra(a["irrita"] + 1, 3, IRRITA[a["irrita"]], "ir"),
        "ciencia": ciencia, "prazo": prazo, "onde": onde, "stories": stories,
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


def secao_combinacoes(combinacoes, classes):
    lis = []
    for r in combinacoes:
        if r["a"] == "irritada" or r["b"] == "irritada":
            continue
        cor = {"ok": "Pode junto", "horarios": "Alternar", "nao": "Evitar"}.get(r["resultado"], r["resultado"])
        lis.append(
            '<li data-classes="%s %s" data-res="%s"><span class="at-cor %s">%s</span> '
            '<b>%s e %s.</b> %s%s</li>' % (
                esc(r["a"]), esc(r["b"]), esc(r["resultado"]), esc(r["resultado"]), esc(cor),
                esc(classes.get(r["a"], r["a"])), esc(classes.get(r["b"], r["b"])),
                esc(r["motivo"]), (" " + esc(r["nota"])) if r.get("nota") else ""))
    return (
        '<section class="at-combina-mapa" id="mapa-combina" aria-labelledby="titulo-combina">'
        '<h2 id="titulo-combina">O que combina com o quê</h2>'
        '<p>Verde pode usar junto, amarelo é para alternar manhã e noite, vermelho é para evitar juntos. '
        'As regras são as do <a href="/ferramentas/ingredientes/">verificador de ingredientes</a>. '
        'Com JavaScript, toque num ativo para ver só as ligações dele. Sem JavaScript, a lista abaixo já cobre os pares que têm regra.</p>'
        '<div class="at-grafo" id="at-grafo" hidden>'
        '<p class="at-grafo-foco" id="at-grafo-foco" aria-live="polite"></p>'
        '<div class="at-grafo-palco"><svg class="at-grafo-linhas" id="at-grafo-linhas" aria-hidden="true"></svg>'
        '<div class="at-grafo-nos" id="at-grafo-nos"></div></div>'
        '<p class="ig-nota">Linha só aparece para regra explícita do verificador. Hidratante, antioxidante, filtro solar e clareador suave combinam com os outros por uma regra geral: o texto diz isso, sem desenhar uma teia.</p>'
        '</div>'
        '<ul class="at-regras" id="at-regras">%s</ul>'
        '</section>' % "".join(lis))


def corpo(cfg, ativos, combinacoes, classes):
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
    partes.append(secao_combinacoes(combinacoes, classes))
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
        '<p>As combinações do mapa, do passaporte e do comparador saem das regras do <a href="/ferramentas/ingredientes/">verificador de ingredientes</a>. Quando não há regra cadastrada para um par, a página diz que não sabe. Preço só aparece quando o produto está no catálogo do site, com a data em que foi conferido. O prazo é uma faixa usual, não uma garantia. Para montar a rotina inteira, veja a <a href="/rotina-de-skincare/">rotina de skincare passo a passo</a>.</p>'
        '</section>' % (n_ev, SEM_FICHA))
    return "\n".join(partes)


def gerar_stories(ativos):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        faltam = [a["id"] for a in ativos if not (RAIZ / "img" / "stories" / (a["id"] + ".png")).exists()]
        if faltam:
            sys.exit("Instale Pillow para gerar os cards de stories. Faltam: " + ", ".join(faltam[:8]))
        print("Pillow ausente: os cards de stories já gerados foram mantidos.")
        return
    pasta = RAIZ / "img" / "stories"
    pasta.mkdir(parents=True, exist_ok=True)
    fonte_nome = ImageFont.truetype(str(RAIZ / "fonts" / "cormorant-500.ttf"), 92)
    fonte_corpo = ImageFont.truetype(str(RAIZ / "fonts" / "manrope-400.ttf"), 40)
    fonte_marca = ImageFont.truetype(str(RAIZ / "fonts" / "manrope-600.ttf"), 36)
    fonte_selo = ImageFont.truetype(str(RAIZ / "fonts" / "manrope-600.ttf"), 32)

    def quebra(draw, texto, fonte, largura):
        linhas, atual = [], ""
        for palavra in texto.split():
            teste = (atual + " " + palavra).strip()
            if draw.textlength(teste, font=fonte) <= largura:
                atual = teste
            else:
                if atual:
                    linhas.append(atual)
                atual = palavra
        if atual:
            linhas.append(atual)
        return linhas

    for a in ativos:
        im = Image.new("RGB", (1080, 1920), "#f7f8f7")
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, 1080, 28), fill="#9b405b")
        d.text((80, 120), "PRODUTO SKINCARE", font=fonte_marca, fill="#9b405b")
        y = 280
        for linha in quebra(d, a["nome"], fonte_nome, 920)[:4]:
            d.text((80, y), linha, font=fonte_nome, fill="#252b2a")
            y += 100
        y += 40
        if a["ev"]:
            selo = "Ficha com fontes · evidência " + a["ev"]
            cor, tinta = "#e7efea", "#375d4e"
        else:
            selo = "Sem ficha com fontes ainda"
            cor, tinta = "#eef0ef", "#39413f"
        caixa = d.textbbox((0, 0), selo, font=fonte_selo)
        larg = caixa[2] - caixa[0] + 48
        d.rounded_rectangle((80, y, 80 + larg, y + 72), radius=36, fill=cor)
        d.text((104, y + 16), selo, font=fonte_selo, fill=tinta)
        y += 120
        for linha in quebra(d, a["resumo"], fonte_corpo, 920)[:8]:
            d.text((80, y), linha, font=fonte_corpo, fill="#39413f")
            y += 56
        d.text((80, 1760), "produtoskincare.com.br/ativos/", font=fonte_corpo, fill="#65716d")
        d.rectangle((0, 1892, 1080, 1920), fill="#9b405b")
        im.save(pasta / (a["id"] + ".png"), "PNG", optimize=True)


def main():
    cfg, ativos, versao, combinacoes, classes = carregar()
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
    gerar_stories(ativos)
    novo = "<!-- atlas:inicio -->\n<article class=\"at\">\n" + corpo(cfg, ativos, combinacoes, classes) + "\n</article>\n<!-- atlas:fim -->"
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
