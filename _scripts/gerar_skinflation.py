# -*- coding: utf-8 -*-
"""Índice Skinflation: quanto variou o preço por ml (ou g) da cesta do catálogo, mês a mês.

Fontes (nada é digitado aqui):

  - _scripts/precos/dados/precos.ndjson   observações de preço, datadas
  - produtos/snapshots.json               volume registrado em cada data
  - _scripts/precos/dados/tamanhos.json   volume atual (quando o snapshot não cobre a data)
  - produtos.json                         nome e passo de cada produto
  - _scripts/precos/dados/ipca.json       opcional: IPCA mensal, para comparar (ver abaixo)

Saídas:

  skinflation/index.html     a página
  skinflation/indice.json    a série, a cesta e o método, para quem quiser citar ou refazer a conta

Método (o mesmo texto está na página):

  1. Leitura do mês de um produto = mediana do preço por ml (ou g) das observações daquele mês
     que não são promoção. Mês só com promoção fica sem leitura.
  2. O volume usado é o registrado na data da observação. Se o frasco encolhe e o preço fica,
     o preço por ml sobe: é isso que o índice mede e o preço de etiqueta esconde.
  3. Entre dois meses, só entram produtos com leitura nos dois (pares casados). A variação é a
     média geométrica das razões de preço por ml. O índice é encadeado, base 100 no primeiro mês.
  4. Mês com menos de MIN_PARES produtos casados não é publicado.
  5. O índice "etiqueta" repete a conta com o preço do frasco, sem dividir pelo volume.
     A diferença entre os dois é o efeito de mudança de tamanho.

IPCA (opcional). Para a página comparar com a inflação oficial, crie
_scripts/precos/dados/ipca.json com a variação mensal publicada pelo IBGE, em %:

    { "fonte": "IBGE, IPCA, variação mensal", "consultado_em": "2026-12-15",
      "mensal": { "2026-12": 0.52 } }

Sem o arquivo, ou sem todos os meses do período, a comparação não aparece.

Uso, na raiz do site:

    python3 _scripts/gerar_skinflation.py
    python3 -I _scripts/seo.py
    python3 -I _scripts/prontidao.py

É determinístico: a data de referência é a da observação mais nova, não a do dia em que roda.
"""
import json
import math
import sys
from pathlib import Path
from statistics import median

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pagina_base import RAIZ, esc, pagina  # noqa: E402

MIN_PARES = 10          # menos que isso, o mês não é publicado
MIN_PARES_PASSO = 5     # idem para o recorte por passo da rotina
ARQ_OBS = RAIZ / "_scripts" / "precos" / "dados" / "precos.ndjson"
ARQ_TAMANHOS = RAIZ / "_scripts" / "precos" / "dados" / "tamanhos.json"
ARQ_IPCA = RAIZ / "_scripts" / "precos" / "dados" / "ipca.json"
ARQ_SNAPSHOTS = RAIZ / "produtos" / "snapshots.json"
ARQ_MUDANCAS = RAIZ / "produtos" / "mudancas.json"
ARQ_PRODUTOS = RAIZ / "produtos.json"
DESTINO = RAIZ / "skinflation"
CAMINHO = "/skinflation/"

MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro",
         "outubro", "novembro", "dezembro"]
PASSOS = {"limpeza": "Limpeza", "tratamento": "Tratamento", "hidratacao": "Hidratante", "protetor": "Protetor solar"}


# ---------- conta (sem ler arquivo: é o que os testes exercitam) ----------

def volume_em(pid, data, snapshots, tamanhos):
    """(valor, unidade) do volume registrado para o produto na data da observação, ou (None, None)."""
    linha = [e for e in snapshots.get(pid, []) if e.get("volume_ml") or e.get("volume_g")]
    anteriores = [e for e in linha if e.get("em", "") <= data]
    e = (anteriores[-1] if anteriores else (linha[0] if linha else None)) or {}
    if not e:
        t = tamanhos.get(pid, {})
        e = {"volume_ml": t.get("size_ml"), "volume_g": t.get("size_g")}
    if e.get("volume_ml"):
        return e["volume_ml"], "ml"
    if e.get("volume_g"):
        return e["volume_g"], "g"
    return None, None


