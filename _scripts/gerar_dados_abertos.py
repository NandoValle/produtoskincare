# -*- coding: utf-8 -*-
"""Dataset aberto do catálogo: arquivos de /dados/ e a página /dados-abertos/.

Fontes (nada é digitado aqui; tudo vem dos arquivos que o site já usa):

  - produtos.json                          catálogo
  - _scripts/precos/dados/precos.ndjson    todas as observações de preço, datadas
  - _scripts/precos/dados/tamanhos.json    volume conferido e a fonte dele
  - precos.json                            tipo do link (oferta conferida ou busca)
  - produtos/snapshots.json                fórmula (INCI) registrada, com fonte e data
  - produtos/mudancas.json                 mudanças detectadas entre registros
  - _scripts/dados_abertos.json            versão e changelog do dataset

Saídas:

  dados/produtos.csv|json   dados/precos.csv|json   dados/inci.csv|json
  dados/mudancas.csv|json   dados/index.json (manifesto)   dados-abertos/index.html

Regras que o script impõe (e falha se forem quebradas):

  1. Nenhum preço sem data.
  2. Nenhum link com identificador de afiliado.
  3. Só entram campos da lista CAMPOS abaixo: nada de dado pessoal, nada de nota ou
     número de avaliações de loja (não são nossos para licenciar).

Uso, na raiz do site:

    python3 -I _scripts/gerar_dados_abertos.py
    python3 -I _scripts/seo.py
    python3 -I _scripts/prontidao.py

É idempotente: sem mudança nas fontes, os arquivos saem iguais.
"""
import csv
import io
import json
import re
import sys
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pagina_base import RAIZ, SITE, esc, pagina  # noqa: E402

DADOS = RAIZ / "dados"
CONFIG = RAIZ / "_scripts" / "dados_abertos.json"
LICENCA = "CC BY 4.0"
LICENCA_URL = "https://creativecommons.org/licenses/by/4.0/deed.pt-br"
SEPARADOR = "|"  # separa itens de lista dentro de uma célula do CSV

# Parâmetros de rastreio e afiliado que saem dos links.
PARAMS_FORA = re.compile(r"^(tag|ref|ref_|linkCode|linkId|matt_.*|affiliate.*|sub_id.*|utm_.*|smtt|uls_trackid)$", re.I)
# Se um destes aparecer em qualquer arquivo publicado, o script falha.
MARCAS_AFILIADO = ("tag=", "matt_tool", "matt_word", "affiliate_id", "an_redir", "sub_id")

