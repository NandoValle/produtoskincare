/* Testes das regras de ativos (/regras-ativos.js). Sem dependências:
 *
 *     node _scripts/testar_regras.js
 *
 * Rode sempre que mudar uma regra. Cada caso abaixo é um exemplo documentado do que a
 * regra deve responder; se a regra mudar de propósito, mude o caso junto e suba a VERSAO.
 */
"use strict";
const path = require("path");
const fs = require("fs");
const R = require(path.join(__dirname, "..", "regras-ativos.js"));
const CATALOGO = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "produtos.json"), "utf8")).produtos;
const produto = id => {
  const p = CATALOGO.find(x => x.id === id);
  if (!p) throw new Error("produto não está no catálogo: " + id);
  return p;
};

let falhas = 0, total = 0;
function caso(nome, obtido, esperado) {
  total++;
  const ok = JSON.stringify(obtido) === JSON.stringify(esperado);
  if (!ok) falhas++;
  console.log(`${ok ? "ok   " : "FALHA"} ${nome}${ok ? "" : `\n      esperado: ${JSON.stringify(esperado)}\n      obtido:   ${JSON.stringify(obtido)}`}`);
}
const regras = (p, perfil) => R.contraindicacoes(p, perfil).map(c => `${c.acao}:${c.regra}`).sort();
const sens = { sensivel: true }, comum = { sensivel: false };

/* ===== Detecção de ativos ===== */
console.log("\nDetecção");
const ids = t => R.detectar(t).map(a => a.id);
caso("lista INCI com retinol, ácido glicólico e hialuronato", ids("Aqua, Glycolic Acid, Retinol, Sodium Hyaluronate"), ["retinol", "glicolico", "hialuronico"]);
caso("ácido hialurônico não é AHA", R.detectar("ácido hialurônico").map(a => a.classe), ["hidratante"]);
caso("ácido cítrico (ajuste de pH) não conta como AHA", ids("Citric Acid, Glycerin"), ["glicerina"]);
caso("nomes em português com acento", ids("ácido salicílico, peróxido de benzoíla"), ["salicilico", "bpo"]);
caso("concentração do retinol no catálogo", R.concentracao("Principia RN-0,3 Retinol retinol 0,3%", "retinoide"), 0.3);
caso("concentração com ponto decimal", R.concentracao("Glycolic Acid 7.5%", "aha"), 7.5);

/* ===== Feature 3: pele sensível e contraindicações (produtos reais do catálogo) ===== */
console.log("\nContraindicações por perfil");
caso("sensível: retinol 0,3% sai da rotina (e não carrega avisos)", regras(produto("principia-rn03"), sens), ["remover:sens-retinoide"]);
caso("sensível: retinol sem concentração informada também sai", regras(produto("loreal-revitalift-noturno"), sens).filter(r => r.startsWith("remover")), ["remover:sens-retinoide"]);
caso("pele comum: retinol 0,3% fica, sem aviso", regras(produto("principia-rn03"), comum), []);
caso("sensível: vitamina C fica, com aviso de ardência", regras(produto("principia-vc10"), sens), ["avisar:sens-fragrancia-desconhecida", "avisar:sens-vitc"]);
caso("sensível: 'sem fragrância' na descrição não gera aviso de fragrância", regras(produto("creamy-calming-cream"), sens), []);
caso("sensível: produto com fragrancia=true sai", regras({ nome: "Creme X", ativos: ["glicerina"], fragrancia: true }, sens), ["remover:sens-fragrancia"]);
caso("todos: retinol 1% recebe aviso de concentração alta", regras({ nome: "Sérum Retinol 1%", ativos: ["retinol 1%"] }, comum), ["avisar:retinoide-alto"]);
caso("sensível: ácido glicólico 15% (forte) sai", regras({ nome: "Tônico", ativos: ["ácido glicólico 15%"], fragrancia: false }, sens), ["remover:sens-acido-forte"]);
caso("sensível: ácido glicólico 5% fica, com aviso", regras({ nome: "Tônico", ativos: ["ácido glicólico 5%"], fragrancia: false }, sens), ["avisar:sens-acido"]);
caso("todos: ácido salicílico 2% não é 'forte'", regras({ nome: "Gel", ativos: ["ácido salicílico 2%"] }, comum), []);
caso("todos: ácido salicílico 5% é 'forte'", regras({ nome: "Peeling", ativos: ["ácido salicílico 5%"] }, comum), ["avisar:acido-forte"]);

/* ===== Integridade da lista ===== */
console.log("\nIntegridade");
const classes = new Set([...R.ATIVOS.map(a => a.classe), ...Object.values(R.ESTADOS).map(e => e.classe)]);
caso("toda regra de combinação usa classes conhecidas", R.COMBINACOES.filter(c => !classes.has(c.a) || !classes.has(c.b)).map(c => c.id), []);
caso("ids de regras únicos", R.COMBINACOES.length + R.PERFIL.length, new Set([...R.COMBINACOES, ...R.PERFIL].map(r => r.id)).size);
caso("toda regra tem motivo", [...R.COMBINACOES, ...R.PERFIL].filter(r => !r.motivo).map(r => r.id), []);
caso("versão registrada no histórico", R.HISTORICO.some(h => h.versao === R.VERSAO), true);

console.log(`\n${total - falhas}/${total} casos passaram (regras v${R.VERSAO}).`);
process.exit(falhas ? 1 : 0);
