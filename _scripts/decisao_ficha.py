"""Abre cada ficha de ativo (/ativos/<slug>/ e /ingredientes/<slug>/) com quatro respostas de decisão.

    python -I _scripts/decisao_ficha.py

As quatro respostas ficam logo depois do título, antes de "Em poucas palavras":

  1. Por que considerar?
  2. Quando faz sentido pular?
  3. Em que etapa entra?
  4. O que sabemos sobre o benefício? (o ingrediente e a fórmula final, em linhas separadas)

Depois da etapa entra um quinto item, "Você já tem este ativo em casa?", que sai oculto do HTML:
o /ritual.js o preenche no navegador com a Minha prateleira de quem visita (salva só no aparelho).

O script NÃO escreve conteúdo novo sobre o ativo: cada resposta é montada com o que a própria
ficha já diz (resumo, selos, nível, categoria, caixa de evidência). O que a ficha não diz fica
de fora. Referências, detalhes e combinações continuam logo abaixo, como estavam.

Também tira das fichas o link genérico "Ver opções com X na Amazon": é uma busca, não uma oferta
conferida. Quando o catálogo não tem produto com o ativo, a ficha diz isso e não aponta loja.

Pode rodar quantas vezes quiser: o bloco fica entre <!-- decisao:inicio --> e <!-- decisao:fim -->.
"""
import html
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
INI, FIM = "<!-- decisao:inicio -->", "<!-- decisao:fim -->"

CSS = """<style>
.ig-decisao{margin:22px 0;border-top:1px solid var(--linha);border-bottom:1px solid var(--linha)}
.ig-decisao dl{margin:0}
.ig-decisao div.ig-d{padding:16px 0;border-top:1px solid var(--linha)}
.ig-decisao div.ig-d:first-child{border-top:0}
.ig-decisao dt{font-family:var(--fonte-display,Georgia,serif);font-size:1.18rem;line-height:1.3;margin:0 0 6px}
.ig-decisao dd{margin:0}
.ig-decisao dd p{margin:0 0 6px}
.ig-decisao dd ul{margin:0;padding-left:20px}
.ig-decisao dd li+li{margin-top:4px}
.ig-decisao .ig-d-rotulo{font-weight:700}
</style>"""

# Etapa da rotina pela categoria do guia (só nas fichas de /ativos/, que trazem a categoria).
ETAPA = {
    "filtros solares": "No protetor solar, que é o último passo da rotina da manhã.",
    "hidratantes": "Costuma vir no hidratante: depois da limpeza e do tratamento, antes do protetor solar de manhã.",
    "barreira e emolientes": "Costuma vir no hidratante: depois da limpeza e do tratamento, antes do protetor solar de manhã.",
    "calmantes e reparadores": "Costuma vir em séruns e hidratantes: depois da limpeza, antes do protetor solar de manhã.",
    "autobronzeadores": "",
}
TRATAMENTO = "Na etapa de tratamento: depois da limpeza e antes do hidratante."
PELES = ["oleosa", "mista", "normal", "seca", "sensível"]
UNIVERSAL = "Se o que você já usa cuida do mesmo objetivo e a sua pele vai bem."


def texto(trecho):
    return html.unescape(re.sub(r"<[^>]+>", "", trecho)).strip()


def campo(resumo, rotulo):
    m = re.search(r"<li><b>%s:</b>\s*(.*?)</li>" % re.escape(rotulo), resumo, re.S)
    return m.group(1).strip() if m else ""


def frase(t):
    t = t.strip()
    t = t[0].upper() + t[1:] if t else t
    return t if not t or t[-1] in ".!?" else t + "."