# Dicionário de campos: é a fonte única da página, do manifesto e da ordem das colunas.
CAMPOS = {
    "produtos": [
        ("id", "texto", "Identificador do produto no site. Estável: não muda entre versões."),
        ("nome", "texto", "Nome comercial do produto."),
        ("marca", "texto", "Marca."),
        ("origem", "texto", "País de origem da marca."),
        ("passo", "texto", "Passo da rotina em que o produto entra (limpeza, hidratante, protetor, tratamento…)."),
        ("periodo", "lista", "Quando usar: manha, noite ou os dois."),
        ("grupo", "texto", "Grupo de produtos equivalentes usado pelo site para comparar opções."),
        ("tipos_pele", "lista", "Tipos de pele para os quais o site indica o produto."),
        ("condicoes", "lista", "Queixas para as quais o site indica o produto (acne, manchas…)."),
        ("evitar", "lista", "Situações em que o site não indica o produto."),
        ("textura", "texto", "Textura declarada (gel, creme, loção, sérum…)."),
        ("ativos", "lista", "Ativos de destaque do produto, como o site os registra. Não é a lista INCI."),
        ("tamanho", "texto", "Tamanho do frasco como aparece no site (ex.: 454 g)."),
        ("volume_ml", "número", "Volume conferido, em ml. Vazio quando não foi conferido."),
        ("volume_g", "número", "Peso conferido, em g. Vazio quando não foi conferido."),
        ("volume_fonte", "texto", "De onde veio o volume (endereço da ficha da loja ou embalagem)."),
        ("preco", "número", "Último preço registrado, em reais."),
        ("preco_em", "data", "Data em que esse preço foi conferido (AAAA-MM-DD)."),
        ("loja", "texto", "Loja em que o preço foi conferido."),
        ("link_tipo", "texto", "oferta = link direto para o anúncio conferido; busca = link de busca na loja, sem oferta verificada."),
        ("url", "texto", "Endereço na loja, sem identificador de afiliado."),
        ("pagina", "texto", "Página do produto no site."),
    ],
    "precos": [
        ("produto_id", "texto", "Identificador do produto (campo id de produtos)."),
        ("conferido_em", "data", "Data da observação (AAAA-MM-DD). Não existe linha sem data."),
        ("preco", "número", "Preço observado."),
        ("moeda", "texto", "Moeda (BRL)."),
        ("loja", "texto", "Loja da observação."),
        ("promocao", "booleano", "true quando o preço estava marcado como promoção na loja."),
        ("origem", "texto", "Como a observação entrou: team = conferência manual da equipe; feed = feed oficial da loja."),
        ("url", "texto", "Endereço conferido, sem identificador de afiliado."),
    ],
    "inci": [
        ("produto_id", "texto", "Identificador do produto (campo id de produtos)."),
        ("registrado_em", "data", "Data em que a lista foi registrada no site."),
        ("lido_em", "data", "Data da leitura da embalagem ou da fonte, quando informada."),
        ("fonte", "texto", "De onde veio a lista: embalagem, site da marca ou outro, sempre anotado."),
        ("inci", "texto", "Lista de ingredientes como está na fonte, na ordem da fonte."),
    ],
    "mudancas": [
        ("produto_id", "texto", "Identificador do produto (campo id de produtos)."),
        ("em", "data", "Data em que a mudança foi detectada."),
        ("tipo", "texto", "preco, volume ou formula."),
        ("de", "texto", "Valor no registro anterior."),
        ("para", "texto", "Valor no registro novo."),
        ("entraram", "lista", "Só em formula: ingredientes que não estavam na lista anterior."),
        ("sairam", "lista", "Só em formula: ingredientes que estavam na lista anterior e não estão mais."),
        ("leitura", "texto", "A mudança em uma frase."),
    ],
}
TITULOS = {
    "produtos": ("Produtos", "Uma linha por produto do catálogo."),
    "precos": ("Preços datados", "Uma linha por observação de preço. É o histórico: nunca é sobrescrito."),
    "inci": ("Fórmulas (INCI)", "Uma linha por versão registrada da lista de ingredientes de um produto."),
    "mudancas": ("Mudanças detectadas", "Uma linha por mudança de preço, volume ou fórmula entre dois registros."),
}


def ler(caminho, padrao=None):
    caminho = RAIZ / caminho
    if not caminho.exists():
        return padrao
    return json.loads(caminho.read_text(encoding="utf-8"))


def sem_afiliado(url):
    """Devolve o endereço da loja sem redirecionador nem parâmetro de afiliado."""
    if not url:
        return ""
    partes = urlsplit(url)
    consulta = parse_qsl(partes.query, keep_blank_values=True)
    if partes.path.rstrip("/").endswith("an_redir"):  # redirecionador de afiliado da Shopee
        destino = dict(consulta).get("origin_link")
        return sem_afiliado(destino) if destino else ""
    limpa = [(k, v) for k, v in consulta if not PARAMS_FORA.match(k)]
    return urlunsplit((partes.scheme, partes.netloc, partes.path, urlencode(limpa), ""))


