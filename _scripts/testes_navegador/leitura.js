// Leitura confortável e caminhos de "rever a rotina" (brief de 24/11/2026).
// Testa o que não pode depender de cor, animação, foto nem mouse:
//   - fonte do navegador em 32 px (200%) em telas de 320 e 390 px: nada cortado, sem rolagem lateral;
//   - quiz do começo ao resultado só com o teclado, com imagens bloqueadas e animação reduzida;
//   - estado dos botões exposto ao leitor de tela (aria-pressed / aria-checked / aria-selected);
//   - "Rever minha rotina" e "Algo não bate?" das fichas, pelo teclado e sem JavaScript.
// Uso: node leitura.js http://127.0.0.1:8765
const { chromium } = require("playwright");
const BASE = process.argv[2] || "http://127.0.0.1:8765";
const falhas = [];
function checar(nome, ok, extra) { console.log(`${ok ? "OK   " : "FALHA"} ${nome}${extra ? " — " + extra : ""}`); if (!ok) falhas.push(nome); }

// Elementos de texto que passam da largura da tela ou têm o texto cortado pela própria caixa.
const cortes = p => p.evaluate(() => {
  const ruins = [];
  if (document.documentElement.scrollWidth > innerWidth + 1) ruins.push("rolagem lateral: " + document.documentElement.scrollWidth + " > " + innerWidth);
  for (const el of document.querySelectorAll("main h1, main h2, main h3, main p, main li, main a, main button, main label, main legend, main summary, main dt, main dd, main td, main th")) {
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) continue;
    const cs = getComputedStyle(el);
    if (cs.visibility === "hidden") continue;
    let rolavel = false;
    for (let a = el.parentElement; a && a !== document.body; a = a.parentElement) {
      const o = getComputedStyle(a).overflowX;
      if (o === "auto" || o === "scroll") { rolavel = true; break; }
    }
    if (rolavel) continue; // faixa que rola de propósito (tabela larga, trilho)
    const rotulo = el.tagName + ": " + (el.textContent || "").trim().slice(0, 40);
    if (r.right > innerWidth + 1 || r.left < -1) ruins.push("fora da tela — " + rotulo);
    else if (cs.overflow !== "visible" && (el.scrollWidth > el.clientWidth + 1) && cs.textOverflow !== "ellipsis") ruins.push("texto cortado — " + rotulo);
  }
  return ruins.slice(0, 6);
});

