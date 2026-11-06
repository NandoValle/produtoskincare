#!/usr/bin/env bash
# Testes de navegador do provador e do verificador de ingredientes.
# Sobe o site localmente (python3 -m http.server) e roda cada teste com o Playwright.
#
# Requisitos: Node 18+, Python 3 e Playwright com o Chromium:
#   npm install playwright && npx playwright install chromium
#
# Uso, na raiz do repositório:
#   _scripts/testes_navegador/rodar.sh
set -uo pipefail
cd "$(dirname "$0")/../.."
PORTA="${PORTA:-8765}"
python3 -m http.server "$PORTA" --bind 127.0.0.1 >/dev/null 2>&1 &
SERVIDOR=$!
trap 'kill $SERVIDOR 2>/dev/null' EXIT
sleep 1
BASE="http://127.0.0.1:$PORTA"
falhou=0
node _scripts/testar_regras.js >/dev/null && echo "ok    regras (node _scripts/testar_regras.js)" || { echo "FALHA regras"; falhou=1; }
for t in link link_extra sensivel orcamento verificador confianca; do
  if saida=$(node "_scripts/testes_navegador/$t.js" "$BASE" 2>&1); then
    echo "ok    $t"
  else
    echo "FALHA $t"; echo "$saida" | grep -E "FALHA|DIFERENTE|Error" | head -20; falhou=1
  fi
done
exit $falhou
