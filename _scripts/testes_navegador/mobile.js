// Consertos mobile/visual (brief de 06/11/2026), em 390 px e no desktop. Uso: node mobile.js http://127.0.0.1:8765
const { chromium } = require("playwright");
const BASE = process.argv[2] || "http://127.0.0.1:8765";
const falhas = [];
function checar(nome, ok, extra) { console.log(`${ok ? "OK   " : "FALHA"} ${nome}${extra ? " — " + extra : ""}`); if (!ok) falhas.push(nome); }

(async () => {
  const browser = await chromium.launch();
  const erros = [];
  const nova = async (largura) => {
    const p = await browser.newPage({ viewport: { width: largura, height: 844 } });
    p.on("pageerror", e => erros.push(`${largura}px: ${e.message}`));
    return p;
  };
  const semRolagemLateral = p => p.evaluate(() => document.documentElement.scrollWidth <= innerWidth);

  // 1. Tabelas dos guias de pele: nada da coluna "Por quê" cortado em 390 px.
  const m = await nova(390);
  for (const tipo of ["oleosa", "seca", "mista", "normal"]) {
    await m.goto(`${BASE}/pele/${tipo}/`);
    const r = await m.evaluate(() => {
      const tds = [...document.querySelectorAll("table td")];
      const cortadas = tds.filter(td => td.getBoundingClientRect().right > innerWidth + 0.5 || td.scrollWidth > td.clientWidth + 1).length;
      const tabelas = [...document.querySelectorAll("table")].filter(t => t.scrollWidth > t.clientWidth + 1).length;
      const porque = tds.filter(td => td.dataset.label === "Por quê").length;
      return { cortadas, tabelas, porque };
    });
    checar(`guia ${tipo}: nenhuma célula cortada em 390 px`, r.cortadas === 0 && r.tabelas === 0, JSON.stringify(r));
    checar(`guia ${tipo}: coluna "Por quê" presente`, r.porque > 0);
    checar(`guia ${tipo}: sem rolagem lateral`, await semRolagemLateral(m));
  }

  // 2. Catálogo: busca e filtros reduzem a lista; estado vazio claro.
  for (const largura of [390, 1280]) {
    const p = await nova(largura);
    await p.goto(`${BASE}/produtos/`);
    const visiveis = () => p.evaluate(() => document.querySelectorAll("[data-pf-nome]:not([hidden])").length);
    const total = await visiveis();
    checar(`catálogo ${largura}px: filtros visíveis`, await p.isVisible("#pf-busca") && await p.isVisible("#pf-tipo") && await p.isVisible("#pf-preco"));
    await p.fill("#pf-busca", "cerave");
    const nBusca = await visiveis();
    checar(`catálogo ${largura}px: busca por nome reduz a lista`, nBusca > 0 && nBusca < total, `${nBusca} de ${total}`);
    await p.fill("#pf-busca", "");
    await p.selectOption("#pf-tipo", "seca");
    await p.selectOption("#pf-preco", "50");
    const nFiltro = await visiveis();
    const precosOk = await p.evaluate(() => [...document.querySelectorAll("[data-pf-nome]:not([hidden])")].every(li => +li.dataset.pfPreco <= 50));
    checar(`catálogo ${largura}px: tipo + faixa reduzem a lista`, nFiltro > 0 && nFiltro < total && precosOk, `${nFiltro} de ${total}`);
    await p.fill("#pf-busca", "nenhumprodutoassim");
    checar(`catálogo ${largura}px: estado vazio com mensagem`, (await visiveis()) === 0 && await p.isVisible("#pf-vazio") && /Nenhum produto/.test(await p.textContent("#pf-vazio")));
    await p.click("#pf-vazio .pf-limpar");
    checar(`catálogo ${largura}px: limpar filtros volta a lista toda`, (await visiveis()) === total && await p.isHidden("#pf-vazio"));
    checar(`catálogo ${largura}px: sem rolagem lateral`, await semRolagemLateral(p));
    await p.close();
  }

  // 3. Rodapé: acordeões fechados no celular, tudo aberto no desktop.
  await m.goto(`${BASE}/`);
  const rod = () => m.evaluate(() => ({
    altura: document.querySelector(".ps-rodape").getBoundingClientRect().height,
    botoes: [...document.querySelectorAll(".ps-rodape-toggle")].filter(b => b.offsetParent).length,
    abertas: [...document.querySelectorAll(".ps-rodape-grid > nav ul")].filter(u => u.offsetParent).length
  }));
  let r = await rod();
  checar("rodapé 390px: grupos viram acordeões fechados", r.botoes >= 5 && r.abertas === 0, JSON.stringify(r));
  checar("rodapé 390px: bem menor que 1600 px", r.altura < 900, `${Math.round(r.altura)} px`);
  await m.click(".ps-rodape-toggle >> text=Ferramentas");
  r = await rod();
  checar("rodapé 390px: tocar abre só aquele grupo", r.abertas === 1 && await m.isVisible(".ps-rodape a[href='/provador/']"));
  const d = await nova(1280);
  await d.goto(`${BASE}/`);
  const rd = await d.evaluate(() => ({
    botoes: [...document.querySelectorAll(".ps-rodape-toggle")].filter(b => b.offsetParent).length,
    abertas: [...document.querySelectorAll(".ps-rodape-grid > nav ul")].filter(u => u.offsetParent).length
  }));
  checar("rodapé desktop: todas as colunas abertas, sem botões", rd.botoes === 0 && rd.abertas >= 5, JSON.stringify(rd));

  // 6. Cards de tipo na home: o link fica numa linha.
  // O cartão novo tem min-height 44 px e borda em cima, então a altura não diz se o texto quebrou.
  // Cada trecho de texto deve ocupar uma linha só (mais de um retângulo = quebrou).
  const linhas = await m.evaluate(() => [...document.querySelectorAll(".ps-card-link")].map(e => {
    const w = document.createTreeWalker(e, NodeFilter.SHOW_TEXT); let max = 0, t;
    while ((t = w.nextNode())) { if (!t.textContent.trim()) continue; const r = document.createRange(); r.selectNodeContents(t); max = Math.max(max, [...r.getClientRects()].filter(x => x.width > 0).length); }
    return max;
  }));
  checar("home 390px: link dos cards em uma linha", linhas.length === 4 && linhas.every(n => n === 1), linhas.join(","));
  checar("home 390px: sem rolagem lateral", await semRolagemLateral(m));

  // 7. Header desktop: uma linha só, sem estourar.
  const hd = await d.evaluate(() => { const h = document.querySelector(".ps-header"); return { altura: h.getBoundingClientRect().height, cabe: h.scrollWidth <= h.clientWidth, fonte: parseFloat(getComputedStyle(document.querySelector(".ps-nav a")).fontSize) }; });
  checar("header desktop: uma linha, cabe na largura", hd.altura < 100 && hd.cabe, JSON.stringify(hd));
  checar("header desktop: menu com pelo menos 15 px", hd.fonte >= 15);

  // 4 e 5. Resultado do provador em 390 px: tabelas cabem e o botão de tema não flutua sobre o texto.
  await m.goto(`${BASE}/provador/`);
  await m.click("#btnJaSei");
  await m.click('#chipsTipoJaSei .chip[data-tipo="seca"]');
  await m.check("#chkSensivelJaSei");
  await m.click("#btnJaSeiContinuar");
  await m.click('#chipsPreocupacoes .chip[data-conc="manchas"]');
  await m.click("#btnPreocupacoesContinuar");
  await m.click("#btnVerResultado");
  await m.click("#btnPularSelfie");
  await m.waitForSelector("#telaResultado:not([hidden])");
  const tabs = await m.evaluate(() => [...document.querySelectorAll("#telaResultado .tabela-eixos, #telaResultado .tabela-comparacao")].filter(t => t.offsetParent).map(t => t.scrollWidth - t.clientWidth));
  checar("resultado 390px: tabela dos 4 eixos e comparação sem rolagem interna", tabs.length >= 1 && tabs.every(x => x <= 1), tabs.join(","));
  checar("resultado 390px: sem rolagem lateral", await semRolagemLateral(m));
  await m.evaluate(() => scrollTo(0, 900));
  const tema = await m.$eval("#btnTema", e => e.getBoundingClientRect().bottom);
  checar("provador 390px: botão de tema sai de cima do texto ao rolar", tema <= 0, `bottom=${Math.round(tema)}`);

  checar("sem erros de JavaScript", !erros.length, erros.join("; "));
  await browser.close();
  console.log(falhas.length ? `\n${falhas.length} falha(s)` : "\nTodos os testes de mobile/visual passaram.");
  process.exit(falhas.length ? 1 : 0);
})();