(async () => {
  const erros = [];
  // Navegador com a fonte padrão em 32 px: é o que "fonte ampliada" faz no desktop e em vários celulares.
  const grande = await chromium.launch({ args: ["--blink-settings=defaultFontSize=32,minimumFontSize=0"] });
  const normal = await chromium.launch();
  const pagina = async (browser, largura, opcoes = {}) => {
    const ctx = await browser.newContext({ viewport: { width: largura, height: 800 }, reducedMotion: "reduce", ...opcoes });
    const p = await ctx.newPage();
    p.on("pageerror", e => erros.push(e.message));
    return p;
  };

  // 0. A fonte ampliada chegou mesmo à página.
  {
    const p = await pagina(grande, 390);
    await p.goto(`${BASE}/ferramentas/rever-rotina/`);
    const px = await p.evaluate(() => parseFloat(getComputedStyle(document.querySelector("main p")).fontSize));
    checar("fonte ampliada: texto do corpo com 30 px ou mais", px >= 30, px + " px");
    await p.close();
  }

  // 1. Fonte em 200%: páginas-chave sem corte nem rolagem lateral, em 320 e 390 px.
  const paginas = ["/", "/provador/", "/ferramentas/rever-rotina/", "/produtos/cerave-gel-limpeza/", "/produtos/", "/blog/rotina-de-skincare-para-iniciantes/", "/pele/oleosa/"];
  for (const largura of [320, 390]) {
    const p = await pagina(grande, largura);
    for (const url of paginas) {
      await p.goto(BASE + url);
      await p.waitForTimeout(150);
      const r = await cortes(p);
      checar(`fonte 200% em ${largura}px: ${url}`, r.length === 0, r.join(" | "));
    }
    await p.close();
  }

  // 2. Quiz inteiro só com o teclado, fonte 200%, 390 px, imagens bloqueadas, animação reduzida.
  {
    const p = await pagina(grande, 390);
    await p.route(/\.(png|jpe?g|webp|avif|gif|svg)(\?|$)/, r => r.abort());
    await p.goto(`${BASE}/provador/`);
    const foco = () => p.evaluate(() => { const e = document.activeElement; return e ? (e.id || e.name || e.tagName) : ""; });
    const irPara = async (seletor, limite = 60) => {
      for (let i = 0; i < limite; i++) {
        if (await p.evaluate(s => document.activeElement && document.activeElement.matches(s), seletor)) return true;
        await p.keyboard.press("Tab");
      }
      return false;
    };
    checar("quiz: chego ao botão de começar pelo teclado", await irPara("#btnComecar"));
    await p.keyboard.press("Enter");
    await p.waitForSelector("#telaQuiz:not([hidden])");
    let perguntas = 0, semCorte = true, detalhe = "";
    while (await p.isVisible("#telaQuiz") && perguntas < 20) {
      const anterior = await p.textContent("#contadorPergunta");
      const temLegenda = await p.evaluate(() => !!document.querySelector("#areaPergunta fieldset legend"));
      if (!temLegenda) { semCorte = false; detalhe = "pergunta sem legend"; }
      if (!(await irPara("#areaPergunta input"))) { semCorte = false; detalhe = "não alcancei as opções"; break; }
      await p.keyboard.press("Space");
      const r = await cortes(p);
      if (r.length) { semCorte = false; detalhe = r.join(" | "); }
      if (!(await irPara("#btnAvancar:not([disabled])"))) { semCorte = false; detalhe = "Continuar não habilitou"; break; }
      await p.keyboard.press("Enter");
      perguntas++;
      await p.waitForFunction(a => document.getElementById("telaQuiz").hidden || document.getElementById("contadorPergunta").textContent !== a, anterior);
    }
    checar("quiz: todas as perguntas respondidas só com o teclado", perguntas >= 10 && !(await p.isVisible("#telaQuiz")), perguntas + " perguntas");
    checar("quiz: perguntas sem corte em 200% e com legenda", semCorte, detalhe);

    // Preocupações: chips dizem se estão marcados.
    await p.waitForSelector("#telaPreocupacoes:not([hidden])");
    await irPara('#chipsPreocupacoes .chip[data-conc="acne"]');
    await p.keyboard.press("Enter");
    const chip = await p.evaluate(() => {
      const c = document.querySelector('#chipsPreocupacoes .chip[data-conc="acne"]');
      return { pressed: c.getAttribute("aria-pressed"), marca: getComputedStyle(c, "::before").content };
    });
    checar("preocupações: chip marcado expõe aria-pressed", chip.pressed === "true");
    checar("preocupações: chip marcado tem sinal além da cor", /✓/.test(chip.marca), chip.marca);
    checar("preocupações: sem corte em 200%", (await cortes(p)).length === 0, (await cortes(p)).join(" | "));
    await irPara("#btnPreocupacoesContinuar");
    await p.keyboard.press("Enter");

    // Preferências e selfie: seguir pelo teclado até o resultado.
    await p.waitForSelector("#telaPreferencias:not([hidden])");
    checar("preferências: sem corte em 200%", (await cortes(p)).length === 0, (await cortes(p)).join(" | "));
    const btnPref = await p.evaluate(() => [...document.querySelectorAll("#telaPreferencias .botoes .btn:not(.sec)")].map(b => b.id)[0]);
    await irPara("#" + btnPref, 80);
    await p.keyboard.press("Enter");
    if (await p.isVisible("#btnPularSelfie")) {
      checar("selfie (opcional): sem corte em 200%", (await cortes(p)).length === 0, (await cortes(p)).join(" | "));
      await irPara("#btnPularSelfie", 80);
      await p.keyboard.press("Enter");
    }
    await p.waitForSelector("#telaResultado:not([hidden])");
    checar("resultado: cheguei só com o teclado (foco em " + (await foco()) + ")", true);
    const res = await p.evaluate(() => ({
      tipo: document.getElementById("resumoTipo").textContent.trim().length,
      passos: document.querySelectorAll("#painelManha a[href], #painelManha h3, #painelManha h4, #painelManha strong").length,
      texto: document.getElementById("painelManha").textContent.trim().length,
      imgsSemAlt: [...document.querySelectorAll("#telaResultado img")].filter(i => !i.hasAttribute("alt")).length,
      abas: [...document.querySelectorAll(".rotina-tabs [role=tab]")].map(t => t.getAttribute("aria-selected")).join(","),
      orc: [...document.querySelectorAll("#chipsOrcamento [role=radio]")].filter(c => c.getAttribute("aria-checked") === "true").length,
    }));
    checar("resultado: tipo de pele e rotina escritos em texto, sem imagem", res.tipo > 10 && res.texto > 100 && res.passos > 0, JSON.stringify(res));
    checar("resultado: nenhuma imagem sem texto alternativo", res.imgsSemAlt === 0);
    checar("resultado: abas manhã/noite e orçamento dizem o estado", res.abas === "true,false" && res.orc === 1, JSON.stringify(res));
    checar("resultado: sem corte em 200%", (await cortes(p)).length === 0, (await cortes(p)).join(" | "));
    await p.focus("#tabNoite");
    await p.keyboard.press("Enter");
    checar("resultado: aba Noite abre pelo teclado", await p.isVisible("#painelNoite") && (await p.getAttribute("#tabNoite", "aria-selected")) === "true");
    checar("resultado: noite sem corte em 200%", (await cortes(p)).length === 0, (await cortes(p)).join(" | "));
    await p.close();
  }

  // 3. Rever minha rotina: três caminhos pelo teclado; versão sem JavaScript continua útil.
  {
    const p = await pagina(grande, 390);
    await p.goto(`${BASE}/ferramentas/rever-rotina/`);
    const marcar = async sel => { await p.focus(sel); await p.keyboard.press("Space"); };
    await marcar('input[name="rr-passos"][value="limpeza"]');
    await marcar('input[name="rr-passos"][value="hidratante"]');
    await marcar('input[name="rr-passos"][value="tonico"]');
    await marcar('input[name="rr-passos"][value="serum2"]');
    await p.focus("#rr-form-passos button[type=submit]");
    await p.keyboard.press("Enter");
    const t1 = await p.textContent("#rr-saida-passos");
    checar("rever/passos: rotina mínima escrita e foco no resultado", /De 5 produtos para 3/.test(t1) && /Espera na prateleira/.test(t1) && /não marcou: protetor solar/.test(t1) &&
      await p.evaluate(() => document.activeElement.id === "rr-saida-passos"), t1.slice(0, 80));
    checar("rever/passos: resultado não traz link de loja nem de produto", await p.evaluate(() => ![...document.querySelectorAll("#rr-saida-passos a")].some(a => /produtos\/|amazon|shopee|mercadolivre|provador/.test(a.href))));
    await marcar('input[name="rr-peso"][value="um-caro"]');
    await marcar('input[name="rr-cara"][value="protetor"]');
    await marcar('input[name="rr-cara"][value="olhos"]');
    await p.focus("#rr-form-cara button[type=submit]");
    await p.keyboard.press("Enter");
    const t2 = await p.textContent("#rr-saida-cara");
    checar("rever/cara: onde cortar e onde não cortar", /Onde cortar primeiro/.test(t2) && /Creme para a área dos olhos/.test(t2) && /Onde não cortar/.test(t2) && /custo por dia/.test(t2));
    await marcar('input[name="rr-sinal"][value="ardor"]');
    await marcar('input[name="rr-tempo"][value="semanas"]');
    await p.focus("#rr-form-desc button[type=submit]");
    await p.keyboard.press("Enter");
    const t3 = await p.textContent("#rr-saida-desc");
    checar("rever/desconforto: orienta parar, voltar ao básico e ir ao dermatologista, sem diagnosticar", /Pare o produto novo/.test(t3) && /dermatologista/.test(t3) && /não sabe dizer/.test(t3));
    checar("rever/desconforto: nenhum link de compra", await p.evaluate(() => ![...document.querySelectorAll("#desconforto a")].some(a => /produtos\/|amazon|shopee|mercadolivre|equivalente|provador/.test(a.href))));
    await marcar('input[name="rr-sinal"][value="grave"]');
    await p.focus("#rr-form-desc button[type=submit]");
    await p.keyboard.press("Enter");
    const t4 = await p.textContent("#rr-saida-desc");
    checar("rever/desconforto: sinal de alerta manda a atendimento médico e nada mais", /Procure atendimento médico agora/.test(t4) && /192/.test(t4) && !/Fique no básico/.test(t4));
    checar("rever: sem corte em 200% com os resultados abertos", (await cortes(p)).length === 0, (await cortes(p)).join(" | "));
    await p.close();

    const semJs = await pagina(normal, 390, { javaScriptEnabled: false });
    await semJs.goto(`${BASE}/ferramentas/rever-rotina/`);
    const s = await semJs.evaluate(() => ({
      forms: [...document.querySelectorAll(".rr-form")].filter(f => f.getBoundingClientRect().height > 0).length,
      resumos: [...document.querySelectorAll("main h3")].filter(h => /em resumo/.test(h.textContent) && h.getBoundingClientRect().height > 0).length,
      alerta: document.querySelector("#desconforto .ft-nao").getBoundingClientRect().height > 0,
    }));
    checar("rever sem JavaScript: formulários escondidos, três resumos e alerta visíveis", s.forms === 0 && s.resumos === 3 && s.alerta, JSON.stringify(s));
    await semJs.close();

    const home = await pagina(normal, 390);
    await home.goto(`${BASE}/`);
    const links = await home.evaluate(() => [...document.querySelectorAll("#rever a[data-carta]")].map(a => a.getAttribute("href")));
    checar("home: bloco de rever a rotina com os três caminhos", links.length === 3 && links.every(h => h.startsWith("/ferramentas/rever-rotina/")), links.join(" "));
    const mesmoPeso = await home.evaluate(() => {
      const a = document.querySelector("#comecar li a").getBoundingClientRect(), b = document.querySelector("#rever li a").getBoundingClientRect();
      return Math.abs(a.width - b.width) < 2 && b.height >= 44;
    });
    checar("home: caminhos de rever com o mesmo tamanho dos de começar", mesmoPeso);
    await home.click('#rever a[data-carta="rever-desconforto"]');
    await home.waitForURL(/rever-rotina/);
    checar("home → desconforto: abre na seção certa", await home.evaluate(() => document.getElementById("desconforto").getBoundingClientRect().top < innerHeight / 2));
    await home.close();
  }

  // 4. Ficha: o que foi conferido e "Algo não bate?".
  {
    const p = await pagina(grande, 390);
    await p.goto(`${BASE}/produtos/cerave-gel-limpeza/`);
    const f = await p.evaluate(() => ({
      itens: [...document.querySelectorAll(".pd-conf dt")].map(d => d.textContent).join(","),
      datas: [...document.querySelectorAll(".pd-conf .pd-quando")].filter(q => /\d{2}\/\d{2}\/\d{4}/.test(q.textContent)).length,
      ressalva: /Não são revisão científica/.test(document.getElementById("conferido").parentElement.textContent),
      revisado: /revisad[oa] (por|cientificamente)|revisão científica em/i.test(document.querySelector("main").textContent),
    }));
    checar("ficha: preço, embalagem, fórmula e link com data", f.itens === "Preço,Nota na loja,Embalagem,Fórmula,Link" && f.datas === 5, JSON.stringify(f));
    checar("ficha: conferência não é apresentada como revisão científica", f.ressalva && !f.revisado);
    const selo = await p.evaluate(() => { const b = document.querySelector('.ps-precos[data-precos-id="cerave-gel-limpeza"]'); return b ? { dentro: !!b.closest("main article"), texto: b.textContent } : null; });
    checar("ficha: selo de preço presente, dentro do conteúdo e com o widget carregado", !!selo && selo.dentro && /R\$ 96,90/.test(selo.texto) && /Avise-me se cair/.test(selo.texto), JSON.stringify(selo).slice(0, 120));
    await p.focus("#algo-nao-bate summary");
    await p.keyboard.press("Enter");
    checar("ficha: 'Algo não bate?' abre pelo teclado", await p.isVisible("#algo-nao-bate form"));
    const opcoes = await p.evaluate(() => [...document.querySelectorAll('#algo-nao-bate input[name="bate"]')].map(i => i.value).join("|"));
    checar("ficha: opções fórmula, embalagem, preço e link", /Fórmula.*Embalagem.*Preço.*Link/.test(opcoes), opcoes);
    checar("ficha: sem corte em 200% com o formulário aberto", (await cortes(p)).length === 0, (await cortes(p)).join(" | "));
    await p.evaluate(() => { window.__destino = ""; document.querySelector("[data-pd-bate]").addEventListener("submit", () => {}, true); });
    await p.focus('#algo-nao-bate input[value="Preço"]');
    await p.keyboard.press("Space");
    await p.fill("#pd-bate-msg", "Na loja está R$ 89,90");
    await p.focus("#algo-nao-bate button[type=submit]");
    await p.keyboard.press("Enter");
    checar("ficha: envio avisa que a mensagem foi montada", /Mensagem montada/.test(await p.textContent("[data-pd-bate-aviso]")));
    await p.close();

    const semJs = await pagina(normal, 390, { javaScriptEnabled: false });
    await semJs.goto(`${BASE}/produtos/cerave-gel-limpeza/`);
    await semJs.click("#algo-nao-bate summary");
    const mail = await semJs.getAttribute('#algo-nao-bate a[href^="mailto:"]', "href");
    checar("ficha sem JavaScript: selo de preço estático com preço e data", /histórico em construção[\s\S]*R\$ 96,90[\s\S]*conferido em \d{2}\/\d{2}\/\d{4}/.test(await semJs.textContent(".ps-precos")));
    checar("ficha sem JavaScript: resta o e-mail com assunto pronto, sem formulário quebrado", /subject=Algo/.test(mail) && !(await semJs.isVisible("#algo-nao-bate form")), mail);
    await semJs.close();
  }

  // 5. Modo leitura: botão com estado, letra maior, escolha lembrada, sem corte no celular.
  {
    const p = await pagina(normal, 390);
    await p.goto(`${BASE}/blog/rotina-de-skincare-para-iniciantes/`);
    const tamanho = () => p.evaluate(() => parseFloat(getComputedStyle(document.querySelector("main.ig article p")).fontSize));
    const antes = await tamanho();
    await p.focus(".ps-leitura-btn");
    await p.keyboard.press("Enter");
    const depois = await tamanho();
    checar("modo leitura: liga pelo teclado e aumenta a letra", depois > antes * 1.15 && (await p.getAttribute(".ps-leitura-btn", "aria-pressed")) === "true", `${antes} → ${depois} px`);
    checar("modo leitura: estado tem sinal além da cor", /✓/.test(await p.evaluate(() => getComputedStyle(document.querySelector(".ps-leitura-btn"), "::before").content)));
    checar("modo leitura: sem corte em 390 px", (await cortes(p)).length === 0, (await cortes(p)).join(" | "));
    await p.goto(`${BASE}/produtos/cerave-gel-limpeza/`);
    checar("modo leitura: escolha vale na página seguinte", (await p.getAttribute("html", "data-leitura")) === "1" && (await cortes(p)).length === 0, (await cortes(p)).join(" | "));
    await p.setViewportSize({ width: 320, height: 700 });
    checar("modo leitura: sem corte em 320 px", (await cortes(p)).length === 0, (await cortes(p)).join(" | "));
    await p.click(".ps-leitura-btn");
    checar("modo leitura: desliga", (await p.getAttribute("html", "data-leitura")) === null && (await p.getAttribute(".ps-leitura-btn", "aria-pressed")) === "false");
    await p.close();

    const g = await pagina(grande, 320);
    await g.goto(`${BASE}/blog/rotina-de-skincare-para-iniciantes/`);
    await g.click(".ps-leitura-btn");
    checar("modo leitura + fonte 200% em 320 px: sem corte", (await cortes(g)).length === 0, (await cortes(g)).join(" | "));
    await g.close();
  }

  checar("nenhum erro de JavaScript nas páginas", erros.length === 0, erros.slice(0, 3).join(" | "));
  await grande.close();
  await normal.close();
  if (falhas.length) { console.log(`\n${falhas.length} FALHA(S)`); process.exit(1); }
  console.log("\nTudo certo.");
})().catch(e => { console.error("FALHA", e); process.exit(1); });
