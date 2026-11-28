"""Links dos posts do blog para as fichas de ativos (/ativos/<slug>/ e /ingredientes/<slug>/).

Na primeira menção de cada ativo no corpo do post, o nome vira link para a ficha dele.
Regras:
  - só no corpo: do <h1> até o bloco de perguntas frequentes, "Leia também" ou "Fontes";
  - só em texto de parágrafo, item de lista ou célula de tabela; nunca dentro de link,
    título (h1 a h6), botão, script, estilo ou figura;
  - cada ficha recebe no máximo um link por post, e nenhum se o post já aponta para ela;
  - no máximo MAX_LINKS links novos por post.
Os links criados levam class="ln-ativo", então o script pode rodar de novo sem duplicar nada
e "--remover" desfaz tudo o que ele pôs.

O mapa ativo -> ficha vem da página do guia (ferramentas/ativos/index.html,
GUIA_ATIVOS_CONFIG.fichas). Os nomes procurados no texto ficam em NOMES, abaixo: são escritos
à mão, de propósito, para não ligar palavras genéricas ("colágeno", "zinco", "enzimas") a
fichas de ingrediente.

Uso:
    python3 -I _scripts/links_ativos.py            # põe os links
    python3 -I _scripts/links_ativos.py --simular  # só mostra o que faria
    python3 -I _scripts/links_ativos.py --remover  # tira os links que este script pôs
Depois: seo.py e prontidao.py (CLAUDE.md).
"""
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MAX_LINKS = 12

# id do guia -> nomes como aparecem no texto (com acento). Sem distinção de maiúsculas,
# exceto os que estão em SIGLAS. Os mais longos são procurados primeiro.
NOMES = {
    "retinol": ["retinol"], "retinal": ["retinal", "retinaldeído"], "palmitato-retinila": ["palmitato de retinila"],
    "tretinoina": ["tretinoína", "ácido retinoico"], "adapaleno": ["adapaleno"], "tazaroteno": ["tazaroteno"],
    "trifaroteno": ["trifaroteno"], "bakuchiol": ["bakuchiol"],
    "glicolico": ["ácido glicólico"], "latico": ["ácido lático", "ácido láctico"], "mandelico": ["ácido mandélico"],
    "salicilico": ["ácido salicílico"], "gluconolactona": ["gluconolactona"], "lactobionico": ["ácido lactobiônico"],
    "piruvico": ["ácido pirúvico"], "betaina-salicilato": ["betaína salicilato"],
    "ureia": ["ureia"], "hialuronico": ["ácido hialurônico", "hialuronato de sódio"], "glicerina": ["glicerina"],
    "trealose": ["trealose"], "hidroxietilureia": ["hidroxietilureia"],
    "niacinamida": ["niacinamida"], "tranexamico": ["ácido tranexâmico"], "azelaico": ["ácido azelaico"],
    "kojico": ["ácido kójico"], "alfa-arbutina": ["alfa-arbutina", "arbutina"], "tiamidol": ["tiamidol"],
    "melasyl": ["melasyl"], "cisteamina": ["cisteamina"], "hidroquinona": ["hidroquinona"],
    "acido-elagico": ["ácido elágico"], "hexilresorcinol": ["hexilresorcinol"], "nag": ["N-acetilglucosamina"],
    "vitc-pura": ["vitamina C"], "vitamina-e": ["vitamina E"], "ferulico": ["ácido ferúlico"],
    "resveratrol": ["resveratrol"], "q10": ["coenzima Q10"], "cha-verde": ["chá verde"], "astaxantina": ["astaxantina"],
    "acido-lipoico": ["ácido lipoico"], "idebenona": ["idebenona"], "glutationa": ["glutationa"],
    "ergotioneina": ["ergotioneína"], "silimarina": ["silimarina"],
    "pantenol": ["pantenol", "dexpantenol"], "aloe": ["aloe vera", "babosa"], "ectoina": ["ectoína"],
    "centella": ["centella asiática", "centella"], "alantoina": ["alantoína"], "bisabolol": ["bisabolol"],
    "aveia": ["aveia coloidal"], "canabidiol": ["canabidiol"], "calendula": ["calêndula"],
    "ceramidas": ["ceramidas", "ceramida"], "esqualano": ["esqualano"], "karite": ["manteiga de karité"],
    "rosa-mosqueta": ["óleo de rosa mosqueta", "rosa mosqueta"], "petrolato": ["petrolato", "vaselina"],
    "dimeticona": ["dimeticona"], "jojoba": ["óleo de jojoba"],
    "peroxido-benzoila": ["peróxido de benzoíla"], "enxofre": ["enxofre"], "melaleuca": ["óleo de melaleuca", "tea tree"],
    "clindamicina": ["clindamicina"], "succinico": ["ácido succínico"],
    "argireline": ["argireline"], "ghk-cu": ["peptídeo de cobre", "GHK-Cu"], "mucina-caracol": ["mucina de caracol"],
    "pdrn": ["PDRN"], "matrixyl-3000": ["Matrixyl 3000"], "matrixyl": ["Matrixyl"],
    "adenosina": ["adenosina"], "carnosina": ["carnosina"], "pro-xylane": ["Pro-Xylane"],
    "cafeina": ["cafeína"], "vitamina-k": ["vitamina K"],
    "oxido-zinco": ["óxido de zinco"], "dioxido-titanio": ["dióxido de titânio"],
    "tinosorb-s": ["bemotrizinol", "Tinosorb S"], "tinosorb-m": ["bisoctrizol", "Tinosorb M"],
    "avobenzona": ["avobenzona"], "octocrileno": ["octocrileno"], "mexoryl-sx": ["Mexoryl SX", "ecamsule"],
    "mexoryl-xl": ["Mexoryl XL"], "mexoryl-400": ["Mexoryl 400"], "uvinul-a": ["Uvinul A Plus", "DHHB"],
    "uvinul-t": ["etilhexil triazona"], "homosalato": ["homosalato"], "octisalato": ["octisalato"],
    "octinoxato": ["octinoxato"], "oxibenzona": ["oxibenzona", "benzofenona-3"], "ensulizol": ["ensulizol"],
}
SIGLAS = {"PDRN", "DHHB", "GHK-Cu"}  # só casam com maiúsculas exatas
# menções que falam de outra coisa: não viram link (ex.: preenchedor injetável não é o ativo tópico)
NAO_ANTES = {"hialuronico": re.compile(r"(preench\w*|injet\w*|aplica\w*)\s+(?:de|com)\s+$", re.I)}

