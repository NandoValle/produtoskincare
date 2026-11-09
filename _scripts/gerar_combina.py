"""Gera as páginas "Posso usar X com Y?" (/combina/<x>-com-<y>/) e o índice /combina/.

Cada resposta sai das regras de /regras-ativos.js (lidas por _scripts/regras_dados.js), as mesmas
do verificador de ingredientes e do provador. O script não escreve regra nenhuma:
- só vira página o par que tem regra cadastrada (combinação específica ou regra geral);
- par "sem regra cadastrada" nunca vira página, porque não sabemos a resposta.

Para mudar uma resposta, mude a regra em /regras-ativos.js e rode de novo:

    python3 _scripts/gerar_combina.py
    python3 _scripts/menu.py
    python3 _scripts/seo.py
"""
import json
import shutil
import subprocess

from gerar_produtos import CATALOGO, PASSOS, reais
from pagina_base import RAIZ, esc, pagina

DESTINO = RAIZ / "combina"

# Representante de cada classe de ativo: id em ATIVOS (regras-ativos.js), nome na página e slug.
CLASSE = {
    "retinoide": ("retinol", "retinol", "retinol"),
    "aha": ("glicolico", "ácido glicólico", "acido-glicolico"),
    "bha": ("salicilico", "ácido salicílico", "acido-salicilico"),
    "vitc": ("vitc", "vitamina C", "vitamina-c"),
    "bpo": ("bpo", "peróxido de benzoíla", "peroxido-de-benzoila"),
    "niacinamida": ("niacinamida", "niacinamida", "niacinamida"),
    "azelaico": ("azelaico", "ácido azelaico", "acido-azelaico"),
    "hidratante": ("hialuronico", "ácido hialurônico", "acido-hialuronico"),
    "filtro": ("filtro", "protetor solar", "protetor-solar"),
}
# Pares com regra específica em COMBINACOES (ordem: como a pessoa costuma perguntar).
ESPECIFICOS = [
    ("retinoide", "vitc"), ("retinoide", "aha"), ("retinoide", "bha"), ("retinoide", "niacinamida"),
    ("retinoide", "bpo"), ("retinoide", "retinoide"), ("vitc", "niacinamida"), ("vitc", "aha"), ("vitc", "bha"),
    ("aha", "bha"), ("bpo", "vitc"), ("bpo", "aha"), ("bpo", "bha"),
]
# Pares que caem na regra geral (hidratantes e filtro solar combinam com os outros ativos).
GERAIS = [
    ("retinoide", "hidratante"), ("aha", "hidratante"), ("bha", "hidratante"), ("vitc", "hidratante"),
    ("niacinamida", "hidratante"), ("azelaico", "hidratante"),
    ("retinoide", "filtro"), ("aha", "filtro"), ("bha", "filtro"), ("vitc", "filtro"),
]
# "Posso usar X com a pele irritada?"
IRRITADA = ["retinoide", "aha", "bha", "vitc", "bpo"]

ICONE = {"ok": "✅", "horarios": "🕐", "nao": "⛔", "sem_regra": "❔"}
CLASSE_CSS = {"ok": "cb-ok", "horarios": "cb-horarios", "nao": "cb-nao", "sem_regra": "cb-sem"}
FOTOSSENSIVEIS = {"retinoide", "aha", "bha"}

CSS = """
.cb-resposta{border-radius:var(--raio,14px);padding:18px 20px;margin:18px 0;border-left:4px solid}
.cb-resposta p{margin:.3em 0}
.cb-veredito{font-family:var(--fonte-display);font-size:1.35rem;margin:0 0 .2em}
.cb-ok{background:#eef4f0;border-color:#3f6b55;color:#1f3a2c}
.cb-horarios{background:#fff4dd;border-color:#b7791f;color:#5c3d00}
.cb-nao{background:#fdf2f4;border-color:#b4546a;color:#5a1d2b}
.cb-sem{background:#f4f4f4;border-color:#6b6b6b;color:#333}
.cb-btns{display:flex;flex-wrap:wrap;gap:10px;margin:18px 0}
.cb-btn{display:inline-flex;align-items:center;min-height:48px;padding:8px 20px;border-radius:999px;background:var(--rosa);color:#fff;font-weight:600;text-decoration:none}
.cb-btn.cb-sec{background:transparent;color:inherit;border:1.5px solid currentColor}
.cb-lista{columns:2;gap:24px}@media(max-width:560px){.cb-lista{columns:1}}
.cb-tabela{width:100%;border-collapse:collapse;font-size:.95rem;margin:12px 0}
.cb-tabela th,.cb-tabela td{padding:9px 10px;border-bottom:1px solid var(--linha);text-align:left;vertical-align:top}
@media(prefers-color-scheme:dark){.cb-ok,.cb-horarios,.cb-nao,.cb-sem{color:#1a1614}}
"""


