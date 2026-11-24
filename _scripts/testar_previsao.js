// Testes das regras da Previsão da pele (/previsao-pele.js). Uso: node _scripts/testar_previsao.js
"use strict";
const assert = require("assert");
const path = require("path");
const P = require(path.join(__dirname, "..", "previsao-pele.js"));
const catalogo = require(path.join(__dirname, "..", "produtos.json")).produtos;

let n = 0;
function teste(nome, fn) { fn(); n++; }
const por = id => catalogo.find(p => p.id === id);

teste("o interruptor da consulta ao vivo começa desligado", () => assert.strictEqual(P.CONFIG.ativo, false));

teste("faixas do UV iguais às da tabela da página de clima", () => {
  assert.strictEqual(P.nivelDoUV(2.9).id, "baixo");
  assert.strictEqual(P.nivelDoUV(3).id, "moderado");
  assert.strictEqual(P.nivelDoUV(6).id, "alto");
  assert.strictEqual(P.nivelDoUV(8).id, "muito-alto");
  assert.strictEqual(P.nivelDoUV(11).id, "extremo");
  assert.strictEqual(P.nivelDoUV(null), null);
});

teste("umidade: abaixo de 40 é seco, acima de 75 é úmido", () => {
  assert.strictEqual(P.arDaUmidade(32), "seco");
  assert.strictEqual(P.arDaUmidade(40), "medio");
  assert.strictEqual(P.arDaUmidade(76), "umido");
});

teste("leitura fala em 'pode pedir', nunca em 'precisa'", () => {
  const l = P.leitura({ uv: 11, ar: "seco", suor: false, uvExato: 11, umidade: 32 });
  assert.ok(/pode pedir/.test(l.frase));
  assert.ok(!/precisa/.test(l.frase));
  assert.strictEqual(l.condicoes, "UV extremo (11), ar seco (32%)");
  assert.deepStrictEqual(l.pede, ["proteção solar", "hidratação reforçada"]);
});

teste("dia sem nada de especial não inventa necessidade", () => {
  const l = P.leitura({ uv: 1, ar: "medio", suor: false });
  assert.deepStrictEqual(l.pede, []);
});

teste("rotina: protetor sempre na manhã; reaplicação a cada 2h com UV 6 ou mais", () => {
  [null, 1, 4, 6.5, 9, 11].forEach(uv => {
    const r = P.rotinaDeHoje({ uv, ar: "medio", suor: false }, "");
    assert.strictEqual(r.manha[r.manha.length - 1].passo, "Protetor solar");
    assert.strictEqual(r.durante.some(t => /a cada 2 horas/.test(t)), uv != null && uv >= 6);
  });
  assert.ok(P.rotinaDeHoje({ uv: 1, ar: "medio", suor: true }, "").durante.some(t => /suar/.test(t)));
});

teste("nota fica entre 0 e 100 e os motivos somam a nota", () => {
  const conds = [{ uv: null, ar: "medio" }, { uv: 1, ar: "seco" }, { uv: 11, ar: "umido" }, { uv: 9, ar: "seco", suor: true }];
  conds.forEach(c => ["", "oleosa", "seca", "sensivel"].forEach(pele => catalogo.forEach(p => {
    const r = P.pontuar(p, c, pele);
    assert.ok(r.nota >= 0 && r.nota <= 100);
    const soma = 50 + r.motivos.reduce((a, m) => a + m.pontos, 0);
    assert.strictEqual(r.nota, Math.max(0, Math.min(100, soma)));
  })));
});

teste("ar seco favorece creme; ar úmido favorece gel", () => {
  const creme = por("cetaphil-creme-hidratante"), gel = por("neutrogena-hydro-boost");
  assert.ok(P.pontuar(creme, { uv: 4, ar: "seco" }, "").nota > P.pontuar(gel, { uv: 4, ar: "seco" }, "").nota);
  assert.ok(P.pontuar(gel, { uv: 4, ar: "umido" }, "").nota > P.pontuar(creme, { uv: 4, ar: "umido" }, "").nota);
});

teste("produto que o catálogo manda evitar para a pele cai para o fim", () => {
  const ord = P.ordenar(catalogo, { uv: 9, ar: "seco" }, "seca");
  const evitar = ord.filter(x => (x.produto.evitar || []).includes("seca"));
  assert.ok(evitar.length > 0);
  evitar.forEach(x => assert.ok(x.nota <= 50, x.produto.id + " " + x.nota));
  P.melhorPorPasso(ord).forEach(m => assert.ok(!(m.item.produto.evitar || []).includes("seca")));
});

teste("um melhor por passo, nos quatro passos", () => {
  const m = P.melhorPorPasso(P.ordenar(catalogo, { uv: 9, ar: "umido" }, "oleosa"));
  assert.deepStrictEqual(m.map(x => x.item.produto.passo), ["limpeza", "tratamento", "hidratacao", "protetor"]);
});

teste("passo sem motivo no dia não ganha sugestão", () => {
  const m = P.melhorPorPasso(P.ordenar(catalogo, { uv: 4, ar: "medio" }, ""));
  assert.ok(m.length > 0 && m.every(x => x.item.nota > 50));
  assert.ok(!m.some(x => x.item.produto.passo === "tratamento"));
});

teste("link de busca não conta como oferta verificada", () => {
  assert.strictEqual(P.ehBusca("https://www.amazon.com.br/s?k=gel"), true);
  assert.strictEqual(P.ehBusca("https://lista.mercadolivre.com.br/gel"), true);
  assert.strictEqual(P.ehBusca("https://s.shopee.com.br/an_redir?origin_link=https%3A%2F%2Fshopee.com.br%2Fsearch%3Fkeyword%3Dgel"), true);
  assert.strictEqual(P.ehBusca("https://www.amazon.com.br/dp/B07XP6N3BC?tag=x"), false);
});

teste("resposta do serviço de previsão vira condições", () => {
  const c = P.condicoesDaPrevisao({
    current: { time: "2026-11-24T10:15", temperature_2m: 31.2, relative_humidity_2m: 32 },
    hourly: { time: ["2026-11-24T08:00", "2026-11-24T09:00", "2026-11-24T10:00", "2026-11-24T16:00", "2026-11-24T17:00"], uv_index: [1, 3.2, 7, 4, 2] },
    daily: { uv_index_max: [11.4] }
  });
  assert.strictEqual(c.uv, 11.4); assert.strictEqual(c.uvAgora, 7); assert.strictEqual(c.ar, "seco");
  assert.strictEqual(c.janela, "9h e 17h"); assert.strictEqual(c.suor, true);
});

console.log("ok: " + n + " testes da previsão da pele");
