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

/* ===== Feature 4: combinações documentadas (critério de pronto) =====
 * Entrada → resultado esperado (regra). As 6 primeiras também estão como "Exemplos para
 * testar" em /ferramentas/ingredientes/, para conferir na página.
 *
 *  #  Entrada                                   Resultado              Regra
 *  1  retinol + ácido glicólico                 horários diferentes    retinoide-aha
 *  2  retinol + ácido salicílico                horários diferentes    retinoide-bha
 *  3  retinol + vitamina C                      horários diferentes    retinoide-vitc
 *  4  peróxido de benzoíla + tretinoína         horários diferentes    bpo-retinoide (com nota)
 *  5  ácido glicólico + pele irritada           não combine            irritada-aha
 *  6  vitamina C + niacinamida                  pode usar junto        vitc-niacinamida
 *  7  ácido salicílico + pele irritada          não combine            irritada-bha
 *  8  retinol + tretinoína                      não combine            retinoide-retinoide
 *  9  retinol + ácido glicólico, pele sensível  não combine            retinoide-aha (mais rígida)
 * 10  niacinamida + ácido hialurônico           pode usar junto        neutra-hidratante
 * 11  INCI colado com retinol e glycolic acid   horários diferentes    (geral)
 * 12  retinol + vitamina C + niacinamida        horários diferentes    (geral, 3 pares)
 */
console.log("\nCombinações documentadas");
const A = id => { const a = R.ATIVOS.find(x => x.id === id); if (!a) throw new Error("ativo desconhecido: " + id); return a; };
const IRRITADA = R.ESTADOS.irritada;
const par = (x, y, ctx) => { const r = R.avaliarPar(x, y, ctx); return [r.resultado, r.regra]; };
caso("1  retinol + ácido glicólico", par(A("retinol"), A("glicolico")), ["horarios", "retinoide-aha"]);
caso("2  retinol + ácido salicílico", par(A("retinol"), A("salicilico")), ["horarios", "retinoide-bha"]);
caso("3  retinol + vitamina C", par(A("retinol"), A("vitc")), ["horarios", "retinoide-vitc"]);
caso("4  peróxido de benzoíla + tretinoína", par(A("bpo"), A("tretinoina")), ["horarios", "bpo-retinoide"]);
caso("4b tem nota sobre o medicamento combinado", /adapaleno/.test(R.avaliarPar(A("bpo"), A("tretinoina")).nota), true);
caso("5  ácido glicólico + pele irritada", par(A("glicolico"), IRRITADA), ["nao", "irritada-aha"]);
caso("6  vitamina C + niacinamida", par(A("vitc"), A("niacinamida")), ["ok", "vitc-niacinamida"]);
caso("7  ácido salicílico + pele irritada", par(IRRITADA, A("salicilico")), ["nao", "irritada-bha"]);
caso("8  retinol + tretinoína (dois retinoides)", par(A("retinol"), A("tretinoina")), ["nao", "retinoide-retinoide"]);
caso("9  retinol + ácido glicólico em pele sensível", par(A("retinol"), A("glicolico"), { sensivel: true }), ["nao", "retinoide-aha"]);
caso("10 niacinamida + ácido hialurônico", par(A("niacinamida"), A("hialuronico")), ["ok", "neutra-hidratante"]);
const inci = R.avaliar(R.detectar("Aqua, Glycerin, Glycolic Acid, Retinol, Sodium Hyaluronate, Citric Acid"));
caso("11 INCI colado: resultado geral", inci.resultado, "horarios");
const tres = R.avaliar([A("retinol"), A("vitc"), A("niacinamida")]);
caso("12 três ativos: geral e número de pares", [tres.resultado, tres.pares.length, tres.pares[0].regra], ["horarios", 3, "retinoide-vitc"]);
caso("a ordem dos ativos não muda o resultado", par(A("glicolico"), A("retinol")), par(A("retinol"), A("glicolico")));
caso("pele irritada + ativo sem regra: sem regra cadastrada (não 'ok')", par(IRRITADA, A("niacinamida")), ["sem_regra", "irritada-sem-regra"]);
caso("par sem regra cadastrada (ácido azelaico + ácido salicílico): sem_regra", par(A("azelaico"), A("salicilico")), ["sem_regra", "sem-regra"]);
caso("par sem regra cadastrada (niacinamida + peróxido de benzoíla): sem_regra", par(A("niacinamida"), A("bpo")), ["sem_regra", "sem-regra"]);
caso("motivo do par sem regra não diz que é seguro", /não quer dizer que é seguro/.test(R.avaliarPar(A("azelaico"), A("salicilico")).motivo), true);
caso("geral com um par sem regra e os outros ok: sem_regra", R.avaliar([A("azelaico"), A("salicilico"), A("hialuronico")]).resultado, "sem_regra");
caso("geral: regra explícita pesa mais que par sem regra", R.avaliar([A("retinol"), A("glicolico"), A("azelaico")]).resultado, "horarios");
caso("todo resultado possível tem rótulo", ["ok", "sem_regra", "horarios", "nao"].every(k => R.ROTULOS[k]), true);
caso("motivo curto (até 280 caracteres) em toda combinação", R.COMBINACOES.filter(c => c.motivo.length > 280 || (c.sensivelMotivo || "").length > 280).map(c => c.id), []);

/* ===== Integridade da lista ===== */
console.log("\nIntegridade");
const classes = new Set([...R.ATIVOS.map(a => a.classe), ...Object.values(R.ESTADOS).map(e => e.classe)]);
caso("toda regra de combinação usa classes conhecidas", R.COMBINACOES.filter(c => !classes.has(c.a) || !classes.has(c.b)).map(c => c.id), []);
caso("ids de regras únicos", R.COMBINACOES.length + R.PERFIL.length, new Set([...R.COMBINACOES, ...R.PERFIL].map(r => r.id)).size);
caso("toda regra tem motivo", [...R.COMBINACOES, ...R.PERFIL].filter(r => !r.motivo).map(r => r.id), []);
caso("versão registrada no histórico", R.HISTORICO.some(h => h.versao === R.VERSAO), true);

console.log(`\n${total - falhas}/${total} casos passaram (regras v${R.VERSAO}).`);
process.exit(falhas ? 1 : 0);
