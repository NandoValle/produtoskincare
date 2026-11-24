#!/usr/bin/env python3
"""Falha enquanto a página do Programa tiver link de checkout pendente.

Os dois botões de compra de /programa-12-semanas/ nasceram com o marcador
CHECKOUT-PENDENTE no href, à espera dos links da plataforma de pagamento (Hubla).
Esta checagem impede que o marcador vá para o ar por engano.

    python _scripts/checar_checkout.py

Só usa a biblioteca padrão.
"""
import re
import sys
from pathlib import Path

PAGINA = Path(__file__).resolve().parent.parent / "programa-12-semanas" / "index.html"
BOTOES = ("cta-checkout", "cta-caderno")


def main():
    html = PAGINA.read_text(encoding="utf-8")
    erros = []
    for botao in BOTOES:
        m = re.search(r'<a\b[^>]*\bid="%s"[^>]*>' % botao, html)
        if not m:
            erros.append("botão #%s não encontrado" % botao)
            continue
        href = re.search(r'\bhref="([^"]*)"', m.group(0))
        destino = href.group(1) if href else ""
        if "CHECKOUT-PENDENTE" in destino:
            erros.append("#%s ainda aponta para o marcador (%s)" % (botao, destino))
        elif not destino.startswith("https://"):
            erros.append("#%s não aponta para um checkout https (%s)" % (botao, destino))
    if erros:
        print("Checkout do Programa incompleto:")
        for e in erros:
            print("  - " + e)
        print("Troque os href pelos links de checkout da Hubla antes de publicar.")
        return 1
    print("Checkout do Programa: os dois botões apontam para links https.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