# contextos onde o texto não recebe link
PROIBIDOS = {"a", "h1", "h2", "h3", "h4", "h5", "h6", "script", "style", "button", "figure", "figcaption",
             "noscript", "summary", "th", "code", "pre"}
FIM_DO_CORPO = re.compile(r'<!-- faq:inicio -->|<h2 id="relacionados"|<h2 id="fontes"|</main>')
LINK_NOSSO = re.compile(r'<a href="[^"]*" class="ln-ativo">(.*?)</a>', re.S)


def fichas():
    pagina = (RAIZ / "ferramentas" / "ativos" / "index.html").read_text(encoding="utf-8")
    return json.loads(re.search(r"GUIA_ATIVOS_CONFIG\.fichas = (\{.*?\});", pagina).group(1))


def padrao(nome):
    corpo = re.escape(nome).replace(r"\-", "[-‑ ]")
    return r"(?<![\w-])" + corpo + r"(?![\w-])"


def montar_regex(restantes):
    """Uma regex com todos os nomes ainda sem link, os mais longos primeiro."""
    itens = sorted(((n, i) for i, ns in restantes.items() for n in ns), key=lambda x: -len(x[0]))
    if not itens:
        return None, {}
    grupos, dono = [], {}
    for k, (nome, i) in enumerate(itens):
        g = "g%d" % k
        dono[g] = i
        pat = padrao(nome)
        grupos.append("(?P<%s>%s)" % (g, pat if nome in SIGLAS else "(?i:" + pat + ")"))
    return re.compile("|".join(grupos)), dono


def linkar(html, mapa, log):
    inicio = html.find("<h1")
    fim_m = FIM_DO_CORPO.search(html, inicio if inicio >= 0 else 0)
    if inicio < 0 or not fim_m:
        return html, []
    fim = fim_m.start()
    corpo = html[inicio:fim]
    ja = set(re.findall(r'href="([^"]+)"', html))
    restantes = {i: ns for i, ns in NOMES.items() if i in mapa and mapa[i] not in ja}
    feitos = []
    regex, dono = montar_regex(restantes)
    pilha, saida, pos = [], [], 0
    for m in re.finditer(r"<!--.*?-->|<(/?)([a-zA-Z][a-zA-Z0-9]*)([^>]*)>", corpo, re.S):
        texto = corpo[pos:m.start()]
        if texto and regex and len(feitos) < MAX_LINKS and not (set(pilha) & PROIBIDOS):
            novo, ultimo, busca = [], 0, 0
            while regex and len(feitos) < MAX_LINKS:
                achado = regex.search(texto, busca)
                if not achado:
                    break
                i = dono[achado.lastgroup]
                if i in NAO_ANTES and NAO_ANTES[i].search(texto[max(0, achado.start() - 40):achado.start()]):
                    busca = achado.end()
                    continue
                url = mapa[i]
                novo.append(texto[ultimo:achado.start()])
                novo.append('<a href="%s" class="ln-ativo">%s</a>' % (url, achado.group(0)))
                ultimo = busca = achado.end()
                feitos.append((achado.group(0), url))
                restantes.pop(i, None)
                # outros ids que apontam para a mesma ficha também saem
                for j in [j for j in restantes if mapa.get(j) == url]:
                    restantes.pop(j)
                regex, dono = montar_regex(restantes)
            novo.append(texto[ultimo:])
            texto = "".join(novo)
        saida.append(texto)
        saida.append(m.group(0))
        pos = m.end()
        if m.group(2):
            tag = m.group(2).lower()
            if m.group(1):
                if tag in pilha:
                    while pilha and pilha.pop() != tag:
                        pass
            elif not m.group(3).rstrip().endswith("/") and tag not in ("br", "img", "hr", "meta", "link", "input", "source", "wbr"):
                pilha.append(tag)
    saida.append(corpo[pos:])
    return html[:inicio] + "".join(saida) + html[fim:], feitos


def main():
    simular, remover = "--simular" in sys.argv, "--remover" in sys.argv
    mapa = fichas()
    total = 0
    for arq in sorted((RAIZ / "blog").glob("*/index.html")):
        html = arq.read_text(encoding="utf-8")
        if remover:
            novo, n = LINK_NOSSO.subn(r"\1", html)
            if n:
                arq.write_text(novo, encoding="utf-8")
                print("%-60s -%d" % (arq.parent.name, n))
            continue
        novo, feitos = linkar(html, mapa, print)
        if feitos:
            total += len(feitos)
            print("%-60s +%d  %s" % (arq.parent.name, len(feitos), ", ".join(t for t, _ in feitos)))
            if not simular:
                arq.write_text(novo, encoding="utf-8")
    if not remover:
        print("links novos: %d%s" % (total, " (simulação)" if simular else ""))


if __name__ == "__main__":
    main()
