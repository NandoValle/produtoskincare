// Critério de pronto dos 6 consertos de confiança: fluxo mista + acne + sensível, orçamento
// R$ 50 e R$ 100, selfie pulada. Uso: node confianca.js http://127.0.0.1:8765
const { chromium } = require("playwright");
const BASE = process.argv[2] || "http://127.0.0.1:8765";
const falhas = [];
function checar(nome, ok, extra) { console.log(`${ok ? "OK   " : "FALHA"} ${nome}${extra ? " — " + extra : ""}`); if (!ok) falhas.push(nome); }

async function fluxo(browser, faixa, erros) {
  const p = await (await browser.newContext()).newPage();
  p.on("pageerror", e => erros.push(e.message));
  await p.goto(BASE + "/provador/");
  const inicio = await p.textContent("#telaInicio");
  await p.click("#btnComecar");
  const contadores = [], ajudas = [];
  // mista, reage com frequência (sensível), espinhas toda semana; teste do rosto limpo pulado
  for (const v of ["mista", "frequente", "sempre", "mista", "mista", "nao_fiz", "nao", "nao", "nao", "outra"]) {
    contadores.push(await p.textContent("#contadorPergunta"));
    ajudas.push(await p.textContent("#areaPergunta"));
    await p.check(`#areaPergunta input[value="${v}"]`);
    await p.click("#btnAvancar");
  }
  await p.click('#chipsPreocupacoes .chip[data-conc="acne"]');
  await p.click("#btnPreocupacoesContinuar");
  const sensMarcado = await p.isChecked("#chkSensivel");
  const descSens = await p.textContent("#chkSensivel + span");
  await p.check(`input[name=preco][value=${faixa}]`);
  await p.click("#btnVerResultado");
  await p.click("#btnPularSelfie");
  await p.waitForSelector("#telaResultado:not([hidden])");
  const r = await p.evaluate(() => ({
    texto: document.querySelector("#telaResultado").innerText,
    codigo: document.querySelector("#resumoTipo .card strong .pill")?.textContent || "",
    linhas: [...document.querySelectorAll("#resumoTipo table tr")].map(tr => tr.innerText.replace(/\s+/g, " ")),
    titulo: document.querySelector("#resumoTipo .card small")?.textContent || "",
    rotina: [...document.querySelectorAll("#painelManha .nome, #painelNoite .nome")].map(e => e.textContent),
    cta: [...document.querySelectorAll("#telaResultado a")].find(a => /Ver todos os produtos/.test(a.textContent))?.getAttribute("href")
  }));
  await p.context().close();
  return { inicio, contadores, ajudas, sensMarcado, descSens, ...r };
}

(async () => {
  const browser = await chromium.launch();
  const erros = [];
  for (const faixa of ["ate50", "ate100"]) {
    const r = await fluxo(browser, faixa, erros);
    const t = r.texto, rotulo = faixa === "ate50" ? "R$ 50" : "R$ 100";
    checar(`${rotulo}: perfil sensível marcado pelas respostas`, r.sensMarcado);

    // 3. Pele sensível
    checar(`${rotulo} [3] rotina sem retinol nem ácido salicílico`, !r.rotina.some(n => /retinol|salicyl|salic/i.test(n)), r.rotina.join(" | "));
    checar(`${rotulo} [3] progressão não manda introduzir retinol/BHA`, !/Introduza UM ativo forte \(retinol, BHA/.test(t) && /retinol e ácido salicílico \(BHA\) costumam irritar/.test(t));
    checar(`${rotulo} [3] rotina pronta de acne com aviso forte e alternativa`, /Atenção, pele sensível:.*ácido salicílico \(BHA\) e peróxido de benzoíla/.test(t) && /rotina para rosácea/.test(t));
    checar(`${rotulo} [3] caixa de sensível não promete tirar fragrância`, !/Tiramos retinol, ácidos fortes e produtos com fragrância/.test(r.descSens) && /não conferimos o rótulo de todos/.test(r.descSens));

    // 1. Código de 4 eixos coerente entre título e tabela
    const letras = r.linhas.map(l => (l.match(/\b([ODSRPNWT]) · /) || [])[1]).join("");
    checar(`${rotulo} [1] código = letras da tabela`, r.codigo === letras, `${r.codigo} vs ${letras}`);
    const nomesTabela = r.linhas.map(l => (l.match(/[ODSRPNWT] · (.+?) [+−-]?\d/) || [])[1]).join(", ");
    checar(`${rotulo} [1] título por extenso = nomes da tabela`, r.titulo.trim() === nomesTabela, `"${r.titulo.trim()}" vs "${nomesTabela}"`);
    checar(`${rotulo} [1] T nunca descrito como tendência a rugas`, !(/T$/.test(r.codigo) && /rugas/.test(r.titulo)));

    // 2. Subtom sem selfie
    checar(`${rotulo} [2] subtom não avaliado (sem Neutro/Quente/Frio inventado)`, /Subtom: não avaliado/.test(t) && !/Subtom estimado/.test(t));

    // 5. CTA
    checar(`${rotulo} [5] "Ver todos os produtos" vai para /produtos/`, r.cta === "/produtos/", r.cta);

    // 6. Tempo e fluxo
    checar(`${rotulo} [6] sem "menos de 2 minutos"`, !/menos de 2 minutos/i.test(r.inicio));
    checar(`${rotulo} [6] teste de 45-60 min fora da promessa de tempo e opcional`, /fica fora dessa conta/.test(r.inicio) && /Opcional: pede esperar 45 a 60 minutos/.test(r.ajudas[5]) && /Pular: ainda não fiz o teste/.test(r.ajudas[5]));
    checar(`${rotulo} [6] "Pergunta 10 de 10" avisa que ainda há telas`, /Pergunta 10 de 10 · depois vêm mais 3 telas curtas/.test(r.contadores[9]));
  }

  // 4. Checker: par sem regra não sai como seguro
  {
    const p = await (await browser.newContext()).newPage();
    p.on("pageerror", e => erros.push(e.message));
    await p.goto(BASE + "/ferramentas/ingredientes/?ativos=azelaico,salicilico");
    await p.waitForSelector("#resultado .veredito");
    const geral = await p.textContent("#resultado .veredito");
    checar("[4] par sem regra → sem regra cadastrada", /Sem regra cadastrada/.test(geral) && !/Pode usar junto/.test(await p.textContent("#resultado")), geral);
    await p.goto(BASE + "/ferramentas/ingredientes/?ativos=retinol,glicolico");
    await p.waitForSelector("#resultado .veredito");
    checar("[4] regra explícita mantida (retinol + glicólico)", /horários diferentes/.test(await p.textContent("#resultado .veredito")));
  }

  // 6. Guia de pele oleosa
  {
    const p = await (await browser.newContext()).newPage();
    await p.goto(BASE + "/pele/oleosa/");
    const corpo = await p.textContent("body");
    checar("[6] guia de pele oleosa sem '5 perguntas rápidas' nem '2 minutos'", !/5 perguntas rápidas|2 minutos/.test(corpo));
  }

  checar("sem erros de JavaScript", !erros.length, erros.join("; "));
  await browser.close();
  console.log(falhas.length ? `\n${falhas.length} falha(s)` : "\nTodos os testes dos consertos de confiança passaram.");
  process.exit(falhas.length ? 1 : 0);
})();