def dados(pedido):
    saida = subprocess.run(["node", str(RAIZ / "_scripts" / "regras_dados.js")], input=json.dumps(pedido),
                           capture_output=True, text=True, check=True)
    return json.loads(saida.stdout)


def nome(classe, maiuscula=False):
    n = "a pele irritada" if classe == "irritada" else CLASSE[classe][1]
    return n[0].upper() + n[1:] if maiuscula else n


def slug_par(a, b):
    if a == b:
        return f"dois-{'retinoides' if a == 'retinoide' else CLASSE[a][2]}"
    if b == "irritada":
        return f"{CLASSE[a][2]}-com-pele-irritada"
    return f"{CLASSE[a][2]}-com-{CLASSE[b][2]}"


def titulo_par(a, b):
    if a == b:
        return "Posso usar dois retinoides juntos?"
    if b == "irritada":
        return f"Posso usar {nome(a)} com a pele irritada?"
    return f"Posso usar {nome(a)} com {nome(b)}?"


def parecidos(classe, ativos):
    return [x["nome"] for x in ativos if x["classe"] == classe]


def encaixe(a, b, r):
    """Como encaixar na rotina, a partir do resultado da regra (sem regra nova)."""
    res = r["resultado"]
    if b == "irritada":
        linhas = [f"Pause {nome(a)} enquanto a pele está irritada e fique com o básico: limpeza suave, hidratante e protetor solar.",
                  "Volte devagar quando a pele estiver calma, uma noite por vez.",
                  "Se a irritação não melhorar em alguns dias, procure um dermatologista. Se o produto foi receitado, avise quem receitou."]
    elif res == "ok":
        linhas = ["Podem entrar na mesma rotina, inclusive na mesma aplicação.",
                  "Comece um ativo novo por vez, para saber qual deles a pele não tolerou se algo arder."]
    elif res == "horarios":
        linhas = ["Não aplique os dois na mesma aplicação: separe manhã e noite, ou use em noites alternadas, como explica a resposta acima.",
                  "Comece um de cada vez e só acrescente o segundo quando a pele estiver tolerando bem o primeiro."]
    else:
        linhas = ["Escolha um dos dois para a sua rotina.", "Se os dois foram receitados, siga a orientação de quem receitou."]
    if (a in FOTOSSENSIVEIS or b in FOTOSSENSIVEIS) and b != "irritada":
        linhas.append("Use protetor solar todos os dias enquanto estiver usando ácidos ou retinoides.")
    return linhas


def produtos_da_classe(classe, produtos, classes_prod):
    return [p for p in produtos if classe in classes_prod.get(p["id"], [])]


def lista_produtos(titulo, itens):
    if not itens:
        return ""
    lis = "".join(f'<li><a href="/produtos/{esc(p["id"])}/">{esc(p["nome"])}</a> · {esc(PASSOS.get(p["passo"], p["passo"]))} · '
                  f'{reais(p["preco"])}</li>' for p in itens[:6])
    return f'<h3>{esc(titulo)}</h3><ul>{lis}</ul>'


