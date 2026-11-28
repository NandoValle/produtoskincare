// "Use o que você já tem": oferta só onde há lacuna. Uso: node tenho.js http://127.0.0.1:8765
const { chromium } = require("playwright");
const BASE = process.argv[2] || "http://127.0.0.1:8765";
const falhas = [];
function checar(nome, ok, extra) { console.log(`${ok ? "OK   " : "FALHA"} ${nome}${extra ? " — " + extra : ""}`); if (!ok) falhas.push(nome); }

(async () => {
  const browser = await chromium.launch();
  const erros = [];
  const p = await browser.newPage(); p.on("pageerror", e => erros.push(e.message));
  const passos = () => p.$$eval("#painelManha .passo", els => els.map(e => ({
    cat: e.querySelector(".cat").textContent.trim(), link: !!e.querySelector("a.link-produto"), preco: !!e.querySelector(".preco"),
    criterio: e.querySelectorAll(".criterio").length })));
  const jaTenho = r => r.filter(x => x.cat.includes("já tenho"));
  await p.goto(BASE + "/provador/?tipo=oleosa&conc=acne&preco=qualquer&rotina=5");
  await p.waitForSelector("#telaResultado:not([hidden])");

  let r = await passos();
  checar("sem resposta: os 4 passos aparecem com produto", r.length === 4 && r.every(x => x.preco));
  checar("todo produto traz critério e ressalva antes do link", r.every(x => x.criterio === 2));
  checar("sem resposta: os três blocos ficam escondidos", (await p.$$("#blocosTenho .tenho-bloco")).length === 0);

  await p.click('[data-tenho="limpeza"]'); await p.click('[data-tenho="hidratacao"]');
  r = await passos();
  checar("já tenho: limpeza e hidratação sem preço e sem link", jaTenho(r).length === 2 && jaTenho(r).every(x => !x.link && !x.preco));
  checar("pode esperar: tratamento sem oferta enquanto falta a base", r.some(x => x.cat.includes("Tratamento · pode esperar") && !x.link && !x.preco));
  checar("vale completar: só o protetor tem oferta", r.filter(x => x.preco).length === 1 && r.find(x => x.preco).cat.includes("Protetor"));
  checar("três blocos na tela", (await p.$$("#blocosTenho .tenho-bloco")).length === 3);
  checar("link do resultado guarda o que a pessoa tem", p.url().includes("tenho=limpeza%2Chidratacao"), p.url());

  await p.click('[data-tenho="protetor"]');
  r = await passos();
  checar("base completa: o tratamento vira lacuna, com oferta", r.some(x => x.cat.startsWith("Tratamento") && x.preco));

  await p.click('[data-tenho="tratamento"]');
  r = await passos();
  checar("tudo marcado: nenhuma oferta na rotina", r.every(x => !x.link && !x.preco));
  checar("tudo marcado: 'não há nada para comprar'", (await p.textContent("#blocosTenho")).includes("Não há nada para comprar agora"));
  checar("tudo marcado: sem carrinho e sem custo", (await p.textContent("#notasExtras")).includes("Nada para comprar agora") && !(await p.$('[data-produto="rotina-completa-amazon"]')));

  const url = p.url();
  await p.goto(url); await p.waitForSelector("#telaResultado:not([hidden])");
  checar("link reaberto mantém as marcações", (await p.$$("#chipsTenho .chip.on")).length === 4);

  checar("sem erros de JavaScript", erros.length === 0, erros.join(" | "));
  await browser.close();
  if (falhas.length) { console.log("\nFALHAS: " + falhas.join("; ")); process.exit(1); }
})();