def montar():
    catalogo = ler("produtos.json")
    tamanhos = (ler("_scripts/precos/dados/tamanhos.json", {}) or {}).get("produtos", {})
    resumo_precos = (ler("precos.json", {}) or {}).get("produtos", {})
    snapshots = (ler("produtos/snapshots.json", {}) or {}).get("produtos", {})
    mudancas_src = (ler("produtos/mudancas.json", {}) or {}).get("itens", [])

    produtos = []
    for p in catalogo["produtos"]:
        tam = tamanhos.get(p["id"], {})
        atual = (resumo_precos.get(p["id"]) or {}).get("current") or {}
        tem_preco = p.get("preco") is not None and p.get("preco_em")
        produtos.append({
            "id": p["id"], "nome": p.get("nome", ""), "marca": p.get("marca", ""), "origem": p.get("origem", ""),
            "passo": p.get("passo", ""), "periodo": p.get("periodo", []), "grupo": p.get("grupo", ""),
            "tipos_pele": p.get("tipos", []), "condicoes": p.get("conc", []), "evitar": p.get("evitar", []),
            "textura": p.get("textura", ""), "ativos": p.get("ativos", []), "tamanho": p.get("tamanho", ""),
            "volume_ml": tam.get("size_ml"), "volume_g": tam.get("size_g"),
            "volume_fonte": sem_afiliado(tam.get("fonte")) if str(tam.get("fonte", "")).startswith("http") else (tam.get("fonte") or ""),
            # Regra 1: preço só sai acompanhado da data.
            "preco": p.get("preco") if tem_preco else None,
            "preco_em": p.get("preco_em") if tem_preco else None,
            "loja": p.get("plataforma", ""),
            "link_tipo": atual.get("link_tipo", ""),
            "url": sem_afiliado(p.get("link")),
            "pagina": f"{SITE}/produtos/{p['id']}/",
        })

    precos = []
    ndjson = RAIZ / "_scripts" / "precos" / "dados" / "precos.ndjson"
    for linha in ndjson.read_text(encoding="utf-8").splitlines():
        if not linha.strip():
            continue
        o = json.loads(linha)
        if not o.get("checked_at") or o.get("price_cents") is None:
            continue  # Regra 1
        precos.append({
            "produto_id": o["product_id"], "conferido_em": o["checked_at"][:10],
            "preco": round(o["price_cents"] / 100, 2), "moeda": o.get("currency", "BRL"),
            "loja": o.get("retailer", ""), "promocao": bool(o.get("promo")),
            "origem": o.get("source", ""), "url": sem_afiliado(o.get("url")),
        })
    precos.sort(key=lambda x: (x["produto_id"], x["conferido_em"], x["loja"]))

    inci = []
    for pid in sorted(snapshots):
        visto = None
        for e in snapshots[pid]:
            if e.get("inci") and e["inci"] != visto:
                visto = e["inci"]
                inci.append({"produto_id": pid, "registrado_em": e.get("em"), "lido_em": e.get("inci_em"),
                             "fonte": e.get("inci_fonte") or "", "inci": e["inci"]})

    def texto(v):
        if isinstance(v, list):
            return ", ".join(str(x) for x in v)
        return "" if v is None else str(v)

    mudancas = [{
        "produto_id": m["produto_id"], "em": m["em"], "tipo": m["tipo"], "de": texto(m.get("de")),
        "para": texto(m.get("para")), "entraram": m.get("entraram", []), "sairam": m.get("sairam", []),
        "leitura": m.get("leitura", ""),
    } for m in mudancas_src]

    return {"produtos": produtos, "precos": precos, "inci": inci, "mudancas": mudancas}


def celula(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, list):
        return SEPARADOR.join(str(x) for x in v)
    return str(v)


def em_csv(nome, linhas):
    colunas = [c for c, _, _ in CAMPOS[nome]]
    saida = io.StringIO()
    w = csv.writer(saida, lineterminator="\n")
    w.writerow(colunas)
    for l in linhas:
        w.writerow([celula(l.get(c)) for c in colunas])
    return saida.getvalue()


def conferir(tabelas, textos):
    for nome, linhas in tabelas.items():
        colunas = {c for c, _, _ in CAMPOS[nome]}
        for l in linhas:
            assert set(l) == colunas, f"{nome}: campos fora do dicionário: {set(l) ^ colunas}"
    for p in tabelas["produtos"]:
        assert (p["preco"] is None) == (p["preco_em"] is None), f"preço sem data: {p['id']}"
    for o in tabelas["precos"]:
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", o["conferido_em"]), f"preço sem data: {o}"
    for caminho, t in textos.items():
        for marca in MARCAS_AFILIADO:
            assert marca not in t, f"{caminho}: sobrou identificador de afiliado ({marca})"


def data_br(iso):
    a, m, d = iso.split("-")
    return f"{d}/{m}/{a}"


