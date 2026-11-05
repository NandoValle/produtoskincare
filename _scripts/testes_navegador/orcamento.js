// Feature 2: orçamento + onde comprar. Uso: node orcamento.js http://127.0.0.1:8765
const { chromium } = require("playwright");
const BASE = process.argv[2] || "http://127.0.0.1:8765";
const falhas = [];
function checar(nome, ok, extra) { console.log(`${ok ? "OK   " : "FALHA"} ${nome}${extra ? " — " + extra : ""}`); if (!ok) falhas.push(nome); }
const TETO = { ate50: 50, ate100: 100, ate200: 200, qualquer: Infinity };

async function lerRotina(page) {
  return page.$$eval("#painelManha .passo, #painelNoite .passo", passos => passos.map(el => {
    const nome = el.querySelector(".nome"), preco = el.querySelector(".preco"), a = el.querySelector("a.link-produto");
    const m = preco && preco.textContent.match(/R\$\s*([\d.]+,\d{2})/);
    return {
      cat: el.querySelector(".cat").textContent.trim(),
      papel: (el.querySelector(".papel") || {}).textContent || "",
      nome: nome ? nome.textContent.trim() : null,
      preco: m ? parseFloat(m[1].replace(/\./g, "").replace(",", ".")) : null,
      faixaItem: preco ? (preco.textContent.match(/faixa ([^)]+)$/) || [])[1] || "" : "",
      href: a ? a.href : null, rel: a ? a.rel : null, alvo: a ? a.target : null,
      nota: (el.querySelector(".tipo-link") || {}).textContent || "",
      semNaFaixa: /O mais barato que encontramos/.test(el.textContent)
    };
  }));
}

(async () => {
  const browser = await chromium.launch();
  const erros = [];
  const ctx = await browser.newContext({ permissions: ["clipboard-read", "clipboard-write"] });
  const p = await ctx.newPage(); p.on("pageerror", e => erros.push(e.message));
  await p.goto(BASE + "/provador/");
  await p.click("#btnJaSei");
  await p.click('#chipsTipoJaSei .chip[data-tipo="oleosa"]');
  await p.click("#btnJaSeiContinuar");
  await p.click('#chipsPreocupacoes .chip[data-conc="acne"]');
  await p.click('#chipsPreocupacoes .chip[data-conc="manchas"]');
  await p.click("#btnPreocupacoesContinuar");
  await p.check('input[name=preco][value="ate100"]');
  await p.click("#btnVerResultado");
  await p.click("#btnPularSelfie");
  await p.waitForSelector("#telaResultado:not([hidden])");
  checar("faixa escolhida nas preferências vem marcada no resultado", await p.getAttribute('#chipsOrcamento [data-faixa="ate100"]', "aria-checked") === "true");

  const porFaixa = {};
  for (const f of ["ate50", "ate100", "ate200", "qualquer"]) {
    await p.click(`#chipsOrcamento [data-faixa="${f}"]`);
    await p.waitForFunction(fx => document.querySelector(`#chipsOrcamento [data-faixa="${fx}"]`)?.getAttribute("aria-checked") === "true", f);
    const r = await lerRotina(p);
    porFaixa[f] = r;
    const comProduto = r.filter(x => x.nome);
    console.log(`\n[${f}] ${comProduto.map(x => `${x.nome} (${x.preco})`).join(" | ")}`);
    if (r.some(x => x.semNaFaixa)) console.log(`   sem produto na faixa: ${r.filter(x => x.semNaFaixa).map(x => x.cat).join(", ")}`);
    checar(`[${f}] nenhum produto acima do teto`, comProduto.every(x => x.preco !== null && x.preco <= TETO[f]));
    checar(`[${f}] todo item mostra o papel na rotina`, r.every(x => x.papel.length > 10));
    checar(`[${f}] todo item com preço mostra a faixa do item`, comProduto.every(x => x.faixaItem));
    checar(`[${f}] endereço atualizado com a faixa`, new URL(p.url()).searchParams.get("preco") === f);
    for (const x of comProduto) {
      const u = new URL(x.href);
      const amazonAfiliado = /amazon\.com\.br$/.test(u.hostname) && u.searchParams.has("tag");
      if (!/^(www\.)?(amazon\.com\.br|shopee\.com\.br|lista\.mercadolivre\.com\.br|produto\.mercadolivre\.com\.br)$/.test(u.hostname) || u.protocol !== "https:" || x.alvo !== "_blank")
        checar(`[${f}] link válido: ${x.nome}`, false, x.href);
      if (amazonAfiliado !== /link de afiliado/.test(x.nota)) checar(`[${f}] rótulo de afiliado correto: ${x.nome}`, false, x.nota + " " + x.href);
      if (amazonAfiliado !== /sponsored/.test(x.rel)) checar(`[${f}] rel=sponsored só em afiliado: ${x.nome}`, false, x.rel);
    }
  }
  const nomes = f => JSON.stringify(porFaixa[f].map(x => x.nome));
  checar("mudar a faixa muda a lista (até R$ 50 × sem limite)", nomes("ate50") !== nomes("qualquer"));
  const cheios = f => porFaixa[f].filter(x => x.nome).length;
  checar("subir o teto nunca tira produto que cabia (passos preenchidos não diminuem)", cheios("ate50") <= cheios("ate100") && cheios("ate100") <= cheios("ate200") && cheios("ate200") <= cheios("qualquer"),
    ["ate50", "ate100", "ate200", "qualquer"].map(f => f + ":" + cheios(f)).join(" "));
  checar("passo sem produto na faixa mostra o mais barato como referência", porFaixa.ate50.some(x => x.semNaFaixa));

  // Depois de trocar a faixa, o link copiado reabre a mesma lista (feature 1 continua valendo)
  await p.click('#chipsOrcamento [data-faixa="ate50"]');
  await p.waitForTimeout(100);
  await p.click("#btnCopiarLink"); await p.waitForTimeout(100);
  const link = await p.evaluate(() => navigator.clipboard.readText());
  const b = await (await browser.newContext()).newPage(); b.on("pageerror", e => erros.push(e.message));
  await b.goto(link);
  await b.waitForSelector("#telaResultado:not([hidden])");
  checar("link depois de trocar a faixa reabre a mesma lista", JSON.stringify(await lerRotina(b)) === JSON.stringify(await lerRotina(p)));

  // Link antigo com a faixa "economico" (até R$ 60) abre na faixa nova mais próxima
  await b.goto(BASE + "/provador/?tipo=oleosa&conc=acne&preco=economico");
  await b.waitForSelector("#telaResultado:not([hidden])");
  checar("link antigo preco=economico abre em 'Até R$ 50'", await b.getAttribute('#chipsOrcamento [data-faixa="ate50"]', "aria-checked") === "true");

  checar("sem erros de JavaScript", !erros.length, erros.join("; "));
  await browser.close();
  console.log(falhas.length ? `\n${falhas.length} falha(s)` : "\nTodos os testes de orçamento passaram.");
  process.exit(falhas.length ? 1 : 0);
})();
