"""Gera /skincare-premium/index.html a partir de skincare-premium-amazon.json.

Rode de novo sempre que atualizar o JSON (ver importar_skincare_premium.py):
    python3 -I _scripts/gerar_skincare_premium.py
Depois: seo.py e prontidao.py, como em toda página.

Link de cada produto: com "asin" no JSON, vai direto ao anúncio (/dp/ASIN?tag=...).
Sem "asin", o botão diz "Buscar na Amazon" e leva a uma busca pelo nome do anúncio, com a tag.
"""
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote_plus

sys.path.insert(0, str(Path(__file__).resolve().parent))
from menu import bloco as menu_superior

RAIZ = Path(__file__).resolve().parent.parent
CAMINHO = "/skincare-premium/"
dados = json.loads((RAIZ / "skincare-premium-amazon.json").read_text(encoding="utf-8"))
produtos = dados["produtos"]
TAG = dados["tag_afiliado"]
data = dados["atualizado_em"]
data_br = "/".join(reversed(data.split("-")))
LINK_CATEGORIA = f"https://www.amazon.com.br/b?node={dados['node']}&tag={TAG}"
ORDEM_CAT = ["Limpeza", "Hidratante e tratamento", "Protetor solar", "Sérum", "Máscara", "Outros"]
categorias = [c for c in ORDEM_CAT if any(p["categoria"] == c for p in produtos)]
marcas = sorted({p["marca"] for p in produtos if p["marca"] != "Outras marcas"}, key=str.lower)
if any(p["marca"] == "Outras marcas" for p in produtos):
    marcas.append("Outras marcas")

e = html.escape


def brl(v):
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def link(p):
    if p.get("asin"):
        return f"https://www.amazon.com.br/dp/{p['asin']}?tag={TAG}"
    return f"https://www.amazon.com.br/s?k={quote_plus(p['nome'][:180])}&tag={TAG}"


def nome_curto(p):
    # O que vem depois de " | " no anúncio é texto de venda do vendedor.
    return p["nome"].split(" | ")[0].strip()


_modelo = (RAIZ / "blog" / "protetor-solar-pele-oleosa" / "index.html").read_text(encoding="utf-8")
rodape = re.search(r'(<footer class="ps-rodape">.*?</footer>)', _modelo, re.S).group(1)
rodape = rodape.replace(f'<a href="{CAMINHO}">', f'<a href="{CAMINHO}" aria-current="page">', 1)

diretos = sum(1 for p in produtos if p.get("asin"))
cards = []
for p in produtos:
    nota = (f" · ⭐ {str(p['avaliacao']).replace('.', ',')} ({e(p['reviews'])} avaliações)" if p.get("avaliacao")
            else " · sem avaliações")
    botao = "Ver na Amazon ↗" if p.get("asin") else "Buscar na Amazon ↗"
    cards.append(f"""<li class="mv-item" data-cat="{e(p['categoria'])}" data-marca="{e(p['marca'])}">
<span class="mv-cat">{e(p['categoria'])}</span>
<h2 class="mv-nome">{e(nome_curto(p))}</h2>
<p class="mv-meta">{e(p['marca'])}{nota}</p>
<p class="mv-preco"><strong>{brl(p['preco'])}</strong> <small>em {data_br}</small></p>
<a class="mv-btn" href="{e(link(p))}" target="_blank" rel="sponsored nofollow noopener" data-produto="{e(nome_curto(p))}">{botao}</a>
</li>""")

ld = json.dumps({"@context": "https://schema.org", "@type": "ItemList",
                 "name": "Skincare Premium na Amazon Brasil", "numberOfItems": len(produtos),
                 "itemListElement": [{"@type": "ListItem", "position": i, "name": nome_curto(p)}
                                     for i, p in enumerate(produtos, 1)]}, ensure_ascii=False)

chips = "".join(f'<button type="button" class="rt-chip" data-cat="{e(c)}" aria-pressed="false">{e(c)}</button>'
                for c in categorias)
