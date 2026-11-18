#!/usr/bin/env node
/*
 * gerar-manifesto.mjs — gera webmcp-tools.json a partir das fontes reais do site.
 *
 * Fontes:
 *   1. webmcp.js  → 3 ferramentas imperativas (executado em sandbox com document.modelContext
 *                   falso; as definições são capturadas em registerTool, sem executar execute()).
 *   2. home.html  → 1 ferramenta declarativa (form[toolname] + campos com toolparamdescription).
 *
 * Uso:
 *   node gerar-manifesto.mjs                  # gera webmcp-tools.json + trecho-head.html
 *   node gerar-manifesto.mjs --check          # sai com código 1 se o manifesto publicado divergir
 *
 * O --check deve rodar no CI antes de cada deploy: manifesto e código nunca podem divergir.
 */
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { runInNewContext } from "node:vm";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const AQUI = dirname(fileURLToPath(import.meta.url));
const RAIZ = join(AQUI, "..", ".."); // raiz do repositório (= raiz publicada do site)
const SITE = "https://produtoskincare.com.br";
// Caminhos das fontes: sobrescrevíveis para rodar em qualquer layout de repositório.
const FONTES = {
  webmcp: process.env.WEBMCP_JS || join(RAIZ, "webmcp.js"),
  home: process.env.HOME_HTML || join(RAIZ, "index.html"),
};

// ---------- 1. ferramentas imperativas: extrair do webmcp.js em sandbox ----------
function extrairImperativas() {
  const codigo = readFileSync(FONTES.webmcp, "utf8");
  const capturadas = [];
  const sandbox = {
    window: { isSecureContext: true, addEventListener() {}, console },
    document: {
      modelContext: {
        registerTool(ferramenta) {
          capturadas.push(ferramenta);
          return Promise.resolve();
        },
      },
    },
    location: { origin: SITE },
    fetch: () => Promise.reject(new Error("fetch não chamado no registro")),
    DOMException,
    AbortController,
    console,
  };
  runInNewContext(codigo, sandbox, { filename: "webmcp.js" });
  return capturadas.map((f) => ({
    kind: "imperative",
    name: f.name,
    title: f.title,
    description: f.description,
    inputSchema: f.inputSchema,
    annotations: f.annotations || {},
    execute: undefined, // manifesto é só de descoberta; execute continua no webmcp.js
    sources: ["imperative"],
  }));
}

// ---------- 2. ferramenta declarativa: extrair o form[toolname] do home.html ----------
function attr(tag, nome) {
  const m = tag.match(new RegExp(nome + '="([^"]*)"', "i"));
  return m ? m[1] : null;
}

function extrairDeclarativas() {
  const html = readFileSync(FONTES.home, "utf8");
  const formMatch = html.match(/<form[^>]*toolname="[^"]*"[^>]*>/i);
  if (!formMatch) throw new Error("form[toolname] não encontrado no home.html");
  const formTag = formMatch[0];
  const inicio = formMatch.index;
  const fim = html.indexOf("</form>", inicio);
  const corpo = html.slice(inicio, fim);

  const campos = [];
  const re = /<(select|input)([^>]*)>/gi;
  let m;
  while ((m = re.exec(corpo))) {
    const tag = m[0];
    const descricao = attr(tag, "toolparamdescription");
    if (!descricao) continue;
    const tipo = m[1].toLowerCase() === "select" ? "select-one" : attr(tag, "type") || "text";
    const opcoes = [];
    if (m[1].toLowerCase() === "select") {
      const nome = attr(tag, "name");
      const blocoSelect = corpo.slice(m.index, corpo.indexOf("</select>", m.index));
      const reOpt = /<option[^>]*value="([^"]*)"/gi;
      let o;
      while ((o = reOpt.exec(blocoSelect))) opcoes.push(o[1]);
      void nome;
    }
    campos.push({
      name: attr(tag, "name"),
      type: tipo,
      required: /\brequired\b/i.test(tag),
      description: descricao,
      ...(opcoes.length ? { options: opcoes.filter((v) => v !== "") } : {}),
    });
  }

  return [
    {
      kind: "declarative",
      name: attr(formTag, "toolname"),
      description: attr(formTag, "tooldescription"),
      autoSubmit: /\btoolautosubmit\b/i.test(formTag),
      action: attr(formTag, "action"),
      method: (attr(formTag, "method") || "get").toLowerCase(),
      inputSchema: {
        type: "object",
        properties: Object.fromEntries(
          campos.map((c) => [
            c.name,
            {
              type: c.type === "select-one" ? "string" : c.type === "checkbox" ? "boolean" : "string",
              ...(c.options ? { enum: c.options } : {}),
              description: c.description,
            },
          ])
        ),
        required: campos.filter((c) => c.required).map((c) => c.name),
        additionalProperties: false,
      },
      fields: campos,
      sources: ["declarative"],
    },
  ];
}

// ---------- 3. montar, gravar ou conferir ----------
function removerUndefined(obj) {
  return JSON.parse(JSON.stringify(obj));
}

function gerar() {
  const ferramentas = [...extrairDeclarativas(), ...extrairImperativas()];
  return removerUndefined({
    schemaVersion: 1,
    site: SITE,
    note:
      "Manifesto estático das ferramentas WebMCP do Produto Skincare. Gerado por gerar-manifesto.mjs " +
      "a partir de webmcp.js e do form[toolname] da home. Descoberta para agentes e scanners; " +
      "a execução continua em webmcp.js (imperativas) e no próprio form (declarativa). " +
      "Só leitura: nenhuma ferramenta compra, cadastra ou envia dados.",
    tools: ferramentas,
  });
}

const manifesto = gerar();
const json = JSON.stringify(manifesto, null, 2) + "\n";
const caminhoJson = join(RAIZ, "webmcp-tools.json"); // publicado em /webmcp-tools.json

if (process.argv.includes("--check")) {
  if (!existsSync(caminhoJson)) {
    console.error("FALHA: webmcp-tools.json não existe. Rode sem --check e publique.");
    process.exit(1);
  }
  const publicado = readFileSync(caminhoJson, "utf8");
  if (publicado !== json) {
    console.error("FALHA: webmcp-tools.json publicado diverge das fontes (webmcp.js / home.html).");
    process.exit(1);
  }
  console.log("OK: manifesto em dia com as fontes (" + manifesto.tools.length + " ferramentas).");
  process.exit(0);
}

writeFileSync(caminhoJson, json);

// trecho de <head> — link rel + bloco inline application/mcp+json (mesmo conteúdo, gerado junto)
const inline = JSON.stringify(manifesto, null, 2)
  .split("\n")
  .map((l) => "  " + l)
  .join("\n");
writeFileSync(
  join(AQUI, "trecho-head.html"),
  `<!-- WebMCP: descoberta estática das ferramentas (gerado por gerar-manifesto.mjs; não editar à mão) -->
<link rel="alternate" type="application/webmcp+json" href="/webmcp-tools.json" title="Ferramentas WebMCP do Produto Skincare">
<script type="application/mcp+json">
${inline}
</script>
`,
  "utf8"
);

console.log("Gerado webmcp-tools.json com " + manifesto.tools.length + " ferramentas:");
for (const t of manifesto.tools) console.log(" - [" + t.kind + "] " + t.name);