def leituras_mensais(observacoes, snapshots, tamanhos):
    """{mes: {produto: {"preco", "unitario", "volume", "unidade", "n", "em"}}}; só observações sem promoção."""
    por = {}
    for o in observacoes:
        if o.get("promo") or o.get("price_cents") is None:
            continue
        data = str(o["checked_at"])[:10]
        vol, unidade = volume_em(o["product_id"], data, snapshots, tamanhos)
        if not vol:
            continue
        por.setdefault(data[:7], {}).setdefault(o["product_id"], []).append((data, o["price_cents"] / 100, vol, unidade))
    saida = {}
    for mes, produtos in por.items():
        saida[mes] = {}
        for pid, lista in produtos.items():
            lista.sort()
            ultimo = lista[-1]
            saida[mes][pid] = {
                "preco": round(median(x[1] for x in lista), 2),
                "unitario": median(x[1] / x[2] for x in lista),
                "volume": ultimo[2], "unidade": ultimo[3], "n": len(lista), "em": ultimo[0],
            }
    return saida


def media_geometrica(razoes):
    return math.exp(sum(math.log(r) for r in razoes) / len(razoes))


def serie(leituras, campo="unitario", filtro=None, min_pares=MIN_PARES):
    """Índice encadeado de pares casados. Devolve uma linha por mês:
    {"mes", "produtos", "pares", "indice" (None se não publicado), "variacao" (% sobre o mês publicado anterior)}."""
    linhas, base = [], None  # base = (mes, indice) do último mês publicado
    for mes in sorted(leituras):
        atual = {p: v for p, v in leituras[mes].items() if filtro is None or filtro(p)}
        linha = {"mes": mes, "produtos": len(atual), "pares": None, "indice": None, "variacao": None}
        if base is None:
            if len(atual) >= min_pares:
                linha["indice"] = 100.0
                base = (mes, 100.0)
        else:
            antes = {p: v for p, v in leituras[base[0]].items() if filtro is None or filtro(p)}
            # Mesmo produto, mesma unidade (ml com ml, g com g): trocar de unidade não é variação de preço.
            comuns = [p for p in atual if p in antes and antes[p][campo] > 0 and antes[p]["unidade"] == atual[p]["unidade"]]
            linha["pares"] = len(comuns)
            if len(comuns) >= min_pares:
                elo = media_geometrica([atual[p][campo] / antes[p][campo] for p in comuns])
                linha["indice"] = base[1] * elo
                linha["variacao"] = (elo - 1) * 100
                base = (mes, linha["indice"])
        linhas.append(linha)
    return linhas


def ipca_acumulado(mensal, meses_publicados):
    """IPCA acumulado (%) do mês seguinte à base até cada mês publicado; None se faltar algum mês."""
    saida, fator, completo = {}, 1.0, True
    if not meses_publicados:
        return saida
    saida[meses_publicados[0]] = 0.0
    ano, mes = map(int, meses_publicados[0].split("-"))
    for alvo in meses_publicados[1:]:
        while f"{ano:04d}-{mes:02d}" < alvo:
            mes += 1
            if mes == 13:
                ano, mes = ano + 1, 1
            v = mensal.get(f"{ano:04d}-{mes:02d}")
            if v is None:
                completo = False
            else:
                fator *= 1 + v / 100
        saida[alvo] = (fator - 1) * 100 if completo else None
    return saida


# ---------- texto ----------

def num(v, casas=1):
    return f"{v:.{casas}f}".replace(".", ",")


def reais(v, casas=2):
    return "R$ " + num(v, casas)


def pct(v):
    return ("+" if v > 0 else "") + num(v, 1) + "%"


def nome_mes(mes):
    return f"{MESES[int(mes[5:7]) - 1]} de {mes[:4]}"


def data_br(iso):
    return f"{iso[8:10]}/{iso[5:7]}/{iso[:4]}"


def carregar(caminho, padrao):
    return json.loads(caminho.read_text(encoding="utf-8")) if caminho.exists() else padrao


