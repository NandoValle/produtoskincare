#!/usr/bin/env python3
"""Gera as páginas estáticas /rotinas/ a partir de rotinas/rotinas.json e produtos.json.

Uso (na raiz do repositório):  python3 scripts/gerar_rotinas.py
Rode de novo sempre que mudar rotinas.json ou os preços/links do produtos.json.
Depois rode  python3 _scripts/seo.py  para refazer Open Graph, JSON-LD e sitemap.
"""
import html
import json
import pathlib
import re

RAIZ = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://produtoskincare.com.br"

dados = json.loads((RAIZ / "rotinas" / "rotinas.json").read_text(encoding="utf-8-sig"))
catalogo = {p["id"]: p for p in json.loads((RAIZ / "produtos.json").read_text(encoding="utf-8-sig"))["produtos"]}
extras = dados["extras"]
FAIXAS = dados["faixas"]
PASSOS = {"limpeza": "Limpeza", "tratamento": "Tratamento", "hidratacao": "Hidratação", "protetor": "Protetor solar"}
LOJAS = {"amazon": "Amazon", "shopee": "Shopee", "mercadolivre": "Mercado Livre", "tiktok": "TikTok Shop"}
PREP = {"Mercado Livre": "no", "TikTok Shop": "no"}
COR_EVID = {"Forte": "verde", "Moderada": "", "Emergente": "cinza"}

e = html.escape


def produto(passo):
    if "id" in passo:
        p = catalogo.get(passo["id"])
        if not p:
            raise SystemExit(f"Produto '{passo['id']}' não existe no produtos.json")
        return p
    p = extras.get(passo["extra"])
    if not p:
        raise SystemExit(f"Extra '{passo['extra']}' não existe em rotinas.json")
    return {**p, "id": passo["extra"], "preco": None}