def pagina_par(item, todos, d, produtos):
    a, b, r, rs = item["a"], item["b"], item["normal"], item["sensivel"]
    titulo = titulo_par(a, b)
    ida, idb = CLASSE[a][0], ("irritada" if b == "irritada" else CLASSE[b][0])
    nota = f'<p><small>{esc(r["nota"])}</small></p>' if r["nota"] else ""
    if rs["resultado"] != r["resultado"]:
        sens = (f'<p><strong>Se a sua pele é sensível: {ICONE[rs["resultado"]]} {esc(rs["rotulo"])}.</strong> {esc(rs["motivo"])}</p>')
    else:
        sens = "<p>Para pele sensível, a resposta para a combinação é a mesma. Mesmo assim, comece devagar e pare se arder ou avermelhar.</p>"
    # Aviso de perfil (o mesmo do provador) para pele sensível, por ativo.
    for c in dict.fromkeys([a, b]):
        regra = next((x for x in d["perfil"] if x["quando"] == "sensivel" and c in x.get("classes", [])), None)
        if regra:
            sens += f"<p><strong>{esc(nome(c, True))} em pele sensível</strong> (a regra que o provador usa): {esc(regra["motivo"])}</p>"
    vale = []
    for c in ([a] if a == b else [a, b]):
        if c == "irritada":
            continue
        nomes = parecidos(c, d["ativos"])
        if len(nomes) > 1:
            grupo = d["classes"].get(c, c)
            vale.append(f"<li><strong>{esc(grupo[0].upper() + grupo[1:])}</strong>: a regra vale para {esc(', '.join(nomes))}.</li>")
    vale_html = (f'<h2>Vale também para os parecidos</h2><p>As regras são por grupo de ativo, não por produto:</p><ul>{"".join(vale)}</ul>'
                 if vale else "")
    prods = lista_produtos(f"Com {nome(a)}", produtos_da_classe(a, produtos, d["produtos"]))
    if b not in ("irritada", a):
        prods += lista_produtos(f"Com {nome(b)}", produtos_da_classe(b, produtos, d["produtos"]))
    prods_html = (f'<section><h2>No nosso catálogo</h2>{prods}<p class="ig-nota">"Com" quer dizer que o anúncio destaca o ativo. '
                  "Confira a lista completa de ingredientes na embalagem.</p></section>") if prods else ""
    q = f"{ida},{idb}" if b != "irritada" else f"{ida}&irritada=1"
    if a == b:
        q = "retinol,tretinoina"
    outros = [x for x in todos if x is not item and (a in (x["a"], x["b"]) or b in (x["a"], x["b"]))][:6]
    rel = "".join(f'<li><a href="/combina/{slug_par(x["a"], x["b"])}/">{esc(titulo_par(x["a"], x["b"]))}</a></li>' for x in outros)
    encaixe_html = "".join(f"<li>{esc(t)}</li>" for t in encaixe(a, b, r))
    resposta_faq = r["motivo"] if r["motivo"].startswith(r["rotulo"] + ".") else f'{r["rotulo"]}. {r["motivo"]}'
    faq = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{
        "@type": "Question", "name": titulo,
        "acceptedAnswer": {"@type": "Answer", "text": resposta_faq}}]}
    faq_txt = json.dumps(faq, ensure_ascii=False).replace("</", "<\\/")
    corpo = f"""<article>
<div class="ig-cab">
<h1>{esc(titulo)}</h1>
<p class="ig-meta">Resposta das regras de combinação do Produto Skincare, versão {esc(d["versao"])}</p>
</div>
<div class="cb-resposta {CLASSE_CSS[r["resultado"]]}">
<p class="cb-veredito">{ICONE[r["resultado"]]} {esc(r["rotulo"])}</p>
<p>{esc(r["motivo"])}</p>{nota}
</div>
<section>{sens}</section>
<section>
<h2>Como encaixar na rotina</h2>
<ul>{encaixe_html}</ul>
</section>
<section>{vale_html}</section>
<div class="cb-btns">
<a class="cb-btn" href="/ferramentas/ingredientes/?ativos={q}">Verificar a minha combinação</a>
<a class="cb-btn cb-sec" href="/ferramentas/prateleira/">Conferir com os produtos que eu já tenho</a>
</div>
{prods_html}
<section>
<h2>De onde vem esta resposta</h2>
<p>Ela sai de uma lista fixa de regras, a mesma do <a href="/ferramentas/ingredientes/">verificador de ingredientes</a> e do <a href="/provador/">provador</a>. As regras seguem orientações de uso comuns em dermatologia cosmética, sem citação de estudo específico, e ainda não foram revisadas por dermatologista. Quando não temos regra para um par, dizemos que não sabemos, em vez de dizer que pode.</p>
<p>É informação geral, não diagnóstico. Se arder, avermelhar ou descamar muito, pare e procure um dermatologista. Medicamento receitado segue a orientação de quem receitou.</p>
</section>
<section aria-labelledby="relacionados">
<h2 id="relacionados">Leia também</h2>
<ul class="ig-rel">{rel}<li><a href="/combina/">Todas as combinações</a></li></ul>
</section>
<script type="application/ld+json">{faq_txt}</script>
</article>"""
    descricao = f'{titulo} {r["rotulo"]}. {r["motivo"]}'[:300]
    trilha_nome = titulo.replace("Posso usar ", "").rstrip("?")
    return pagina(titulo, descricao, f"/combina/{slug_par(a, b)}/",
                  [("/", "Início"), ("/combina/", "Posso usar junto?"), (None, trilha_nome[0].upper() + trilha_nome[1:])],
                  corpo, css_extra=CSS)