CSS = """
.sk-numero{font-family:var(--fonte-display);font-size:clamp(2.6rem,9vw,4rem);font-weight:300;line-height:1}
.sk-destaque{display:flex;flex-wrap:wrap;gap:8px 28px;align-items:baseline}
.sk-destaque p{margin:0}
.sk-tabela{width:100%;border-collapse:collapse;font-size:.94rem}
.sk-tabela th,.sk-tabela td{padding:9px 10px;border-bottom:1px solid var(--linha);text-align:left;vertical-align:top}
.sk-tabela td.n,.sk-tabela th.n{text-align:right;white-space:nowrap}
.sk-tabela caption{text-align:left;font-size:.88rem;color:var(--suave);padding-bottom:8px}
.sk-rolagem{overflow-x:auto}
.sk-lista{margin:8px 0 0;padding-left:1.1em}.sk-lista li{margin:.45em 0}
"""


def montar():
    observacoes = [json.loads(l) for l in ARQ_OBS.read_text(encoding="utf-8").splitlines() if l.strip()]
    snapshots = carregar(ARQ_SNAPSHOTS, {}).get("produtos", {})
    tamanhos = carregar(ARQ_TAMANHOS, {}).get("produtos", {})
    catalogo = {p["id"]: p for p in carregar(ARQ_PRODUTOS, {}).get("produtos", [])}
    mudancas = [m for m in carregar(ARQ_MUDANCAS, {}).get("itens", []) if m.get("tipo") == "volume"]
    ipca = carregar(ARQ_IPCA, {})

    leituras = leituras_mensais(observacoes, snapshots, tamanhos)
    if not leituras:
        raise SystemExit("sem observações de preço com volume: não há índice a gerar")
    geral = serie(leituras)
    etiqueta = {l["mes"]: l for l in serie(leituras, campo="preco")}
    publicados = [l["mes"] for l in geral if l["indice"] is not None]
    if not publicados:
        raise SystemExit(f"nenhum mês com {MIN_PARES} produtos ou mais: não há índice a gerar")
    acumulado = ipca_acumulado(ipca.get("mensal", {}), publicados) if ipca.get("mensal") else {}
    por_passo = {}
    for passo in PASSOS:
        s = serie(leituras, filtro=lambda p, passo=passo: catalogo.get(p, {}).get("passo") == passo, min_pares=MIN_PARES_PASSO)
        if any(l["indice"] is not None for l in s):
            por_passo[passo] = s

    as_of = max(str(o["checked_at"])[:10] for o in observacoes)
    base, ultimo_mes = publicados[0], publicados[-1]
    ultimo = next(l for l in geral if l["mes"] == ultimo_mes)
    so_base = len(publicados) == 1
    cesta = leituras[ultimo_mes]
    sem_volume = sorted({o["product_id"] for o in observacoes} - {p for m in leituras.values() for p in m})

    # ----- JSON aberto -----
    dados = {
        "nome": "Índice Skinflation", "editor": "Produto Skincare", "url": "https://produtoskincare.com.br/skinflation/",
        "licenca": "CC BY 4.0", "dados_ate": as_of, "base": {"mes": base, "valor": 100},
        "metodo": {
            "leitura": "mediana do preço por ml (ou g) das observações do mês, sem promoções",
            "agregacao": "média geométrica das razões entre meses, só com produtos presentes nos dois (pares casados), encadeada",
            "minimo_de_pares": MIN_PARES, "minimo_de_pares_por_passo": MIN_PARES_PASSO,
            "etiqueta": "a mesma conta com o preço do frasco, sem dividir pelo volume",
        },
        "limites": "Cesta pequena e escolhida pela curadoria do site, um anúncio por produto. Não é estatística do mercado brasileiro de cosméticos.",
        "serie": [{
            "mes": l["mes"], "produtos": l["produtos"], "pares": l["pares"],
            "indice": None if l["indice"] is None else round(l["indice"], 2),
            "variacao_pct": None if l["variacao"] is None else round(l["variacao"], 2),
            "indice_etiqueta": None if etiqueta[l["mes"]]["indice"] is None else round(etiqueta[l["mes"]]["indice"], 2),
            "ipca_acumulado_pct": None if acumulado.get(l["mes"]) is None else round(acumulado[l["mes"]], 2),
        } for l in geral],
        "por_passo": {passo: [{"mes": l["mes"], "produtos": l["produtos"], "pares": l["pares"],
                               "indice": None if l["indice"] is None else round(l["indice"], 2)} for l in s]
                      for passo, s in por_passo.items()},
        "cesta": [{
            "id": pid, "nome": catalogo.get(pid, {}).get("nome", pid), "passo": catalogo.get(pid, {}).get("passo"),
            "mes": ultimo_mes, "preco": v["preco"], "volume": v["volume"], "unidade": v["unidade"],
            "preco_por_unidade": round(v["unitario"], 4), "observacoes_no_mes": v["n"], "conferido_em": v["em"],
        } for pid, v in sorted(cesta.items())],
        "mudancas_de_tamanho": mudancas,
    }
    if ipca.get("mensal"):
        dados["ipca"] = {"fonte": ipca.get("fonte"), "consultado_em": ipca.get("consultado_em")}

    # ----- página -----
    tem_ipca = any(v is not None for m, v in acumulado.items() if m != base)
    if so_base:
        destaque = f"""<div class="sk-destaque"><p class="sk-numero">100,0</p>
<p><strong>Base: {nome_mes(base)}.</strong> O índice começa aqui. A primeira variação aparece quando houver preços conferidos em um segundo mês.</p></div>"""
    else:
        var_total = ultimo["indice"] - 100
        linha_ipca = ""
        if acumulado.get(ultimo_mes) is not None:
            linha_ipca = f" No mesmo período, o IPCA acumulou {pct(acumulado[ultimo_mes])}."
        destaque = f"""<div class="sk-destaque"><p class="sk-numero">{num(ultimo['indice'])}</p>
<p><strong>{nome_mes(ultimo_mes).capitalize()}.</strong> O preço por ml da cesta variou {pct(var_total)} desde {nome_mes(base)} (base 100), em {ultimo['pares']} produtos comparáveis.{linha_ipca}</p></div>"""

    cab_ipca = '<th scope="col" class="n">IPCA acumulado</th>' if tem_ipca else ""
    linhas_serie = []
    for l in geral:
        e = etiqueta[l["mes"]]
        if l["indice"] is None:
            motivo = f"não publicado: {l['pares'] if l['pares'] is not None else l['produtos']} produtos comparáveis (mínimo {MIN_PARES})"
            linhas_serie.append(f'<tr><th scope="row">{nome_mes(l["mes"])}</th><td colspan="{5 if tem_ipca else 4}">{motivo}</td></tr>')
            continue
        col_ipca = ""
        if tem_ipca:
            a = acumulado.get(l["mes"])
            col_ipca = f'<td class="n">{"—" if a is None else pct(a)}</td>'
        linhas_serie.append(
            f'<tr><th scope="row">{nome_mes(l["mes"])}</th><td class="n">{num(l["indice"])}</td>'
            f'<td class="n">{"base" if l["variacao"] is None else pct(l["variacao"])}</td>'
            f'<td class="n">{"—" if e["indice"] is None else num(e["indice"])}</td>'
            f'<td class="n">{l["produtos"] if l["pares"] is None else l["pares"]}</td>{col_ipca}</tr>')

    linhas_cesta = []
    for pid, v in sorted(cesta.items(), key=lambda kv: (catalogo.get(kv[0], {}).get("passo", ""), catalogo.get(kv[0], {}).get("nome", kv[0]))):
        p = catalogo.get(pid, {})
        linhas_cesta.append(
            f'<tr><td><a href="/produtos/{esc(pid)}/">{esc(p.get("nome", pid))}</a></td><td>{esc(PASSOS.get(p.get("passo"), p.get("passo") or "—"))}</td>'
            f'<td class="n">{reais(v["preco"])}</td><td class="n">{num(v["volume"], 0)} {v["unidade"]}</td>'
            f'<td class="n">{reais(v["unitario"])} /{v["unidade"]}</td><td class="n">{data_br(v["em"])}</td></tr>')

    if por_passo and not so_base:
        blocos = []
        for passo, s in por_passo.items():
            fim = [l for l in s if l["indice"] is not None][-1]
            blocos.append(f'<tr><th scope="row">{PASSOS[passo]}</th><td class="n">{num(fim["indice"])}</td><td class="n">{nome_mes(fim["mes"])}</td><td class="n">{fim["pares"] if fim["pares"] is not None else fim["produtos"]}</td></tr>')
        sec_passo = f"""<section aria-labelledby="sk-passo">
<h2 id="sk-passo">Por passo da rotina</h2>
<div class="sk-rolagem"><table class="sk-tabela"><caption>Mesmo método, só com os produtos de cada passo. Passo com menos de {MIN_PARES_PASSO} produtos comparáveis não aparece.</caption>
<thead><tr><th scope="col">Passo</th><th scope="col" class="n">Índice</th><th scope="col" class="n">Mês</th><th scope="col" class="n">Produtos</th></tr></thead>
<tbody>{''.join(blocos)}</tbody></table></div>
</section>"""
    else:
        sec_passo = ""

    if mudancas:
        itens = "".join(f'<li><strong>{esc(m["produto"])}</strong> ({data_br(m["em"])}): {esc(m["leitura"])}. <a href="/produtos/{esc(m["produto_id"])}/">Ver produto</a></li>' for m in mudancas)
        sec_tamanho = f'<ul class="sk-lista">{itens}</ul>'
    else:
        sec_tamanho = '<p>Nenhuma mudança de tamanho registrada até agora nos produtos da cesta.</p>'

    nota_ipca = ("" if tem_ipca else
                 '<li><strong>Comparação com a inflação oficial (IPCA):</strong> ainda não publicada. Ela entra quando houver um segundo mês de índice e a variação do IPCA do período, com a fonte.</li>')
    if tem_ipca:
        nota_ipca = f'<li><strong>IPCA:</strong> variação mensal acumulada desde o mês seguinte à base. Fonte: {esc(ipca.get("fonte") or "IBGE")}{", consultado em " + data_br(ipca["consultado_em"]) if ipca.get("consultado_em") else ""}.</li>'
    excluidos = (f'<li><strong>Fora da conta:</strong> {len(sem_volume)} produto(s) sem volume conferido ou só com preço promocional.</li>' if sem_volume else "")

    corpo = f"""<article>
<div class="ig-cab">
<h1>Índice Skinflation</h1>
<p class="ig-lede">Quanto variou o preço por ml dos produtos de skincare do nosso catálogo, mês a mês. O índice acompanha o preço por ml, e não o preço da etiqueta, porque um frasco que encolhe com o mesmo preço ficou mais caro.</p>
<p class="ig-meta">Dados até {data_br(as_of)} · {len(cesta)} produtos na cesta · base 100 em {nome_mes(base)}</p>
</div>

<section class="ig-caixa" aria-labelledby="sk-agora">
<h2 id="sk-agora">Leitura atual</h2>
{destaque}
</section>

<section aria-labelledby="sk-serie">
<h2 id="sk-serie">A série</h2>
<div class="sk-rolagem"><table class="sk-tabela"><caption>Índice de preço por ml (ou g), base 100 em {nome_mes(base)}. "Etiqueta" é a mesma conta com o preço do frasco, sem dividir pelo volume: quando os dois se afastam, é efeito de mudança de tamanho.</caption>
<thead><tr><th scope="col">Mês</th><th scope="col" class="n">Índice (por ml)</th><th scope="col" class="n">No mês</th><th scope="col" class="n">Etiqueta</th><th scope="col" class="n">Produtos</th>{cab_ipca}</tr></thead>
<tbody>{''.join(linhas_serie)}</tbody></table></div>
</section>
{sec_passo}
<section aria-labelledby="sk-tamanho">
<h2 id="sk-tamanho">Frascos que mudaram de tamanho</h2>
{sec_tamanho}
<p class="ig-nota">Vem do <a href="/ferramentas/extrato-cosmetico/">Extrato do cosmético</a>, que guarda o volume de cada produto com data e fonte.</p>
</section>

<section aria-labelledby="sk-cesta">
<h2 id="sk-cesta">A cesta</h2>
<div class="sk-rolagem"><table class="sk-tabela"><caption>Leitura de {nome_mes(ultimo_mes)}: último preço registrado, volume conferido e preço por ml (ou g). O preço muda: vale o da loja na hora da compra.</caption>
<thead><tr><th scope="col">Produto</th><th scope="col">Passo</th><th scope="col" class="n">Preço</th><th scope="col" class="n">Volume</th><th scope="col" class="n">Por ml ou g</th><th scope="col" class="n">Conferido em</th></tr></thead>
<tbody>{''.join(linhas_cesta)}</tbody></table></div>
</section>

<section class="ig-caixa" aria-labelledby="sk-metodo">
<h2 id="sk-metodo">Como a conta é feita</h2>
<ul class="sk-lista">
<li><strong>Leitura do mês:</strong> para cada produto, a mediana do preço por ml (ou g) das observações daquele mês. Preço marcado como promoção não entra.</li>
<li><strong>Volume:</strong> o registrado na data da observação, sempre com fonte. Se o frasco diminui e o preço fica, o preço por ml sobe e o índice sobe junto.</li>
<li><strong>Só o que dá para comparar:</strong> entre dois meses, entram apenas os produtos com leitura nos dois. Produto novo no catálogo não mexe no índice no mês em que entra.</li>
<li><strong>Agregação:</strong> média geométrica das variações de cada produto, encadeada mês a mês. Todos os produtos pesam igual.</li>
<li><strong>Mínimo:</strong> mês com menos de {MIN_PARES} produtos comparáveis não é publicado.</li>
{nota_ipca}
{excluidos}
</ul>
</section>

<section class="ig-caixa" aria-labelledby="sk-limites">
<h2 id="sk-limites">O que este índice não é</h2>
<ul class="sk-lista">
<li><strong>Não é estatística do mercado.</strong> A cesta tem {len(cesta)} produtos escolhidos pela curadoria do site, não uma amostra do que o Brasil compra.</li>
<li><strong>Não é o menor preço.</strong> Cada produto é acompanhado em um anúncio de uma loja. O mesmo produto pode custar outro valor em outro lugar.</li>
<li><strong>Não pesa por venda.</strong> Um sérum caro e um sabonete barato contam igual.</li>
<li><strong>Não explica a causa.</strong> O índice mostra que o preço por ml mudou. Não diz por quê.</li>
</ul>
</section>

<section aria-labelledby="sk-dados">
<h2 id="sk-dados">Dados e citação</h2>
<p>A série, a cesta e o método estão em <a href="/skinflation/indice.json">/skinflation/indice.json</a>, sob licença <a href="https://creativecommons.org/licenses/by/4.0/deed.pt-br" rel="noopener">CC BY 4.0</a>. Os preços observados, um a um, estão nos <a href="/dados-abertos/">dados abertos</a>.</p>
<p>Para citar: Índice Skinflation, Produto Skincare, dados até {data_br(as_of)}, produtoskincare.com.br/skinflation/.</p>
</section>

<section aria-labelledby="sk-leia">
<h2 id="sk-leia">Leia também</h2>
<ul class="ig-rel">
<li><a href="/ferramentas/precos/">Histórico de preços</a></li>
<li><a href="/ferramentas/extrato-cosmetico/">Extrato do cosmético</a></li>
<li><a href="/ferramentas/matematica/">A matemática do frasco</a></li>
<li><a href="/dados-abertos/">Dados abertos</a></li>
</ul>
</section>
</article>"""

    descricao = "Quanto variou o preço por ml dos produtos de skincare do catálogo, mês a mês. Mede o frasco que encolhe com o mesmo preço. Método e dados abertos."
    html = pagina("Índice Skinflation: o preço por ml do skincare, mês a mês", descricao, CAMINHO,
                  [("/", "Início"), (None, "Índice Skinflation")], corpo, css_extra=CSS, larga=True,
                  aviso="Conteúdo informativo. Preços conferidos na data indicada; podem ter mudado na loja.")
    return html, dados


def main():
    html, dados = montar()
    DESTINO.mkdir(parents=True, exist_ok=True)
    (DESTINO / "index.html").write_text(html, encoding="utf-8")
    (DESTINO / "indice.json").write_text(json.dumps(dados, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    pub = [l for l in dados["serie"] if l["indice"] is not None]
    print(f"gerada {CAMINHO} · dados até {dados['dados_ate']} · {len(pub)} mês(es) publicado(s) · último índice: {pub[-1]['indice']}")


if __name__ == "__main__":
    main()