def brl(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def data_br(iso):
    return "/".join(reversed(iso.split("-")))


def link_attrs(url):
    if url.startswith("/"):
        return f'href="{e(url)}"'
    return f'href="{e(url)}" target="_blank" rel="sponsored noopener"'


def passo_html(passo):
    p = produto(passo)
    loja = LOJAS.get(p.get("plataforma"), "")
    if passo.get("repetido"):
        nota = f'<div class="nota">{e(passo["nota"])}</div>' if passo.get("nota") else ""
        return f'''<li class="passo repetido"><div class="cat">{PASSOS[passo["passo"]]}</div>
<div class="nome">{e(p["nome"])} <span class="sub">(o mesmo da manhã)</span></div>{nota}</li>'''
    if p.get("preco"):
        preco = f'{brl(p["preco"])} <small class="sub">visto em {data_br(p["preco_em"])}</small>'
    else:
        preco = '<small class="sub">ver preço na loja</small>'
    nota = f'<div class="nota">{e(passo["nota"])}</div>' if passo.get("nota") else ""
    return f'''<li class="passo"><div class="cat">{PASSOS[passo["passo"]]}{" · " + loja if loja else ""}</div>
<div class="nome">{e(p["nome"])}</div>
<div class="porque">{e(p["porque"])}</div>{nota}
<div class="linha-preco"><span>{preco}</span><a class="btn-loja" {link_attrs(p["link"])}>Ver {PREP.get(loja, "na")} {loja or "loja"} →</a></div></li>'''


def total(faixa):
    vistos, soma, sem_preco = set(), 0.0, 0
    for per in ("manha", "noite"):
        for passo in faixa[per]:
            chave = passo.get("id") or passo.get("extra")
            if chave in vistos:
                continue
            vistos.add(chave)
            p = produto(passo)
            if p.get("preco"):
                soma += p["preco"]
            else:
                sem_preco += 1
    return soma, sem_preco, len(vistos)


ESTILO = """<style>
:root{--fundo:#faf7f2;--papel:#fff;--tinta:#1a1614;--suave:#7a6e65;--linha:rgba(26,22,20,0.08);--rosa:#b4546a;--rosa-claro:#fdf2f4;--verde:#3f6b55;--verde-claro:#eef4f0;--raio:14px;--fonte-display:'Fraunces',Georgia,serif;--fonte-corpo:'Inter',sans-serif}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--fundo);color:var(--tinta);font:16px/1.7 var(--fonte-corpo);padding:0 18px}
main{max-width:760px;margin:0 auto;padding:28px 0 60px}
h1,h2,h3{font-family:var(--fonte-display);font-weight:400;letter-spacing:-0.02em;line-height:1.2}
h1{font-size:clamp(1.8rem,5vw,2.6rem);margin:.3em 0}
h2{font-size:1.35rem;margin:2em 0 .5em}
h3{font-size:1.05rem;margin:1.2em 0 .4em}
a{color:var(--rosa)}
.marca{font-family:var(--fonte-display);font-weight:500;font-size:.95rem}.marca span{color:var(--rosa)}
.sub{color:var(--suave)}
.card{background:var(--papel);border:1px solid var(--linha);border-radius:var(--raio);padding:20px;margin:16px 0;display:block;text-decoration:none;color:inherit}
.aviso{border-left:3px solid var(--verde);background:var(--verde-claro);border-radius:0 var(--raio) var(--raio) 0}
.aviso-rosa{border-left:3px solid var(--rosa);background:var(--rosa-claro);border-radius:0 var(--raio) var(--raio) 0}
.btn{font:inherit;font-weight:600;min-height:48px;padding:0 24px;border-radius:10px;border:0;background:var(--tinta);color:var(--fundo);cursor:pointer;display:inline-flex;align-items:center;text-decoration:none}
.abas{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0}
.abas a{border:1px solid var(--linha);background:var(--papel);border-radius:999px;padding:8px 16px;text-decoration:none;color:var(--tinta);font-weight:600;font-size:.92rem}
.faixa{scroll-margin-top:16px}
.faixa:target{outline:2px solid var(--rosa);outline-offset:4px}
.faixa-topo{display:flex;flex-wrap:wrap;justify-content:space-between;gap:8px;align-items:baseline}
.faixa-topo h2{margin:0}
.total{font-weight:600}
.periodos{display:grid;gap:16px;grid-template-columns:1fr}
@media(min-width:700px){.periodos{grid-template-columns:1fr 1fr}}
.periodo h3{margin-top:0}
ol.passos{list-style:none;padding:0;counter-reset:p}
.passo{border-top:1px solid var(--linha);padding:12px 0}
.passo:first-child{border-top:0}
.cat{font-size:.75rem;text-transform:uppercase;letter-spacing:.06em;color:var(--rosa);font-weight:600}
.nome{font-weight:600;line-height:1.35}
.porque,.nota{font-size:.9rem;color:var(--suave);line-height:1.5;margin-top:4px}
.nota{color:var(--verde)}
.nota::before{content:"→ "}
.linha-preco{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:8px;margin-top:8px;font-size:.92rem}
.btn-loja{font-weight:600;text-decoration:none;border:1px solid var(--rosa);border-radius:8px;padding:6px 12px;font-size:.85rem}
.repetido .nome{font-weight:400}
.pill{display:inline-block;border-radius:999px;padding:2px 10px;font-size:.75rem;font-weight:600;background:var(--rosa-claro);color:var(--rosa)}
.pill.verde{background:var(--verde-claro);color:var(--verde)}
.pill.cinza{background:#eee;color:#555}
.ativo{padding:10px 0;border-top:1px solid var(--linha)}
.ativo:first-child{border-top:0}
ul{padding-left:20px}li{margin:6px 0}
ol.passos li{margin:0}
.grade{display:grid;gap:12px;grid-template-columns:1fr}
@media(min-width:600px){.grade{grid-template-columns:1fr 1fr}}
:focus-visible{outline:3px solid var(--rosa);outline-offset:2px}
</style>"""

AFILIADO = ("Contém links de afiliado: se você comprar por eles, o site pode receber comissão, sem custo extra para você. "
            "Preços são os vistos na data indicada e podem mudar. Faça teste de sensibilidade antes de usar um produto novo. "
            "Conteúdo informativo, não substitui consulta com dermatologista.")


def cabeca(titulo, descricao, caminho):
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(titulo)}</title>
<meta name="description" content="{e(descricao)}">
<link rel="canonical" href="{SITE}{caminho}">
<!-- Gerado por scripts/gerar_rotinas.py a partir de rotinas/rotinas.json. Edite o JSON, não este arquivo. -->
{ESTILO}
<link rel="stylesheet" href="/premium.css">
</head>
<body>
<main>
"""


# Rodapé do site: o mesmo do artigo-modelo (igual a _scripts/pagina_base.py), para as rotinas
# terem os mesmos links de navegação que o resto do site.
_modelo = (RAIZ / "blog" / "protetor-solar-pele-oleosa" / "index.html").read_text(encoding="utf-8")
_RODAPE_SITE = re.search(r'(<footer class="ps-rodape">.*?</footer>)', _modelo, re.S).group(1)


def rodape(caminho):
    site = _RODAPE_SITE.replace(f'<a href="{caminho}">', f'<a href="{caminho}" aria-current="page">', 1)
    return f"""