def pagina_html(tabelas, cfg, dados_ate):
    versao = cfg["versao"]
    n = {k: len(v) for k, v in tabelas.items()}
    com_inci = len({l["produto_id"] for l in tabelas["inci"]})
    arquivos = "\n".join(
        f'<tr><th scope="row">{esc(TITULOS[k][0])}</th><td>{esc(TITULOS[k][1])}</td><td>{n[k]}</td>'
        f'<td><a href="/dados/{k}.csv" download>CSV</a> · <a href="/dados/{k}.json">JSON</a></td></tr>'
        for k in CAMPOS)
    dicionario = "\n".join(
        f'<h3 id="campos-{k}">{esc(TITULOS[k][0])} <span class="ig-nota">({k}.csv, {k}.json)</span></h3>\n'
        f'<div class="ft-rolagem"><table class="da-tabela"><thead><tr><th scope="col">Campo</th><th scope="col">Tipo</th>'
        f'<th scope="col">O que é</th></tr></thead><tbody>\n'
        + "\n".join(f'<tr><td><code>{esc(c)}</code></td><td>{esc(t)}</td><td>{esc(d)}</td></tr>' for c, t, d in CAMPOS[k])
        + "\n</tbody></table></div>" for k in CAMPOS)
    changelog = "\n".join(
        f'<li><strong>v{esc(c["versao"])}</strong> · {data_br(c["em"])}<ul>'
        + "".join(f"<li>{esc(m)}</li>" for m in c["mudancas"]) + "</ul></li>" for c in cfg["changelog"])
    if com_inci:
        nota_inci = (f"{com_inci} de {n['produtos']} produtos têm lista de ingredientes registrada. "
                     "Os outros ficam de fora do arquivo de fórmulas até alguém registrar a lista com a fonte.")
    else:
        nota_inci = ("Nenhum produto tem lista de ingredientes registrada ainda. O arquivo de fórmulas já existe, "
                     "com as colunas definitivas, e está vazio de propósito: lista INCI só entra com a fonte anotada.")
    citacao = (f"Produto Skincare. Dados abertos do catálogo de skincare no Brasil, versão {versao}. "
               f"{SITE}/dados-abertos/. Licença CC BY 4.0.")
    ld = {
        "@context": "https://schema.org", "@type": "Dataset",
        "name": "Catálogo de skincare no Brasil: produtos, preços datados e fórmulas",
        "description": ("Produtos de skincare vendidos no Brasil com ativos, tipo de pele indicado, volume conferido, "
                        "preços com a data da conferência e histórico de fórmula (INCI). Sem dado pessoal e sem link de afiliado."),
        "url": f"{SITE}/dados-abertos/", "version": versao, "license": "https://creativecommons.org/licenses/by/4.0/",
        "isAccessibleForFree": True, "inLanguage": "pt-BR", "dateModified": dados_ate,
        "creator": {"@type": "Organization", "name": "Produto Skincare", "url": SITE + "/"},
        "distribution": [
            {"@type": "DataDownload", "encodingFormat": fmt, "contentUrl": f"{SITE}/dados/{k}.{ext}"}
            for k in CAMPOS for fmt, ext in (("text/csv", "csv"), ("application/json", "json"))],
    }
    corpo = f"""<article>
<div class="ig-cab">
<h1>Dados abertos</h1>
<p class="ig-lede">O catálogo do site em arquivos que qualquer pessoa pode baixar, conferir e reutilizar: produtos, preços com a data em que foram conferidos, fórmulas e as mudanças detectadas entre um registro e outro. De graça, sem cadastro e sem chave de acesso.</p>
<p class="ig-meta">Versão {esc(versao)} · dados até {data_br(dados_ate)} · licença <a href="{LICENCA_URL}" rel="noopener license">{LICENCA}</a></p>
</div>

<section aria-labelledby="da-arquivos">
<h2 id="da-arquivos">Os arquivos</h2>
<div class="ft-rolagem">
<table class="da-tabela">
<thead><tr><th scope="col">Arquivo</th><th scope="col">O que tem</th><th scope="col">Linhas</th><th scope="col">Baixar</th></tr></thead>
<tbody>
{arquivos}
</tbody>
</table>
</div>
<p class="ig-nota">CSV em UTF-8, separado por vírgula, com a primeira linha de cabeçalho. Campos com mais de um valor (ativos, tipos de pele) usam <code>|</code> entre os itens. No JSON, esses campos são listas. O <a href="/dados/index.json">manifesto</a> traz a versão, a contagem de linhas e o dicionário de campos em formato de máquina.</p>
</section>

<section class="ig-caixa" aria-labelledby="da-limites">
<h2 id="da-limites">O tamanho real do dataset hoje</h2>
<ul class="ft-regras">
<li><strong>{n['produtos']} produtos</strong>, os do catálogo do site. Não é um retrato do mercado brasileiro.</li>
<li><strong>{n['precos']} observações de preço.</strong> Os preços são conferidos à mão pela equipe, na loja e na data que aparecem em cada linha. O histórico começou em novembro de 2026 e cresce a cada conferência.</li>
<li><strong>Fórmulas:</strong> {esc(nota_inci)}</li>
<li><strong>{n['mudancas']} mudanças detectadas.</strong> {"Só há mudança quando existem dois registros diferentes do mesmo produto, e o registro é recente." if not n['mudancas'] else "Cada linha aponta o valor anterior e o novo."}</li>
</ul>
<p>Tem o frasco em casa? <a href="/ferramentas/extrato-cosmetico/#ex-contribuir-titulo">Registre a lista de ingredientes</a> e ela entra no arquivo de fórmulas, com a fonte.</p>
</section>

<section aria-labelledby="da-regras">
<h2 id="da-regras">Regras do dataset</h2>
<ul class="ft-regras">
<li><strong>Nenhum dado pessoal.</strong> Os arquivos falam de produtos, nunca de pessoas. O que você faz no provador e nas ferramentas fica no seu aparelho e não entra aqui.</li>
<li><strong>Nenhum preço sem data.</strong> Cada valor sai com o dia em que foi conferido e a loja. Preço sem data não é publicado.</li>
<li><strong>Nenhum link de afiliado.</strong> Os endereços de loja saem limpos, sem identificador de comissão. Quando o link é de busca, e não de um anúncio conferido, o campo <code>link_tipo</code> diz <code>busca</code>.</li>
<li><strong>Volume e fórmula só com fonte.</strong> Volume não conferido fica vazio. Lista INCI só entra com a origem anotada.</li>
<li><strong>Não é vendido.</strong> O dataset não tem versão paga nem acesso reservado.</li>
<li><strong>Sem nota de loja.</strong> Estrelas e número de avaliações pertencem às lojas e ficam de fora.</li>
</ul>
</section>

<section aria-labelledby="da-licenca">
<h2 id="da-licenca">Licença e como citar</h2>
<p>Os dados estão sob a licença <a href="{LICENCA_URL}" rel="noopener license">Creative Commons Atribuição 4.0 (CC BY 4.0)</a>: você pode copiar, adaptar e usar, inclusive comercialmente, desde que cite a origem.</p>
<p class="ig-caixa">{esc(citacao)}</p>
<p class="ig-nota">Nomes de produtos e marcas pertencem aos fabricantes e aparecem só para identificar o produto. O dataset ainda não está em repositório com DOI.</p>
</section>

<section aria-labelledby="da-enderecos">
<h2 id="da-enderecos">Endereços para ler por programa</h2>
<p>Os arquivos são estáticos e ficam em endereços fixos, só de leitura. Aceitam pedido de qualquer origem (CORS aberto), então dá para ler direto de uma planilha, de um notebook ou do navegador.</p>
<ul>
<li><code>GET {SITE}/dados/index.json</code>: versão, contagens e dicionário</li>
<li><code>GET {SITE}/dados/produtos.json</code></li>
<li><code>GET {SITE}/dados/precos.json</code></li>
<li><code>GET {SITE}/dados/inci.json</code></li>
<li><code>GET {SITE}/dados/mudancas.json</code></li>
</ul>
<p class="ig-nota">Não há filtro nem paginação: cada endereço devolve o arquivo inteiro. Os arquivos são refeitos quando o catálogo muda. Mudança de formato sobe a versão e entra no histórico abaixo.</p>
</section>

<section aria-labelledby="da-campos">
<h2 id="da-campos">Dicionário de campos</h2>
<p>Datas no formato AAAA-MM-DD. Preços em reais, com ponto decimal.</p>
{dicionario}
</section>

<section aria-labelledby="da-historico">
<h2 id="da-historico">Histórico de versões</h2>
<ul class="da-versoes">
{changelog}
</ul>
</section>

<section aria-labelledby="da-leia">
<h2 id="da-leia">Leia também</h2>
<ul class="ig-rel">
<li><a href="/ferramentas/extrato-cosmetico/">Extrato do cosmético</a></li>
<li><a href="/ferramentas/precos/">Termômetro de preços</a></li>
<li><a href="/produtos/">Catálogo de produtos</a></li>
<li><a href="/sobre/">Sobre e critérios de escolha</a></li>
</ul>
<p class="ig-nota">Achou um erro num arquivo? <a href="/contato/">Avise</a>: a correção entra na próxima geração dos dados.</p>
</section>
</article>
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>"""
    css = """
.ft-rolagem{overflow-x:auto}
.ft-regras{margin:8px 0 0;padding-left:1.1em}
.ft-regras li{margin:.45em 0}
.da-tabela{width:100%;border-collapse:collapse;font-size:.94rem}
.da-tabela th,.da-tabela td{padding:9px 10px;border-bottom:1px solid var(--linha);text-align:left;vertical-align:top}
.da-tabela code,.ig code{font-size:.9em;overflow-wrap:anywhere}
.da-versoes{padding-left:1.1em}
"""
    return pagina(
        titulo="Dados abertos de skincare: produtos, preços datados e fórmulas",
        descricao=("Baixe o catálogo do Produto Skincare em CSV e JSON: produtos, preços com a data da conferência, "
                   "fórmulas (INCI) e mudanças detectadas. Licença CC BY 4.0, sem cadastro."),
        caminho="/dados-abertos/", trilha=[("/", "Início"), (None, "Dados abertos")],
        corpo=corpo, css_extra=css, larga=True,
        aviso="Dados informativos sobre produtos. Não substituem consulta com dermatologista.")


