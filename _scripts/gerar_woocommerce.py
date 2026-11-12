"""Gera a seção WooCommerce do site: hub /woocommerce/, páginas de cada grupo
(Vender, Construir, Recursos, Empresa) e o rodapé Woo com todas as colunas,
seletor de moeda, seletor de idioma, lojas de aplicativo e redes sociais.

O conteúdo de cada página fica em _scripts/woocommerce/dados_<grupo>.py.
Rode depois de mudar um desses arquivos:

    python3 _scripts/gerar_woocommerce.py
    python3 _scripts/menu.py
    python3 _scripts/seo.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "woocommerce"))

from pagina_base import RAIZ, pagina, esc  # noqa: E402

from dados_vender import PAGINAS as PAGINAS_VENDER  # noqa: E402
from dados_build import PAGINAS as PAGINAS_BUILD  # noqa: E402
from dados_recursos import PAGINAS as PAGINAS_RECURSOS  # noqa: E402
from dados_empresa import PAGINAS as PAGINAS_EMPRESA  # noqa: E402

BASE = "/woocommerce/"
AVISO = ("Página independente sobre WooCommerce, com links de afiliado. "
         "WooCommerce é marca da Automattic Inc. Conteúdo informativo, não é diagnóstico médico.")

# Ordem dos grupos = ordem da navegação original (Sell, Build, Resources, Company).
GRUPOS = [
    ("vender", "Vender", BASE + "vender/", PAGINAS_VENDER),
    ("construir", "Construir", BASE + "construir/", PAGINAS_BUILD),
    ("recursos", "Recursos", BASE + "recursos/", PAGINAS_RECURSOS),
    ("empresa", "Empresa", BASE + "empresa/", PAGINAS_EMPRESA),
]
TODAS = {p["caminho"]: (g, p) for g, _, _, ps in GRUPOS for p in ps}

CSS = """
.ig-lead{font-size:1.12rem;line-height:1.55;color:var(--tinta);margin:10px 0 18px}
.wo-chips{display:flex;flex-wrap:wrap;gap:8px;list-style:none;padding:0;margin:16px 0 0}
.wo-chips li{margin:0}
.wo-chips a{display:inline-flex;align-items:center;min-height:40px;padding:6px 16px;border:1.5px solid var(--linha-2,var(--linha));border-radius:999px;text-decoration:none;color:var(--tinta);font-weight:600;font-size:.92rem}
.wo-chips a:hover,.wo-chips a[data-atual]{border-color:var(--rosa);background:var(--rosa-claro)}
.wo-cards{list-style:none;padding:0;margin:14px 0;display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px}
.wo-cards li{margin:0}
.wo-cards a{display:flex;flex-direction:column;gap:6px;height:100%;padding:16px 18px;border:1px solid var(--linha);border-radius:var(--raio,14px);background:var(--papel);text-decoration:none;color:var(--tinta)}
.wo-cards a:hover{border-color:var(--rosa)}
.wo-cards strong{font-family:var(--fonte-display);font-size:1.12rem;font-weight:500}
.wo-cards span{font-size:.92rem;color:var(--suave)}
.wo-resumo{border:1.5px solid var(--linha-2,var(--linha));border-radius:0 14px 14px 0;border-left:4px solid var(--rosa);padding:14px 18px;margin:18px 0;background:var(--papel)}
.wo-resumo h2{margin:0 0 6px;font-size:1.05rem}
.wo-resumo ul{margin:6px 0 0}
.wo-cta{display:flex;flex-wrap:wrap;gap:10px;margin:18px 0}
.wo-cta a{display:inline-flex;align-items:center;min-height:48px;padding:10px 22px;border-radius:999px;background:var(--rosa);color:#fff;font-weight:600;text-decoration:none}
.wo-cta a.wo-sec{background:transparent;color:var(--tinta);border:1.5px solid var(--linha-2,var(--linha))}
.wo-rodape{margin:36px 0 0;padding:24px 0 0;border-top:2px solid var(--linha)}
.wo-rodape h2{font-size:1.05rem}
.wo-colunas{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:18px 22px}
.wo-colunas h3{font-family:var(--fonte-display);font-size:1.02rem;font-weight:500;margin:0 0 8px}
.wo-colunas ul{list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:6px}
.wo-colunas li{margin:0;font-size:.93rem}
.wo-colunas a{color:var(--tinta);text-decoration:none;border-bottom:1px solid transparent}
.wo-colunas a:hover{border-bottom-color:var(--rosa)}
.wo-colunas a[aria-current="page"]{font-weight:700;color:var(--rosa)}
.wo-baixo{display:flex;flex-wrap:wrap;gap:14px 26px;align-items:center;margin:22px 0 0;padding:18px 0 0;border-top:1px solid var(--linha);font-size:.92rem}
.wo-baixo ul{display:flex;flex-wrap:wrap;gap:8px 16px;list-style:none;padding:0;margin:0}
.wo-baixo li{margin:0}
.wo-baixo a{color:var(--tinta)}
.wo-lojas a{display:inline-flex;align-items:center;min-height:40px;padding:6px 14px;border:1.5px solid var(--linha-2,var(--linha));border-radius:10px;text-decoration:none;font-weight:600;font-size:.88rem}
.wo-lojas a:hover{border-color:var(--rosa)}
.wo-sel{display:flex;gap:8px;align-items:center}
.wo-sel label{font-size:.88rem;color:var(--suave)}
.wo-sel select{font:inherit;font-size:.9rem;padding:8px 10px;border:1.5px solid var(--linha-2,var(--linha));border-radius:10px;background:var(--papel);color:var(--tinta);min-height:40px}
.wo-legal{margin:14px 0 0;font-size:.85rem;color:var(--suave)}
.wo-legal a{color:var(--suave)}
"""

JS = """
<script>
(function(){
  var chave='woo-moeda', sel=document.getElementById('wo-moeda');
  if(sel){
    var salvo=null; try{salvo=localStorage.getItem(chave);}catch(e){}
    if(salvo) sel.value=salvo;
    sel.addEventListener('change',function(){
      try{localStorage.setItem(chave,sel.value);}catch(e){}
      document.querySelectorAll('.wo-moeda-atual').forEach(function(el){el.textContent=sel.value;});
    });
    document.querySelectorAll('.wo-moeda-atual').forEach(function(el){el.textContent=sel.value;});
  }
  var idi=document.getElementById('wo-idioma');
  if(idi){
    var raizes={'pt-BR':'/','en':'/en/','es':'/es/'};
    idi.addEventListener('change',function(){location.href=raizes[idi.value]||'/';});
  }
})();
</script>
"""

REDES = [
    ("https://www.facebook.com/woocommerce", "Facebook"),
    ("https://x.com/woocommerce", "X"),
    ("https://www.instagram.com/woocommerce", "Instagram"),
    ("https://www.linkedin.com/company/woocommerce", "LinkedIn"),
]
LOJAS = [
    ("https://apps.apple.com/app/woo-commerce/id1485887955", "Download on the App Store"),
    ("https://play.google.com/store/apps/details?id=com.woocommerce.android", "Get it on Google Play"),
]


def _nav_grupos(atual=None):
    itens = []
    for chave, nome, href, _ in GRUPOS:
        marca = ' data-atual' if chave == atual else ""
        itens.append(f'<li><a href="{href}"{marca}>{esc(nome)}</a></li>')
    return '<ul class="wo-chips">' + "".join(itens) + "</ul>"


def _rodape_woo(atual=None):
    """Rodapé Woo completo: colunas Vender/Construir/Recursos/Empresa + lojas, redes,
    seletor de moeda, seletor de idioma e links legais."""
    colunas = []
    for chave, nome, href, paginas in GRUPOS:
        cur_grupo = ' aria-current="page"' if href == atual else ""
        lis = [f'<li><a href="{href}"{cur_grupo}>{esc(nome)}</a></li>']
        if chave == "vender":
            lis.insert(0, f'<li><a href="{BASE}">WooCommerce</a></li>')
        for p in paginas:
            cur = ' aria-current="page"' if p["caminho"] == atual else ""
            lis.append(f'<li><a href="{p["caminho"]}"{cur}>{esc(p["rotulo"])}</a></li>')
        colunas.append(f'<div><h3>{esc(nome)}</h3><ul>{"".join(lis)}</ul></div>')
    lojas = "".join(f'<li><a href="{href}">{esc(t)}</a></li>' for href, t in LOJAS)
    redes = "".join(f'<li><a href="{href}">{esc(t)}</a></li>' for href, t in REDES)
    return f"""<nav class="wo-rodape" aria-label="Navegação do WooCommerce">
<h2>WooCommerce</h2>
<div class="wo-colunas">{"".join(colunas)}</div>
<div class="wo-baixo">
<ul class="wo-lojas">{lojas}</ul>
<ul>{redes}</ul>
<div class="wo-sel"><label for="wo-moeda">Moeda do site</label>
<select id="wo-moeda"><option value="BRL" selected>BRL — Real brasileiro</option><option value="USD">USD — Dólar americano</option></select></div>
<div class="wo-sel"><label for="wo-idioma">Idioma do site</label>
<select id="wo-idioma"><option value="pt-BR" selected>Português do Brasil</option><option value="en">English</option><option value="es">Español</option></select></div>
</div>
<p class="wo-legal"><a href="/termos/">Terms of Service</a> · <a href="/privacidade/">Privacy Policy</a> ·
WooCommerce e o logotipo do Woo são marcas da Automattic Inc. Esta é uma página independente, sem vínculo oficial.</p>
</nav>"""


def _faq(itens):
    if not itens:
        return ""
    linhas = "".join(f"<h3>{esc(q)}</h3>\n<p>{a}</p>\n" for q, a in itens)
    return f'<h2 id="perguntas">Perguntas frequentes</h2>\n{linhas}'


def _corpo_pagina(p, grupo):
    partes = [f"<h1>{esc(p['titulo'])}</h1>", f'<p class="ig-lead">{p["lead"]}</p>']
    for h2, html in p.get("secoes", []):
        partes.append(f"<h2>{esc(h2)}</h2>\n{html}")
    if p.get("resumo_itens"):
        lis = "".join(f"<li>{x}</li>" for x in p["resumo_itens"])
        partes.append(f'<aside class="wo-resumo"><h2>Em resumo</h2><ul>{lis}</ul></aside>')
    if p.get("cta"):
        texto, href = p["cta"]
        secundario = ""
        if p.get("cta2"):
            t2, h2 = p["cta2"]
            secundario = f'<a class="wo-sec" href="{h2}">{esc(t2)}</a>'
        partes.append(f'<div class="wo-cta"><a href="{href}">{esc(texto)}</a>{secundario}</div>')
    partes.append(_faq(p.get("faq", [])))
    partes.append(_rodape_woo(p["caminho"]))
    return '<article class="ig wo">' + "\n".join(partes) + "</article>"


def _corpo_grupo(chave, nome, href, paginas):
    resumo = {"vender": "Tudo o que o WooCommerce oferece para vender: preços, pagamentos, checkout, envios, marketing, temas, extensões e o aplicativo móvel.",
              "construir": "Documentação, recursos para desenvolvedores, o programa WooExpert, parcerias no Marketplace e o programa de afiliados.",
              "recursos": "Blog, documentação, vitrine de clientes, atualizações de produto, newsletter, suporte, hospedagem e agências.",
              "empresa": "Sobre a empresa, imprensa, download gratuito, comunidade, marcas, políticas de suporte e reembolso e contato."}[chave]
    extra = (f'<li><a href="{BASE}"><strong>WooCommerce</strong><span>Visão geral e navegação de todas as ferramentas e páginas.</span></a></li>'
             if chave == "vender" else "")
    cartoes = extra + "".join(
        f'<li><a href="{p["caminho"]}"><strong>{esc(p["rotulo"])}</strong><span>{esc(p["resumo"])}</span></a></li>'
        for p in paginas)
    return f"""<article class="ig wo">
<h1>{esc(nome)} — WooCommerce</h1>
<p class="ig-lead">{esc(resumo)}</p>
{_nav_grupos(chave)}
<h2>Páginas de {esc(nome.lower())}</h2>
<ul class="wo-cards">{cartoes}</ul>
{_rodape_woo(href)}
</article>"""


def _corpo_hub():
    blocos = []
    for chave, nome, href, paginas in GRUPOS:
        cartoes = "".join(
            f'<li><a href="{p["caminho"]}"><strong>{esc(p["rotulo"])}</strong><span>{esc(p["resumo"])}</span></a></li>'
            for p in paginas)
        blocos.append(f'<h2><a href="{href}">{esc(nome)}</a></h2>\n<ul class="wo-cards">{cartoes}</ul>')
    return f"""<article class="ig wo ig-larga">
<h1>WooCommerce</h1>
<p class="ig-lead">Guia em português do WooCommerce: as ferramentas e páginas oficiais organizadas em Vender,
Construir, Recursos e Empresa. Página independente, com links de afiliado — o WooCommerce é gratuito e de código aberto.</p>
{_nav_grupos()}
{"".join(blocos)}
{_rodape_woo(BASE)}
</article>"""


def gerar(caminho, titulo, descricao, trilha, corpo, larga=False):
    html = pagina(titulo, descricao, caminho, trilha, corpo, css_extra=CSS, scripts=JS,
                  larga=larga, aviso=AVISO)
    destino = RAIZ / caminho.strip("/") / "index.html"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(html, encoding="utf-8")
    print("gerada", caminho)


def main():
    gerar(BASE, "WooCommerce: ferramentas e páginas em português",
          "Todas as ferramentas e páginas do WooCommerce organizadas em Vender, Construir, Recursos e Empresa: preços, "
          "pagamentos, checkout, envios, extensões, temas, documentação, suporte e mais.",
          [("/", "Início"), (None, "WooCommerce")], _corpo_hub(), larga=True)
    for chave, nome, href, paginas in GRUPOS:
        gerar(href, f"{nome} — WooCommerce", f"{nome} no WooCommerce: " + (
              "preços, pagamentos, checkout, envios, marketing, aplicativo móvel, extensões e temas."
              if chave == "vender" else
              "documentação, recursos para desenvolvedores, WooExpert, parcerias e afiliados." if chave == "construir" else
              "blog, documentação, vitrine, atualizações, newsletter, suporte, hospedagem e agências." if chave == "recursos" else
              "sobre, imprensa, download gratuito, comunidade, marcas, políticas e contato."),
              [("/", "Início"), (BASE, "WooCommerce"), (None, nome)],
              _corpo_grupo(chave, nome, href, paginas), larga=True)
        for p in paginas:
            gerar(p["caminho"], p["titulo"], p["descricao"],
                  [("/", "Início"), (BASE, "WooCommerce"), (href, nome), (None, p["rotulo"])],
                  _corpo_pagina(p, chave))


if __name__ == "__main__":
    main()
