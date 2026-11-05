"""Gera /mais-vendidos/index.html a partir de top50-skincare-amazon.json.

Rode de novo sempre que atualizar o JSON:
    python3 _scripts/gerar_mais_vendidos.py
"""
import html
import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
dados = json.loads((RAIZ / "top50-skincare-amazon.json").read_text(encoding="utf-8-sig"))
produtos = sorted(dados["produtos"], key=lambda p: p["rank"])
data = dados["atualizado_em"]
data_br = "/".join(reversed(data.split("-")))
categorias = []
for p in produtos:
    if p["categoria"] not in categorias:
        categorias.append(p["categoria"])

e = html.escape


def brl(v):
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# Rodapé do site: o mesmo do artigo-modelo, para a página não perder o rodapé ao ser regerada.
_modelo = (RAIZ / "blog" / "protetor-solar-pele-oleosa" / "index.html").read_text(encoding="utf-8")
rodape = re.search(r'(<footer class="ps-rodape">.*?</footer>)', _modelo, re.S).group(1)
rodape = rodape.replace('<a href="/mais-vendidos/">', '<a href="/mais-vendidos/" aria-current="page">', 1)


def eh_refil(p):
    return "refil" in p["nome"].lower()


tem_refil = any(eh_refil(p) for p in produtos)
cards = []
for p in produtos:
    selo_refil = ' <span class="mv-refil">Refil</span>' if eh_refil(p) else ""
    cards.append(f"""<li class="mv-item" data-cat="{e(p['categoria'])}" data-refil="{'1' if eh_refil(p) else ''}">
<span class="mv-pos" aria-label="Posição {p['rank']}">{p['rank']}</span>
<div class="mv-corpo">
<span class="mv-cat">{e(p['categoria'])}</span>{selo_refil}
<h2 class="mv-nome">{e(p['nome'])}</h2>
<p class="mv-meta">{e(p['marca'])} · ⭐ {str(p['avaliacao']).replace('.', ',')} ({f"{p['reviews']:,}".replace(",", ".")} avaliações)</p>
<p class="mv-preco"><strong>{brl(p['preco'])}</strong> <small>em {data_br}</small></p>
<a class="mv-btn" href="{e(p['link'])}" target="_blank" rel="sponsored nofollow noopener" data-produto="{e(p['nome'])}">Ver na Amazon ↗</a>
</div>
</li>""")

itens_ld = [{"@type": "ListItem", "position": p["rank"], "name": p["nome"], "url": p["link"].split("?")[0]} for p in produtos]
ld = json.dumps({"@context": "https://schema.org", "@type": "ItemList", "name": "Produtos de skincare mais vendidos na Amazon Brasil",
                 "numberOfItems": len(produtos), "itemListElement": itens_ld}, ensure_ascii=False)

botoes = "".join(f'<button type="button" class="rt-chip" data-cat="{e(c)}" aria-pressed="false">{e(c)}</button>' for c in categorias)
if tem_refil:
    botoes += '<button type="button" class="rt-chip" data-cat="__refil" aria-pressed="false">Só refil</button>'
nota_revisao = (f'<p>{e(dados["revisao"])}</p>' if dados.get("revisao") else "")
nota_refil = ('<p class="mv-aviso">Refil é a versão de reposição do produto. Costuma custar menos que a embalagem original '
              'e usar menos plástico. Confira no anúncio se ele serve na embalagem que você tem.</p>') if tem_refil else ""

