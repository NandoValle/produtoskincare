"""Gera as ferramentas que usam a casca dos artigos (pagina_base): prateleira, modo farmácia,
equivalente mais barato, modo 12 semanas e o índice /ferramentas/.

O conteúdo de cada página (HTML e JavaScript) fica em _scripts/ferramentas/<nome>.html.
Rode depois de mudar um desses arquivos:

    python3 _scripts/gerar_ferramentas.py
    python3 _scripts/menu.py
    python3 _scripts/seo.py
"""
from pagina_base import RAIZ, pagina

FONTES = RAIZ / "_scripts" / "ferramentas"

CSS = """
.ft-rotulo{display:block;font-weight:600;margin:14px 0 6px}
.ft-campo{width:100%;font:inherit;padding:12px 14px;border:1.5px solid var(--linha-2,var(--linha));border-radius:12px;background:var(--papel);color:var(--tinta)}
textarea.ft-campo{resize:vertical;min-height:96px}
.ft-campo:focus{outline:3px solid var(--rosa);outline-offset:2px}
.ft-btn{font:inherit;font-weight:600;display:inline-flex;align-items:center;justify-content:center;gap:8px;min-height:48px;padding:8px 22px;border-radius:999px;border:0;background:var(--rosa);color:#fff;cursor:pointer;text-decoration:none;margin:14px 0 0;position:relative}
.ft-btn.ft-sec{background:transparent;color:var(--tinta);border:1.5px solid var(--linha-2,var(--linha))}
.ft-btn:disabled{opacity:.5;cursor:default}
.ft-btn:focus-within{outline:3px solid var(--rosa);outline-offset:2px}
.ft-arquivo{position:absolute;width:1px;height:1px;opacity:0;pointer-events:none}
.ft-ocr{display:flex;flex-direction:column;align-items:flex-start;gap:4px}
.ft-cards-acoes{display:flex;flex-wrap:wrap;gap:0 12px;align-items:center}
.ft-outro{margin-top:14px}.ft-outro summary{cursor:pointer;font-weight:600;min-height:44px;display:flex;align-items:center}
.ft-periodo{border:0;padding:0;margin:0;display:flex;gap:18px;flex-wrap:wrap}.ft-periodo legend{padding:0}
.ft-periodo label,.ft-check{display:flex;gap:8px;align-items:center;min-height:44px;cursor:pointer}
.ft-sugestoes{list-style:none;padding:0;margin:8px 0 0;display:flex;flex-direction:column;gap:6px}
.ft-sugestoes li{margin:0}
.ft-sugestao{font:inherit;width:100%;text-align:left;display:flex;flex-direction:column;gap:2px;padding:10px 14px;border:1px solid var(--linha);border-radius:12px;background:var(--papel);color:var(--tinta);cursor:pointer}
.ft-sugestao span{font-size:.86rem;color:var(--suave)}
.ft-sugestao:hover{border-color:var(--rosa)}
.ft-itens{list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:8px}
.ft-item{margin:0;display:flex;flex-wrap:wrap;justify-content:space-between;gap:8px 16px;padding:12px 14px;border:1px solid var(--linha);border-radius:12px;background:var(--papel)}
.ft-item>div:first-child{display:flex;flex-direction:column;min-width:0;flex:1 1 240px}
.ft-item .ig-nota{margin:0}
.ft-item-acoes{display:flex;flex-wrap:wrap;gap:6px 14px;align-items:center}
.ft-item-acoes label{display:flex;gap:6px;align-items:center;min-height:40px}
.ft-mini{font:inherit;font-size:.88rem;background:none;border:1px solid var(--linha-2,var(--linha));border-radius:999px;padding:6px 12px;min-height:36px;color:var(--tinta);cursor:pointer;text-decoration:none;display:inline-flex;align-items:center}
.ft-ok,.ft-nao,.ft-horarios,.ft-sem,.ft-info{border-radius:0 12px 12px 0;padding:14px 16px;margin:10px 0;border-left:4px solid}
.ft-ok strong,.ft-nao strong,.ft-horarios strong,.ft-sem strong,.ft-info strong{display:block;margin-bottom:4px}
.ft-ok{background:var(--verde-claro);border-color:var(--verde)}
.ft-nao{background:var(--rosa-claro);border-color:var(--rosa)}
.ft-horarios{background:#fff4dd;border-color:#b7791f;color:#5c3d00}
.ft-sem{background:var(--papel);border:1.5px dashed var(--linha-2,var(--linha));border-left:4px solid #6b6b6b}
.ft-info{background:var(--papel);border-color:var(--linha-2,var(--linha))}
.ft-ok ul,.ft-nao ul,.ft-info ul{margin:6px 0 0}
.ft-sub{display:block;font-size:.88rem;opacity:.85;margin:4px 0}
.ft-tabela{width:100%;border-collapse:collapse;font-size:.94rem}
.ft-tabela th,.ft-tabela td{padding:9px 10px;border-bottom:1px solid var(--linha);text-align:left;vertical-align:top}
.ft-tabela tr.ft-agora{background:var(--rosa-claro)}
.ft-rolagem{overflow-x:auto}
.ft-grade{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:10px;list-style:none;padding:0;margin:10px 0}
.ft-grade li{margin:0}
.ft-foto{font:inherit;width:100%;padding:0;border:2px solid transparent;border-radius:12px;background:var(--papel);overflow:hidden;cursor:pointer;color:var(--tinta);text-align:left}
.ft-foto[aria-pressed="true"]{border-color:var(--rosa)}
.ft-foto img{display:block;width:100%;aspect-ratio:3/4;object-fit:cover}
.ft-foto span{display:block;padding:6px 8px;font-size:.84rem}
.ft-camera{position:relative;max-width:420px;border-radius:16px;overflow:hidden;background:#111;aspect-ratio:3/4}
.ft-camera video,.ft-camera img.ft-fantasma{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;transform:scaleX(-1)}
.ft-camera img.ft-fantasma{opacity:.35;pointer-events:none}
.ft-oval{position:absolute;inset:12% 18%;border:2px dashed rgba(255,255,255,.75);border-radius:50%;pointer-events:none}
.ft-lado{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.ft-lado figure{margin:0}.ft-lado img{width:100%;border-radius:12px;display:block}
.ft-lado figcaption{font-size:.88rem;color:var(--suave);margin-top:4px}
.ft-cards{list-style:none;padding:0;margin:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px}
.ft-cards li{margin:0}
.ft-cards a{display:flex;flex-direction:column;gap:6px;height:100%;padding:16px 18px;border:1px solid var(--linha);border-radius:var(--raio);background:var(--papel);text-decoration:none;color:var(--tinta)}
.ft-cards a:hover{border-color:var(--rosa)}
.ft-cards strong{font-family:var(--fonte-display);font-size:1.15rem;font-weight:500}
.ft-cards span{font-size:.92rem;color:var(--suave)}
@media(prefers-color-scheme:dark){.ft-horarios{color:#5c3d00}}
"""

