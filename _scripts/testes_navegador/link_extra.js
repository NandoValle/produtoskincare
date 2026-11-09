// Testes extras da feature 1. Uso: node link_extra.js http://127.0.0.1:8765 [pasta-para-pdf]
const { chromium } = require("playwright");
const BASE = process.argv[2] || "http://127.0.0.1:8765";
const PASTA = process.argv[3] || require("os").tmpdir();
const falhas = [];
function checar(nome, ok, extra) { console.log(`${ok ? "OK   " : "FALHA"} ${nome}${extra ? " — " + extra : ""}`); if (!ok) falhas.push(nome); }

async function nomesDosProdutos(page) {
  return page.$$eval("#painelManha .nome, #painelNoite .nome", els => els.map(e => e.textContent.trim()));
}

(async () => {
  const browser = await chromium.launch();

  // Gera um resultado novo para pegar o link
  const ctx = await browser.newContext({ permissions: ["clipboard-read", "clipboard-write"] });
  const p = await ctx.newPage();
  const errosP = []; p.on("pageerror", e => errosP.push(e.message));
  await p.goto(BASE + "/provador/");
  await p.click("#btnJaSei");
  await p.click('#chipsTipoJaSei .chip[data-tipo="seca"]');
  await p.click("#btnJaSeiContinuar");
  await p.click('#chipsPreocupacoes .chip[data-conc="manchas"]');
  await p.click("#btnPreocupacoesContinuar");
  await p.click("#btnVerResultado");
  await p.click("#btnPularSelfie");
  await p.waitForSelector("#telaResultado:not([hidden])");
  const enderecoBarra = p.url();
  await p.click("#btnCopiarLink"); await p.waitForTimeout(100);
  const copiado = await p.evaluate(() => navigator.clipboard.readText());
  checar("endereço da página já é o link do resultado", enderecoBarra === copiado, enderecoBarra);
  const nomesOriginais = await nomesDosProdutos(p);

  // 1) Catálogo muda depois: o link deve manter os mesmos produtos (preço pode mudar).
  {
    const c = await browser.newContext();
    await c.route("**/produtos.json", async route => {
      const r = await route.fetch(); const d = await r.json();
      // deixa todos os concorrentes muito mais baratos e melhor avaliados
      d.produtos.forEach(x => { if (!copiado.includes(x.id)) { x.preco = 1; x.avaliacao = 5; } });
      await route.fulfill({ response: r, json: d });
    });
    const b = await c.newPage();
    await b.goto(copiado);
    await b.waitForSelector("#telaResultado:not([hidden])");
    const nomes = await nomesDosProdutos(b);
    checar("link mantém os produtos mesmo com o catálogo mudando", JSON.stringify(nomes) === JSON.stringify(nomesOriginais), nomes.join(" | "));
    // sem o link fixado (v1), a escolha mudaria — confirma que o teste é sensível
    await b.goto(BASE + "/provador/?tipo=seca&conc=manchas");
    await b.waitForSelector("#telaResultado:not([hidden])");
    const nomesV1 = await nomesDosProdutos(b);
    checar("(controle) sem itens fixados a escolha muda com o catálogo", JSON.stringify(nomesV1) !== JSON.stringify(nomesOriginais));
    await c.close();
  }

  // 2) Link aberto em aba nova não entra no histórico de quem abre
  {
    const c = await browser.newContext();
    const b = await c.newPage();
    await b.goto(copiado);
    await b.waitForSelector("#telaResultado:not([hidden])");
    await b.waitForTimeout(300);
    const n = await b.evaluate(() => new Promise(res => {
      const r = indexedDB.open("provador-acompanhamento", 1);
      r.onupgradeneeded = () => r.result.createObjectStore("resultados", { keyPath: "id", autoIncrement: true });
      r.onsuccess = () => { const q = r.result.transaction("resultados").objectStore("resultados").count(); q.onsuccess = () => res(q.result); };
    }));
    checar("abrir link não grava no histórico", n === 0, `registros: ${n}`);
    checar("aviso de resultado salvo aparece", await b.isVisible("#avisoLink"));
    // Refazer limpa o endereço
    await b.click("#btnRefazer");
    checar("refazer volta o endereço para /provador/", new URL(b.url()).search === "", b.url());
    await c.close();
  }

  // 3) Parâmetros adulterados (XSS) e inválidos
  {
    const c = await browser.newContext();
    const b = await c.newPage();
    let dialogo = false; b.on("dialog", d => { dialogo = true; d.dismiss(); });
    const erros = []; b.on("pageerror", e => erros.push(e.message));
    await b.goto(BASE + "/provador/?v=2&tipo=oleosa&conc=" + encodeURIComponent('<img src=x onerror=alert(1)>,acne') + "&idade=" + encodeURIComponent("<b>x</b>") + "&itens=" + encodeURIComponent("<x>.y"));
    await b.waitForSelector("#telaResultado:not([hidden])");
    await b.waitForTimeout(300);
    const temImg = await b.$("#resumoTipo img[src=x]");
    checar("conc com HTML é descartado (sem XSS)", !dialogo && !temImg);
    checar("conc válido é mantido", (await b.textContent("#resumoTipo")).includes("Acne"));
    await b.goto(BASE + "/provador/?tipo=" + encodeURIComponent("<script>alert(1)</script>"));
    await b.waitForTimeout(500);
    checar("tipo inválido abre a tela inicial", await b.isVisible("#telaInicio"));
    await b.goto(BASE + "/provador/?tipo=seca");
    await b.waitForSelector("#telaResultado:not([hidden])");
    checar("link antigo (só ?tipo=) continua abrindo", true);
    checar("sem erros de JavaScript", !erros.length, erros.join("; "));
    await c.close();
  }

  // 4) Impressão / PDF: manhã e noite visíveis, com títulos, link e aviso
  {
    await p.emulateMedia({ media: "print" });
    const vis = await p.evaluate(() => {
      const d = s => getComputedStyle(document.querySelector(s)).display;
      const titulos = [...document.querySelectorAll("h3.so-impressao")].map(h => getComputedStyle(h).display !== "none" ? h.textContent : "");
      return { manha: d("#painelManha"), noite: d("#painelNoite"), titulos, rodape: document.querySelector("#rodapeImpressao").textContent, botoes: d(".botoes") };
    });
    checar("PDF: painel da manhã visível", vis.manha !== "none");
    checar("PDF: painel da noite visível", vis.noite !== "none");
    checar("PDF: títulos Manhã e Noite", vis.titulos.join("|").includes("Manhã") && vis.titulos.join("|").includes("Noite"), vis.titulos.join(" | "));
    checar("PDF: rodapé com o link do resultado", vis.rodape.includes(copiado), vis.rodape.slice(0, 80));
    checar("PDF: botões escondidos", vis.botoes === "none");
    const texto = await p.evaluate(() => document.querySelector("#telaResultado").innerText);
    checar("PDF: aviso de diagnóstico e afiliado", /não um diagnóstico médico/.test(texto) && /links de afiliado/.test(texto));
    await p.pdf({ path: PASTA + "/resultado-provador.pdf", format: "A4", printBackground: true });
    console.log("PDF gerado em", PASTA + "/resultado-provador.pdf");
  }
  checar("sem erros de JavaScript na aba original", !errosP.length, errosP.join("; "));

  await browser.close();
  console.log(falhas.length ? `\n${falhas.length} falha(s)` : "\nTodos os testes extras passaram.");
  process.exit(falhas.length ? 1 : 0);
})();