def respostas(pagina):
    resumo = re.search(r'<div class="ig-caixa ig-resumo">(.*?)</div>', pagina, re.S)
    if not resumo:
        return None
    resumo = resumo.group(1)
    selos = re.findall(r'class="ig-selo [a-z]+">([^<]+)', pagina)
    para_quem, quando = campo(resumo, "Para quem"), campo(resumo, "Quando")
    gestacao, atencao = campo(resumo, "Gestação"), campo(resumo, "Atenção")
    orientacoes = "Orientações de uso" in selos  # ficha de /ativos/: não cita estudos

    # 1. Por que considerar?
    if orientacoes:
        objetivos = para_quem.split(";")[0].strip()
        considerar = f"Costuma ser indicado para {objetivos}." if objetivos else ""
    else:
        considerar = f"Costuma fazer sentido para {para_quem[0].lower() + para_quem[1:]}" if para_quem else ""
        considerar = frase(considerar)

    # 2. Quando faz sentido pular?
    pular = []
    if "evitar" in texto(gestacao).lower() or "gestação" in texto(atencao).lower():
        pular.append('Na gestação, na amamentação ou tentando engravidar: veja <a href="#gestacao">gestação e amamentação</a>.')
    if "Receita médica" in selos:
        pular.append("Sem receita: este ativo é medicamento e depende de orientação médica.")
    if "Fotossensibilizante" in selos:
        pular.append("Se você não usa protetor solar todos os dias: ele aumenta a sensibilidade ao sol.")
    if "já tem experiência com ativos mais fortes" in pagina:
        pular.append("Se você está começando: a ficha indica este ativo para quem já tem experiência com ativos mais fortes.")
    elif "já usa algum ativo e sabe como a pele reage" in pagina:
        pular.append("Se este seria o seu primeiro ativo: a ficha indica para quem já usa algum e sabe como a pele reage.")
    if orientacoes and ";" in para_quem:
        indicadas = texto(para_quem.split(";", 1)[1]).lower()
        fora = [p for p in PELES if p not in indicadas]
        if fora and len(fora) < len(PELES):
            pular.append(f"Se a sua pele é {' ou '.join(fora)}: ela não está entre as peles indicadas nesta ficha.")
    if atencao and "gestação" not in texto(atencao).lower():
        pular.append(f"Leve em conta: {texto(atencao)}")
    pular.append(UNIVERSAL)

    # 3. Em que etapa entra?
    cat = re.search(r'faz parte da categoria <a[^>]*>([^<]+)</a>', pagina)
    etapa = ETAPA.get(cat.group(1).strip().lower(), TRATAMENTO) if cat else ""
    # A ficha repete "Quando" em "Como usar", às vezes com mais detalhe: fica a versão mais completa.
    quando_txt = max([texto(q) for q in re.findall(r"<li><b>Quando:</b>\s*(.*?)</li>", pagina, re.S)] or [""], key=len)
    if quando_txt and len(quando_txt) < 24:  # "noite.", "manhã ou noite."
        quando_txt = "Período: " + quando_txt
    etapa = " ".join(x for x in [etapa, frase(quando_txt) if quando_txt else ""] if x)

    # 4. O que sabemos sobre o benefício?
    if orientacoes:
        ingrediente = ("o site ainda não avaliou os estudos deste ativo. Esta ficha reúne orientações de uso "
                       "comuns e não cita pesquisas, então não dá para afirmar aqui o tamanho do benefício.")
    else:
        evid = re.search(r'<aside class="ig-caixa ig-evid[^"]*"[^>]*>\s*<p class="ig-selo [a-z]+">([^<]+)</p>\s*<p>(.*?)</p>', pagina, re.S)
        if not evid:
            return None
        ingrediente = f"{evid.group(1).strip().lower()}. {evid.group(2).strip()}"
    formula = ("nenhum produto foi avaliado nesta ficha. Concentração, veículo e estabilidade mudam de uma marca "
               "para outra, então a evidência do ingrediente não garante o resultado de um produto, e um bom "
               "resultado de um produto não vale para todos os que levam o mesmo ingrediente.")
    return considerar, pular, etapa, ingrediente, formula


RITUAL = object()


def nome_do_ativo(pagina):
    """Nome do título e nome INCI da ficha: é o que o /ritual.js procura na prateleira de quem visita."""
    h1 = re.search(r"<h1>([^<]*)</h1>", pagina)
    inci = re.search(r"aparece como <i>([^<]*)</i>", pagina)
    partes = [html.unescape(h1.group(1)).split(":")[0].strip() if h1 else "", html.unescape(inci.group(1)).strip() if inci else ""]
    return ", ".join(x for x in partes if x)