def pagina_indice(itens, versao):
    grupos = []
    for res, tit in (("nao", "Não combine"), ("horarios", "Use em horários diferentes"), ("ok", "Pode usar junto")):
        linhas = [x for x in itens if x["normal"]["resultado"] == res and x["b"] != "irritada"]
        if linhas:
            lis = "".join(f'<li><a href="/combina/{slug_par(x["a"], x["b"])}/">{esc(titulo_par(x["a"], x["b"]))}</a></li>' for x in linhas)
            grupos.append(f"<h2>{ICONE[res]} {esc(tit)}</h2><ul class=\"cb-lista\">{lis}</ul>")
    irr = "".join(f'<li><a href="/combina/{slug_par(x["a"], x["b"])}/">{esc(titulo_par(x["a"], x["b"]))}</a></li>'
                  for x in itens if x["b"] == "irritada")
    corpo = f"""<article>
<div class="ig-cab">
<h1>Posso usar junto? Combinações de ativos</h1>
<p class="ig-lede">Retinol com vitamina C, ácido com niacinamida, ativo com a pele irritada: a resposta de cada combinação, com o motivo e como encaixar na rotina.</p>
</div>
<p>Não achou a sua? Monte qualquer combinação no <a href="/ferramentas/ingredientes/">verificador de ingredientes</a> ou cadastre os produtos que você já tem na <a href="/ferramentas/prateleira/">minha prateleira</a>.</p>
{"".join(grupos)}
<h2>⛔ Com a pele irritada</h2><ul class="cb-lista">{irr}</ul>
<p class="ig-nota">Respostas das regras versão {esc(versao)}: orientações de uso comuns em dermatologia cosmética, sem citação de estudo específico e ainda sem revisão de dermatologista. Pares sem regra cadastrada não aparecem aqui, porque não sabemos a resposta. Não é diagnóstico.</p>
</article>"""
    return pagina("Posso usar junto? Combinações de ativos de skincare",
                  "Retinol com vitamina C, ácido com niacinamida e outras combinações de ativos: pode usar junto, em horários diferentes ou não combine, com o motivo.",
                  "/combina/", [("/", "Início"), (None, "Posso usar junto?")], corpo, css_extra=CSS, larga=True)


def main():
    pares = ESPECIFICOS + GERAIS + [(c, "irritada") for c in IRRITADA]
    ids = lambda c: "irritada" if c == "irritada" else CLASSE[c][0]  # noqa: E731
    d = dados({"pares": [[ids(a), ids(b)] for a, b in pares]})
    itens = []
    for (a, b), r in zip(pares, d["pares"]):
        if r["normal"]["resultado"] == "sem_regra":
            print(f"pulei {a} + {b}: sem regra cadastrada")
            continue
        itens.append({"a": a, "b": b, "normal": r["normal"], "sensivel": r["sensivel"]})
    produtos = json.loads(CATALOGO.read_text(encoding="utf-8-sig"))["produtos"]
    DESTINO.mkdir(exist_ok=True)
    validos = {slug_par(x["a"], x["b"]) for x in itens}
    for pasta in DESTINO.iterdir():
        if pasta.is_dir() and pasta.name not in validos:
            shutil.rmtree(pasta)
    for x in itens:
        pasta = DESTINO / slug_par(x["a"], x["b"])
        pasta.mkdir(exist_ok=True)
        (pasta / "index.html").write_text(pagina_par(x, itens, d, produtos), encoding="utf-8")
    (DESTINO / "index.html").write_text(pagina_indice(itens, d["versao"]), encoding="utf-8")
    print(f"{len(itens)} combinações geradas em /combina/")


if __name__ == "__main__":
    main()