PAGINAS = [
    {"fonte": "prateleira.html", "caminho": "/ferramentas/prateleira/", "trilha": "Minha prateleira",
     "titulo": "Minha prateleira: o que combina entre os produtos que você já tem",
     "descricao": "Cadastre os produtos de skincare que você já tem e veja o que não combina, o que se repete, que passo falta e quando cada um acaba. Salvo só no seu aparelho."},
    {"fonte": "farmacia.html", "caminho": "/ferramentas/farmacia/", "trilha": "Modo farmácia",
     "titulo": "Modo farmácia: combina com o que eu já tenho?",
     "descricao": "Na loja, fotografe a lista de ingredientes e veja se o produto combina com os que você já usa, se repete algum ativo e se preenche um passo que falta."},
    {"fonte": "equivalente.html", "caminho": "/ferramentas/equivalente/", "trilha": "Equivalente mais barato",
     "titulo": "Equivalente mais barato: mesmos ativos, outro preço",
     "descricao": "Digite o produto de skincare que você usa e veja opções do catálogo com os mesmos ativos e a mesma concentração, com o preço conferido e a data."},
    {"fonte": "12-semanas.html", "caminho": "/ferramentas/12-semanas/", "trilha": "Modo 12 semanas",
     "titulo": "Modo 12 semanas: comece um ativo novo aos poucos",
     "descricao": "Plano semana a semana para começar retinol, ácidos, vitamina C ou ácido azelaico devagar, com lembretes na agenda e diário de fotos só no seu aparelho."},
    {"fonte": "indice.html", "caminho": "/ferramentas/", "trilha": "Ferramentas", "larga": True,
     "titulo": "Ferramentas de skincare grátis",
     "descricao": "Todas as ferramentas do Produto Skincare: provador, prateleira, modo farmácia, verificador de ingredientes, equivalente mais barato, modo 12 semanas e mais."},
]


def main():
    for p in PAGINAS:
        corpo = (FONTES / p["fonte"]).read_text(encoding="utf-8")
        trilha = [("/", "Início")]
        if p["caminho"] != "/ferramentas/":
            trilha.append(("/ferramentas/", "Ferramentas"))
        trilha.append((None, p["trilha"]))
        html = pagina(p["titulo"], p["descricao"], p["caminho"], trilha, corpo, css_extra=CSS, larga=p.get("larga", False),
                      aviso="Ferramenta informativa, não substitui consulta com dermatologista.")
        destino = RAIZ / p["caminho"].strip("/") / "index.html"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(html, encoding="utf-8")
        print("gerada", p["caminho"])


if __name__ == "__main__":
    main()