pagina = f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Skincare Mais Vendidos na Amazon ({data_br[3:]}) | Produto Skincare</title>
<meta name="description" content="Os produtos de skincare mais vendidos na Amazon Brasil em {data_br}: hidratantes, protetores, séruns e limpeza, com preço datado e avaliações.">
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://produtoskincare.com.br/mais-vendidos/">
<link rel="stylesheet" href="/premium.css">
<style>
.mv{{max-width:860px;margin:0 auto;padding:28px max(18px,env(safe-area-inset-right,0px)) 60px max(18px,env(safe-area-inset-left,0px));display:flex;flex-direction:column;gap:28px}}
.mv h1{{font-size:clamp(2rem,6vw,3rem);margin:0;text-wrap:balance}}
.mv p{{margin:0}}
.mv-top{{display:flex;flex-direction:column;gap:12px}}
.mv-top .marca{{font-family:var(--fonte-display);font-weight:500;font-size:1rem;padding-bottom:16px;border-bottom:1px solid var(--linha);text-decoration:none;color:var(--tinta)}}
.mv-top .marca span{{color:var(--rosa)}}
.mv-trilha{{font-size:.88rem;color:var(--suave)}}.mv-trilha a{{color:var(--suave)}}
.mv-lede{{color:var(--suave);font-size:1.05rem;max-width:62ch}}
.mv-aviso{{font-size:.88rem;color:var(--suave);border-left:3px solid var(--linha-2);padding-left:12px}}
.rt-chips{{display:flex;flex-wrap:wrap;gap:8px}}
.rt-chip{{border:1px solid var(--linha-2);background:transparent;color:var(--tinta);border-radius:999px;padding:7px 15px;cursor:pointer;font-size:.92rem;min-height:40px}}
.rt-chip[aria-pressed="true"]{{background:var(--rosa);border-color:var(--rosa);color:var(--papel)}}
.mv-lista{{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px}}
.mv-item{{display:grid;grid-template-columns:44px 1fr;gap:12px;background:var(--papel);border:1px solid var(--linha);border-radius:var(--raio);padding:16px;margin:0}}
.mv-item[hidden]{{display:none}}
.mv-pos{{font-family:var(--fonte-display);font-size:1.3rem;width:44px;height:44px;border-radius:50%;background:var(--rosa-claro);color:var(--rosa);display:grid;place-items:center}}
.mv-corpo{{display:flex;flex-direction:column;gap:6px;min-width:0}}
.mv-refil{{display:inline-block;margin-left:6px;font-size:.66rem;letter-spacing:.08em;text-transform:uppercase;font-weight:700;padding:2px 8px;border-radius:999px;background:var(--verde-claro);color:var(--verde)}}
.mv-cat{{font-size:.7rem;letter-spacing:.08em;text-transform:uppercase;font-weight:600;color:var(--verde)}}
.mv-nome{{font-size:1.15rem;margin:0;line-height:1.25}}
.mv-meta{{font-size:.86rem;color:var(--suave)}}
.mv-preco small{{color:var(--suave);font-size:.8rem}}
.mv-btn{{align-self:flex-start;margin-top:4px;text-decoration:none;font-weight:600;font-size:.9rem;color:var(--papel);background:var(--rosa);padding:9px 16px;border-radius:999px}}
.mv-btn:hover{{background:var(--rosa-2)}}
.mv-foot{{display:flex;flex-direction:column;gap:10px;font-size:.86rem;color:var(--suave);border-top:1px solid var(--linha);padding-top:20px}}
</style>
<script type="application/ld+json">{ld}</script>
<!-- seo:inicio -->
<!-- seo:fim -->
</head>
<body>
<main class="mv" id="conteudo">
<header class="mv-top">
<a class="marca" href="/">Produto <span>Skincare</span></a>
<nav class="mv-trilha" aria-label="Trilha"><a href="/">Início</a> › Mais vendidos</nav>
<h1>Os produtos de skincare mais vendidos na Amazon</h1>
<p class="mv-lede">Lista montada em {data_br} a partir das páginas de mais vendidos da Amazon Brasil em Pele, Dermocosméticos e Premium Beauty. Mais vendido não quer dizer melhor para a sua pele: use a lista como ponto de partida e confira no <a href="/provador/">provador</a> o que combina com você.</p>
<p class="mv-aviso">Preços e posições são os de {data_br} e mudam todo dia. Vale o preço mostrado na Amazon na hora da compra. Contém links de afiliado: se você comprar por eles, posso receber comissão, sem custo extra.</p>
</header>
<div class="rt-chips" role="group" aria-label="Filtrar por categoria"><button type="button" class="rt-chip" data-cat="" aria-pressed="true">Todos</button>{botoes}</div>
{nota_refil}
<ol class="mv-lista" id="lista">
{chr(10).join(cards)}
</ol>
<footer class="mv-foot">
<p>Fonte: {e(dados['fonte'])}, consultada em {data_br}. A ordem segue a nossa compilação dessas listas e pode não coincidir com a posição atual em cada uma.</p>
{nota_revisao}
<p>Conteúdo informativo, não substitui consulta com dermatologista. <a href="/privacidade/">Privacidade</a> · <a href="/sobre/">Sobre o site</a></p>
</footer>
</main>
{rodape}
<script>
(function(){{
  var chips = document.querySelectorAll(".rt-chip"), itens = document.querySelectorAll(".mv-item");
  chips.forEach(function(c){{ c.addEventListener("click", function(){{
    var cat = c.dataset.cat;
    chips.forEach(function(x){{ x.setAttribute("aria-pressed", String(x === c)); }});
    itens.forEach(function(i){{ i.hidden = cat === "__refil" ? !i.dataset.refil : (!!cat && i.dataset.cat !== cat); }});
  }}); }});
}})();
</script>
</body>
</html>
"""
saida = RAIZ / "mais-vendidos" / "index.html"
saida.parent.mkdir(exist_ok=True)
saida.write_text(pagina, encoding="utf-8")
print("gerado", saida, len(produtos), "produtos")
