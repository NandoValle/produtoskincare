#!/usr/bin/env bash
# webmcp-check.sh — canário que fixa a nota do relatório WebMCP/SEO/GEO/AEO.
# Roda contra o site publicado (ou um preview) e falha se qualquer invariante cair.
#
# Uso:  ./webmcp-check.sh [URL-base]        (padrão: https://produtoskincare.com.br)
#       ./webmcp-check.sh --paridade        # só confere manifesto x fontes (roda no CI)
set -u
BASE="${1:-https://produtoskincare.com.br}"
[ "$BASE" = "--paridade" ] && { cd "$(dirname "$0")" && exec node gerar-manifesto.mjs --check; }
FALHAS=0
ok()   { echo "  ok   $1"; }
falha(){ echo "  FALHA $1"; FALHAS=$((FALHAS+1)); }

HTML=$(curl -sL --max-time 20 "$BASE/") || { echo "site inacessível"; exit 1; }
HEADERS=$(curl -sIL --max-time 20 "$BASE/")

echo "== Página inicial ($BASE) =="
echo "$HTML" | grep -qi 'name="robots"[^>]*noindex' && falha "noindex presente" || ok "sem noindex"
echo "$HTML" | grep -q 'rel="canonical"' && ok "canonical presente" || falha "canonical ausente"
TITULO=$(echo "$HTML" | grep -o '<title>[^<]*' | head -1 | sed 's/<title>//')
N=${#TITULO}; [ "$N" -ge 30 ] && [ "$N" -le 70 ] && ok "title $N chars" || falha "title com $N chars (ideal 30-70)"
echo "$HTML" | grep -qi 'name="description"' && ok "meta description" || falha "meta description ausente"
echo "$HTML" | grep -qi 'origin-trial' && ok "WebMCP Origin Trial" || falha "origin trial ausente"
# Validade do token: expiração silenciosa é a regressão clássica que derruba a nota.
TOKEN=$(echo "$HTML" | grep -o 'origin-trial" content="[^"]*"' | head -1 | sed 's/.*content="//; s/"$//')
if [ -n "$TOKEN" ]; then
  python3 - "$TOKEN" <<'PYEOF'
import base64, datetime, re, sys
tok = sys.argv[1] + "=" * (-len(sys.argv[1]) % 4)
m = re.search(rb'"expiry":(\d+)', base64.b64decode(tok))
if not m:
    print("  FALHA token origin trial ilegível (sem campo expiry)"); sys.exit(1)
exp = int(m.group(1))
dias = (datetime.datetime.fromtimestamp(exp, datetime.timezone.utc) - datetime.datetime.now(datetime.timezone.utc)).days
if dias < 0:
    print(f"  FALHA origin trial EXPIRADO há {-dias} dias — renovar em web.dev/origin-trials"); sys.exit(1)
if dias < 30:
    print(f"  FALHA origin trial expira em {dias} dias — renovar agora"); sys.exit(1)
print(f"  ok   origin trial válido por mais {dias} dias")
PYEOF
  [ $? -eq 0 ] || FALHAS=$((FALHAS+1))
fi
echo "$HTML" | grep -q 'application/ld+json' && ok "JSON-LD presente" || falha "JSON-LD ausente"
echo "$HTML" | grep -q 'FAQPage' && ok "FAQPage JSON-LD" || falha "FAQPage ausente"
echo "$HTML" | grep -q '<img[^>]*>' && { echo "$HTML" | grep -o '<img[^>]*>' | grep -vq 'alt=' && falha "img sem alt" || ok "imgs com alt"; } || ok "sem imgs"

echo "== Cabeçalhos HTTP =="
echo "$HEADERS" | grep -qi '^origin-agent-cluster: *?1' && ok "Origin-Agent-Cluster: ?1" || falha "Origin-Agent-Cluster ausente"
echo "$HEADERS" | grep -qi '^permissions-policy:.*tools=(self)' && ok "Permissions-Policy tools=(self)" || falha "Permissions-Policy tools ausente"

echo "== Descoberta WebMCP estática =="
if MANIFESTO=$(curl -sf --max-time 20 "$BASE/webmcp-tools.json"); then
  echo "$MANIFESTO" | python3 -c '
import json, sys
d = json.load(sys.stdin)
ts = d.get("tools", [])
erros = []
if len(ts) != 4:
    erros.append("esperado 4 ferramentas, veio %d" % len(ts))
for t in ts:
    nome = t.get("name", "?")
    if not nome or len(t.get("description", "")) < 80:
        erros.append("nome/descrição curta em %s" % nome)
    if t.get("kind") == "imperative":
        props = t.get("inputSchema", {}).get("properties", {})
        if not props:
            erros.append("inputSchema sem properties em %s" % nome)
        elif not all("description" in p for p in props.values()):
            erros.append("parâmetro sem description em %s" % nome)
if erros:
    print("; ".join(erros)); sys.exit(1)
print("manifesto ok: 4 ferramentas, schemas completos")
' && ok "webmcp-tools.json válido e completo" || falha "webmcp-tools.json inválido"
else
  falha "webmcp-tools.json inacessível (404?)"
fi
echo "$HTML" | grep -q 'application/webmcp+json' && ok "link/inline do manifesto no head" || falha "manifesto não referenciado no <head>"
cd "$(dirname "$0")" && node gerar-manifesto.mjs --check >/dev/null 2>&1 && ok "paridade manifesto x fontes (local)" || falha "paridade manifesto x fontes (local)"

echo "== GEO/AEO =="
LLMS=$(curl -sf --max-time 20 "$BASE/llms.txt") && ok "llms.txt presente (${#LLMS} bytes)" || falha "llms.txt ausente"
echo "$LLMS" | grep -q '^# ' && ok "llms.txt com H1" || falha "llms.txt sem H1"
curl -sf --max-time 20 "$BASE/llms-full.txt" >/dev/null && ok "llms-full.txt presente" || echo "  nota  llms-full.txt ausente (opcional)"
curl -sf --max-time 20 "$BASE/sitemap.xml" | grep -q '<lastmod>' && ok "sitemap com lastmod" || falha "sitemap/lastmod ausente"

echo
[ "$FALHAS" -eq 0 ] && echo "TUDO OK — nota travada." || echo "$FALHAS falha(s) — corrigir antes do deploy."
exit "$FALHAS"