<p class="sub" style="margin-top:30px;font-size:.82rem">{AFILIADO}</p>
<p class="sub" style="font-size:.82rem">© 2026 Produto Skincare.</p>
</main>
{site}
</body>
</html>
"""


def pagina_rotina(slug, r):
    caminho = f"/rotinas/{slug}/"
    partes = [cabeca(f"{r['h1']} | Produto Skincare", r["descricao"], caminho)]
    partes.append(f'''<div class="marca">Produto <span>Skincare</span> · Rotinas</div>
<p class="sub"><a href="/rotinas/">← Todas as rotinas</a></p>
<h1>{r["emoji"]} {e(r["h1"])}</h1>
<div class="card aviso">{e(r["resumo"])}</div>
<nav class="abas" aria-label="Faixas de preço">''')
    for chave, f in FAIXAS.items():
        partes.append(f'<a href="#{chave}">{f["nome"]}</a>')
    partes.append("</nav>")

    for chave, f in FAIXAS.items():
        faixa = r["faixas"][chave]
        soma, sem_preco, n = total(faixa)
        extra_txt = f" + {sem_preco} {'item' if sem_preco == 1 else 'itens'} com preço na loja" if sem_preco else ""
        partes.append(f'''<section class="card faixa" id="{chave}">
<div class="faixa-topo"><h2>{f["nome"]}</h2><span class="total">{n} produtos · {brl(soma)}{extra_txt}</span></div>
<p class="sub" style="margin:4px 0 12px">{e(f["descricao"])}</p>
<div class="periodos">''')
        for per, nome_per in (("manha", "☀️ Manhã"), ("noite", "🌙 Noite")):
            itens = "\n".join(passo_html(p) for p in faixa[per])
            partes.append(f'<div class="periodo"><h3>{nome_per}</h3><ol class="passos">{itens}</ol></div>')
        partes.append("</div></section>")

    v = r.get("viral")
    if v:
        p = extras[v["extra"]]
        loja = LOJAS.get(p.get("plataforma"), "loja")
        partes.append(f'''<h2>🔥 Viral do momento</h2>
<div class="card"><div class="nome">{e(p["nome"])} <span class="pill {COR_EVID.get(v["evidencia"], "")}">Evidência {v["evidencia"].lower()}</span></div>
<div class="porque">{e(p["porque"])}</div>
<p class="sub" style="font-size:.9rem;margin-top:6px">{e(v["texto"])}</p>
<div class="linha-preco"><small class="sub">ver preço na loja</small><a class="btn-loja" {link_attrs(p["link"])}>Ver {"os achados" if p["link"].startswith("/") else PREP.get(loja, "na") + " " + loja} →</a></div></div>''')

    partes.append('<h2>Por que esses ativos</h2><div class="card">')
    for a in r["ativos"]:
        partes.append(f'<div class="ativo"><strong>{e(a["nome"])}</strong> <span class="pill {COR_EVID.get(a["evidencia"], "")}">Evidência {a["evidencia"].lower()}</span><div class="porque">{e(a["texto"])}</div></div>')
    partes.append('</div><p class="sub" style="font-size:.85rem">Forte: vários estudos clínicos ou diretriz médica. Moderada: alguns estudos clínicos. Emergente: estudos pequenos ou só de laboratório.</p>')

    partes.append("<h2>Cuidados</h2><div class=\"card\"><ul>")
    partes.extend(f"<li>{e(c)}</li>" for c in r["cuidados"])
    partes.append("</ul></div>")
    partes.append(f'<h2>Quando procurar dermatologista</h2><div class="card aviso-rosa">{e(r["derma"])}</div>')

    links = ['<a class="btn" href="/provador/">Fazer o provador →</a>']
    if r.get("condicao"):
        links.append(f'<a href="{r["condicao"]}" style="margin-left:12px">Entenda a {e(r["titulo"].lower())} →</a>')
    partes.append(f'<p style="margin-top:24px">{"".join(links)}</p>')
    partes.append(rodape(caminho))
    return "\n".join(partes)


def pagina_indice():
    partes = [cabeca("Rotinas de skincare por faixa de preço | Produto Skincare",
                     "Rotinas prontas para acne, rosácea, melasma e anti-age, cada uma em versão econômica, intermediária e premium.",
                     "/rotinas/")]
    partes.append('''<div class="marca">Produto <span>Skincare</span> · Rotinas</div>
<p class="sub"><a href="/">← Voltar ao início</a></p>
<h1>Rotinas prontas por faixa de preço</h1>
<p class="sub">Escolha sua principal preocupação. Cada rotina tem três versões, da mais econômica à premium, com ativos que têm comprovação científica.</p>
<div class="grade">''')
    for slug, r in dados["rotinas"].items():
        minimo, _, _ = total(r["faixas"]["economica"])
        partes.append(f'''<a class="card" href="/rotinas/{slug}/"><h2 style="margin:0">{r["emoji"]} {e(r["titulo"])}</h2>
<p class="sub" style="margin:6px 0 0;font-size:.92rem">Rotina completa a partir de {brl(minimo)}</p></a>''')
    partes.append('''</div>
<div class="card aviso">Não sabe por onde começar? O <a href="/provador/">provador</a> estima seu tipo de pele e indica a rotina certa. Se quer só o básico por tipo de pele, veja a <a href="/rotina-de-skincare/">rotina passo a passo</a>.</div>''')
    partes.append(rodape("/rotinas/"))
    return "\n".join(partes)


def main():
    (RAIZ / "rotinas" / "index.html").write_text(pagina_indice(), encoding="utf-8")
    for slug, r in dados["rotinas"].items():
        pasta = RAIZ / "rotinas" / slug
        pasta.mkdir(parents=True, exist_ok=True)
        (pasta / "index.html").write_text(pagina_rotina(slug, r), encoding="utf-8")
        print(f"ok /rotinas/{slug}/", " | ".join(f"{k}: {brl(total(r['faixas'][k])[0])}" for k in FAIXAS))


if __name__ == "__main__":
    main()
