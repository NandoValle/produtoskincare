/* Testes da comparação de rótulos (/rotulos.js). Uso: node _scripts/testar_rotulos.js */
const assert = require("assert");
const R = require("../rotulos.js");

const A = "Ingredientes: AQUA / WATER, GLYCERIN, NIACINAMIDE, 1,2-HEXANEDIOL, CETEARYL ALCOHOL, DIMETHICONE, PHENOXYETHANOL, SODIUM HYALURONATE, TOCOPHEROL, CITRIC ACID.";
let c;

// mesma lista, escrita de outro jeito (caixa, barra, ponto final)
c = R.comparar(A, "aqua, Glycerin, Niacinamide, 1,2-Hexanediol, Cetearyl Alcohol, Dimethicone, Phenoxyethanol, Sodium Hyaluronate, Tocopherol, Citric Acid");
assert.strictEqual(c.mesmaLista, true); assert.strictEqual(c.totalA, 10); assert.strictEqual(c.moveu.length, 0);

// vírgula dentro do nome não parte o ingrediente
assert.ok(R.listar(A).some(i => i.nome === "1,2-HEXANEDIOL"));

// ingrediente que entrou e ingrediente que saiu
c = R.comparar(A, "AQUA, GLYCERIN, NIACINAMIDE, 1,2-HEXANEDIOL, CETEARYL ALCOHOL, PHENOXYETHANOL, SODIUM HYALURONATE, TOCOPHEROL, CITRIC ACID, PARFUM");
assert.deepStrictEqual(c.saiu.map(x => x.nome), ["DIMETHICONE"]);
assert.deepStrictEqual(c.entrou.map(x => x.nome), ["PARFUM"]);
assert.strictEqual(c.mesmaLista, false);

// erro de leitura por foto: vira "parecido" (a conferir), não entra como troca nem como igual
c = R.comparar(A, "AQUA, GLYCERIN, NIACINAMIDE, 1,2-HEXANEDIOL, CETEARYL ALCOHOL, DIMETHIC0NE, PHENOXYETHAN0L, SODIUM HYALURONATE, TOCOPHEROL, CITRIC ACID");
assert.strictEqual(c.saiu.length, 0); assert.strictEqual(c.entrou.length, 0); assert.strictEqual(c.parecidos.length, 2); assert.strictEqual(c.mesmaLista, false); assert.strictEqual(c.soConferir, true);

// nome próximo de verdade também cai em "a conferir", nunca em "mesma lista"
c = R.comparar("AQUA, GLYCERIN, METHYLPARABEN, PARFUM", "AQUA, GLYCERIN, ETHYLPARABEN, PARFUM");
assert.strictEqual(c.mesmaLista, false); assert.strictEqual(c.parecidos.length, 1);

// nomes diferentes de verdade: um sai, outro entra
c = R.comparar("AQUA, GLYCERIN, UREA, PARFUM", "AQUA, GLYCERIN, SQUALANE, PARFUM");
assert.deepStrictEqual(c.saiu.map(x => x.nome), ["UREA"]); assert.deepStrictEqual(c.entrou.map(x => x.nome), ["SQUALANE"]);

// mudança de posição
c = R.comparar(A, "AQUA, GLYCERIN, TOCOPHEROL, NIACINAMIDE, 1,2-HEXANEDIOL, CETEARYL ALCOHOL, DIMETHICONE, PHENOXYETHANOL, SODIUM HYALURONATE, CITRIC ACID");
assert.deepStrictEqual(c.moveu.map(x => x.nome), ["TOCOPHEROL"]); assert.strictEqual(c.mesmaLista, true);

// lista curta demais não é comparável
assert.strictEqual(R.comparar("AQUA", A).comparavel, false);

console.log("ok rotulos");
