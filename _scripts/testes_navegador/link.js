// Teste ponta a ponta do link do resultado (feature 1).
// Uso: node link.js http://127.0.0.1:8765 (ou _scripts/testes_navegador/rodar.sh)
// Para cada cenário: faz o quiz numa aba, copia o link, abre o link num contexto
// novo (equivale a aba anônima: sem localStorage, IndexedDB nem sessão) e compara.
const { chromium } = require("playwright");
const BASE = process.argv[2] || "http://127.0.0.1:8765";

const REGIOES = ["#resumoTipo", "#notasExtras", "#avisoSensivel", "#painelManha", "#painelNoite", "#rotinasProntas"];

async function capturar(page) {
  return page.evaluate((regioes) => {
    const out = {};
    for (const sel of regioes) {
      const el = document.querySelector(sel);
      if (!el) { out[sel] = "(ausente)"; continue; }
      if (el.hidden && !sel.startsWith("#painel")) { out[sel] = "(oculto)"; continue; }
      // textContent pega também o painel da noite, que fica oculto na aba "manhã".
      out[sel] = el.textContent.replace(/\s+/g, " ").trim();
    }
    return out;
  }, REGIOES);
}

async function rodarCenario(browser, c) {
  const ctxA = await browser.newContext({ permissions: ["clipboard-read", "clipboard-write"] });
  const a = await ctxA.newPage();
  const erros = [];
  a.on("pageerror", e => erros.push("A: " + e.message));
  await a.goto(BASE + "/provador/");
  await c.fazer(a);
  await a.waitForSelector("#telaResultado:not([hidden])");
  const telaA = await capturar(a);
  await a.click("#btnCopiarLink");
  await a.waitForTimeout(150);
  const link = await a.evaluate(() => navigator.clipboard.readText());

  const ctxB = await browser.newContext();
  const b = await ctxB.newPage();
  b.on("pageerror", e => erros.push("B: " + e.message));
  await b.goto(link);
  await b.waitForSelector("#telaResultado:not([hidden])", { timeout: 5000 }).catch(() => erros.push("B: resultado não abriu"));
  const telaB = await capturar(b);

  const difs = REGIOES.filter(r => telaA[r] !== telaB[r]);
  console.log(`\n=== ${c.nome} ===`);
  console.log("link:", link);
  if (erros.length) console.log("erros JS:", erros);
  if (!difs.length) console.log("OK: o conteúdo do link bate com a tela.");
  for (const r of difs) {
    // mostra o primeiro trecho diferente
    const x = telaA[r], y = telaB[r];
    let i = 0; while (i < x.length && x[i] === y[i]) i++;
    console.log(`DIFERENTE em ${r}:\n  tela: …${x.slice(Math.max(0, i - 60), i + 120)}\n  link: …${y.slice(Math.max(0, i - 60), i + 120)}`);
  }
  await ctxA.close(); await ctxB.close();
  return { nome: c.nome, ok: !difs.length && !erros.length, link, telaA };
}

async function quizCompleto(page, respostas) {
  await page.click("#btnComecar");
  for (const valor of respostas) {
    await page.check(`#areaPergunta input[value="${valor}"]`);
    await page.click("#btnAvancar");
  }
}

async function preferencias(page, { preco, rotina, idade, exp, gestante, iso }) {
  if (preco) await page.check(`input[name=preco][value="${preco}"]`);
  if (rotina) await page.check(`input[name=rotina][value="${rotina}"]`);
  if (idade) await page.check(`input[name=idade][value="${idade}"]`);
  if (exp) await page.check(`input[name=exp][value="${exp}"]`);
  if (gestante) await page.check("#chkGestante");
  if (iso) await page.check("#chkIsotretinoina");
  await page.click("#btnVerResultado");
  await page.click("#btnPularSelfie");
}

const CENARIOS = [
  {
    nome: "Quiz completo · mista · gestante · foco manchas e idade",
    fazer: async (p) => {
      // q1..q5, q6 (teste), q7..q10
      await quizCompleto(p, ["mista", "quase_nunca", "as_vezes", "seca", "mista", "mista", "nao", "nao", "nao", "outra"]);
      await p.click('#chipsPreocupacoes .chip[data-conc="manchas"]');
      await p.click('#chipsPreocupacoes .chip[data-conc="idade"]');
      await p.click("#btnPreocupacoesContinuar");
      await preferencias(p, { exp: "um", gestante: true });
    }
  },
  {
    nome: "Já sei · oleosa · sensível · foco idade · até R$ 50",
    fazer: async (p) => {
      await p.click("#btnJaSei");
      await p.click('#chipsTipoJaSei .chip[data-tipo="oleosa"]');
      await p.check("#chkSensivelJaSei");
      await p.click("#btnJaSeiContinuar");
      await p.click('#chipsPreocupacoes .chip[data-conc="idade"]');
      await p.click("#btnPreocupacoesContinuar");
      await preferencias(p, { preco: "ate50", idade: "30a44" });
    }
  }
];

(async () => {
  const browser = await chromium.launch();
  const res = [];
  for (const c of CENARIOS) res.push(await rodarCenario(browser, c));
  await browser.close();
  console.log("\nResumo:", res.map(r => `${r.ok ? "PASSOU" : "FALHOU"} – ${r.nome}`).join(" | "));
  process.exit(res.every(r => r.ok) ? 0 : 1);
})();