opcoes = "".join(f'<option value="{e(m)}">{e(m)}</option>' for m in marcas)
if diretos == len(produtos):
    nota_link = "Cada botão leva direto ao anúncio do produto na Amazon."
elif diretos == 0:
    nota_link = ("Os botões abrem uma busca na Amazon pelo nome do anúncio, e não o anúncio em si: "
                 "confira tamanho, cor e versão antes de comprar.")
else:
    nota_link = ("\"Ver na Amazon\" leva direto ao anúncio. \"Buscar na Amazon\" abre uma busca pelo nome do anúncio: "
                 "confira tamanho, cor e versão antes de comprar.")

pagina = f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Skincare Premium na Amazon: {len(produtos)} produtos | Produto Skincare</title>
<meta name="description" content="Os {len(produtos)} produtos da categoria Skincare Premium da Amazon Brasil em {data_br}: limpeza, hidratante, protetor solar, sérum e máscara, com preço datado.">
<meta name="robots" content="index, follow">
<link rel="canonical" href="https://produtoskincare.com.br{CAMINHO}">
<link rel="stylesheet" href="/premium.css">
<style>
.mv{{max-width:1000px;margin:0 auto;padding:28px max(18px,env(safe-area-inset-right,0px)) 60px max(18px,env(safe-area-inset-left,0px));display:flex;flex-direction:column;gap:24px}}
.mv h1{{font-size:clamp(2rem,6vw,3rem);margin:0;text-wrap:balance}}
.mv p{{margin:0}}
.mv-top{{display:flex;flex-direction:column;gap:12px}}
.mv-top .marca{{font-family:var(--fonte-display);font-weight:500;font-size:1rem;padding-bottom:16px;border-bottom:1px solid var(--linha);text-decoration:none;color:var(--tinta)}}
.mv-top .marca span{{color:var(--rosa)}}
.mv-trilha{{font-size:.88rem;color:var(--suave)}}.mv-trilha a{{color:var(--suave)}}
.mv-lede{{color:var(--suave);font-size:1.05rem;max-width:62ch}}
.mv-aviso{{font-size:.88rem;color:var(--suave);border-left:3px solid var(--linha-2);padding-left:12px;max-width:72ch}}
.rt-chips{{display:flex;flex-wrap:wrap;gap:8px}}
.rt-chip{{border:1px solid var(--linha-2);background:transparent;color:var(--tinta);border-radius:999px;padding:7px 15px;cursor:pointer;font-size:.92rem;min-height:40px}}
.rt-chip[aria-pressed="true"]{{background:var(--rosa);border-color:var(--rosa);color:var(--papel)}}
.sp-filtros{{display:flex;flex-wrap:wrap;gap:10px;align-items:center}}
.sp-filtros label{{display:flex;flex-direction:column;gap:4px;font-size:.8rem;color:var(--suave);flex:1 1 200px}}
.sp-filtros input,.sp-filtros select{{font:inherit;font-size:1rem;color:var(--tinta);background:var(--papel);border:1px solid var(--linha-2);border-radius:10px;padding:9px 12px;min-height:44px;width:100%}}
.sp-conta{{font-size:.88rem;color:var(--suave)}}
.mv-lista{{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px}}
.mv-item{{display:flex;flex-direction:column;gap:6px;min-width:0;background:var(--papel);border:1px solid var(--linha);border-radius:var(--raio);padding:16px;margin:0}}
.mv-item[hidden]{{display:none}}
.mv-cat{{font-size:.7rem;letter-spacing:.08em;text-transform:uppercase;font-weight:600;color:var(--verde)}}
.mv-nome{{font-size:1.05rem;margin:0;line-height:1.3;overflow-wrap:anywhere}}
.mv-meta{{font-size:.86rem;color:var(--suave)}}
.mv-preco{{margin-top:auto!important;padding-top:4px}}
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
{menu_superior(CAMINHO)}<main class="mv" id="conteudo">
<header class="mv-top">
<a class="marca" href="/">Produto <span>Skincare</span></a>
<nav class="mv-trilha" aria-label="Trilha"><a href="/">Início</a> › <a href="/achados/">Produtos</a> › Skincare Premium</nav>
<h1>Skincare Premium na Amazon</h1>
<p class="mv-lede">Os {len(produtos)} produtos que a Amazon Brasil listava em <a href="{e(LINK_CATEGORIA)}" target="_blank" rel="sponsored nofollow noopener">Beleza Premium › Skincare Premium</a> em {data_br}, na ordem "Em destaque" da loja. É a vitrine da Amazon, não uma seleção nossa: estar aqui não quer dizer que o produto serve para a sua pele. Use o <a href="/provador/">provador</a> para saber por onde começar.</p>
<p class="mv-aviso">Preços de {data_br}, semana de Black Friday: parte deles é promocional ou à vista no Pix e muda a qualquer momento. Vale o preço mostrado na Amazon na hora da compra. {nota_link} Contém links de afiliado: se você comprar por eles, posso receber comissão, sem custo extra.</p>
</header>
<div class="rt-chips" role="group" aria-label="Filtrar por categoria"><button type="button" class="rt-chip" data-cat="" aria-pressed="true">Todos</button>{chips}</div>
<div class="sp-filtros">
<label>Buscar pelo nome<input type="search" id="sp-busca" autocomplete="off" placeholder="ex.: vitamina C, FPS 70"></label>
<label>Marca<select id="sp-marca"><option value="">Todas as marcas</option>{opcoes}</select></label>
</div>
<p class="sp-conta" id="sp-conta" aria-live="polite">{len(produtos)} produtos</p>
<ul class="mv-lista" id="lista">
{chr(10).join(cards)}
</ul>
<footer class="mv-foot">
<p>Fonte: {e(dados['fonte'])}, consultada em {data_br}. Nome, nota e número de avaliações são os do anúncio; promessas que aparecem no nome são do vendedor e não foram verificadas por nós. A categoria de cada item foi deduzida do nome; em "Outros" ficam os itens que a Amazon lista aqui mas não são de cuidado facial, ou cujo nome não diz o tipo.</p>
<p>Veja também: <a href="/mais-vendidos/">mais vendidos na Amazon</a> · <a href="/produtos/">produtos com ficha no site</a></p>
<p>Conteúdo informativo, não substitui consulta com dermatologista. <a href="/privacidade/">Privacidade</a> · <a href="/sobre/">Sobre o site</a></p>
</footer>
</main>
{rodape}
<script>
(function(){{
  var chips = document.querySelectorAll(".rt-chip"), itens = document.querySelectorAll(".mv-item"),
      busca = document.getElementById("sp-busca"), marca = document.getElementById("sp-marca"),
      conta = document.getElementById("sp-conta"), cat = "";
  function limpo(t){{ return t.toLowerCase().normalize("NFD").replace(/[\\u0300-\\u036f]/g, ""); }}
  function aplicar(){{
    var q = limpo(busca.value.trim()), m = marca.value, n = 0;
    itens.forEach(function(i){{
      var ok = (!cat || i.dataset.cat === cat) && (!m || i.dataset.marca === m) && (!q || limpo(i.textContent).indexOf(q) > -1);
      i.hidden = !ok; if (ok) n++;
    }});
    conta.textContent = n === 1 ? "1 produto" : n + " produtos";
  }}
  chips.forEach(function(c){{ c.addEventListener("click", function(){{
    cat = c.dataset.cat;
    chips.forEach(function(x){{ x.setAttribute("aria-pressed", String(x === c)); }});
    aplicar();
  }}); }});
  busca.addEventListener("input", aplicar); marca.addEventListener("change", aplicar);
}})();
</script>
</body>
</html>
"""
saida = RAIZ / "skincare-premium" / "index.html"
saida.parent.mkdir(exist_ok=True)
saida.write_text(pagina, encoding="utf-8")
print("gerado", saida, len(produtos), "produtos,", diretos, "com link direto")