def bloco(r, nome_ativo=""):
    considerar, pular, etapa, ingrediente, formula = r
    itens = []
    if considerar:
        itens.append(("Por que considerar?", f"<p>{considerar}</p>"))
    itens.append(("Quando faz sentido pular?", "<ul>" + "".join(f"<li>{x}</li>" for x in pular) + "</ul>"))
    if etapa:
        itens.append(("Em que etapa entra?", f"<p>{html.escape(etapa, quote=False)}</p>"))
    itens.append(RITUAL)
    itens.append(("O que sabemos sobre o benefício?",
                  f'<p><span class="ig-d-rotulo">Sobre o ingrediente:</span> {ingrediente}</p>'
                  f'<p><span class="ig-d-rotulo">Sobre a fórmula final:</span> {formula}</p>'))
    # "Você já tem este ativo em casa?": fica oculto no HTML e só aparece quando o /ritual.js
    # lê a Minha prateleira, salva no aparelho de quem visita. Não é texto sobre o ativo.
    corpo = "".join(
        f'<div class="ig-d" data-ritual="{html.escape(nome_ativo)}" hidden><dt>Você já tem este ativo em casa?</dt><dd></dd></div>'
        if item is RITUAL else f'<div class="ig-d"><dt>{item[0]}</dt><dd>{item[1]}</dd></div>' for item in itens)
    return (f'{INI}\n{CSS}\n<section class="ig-decisao" aria-label="Para decidir"><dl>{corpo}</dl></section>\n'
            f'<script src="/ritual.js" defer></script>\n{FIM}\n')


BUSCA = re.compile(r'<p><a href="https://www\.amazon\.com\.br/s\?[^"]*"[^>]*>Ver opções com [^<]*</a></p>\n?')
SEM_PRODUTO = re.compile(r'(<p>O catálogo do site ainda não tem um produto que cite [^<]*\.</p>)\n?(?:<p class="ig-nota">Preço na data indicada[^\n]*</p>\n?)?')
NOTA_SEM = '<p class="ig-nota">Sem oferta verificada, o site não indica onde comprar. A orientação de uso acima vale para qualquer produto que traga o ativo.</p>\n'


ITEM_BUSCA = re.compile(r'<li><a href="https://(?:www\.amazon\.com\.br/s\?|shopee\.com\.br/search|lista\.mercadolivre\.com\.br/|s\.shopee\.com\.br/an_redir\?origin_link=https%3A%2F%2Fshopee\.com\.br%2Fsearch)[^"]*"[^>]*>([^<]*?)\s*↗</a><span class="pr-preco">([^<]*)</span></li>')


def tirar_busca(pagina):
    """Sem oferta conferida, a ficha não aponta destino de compra."""
    pagina = BUSCA.sub("", pagina)
    # Produto do catálogo cujo link é só uma busca na loja: fica o nome, sem link e sem preço.
    pagina = ITEM_BUSCA.sub(lambda m: f'<li>{m.group(1)}<span class="pr-preco">{m.group(2).split(" · ")[0]} · sem oferta verificada</span></li>', pagina)
    if "Sem oferta verificada, o site não indica" not in pagina:
        pagina = SEM_PRODUTO.sub(lambda m: m.group(1) + "\n" + NOTA_SEM, pagina)
    return pagina


def main():
    feitas = puladas = 0
    for pasta in ("ativos", "ingredientes"):
        for arq in sorted((RAIZ / pasta).glob("*/index.html")):
            pagina = original = arq.read_text(encoding="utf-8")
            pagina = re.sub(re.escape(INI) + r".*?" + re.escape(FIM) + r"\n?", "", pagina, flags=re.S)
            r = respostas(pagina)
            ancora = re.search(r'<div class="ig-caixa ig-resumo">', pagina)
            if not r or not ancora:
                puladas += 1
                print("sem bloco:", arq.relative_to(RAIZ))
            else:
                pagina = pagina[:ancora.start()] + bloco(r, nome_do_ativo(pagina)) + pagina[ancora.start():]
                feitas += 1
            pagina = tirar_busca(pagina)
            if pagina != original:
                arq.write_text(pagina, encoding="utf-8")
    print(f"decisao_ficha: {feitas} fichas com as quatro respostas, {puladas} sem bloco")


if __name__ == "__main__":
    main()
