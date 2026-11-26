// Página /ativos/ e fichas de ativos. Uso: node ativos.js http://127.0.0.1:8765 (ou rodar.sh)
//  - as três tarefas do topo levam ao lugar certo e as 11 fichas com fontes aparecem;
//  - "Você já tem este ativo em casa?" lê a Minha prateleira do aparelho (vazia, com e sem o
//    ativo), não vira HTML o nome digitado e fica oculto sem JavaScript;
//  - a home traz a mesma contagem de ativos da página.
const { chromium } = require("playwright");
const B = process.argv[2] || "http://127.0.0.1:8765";
const falhas = [];
const ok = (n, c, x) => { console.log((c ? "OK   " : "FALHA") + " " + n + (x ? " — " + x : "")); if (!c) falhas.push(n); };
(async () => {
  const b = await chromium.launch();
  const erros = [];
  async function ficha(url, itens) {
    const c = await b.newContext();
    const p = await c.newPage();
    p.on("pageerror", e => erros.push(e.message));
    await p.goto(B + "/ativos/");
    if (itens !== null) await p.evaluate(i => localStorage.setItem("ps-prateleira-v1", JSON.stringify({ itens: i })), itens);
    await p.goto(B + url);
    await p.waitForTimeout(700);
    const r = await p.evaluate(() => {
      const e = document.querySelector("[data-ritual]");
      return e ? { oculto: e.hidden, texto: e.textContent, html: e.innerHTML } : null;
    });
    await c.close();
    return r;
  }
  let r = await ficha("/ativos/bakuchiol/", null);
  ok("prateleira vazia: convida a montar", r && !r.oculto && /está vazia/.test(r.texto) && /prateleira\//.test(r.html));
  const itens = [
    { uid: "a", nome: "Sérum <img src=x onerror=alert(1)> teste", passo: "tratamento", periodo: ["noite"], texto: "bakuchiol, esqualano" },
    { uid: "b", nome: "CeraVe Gel", passo: "limpeza", periodo: ["manha", "noite"], texto: "ceramidas, niacinamida" }
  ];
  r = await ficha("/ativos/bakuchiol/", itens);
  ok("tem o ativo: diz Sim e lista o produto", r && !r.oculto && /^Você já tem este ativo em casa\?Sim\./.test(r.texto) && /tratamento, uso de noite/.test(r.texto), r && r.texto.slice(0, 160));
  ok("nome digitado não vira HTML", r && !/<img/.test(r.html));
  r = await ficha("/ativos/acido-glicolico/", itens);
  ok("não tem o ativo: Não encontramos", r && /Não encontramos\. Nenhum dos 2 produtos/.test(r.texto), r && r.texto.slice(0, 120));
  r = await ficha("/ingredientes/niacinamida/", itens);
  ok("ficha com fontes também compara", r && /Sim\./.test(r.texto) && /CeraVe Gel \(limpeza, uso de manhã e noite\)/.test(r.texto), r && r.texto.slice(0, 160));
  {
    const c = await b.newContext({ javaScriptEnabled: false });
    const p = await c.newPage();
    await p.goto(B + "/ativos/bakuchiol/");
    ok("sem JavaScript o item fica oculto", await p.$eval("[data-ritual]", e => e.hidden));
    await p.goto(B + "/ativos/");
    ok("sem JavaScript as tarefas ficam ocultas e as 11 fichas aparecem", (await p.$eval("#at-tarefas", e => e.hidden)) && (await p.$$(".at-fontes-lista a")).length === 11);
    await c.close();
  }
  {
    const p = await b.newPage();
    p.on("pageerror", e => erros.push(e.message));
    await p.goto(B + "/ativos/");
    await p.waitForTimeout(500);
    ok("três tarefas visíveis", (await p.$$("#at-tarefas a:visible")).length === 3);
    await p.click('[data-tarefa="objetivo"]');
    ok("objetivo: foco na busca", await p.evaluate(() => document.activeElement.id === "at-q"));
    await p.click('[data-tarefa="rotulo"]');
    ok("rótulo: abre o leitor e foca o campo", await p.evaluate(() => document.getElementById("at-rotulo").open && document.activeElement.id === "at-inci"));
    await p.click('[data-tarefa="junto"]');
    await p.waitForTimeout(300);
    ok("junto: vai ao mapa de combinações", p.url().endsWith("#mapa-combina"));
    const hrefs = await p.$$eval(".at-fontes-lista a", as => as.map(a => a.getAttribute("href")));
    let bons = 0;
    for (const h of hrefs) { const q = await p.request.get(B + h); if (q.ok()) bons++; }
    ok("links das 11 fichas abrem", bons === 11, hrefs.join(" "));
    await p.goto(B + "/");
    const t = await p.textContent("main");
    ok("home diz 127", t.includes("127") && !/88 ativos|88 fichas/.test(t));
  }
  ok("sem erros de JavaScript", !erros.length, erros.join("; "));
  await b.close();
  process.exit(falhas.length ? 1 : 0);
})();
