// Feature 3: marcar pele sensível altera as sugestões e mostra avisos. Uso: node sensivel.js http://127.0.0.1:8765
const { chromium } = require("playwright");
const BASE = process.argv[2] || "http://127.0.0.1:8765";
const falhas = [];
function checar(nome, ok, extra) { console.log(`${ok ? "OK   " : "FALHA"} ${nome}${extra ? " — " + extra : ""}`); if (!ok) falhas.push(nome); }

async function jaSei(page, { tipo, sensivel, conc, marcarNaPreferencia }) {
  await page.goto(BASE + "/provador/");
  await page.click("#btnJaSei");
  await page.click(`#chipsTipoJaSei .chip[data-tipo="${tipo}"]`);
  if (sensivel) await page.check("#chkSensivelJaSei");
  await page.click("#btnJaSeiContinuar");
  for (const c of conc) await page.click(`#chipsPreocupacoes .chip[data-conc="${c}"]`);
  await page.click("#btnPreocupacoesContinuar");
  if (marcarNaPreferencia !== undefined) await page.setChecked("#chkSensivel", marcarNaPreferencia);
  await page.click("#btnVerResultado");
  await page.click("#btnPularSelfie");
  await page.waitForSelector("#telaResultado:not([hidden])");
  return page.evaluate(() => ({
    noite: [...document.querySelectorAll("#painelNoite .nome")].map(e => e.textContent),
    manha: [...document.querySelectorAll("#painelManha .nome")].map(e => e.textContent),
    notas: document.querySelector("#notasExtras").textContent,
    resumo: document.querySelector("#resumoTipo").textContent,
    avisoSensivel: !document.querySelector("#avisoSensivel").hidden,
    selos: [...document.querySelectorAll(".selo-cuidado")].map(e => e.textContent)
  }));
}

(async () => {
  const browser = await chromium.launch();
  const erros = [];
  const nova = async () => { const c = await browser.newContext(); const p = await c.newPage(); p.on("pageerror", e => erros.push(e.message)); return p; };

  // Mesmo perfil, com e sem "sensível": oleosa, foco em sinais de idade e manchas
  const sem = await jaSei(await nova(), { tipo: "oleosa", sensivel: false, conc: ["idade", "manchas"] });
  const com = await jaSei(await nova(), { tipo: "oleosa", sensivel: true, conc: ["idade", "manchas"] });
  console.log("sem sensível, noite:", sem.noite.join(" | "));
  console.log("com sensível, noite:", com.noite.join(" | "));
  checar("sem sensível: a noite tem retinol", sem.noite.some(n => /retinol/i.test(n)));
  checar("com sensível: retinol sai da noite", !com.noite.some(n => /retinol/i.test(n)));
  checar("com sensível: sugestões mudam", JSON.stringify(sem.noite.concat(sem.manha)) !== JSON.stringify(com.noite.concat(com.manha)));
  checar("com sensível: explica o que saiu e por quê", /Saíram da rotina por ser pele sensível/.test(com.notas) && /Retinoides/.test(com.notas));
  checar("com sensível: aviso de fragrância", /Fragrância:/.test(com.notas));
  checar("com sensível: card de pele sensível visível", com.avisoSensivel);
  checar("com sensível: selo no produto com vitamina C (se houver)", !com.manha.some(n => /vitamina c|vc-10|ivy c/i.test(n)) || com.selos.some(s => /pode arder/.test(s)), com.selos.join(" | "));
  checar("sem sensível: nenhum aviso de pele sensível", !/Saíram da rotina|Fragrância:/.test(sem.notas) && !sem.avisoSensivel);
  checar("pill 'Sensível' no resumo", /Sensível/.test(com.resumo) && !/Sensível/.test(sem.resumo));

  // A caixa das preferências manda: marcar lá (sem ter marcado no "Já sei") também vale
  const pelaPref = await jaSei(await nova(), { tipo: "oleosa", sensivel: false, conc: ["idade"], marcarNaPreferencia: true });
  checar("marcar sensível só nas preferências tira o retinol", !pelaPref.noite.some(n => /retinol/i.test(n)) && /Sensível/.test(pelaPref.resumo));
  const desmarcou = await jaSei(await nova(), { tipo: "oleosa", sensivel: true, conc: ["idade"], marcarNaPreferencia: false });
  checar("desmarcar nas preferências vale (volta o retinol)", desmarcou.noite.some(n => /retinol/i.test(n)) && !/Sensível/.test(desmarcou.resumo));

  // Quiz completo: resposta "arde com frequência" pré-marca a caixa, com nota
  {
    const p = await nova();
    await p.goto(BASE + "/provador/");
    await p.click("#btnComecar");
    for (const v of ["oleosa", "frequente", "raro", "oleosa", "oleosa", "oleosa", "nao", "nao", "nao", "outra"]) {
      await p.check(`#areaPergunta input[value="${v}"]`);
      await p.click("#btnAvancar");
    }
    await p.click('#chipsPreocupacoes .chip[data-conc="idade"]');
    await p.click("#btnPreocupacoesContinuar");
    checar("quiz: resposta de reatividade pré-marca 'Tenho pele sensível'", await p.isChecked("#chkSensivel"));
    checar("quiz: nota explica a pré-marcação", /Marcamos pelas suas respostas/.test(await p.textContent("#notaSensivelQuiz")));
  }

  checar("sem erros de JavaScript", !erros.length, erros.join("; "));
  await browser.close();
  console.log(falhas.length ? `\n${falhas.length} falha(s)` : "\nTodos os testes de pele sensível passaram.");
  process.exit(falhas.length ? 1 : 0);
})();