def main():
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    tabelas = montar()
    datas = [p["preco_em"] for p in tabelas["produtos"] if p["preco_em"]]
    datas += [o["conferido_em"] for o in tabelas["precos"]]
    datas += [l["registrado_em"] for l in tabelas["inci"] if l["registrado_em"]]
    datas += [m["em"] for m in tabelas["mudancas"]]
    dados_ate = max(datas)

    textos = {}
    for nome, linhas in tabelas.items():
        textos[f"dados/{nome}.csv"] = em_csv(nome, linhas)
        textos[f"dados/{nome}.json"] = json.dumps({
            "dataset": "Produto Skincare — dados abertos", "arquivo": nome, "versao": cfg["versao"],
            "dados_ate": dados_ate, "licenca": LICENCA, "licenca_url": LICENCA_URL,
            "fonte": f"{SITE}/dados-abertos/", "linhas": len(linhas), "itens": linhas,
        }, ensure_ascii=False, indent=1) + "\n"
    textos["dados/index.json"] = json.dumps({
        "dataset": "Produto Skincare — dados abertos", "versao": cfg["versao"], "dados_ate": dados_ate,
        "licenca": LICENCA, "licenca_url": LICENCA_URL, "pagina": f"{SITE}/dados-abertos/",
        "como_citar": (f"Produto Skincare. Dados abertos do catálogo de skincare no Brasil, versão {cfg['versao']}. "
                       f"{SITE}/dados-abertos/. Licença CC BY 4.0."),
        "arquivos": [{
            "nome": k, "titulo": TITULOS[k][0], "descricao": TITULOS[k][1], "linhas": len(tabelas[k]),
            "csv": f"{SITE}/dados/{k}.csv", "json": f"{SITE}/dados/{k}.json",
            "campos": [{"campo": c, "tipo": t, "descricao": d} for c, t, d in CAMPOS[k]],
        } for k in CAMPOS],
        "changelog": cfg["changelog"],
    }, ensure_ascii=False, indent=1) + "\n"

    conferir(tabelas, textos)
    if "--check" in sys.argv:
        diferentes = [c for c, t in textos.items()
                      if not (RAIZ / c).exists() or (RAIZ / c).read_text(encoding="utf-8") != t]
        if diferentes:
            print("dataset desatualizado:", ", ".join(diferentes))
            print("rode: python3 -I _scripts/gerar_dados_abertos.py")
            sys.exit(1)
        print("dataset em dia com as fontes.")
        return

    DADOS.mkdir(exist_ok=True)
    for caminho, t in textos.items():
        (RAIZ / caminho).write_text(t, encoding="utf-8")
    destino = RAIZ / "dados-abertos" / "index.html"
    destino.parent.mkdir(exist_ok=True)
    destino.write_text(pagina_html(tabelas, cfg, dados_ate), encoding="utf-8")
    print(f"dataset v{cfg['versao']} · dados até {dados_ate} · " +
          " · ".join(f"{k}: {len(v)}" for k, v in tabelas.items()))
    print("gerados: dados/*.csv, dados/*.json, dados/index.json e /dados-abertos/")


if __name__ == "__main__":
    main()
