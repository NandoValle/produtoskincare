"""Gera a grade estática de /achados/ a partir de achados/produtos.json.

A página busca o JSON no navegador e, se ele carregar, redesenha #grade.
Sem JavaScript (ou se o JSON não carregar), fica o HTML entre os marcadores.
Rode depois de editar achados/produtos.json:

    python3 _scripts/gerar_achados.py

Validade do link (100 dias a partir de link_gerado_em) e o aviso de preço
com mais de 30 dias usam as mesmas regras do script da página e a data
de hoje. Não inventa produto, preço nem link: só copia o JSON.
"""
import html
import json
from datetime import datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
JSON = RAIZ / "achados" / "produtos.json"
PAGINA = RAIZ / "achados" / "index.html"
INICIO = "<!-- grade-estatica:inicio -->"
FIM = "<!-- grade-estatica:fim -->"
VALIDADE_DIAS = 100
PRECO_VELHO_DIAS = 30
SELOS = {
    "forte": "Ativo com evidência forte",
    "moderada": "Ativo com evidência moderada",
    "emergente": "Ativo com evidência emergente",
}
DIA = 86400


def esc(valor):
    return html.escape(str(valor), quote=True)


def data_br(iso):
    partes = str(iso or "").split("-")
    if len(partes) != 3:
        return ""
    ano, mes, dia = partes
    return f"{dia}/{mes}/{ano}"


def brl(valor):
    return "R$ " + f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def host_oficial(url):
    try:
        host = html.unescape(url).split("/")[2].lower()
    except IndexError:
        return False
    return host == "tiktok.com" or host.endswith(".tiktok.com")


def instante(iso):
    return datetime.fromisoformat(str(iso) + "T00:00:00")


def dias_restantes(item, agora):
    if not item.get("link_gerado_em"):
        return None
    try:
        gerado = instante(item["link_gerado_em"])
    except ValueError:
        return None
    return int((gerado.timestamp() + VALIDADE_DIAS * DIA - agora.timestamp()) // DIA)


def link_valido(item, agora):
    dias = dias_restantes(item, agora)
    return host_oficial(item.get("link", "")) and dias is not None and dias >= 0


def preco_velho(iso, agora):
    try:
        idade = (agora.timestamp() - instante(iso).timestamp()) / DIA
    except ValueError:
        return False
    return idade > PRECO_VELHO_DIAS


def card(produto, agora):
    linhas = ['    <article class="card">']
    if produto.get("foto"):
        src = "/" + str(produto["foto"]).lstrip("/")
        linhas.append(
            f'      <img class="foto" src="{esc(src)}" alt="{esc(produto["nome"])}" loading="lazy" decoding="async">'
        )
    if produto.get("categoria"):
        linhas.append(f'      <span class="cat">{esc(produto["categoria"])}</span>')
    linhas.append(f'      <h2>{esc(produto["nome"])}</h2>')
    if produto.get("marca"):
        linhas.append(f'      <p class="marca-prod">{esc(produto["marca"])}</p>')
    if produto.get("porque"):
        linhas.append(f'      <p class="porque">{esc(produto["porque"])}</p>')
    selo = SELOS.get(produto.get("evidencia"))
    if selo:
        linhas.append(
            '      <span class="selo" title="O selo avalia o ativo principal, não a fórmula deste produto.">'
            f'<a href="/ingredientes/peptideo-de-cobre/">{esc(selo)}</a></span>'
        )
    linhas.append('      <div class="preco">')
    if isinstance(produto.get("preco"), (int, float)) and not isinstance(produto.get("preco"), bool):
        linhas.append(f"        <strong>{esc(brl(produto['preco']))}</strong>")
    else:
        linhas.append("        <strong>Preço não conferido</strong>")
    if produto.get("preco_em"):
        aviso = ""
        if preco_velho(produto["preco_em"], agora):
            aviso = '<span class="velho">pode ter mudado: confira na loja</span>'
        linhas.append(f'        <small>preço visto em {esc(data_br(produto["preco_em"]))}{aviso}</small>')
    else:
        linhas.append("        <small>veja o preço atual na loja</small>")
    linhas.append("      </div>")
    if link_valido(produto, agora):
        linhas.append(
            f'      <a class="botao" href="{esc(produto["link"])}" target="_blank" '
            f'rel="sponsored nofollow noopener" data-produto="{esc(produto["nome"])}">Ver no TikTok Shop</a>'
        )
    else:
        linhas.append('      <a class="botao" aria-disabled="true">Link indisponível</a>')
    outras = [o for o in produto.get("ofertas") or [] if link_valido(o, agora)]
    if outras:
        linhas.append('      <details class="ofertas">')
        linhas.append(f"        <summary>Outras lojas com este produto ({len(outras)})</summary>")
        linhas.append("        <ul>")
        for i, oferta in enumerate(outras):
            texto = f"Loja {i + 2}"
            if isinstance(oferta.get("preco"), (int, float)) and not isinstance(oferta.get("preco"), bool):
                texto += f" · {brl(oferta['preco'])} em {data_br(oferta.get('preco_em'))}"
            linhas.append(
                f'          <li><a href="{esc(oferta["link"])}" target="_blank" '
                f'rel="sponsored nofollow noopener" data-produto="{esc(produto["nome"])}">{esc(texto)} ↗</a></li>'
            )
        linhas.append("        </ul>")
        linhas.append("      </details>")
    linhas.append("    </article>")
    return "\n".join(linhas)


def main():
    produtos = json.loads(JSON.read_text(encoding="utf-8"))
    if not isinstance(produtos, list) or not produtos:
        raise SystemExit("achados/produtos.json não tem uma lista de produtos")
    agora = datetime.now()
    bloco = "\n".join(card(p, agora) for p in produtos)
    texto = PAGINA.read_text(encoding="utf-8")
    if INICIO not in texto or FIM not in texto or texto.index(INICIO) > texto.index(FIM):
        raise SystemExit("marcadores da grade estática não encontrados em achados/index.html")
    antes, resto = texto.split(INICIO, 1)
    _, depois = resto.split(FIM, 1)
    PAGINA.write_text(f"{antes}{INICIO}\n{bloco}\n    {FIM}{depois}", encoding="utf-8")
    links = PAGINA.read_text(encoding="utf-8").split(INICIO, 1)[1].split(FIM, 1)[0]
    faltando = [p["nome"] for p in produtos if p["nome"] not in links]
    if faltando or links.count("<article") != len(produtos):
        raise SystemExit(f"grade gerada incompleta: {faltando}")
    print(f"{len(produtos)} produtos gravados em achados/index.html")


if __name__ == "__main__":
    main()
