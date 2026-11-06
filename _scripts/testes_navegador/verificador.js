// Feature 4: verificador de combinações na página. Uso: node verificador.js http://127.0.0.1:8765
const { chromium } = require("playwright");
const BASE = process.argv[2] || "http://127.0.0.1:8765";
const URL_PAG = BASE + "/ferramentas/ingredientes/";
const falhas = [];
function checar(nome, ok, extra) { console.log(`${ok ? "OK   " : "FALHA"} ${nome}${extra ? " — " + extra : ""}`); if (!ok) falhas.push(nome); }

// As 5 combinações do brief (+1), feitas como a pessoa faria: clicando nos ativos.
const CASOS = [
  { nome: "retinol + ácido glicólico", ativos: ["retinol", "glicolico"], esperado: "Use em horários diferentes" },
  { nome: "retinol + vitamina C", ativos: ["retinol", "vitc"], esperado: "Use em horários diferentes" },
  { nome: "peróxido de benzoíla + tretinoína", ativos: ["bpo", "tretinoina"], esperado: "Use em horários diferentes" },
  { nome: "ácido salicílico + pele irritada", ativos: ["salicilico"], irritada: true, esperado: "Não combine" },
  { nome: "ácido glicólico + pele irritada", ativos: ["glicolico"], irritada: true, esperado: "Não combine" },
  { nome: "vitamina C + niacinamida", ativos: ["vitc", "niacinamida"], esperado: "Pode usar junto" },
  { nome: "retinol + ácido glicólico, pele sensível", ativos: ["retinol", "glicolico"], sensivel: true, esperado: "Não combine" },
  // Par sem regra cadastrada: "não sabemos", nunca "pode usar junto"
  { nome: "ácido azelaico + ácido salicílico (sem regra)", ativos: ["azelaico", "salicilico"], esperado: "Sem regra cadastrada", naoEsperado: "Pode usar junto" },
  { nome: "niacinamida + pele irritada (sem regra)", ativos: ["niacinamida"], irritada: true, esperado: "Sem regra cadastrada", naoEsperado: "Pode usar junto" }
];

(async () => {
  const browser = await chromium.launch();
  const erros = [];
  const page = async () => { const p = await (await browser.newContext()).newPage(); p.on("pageerror", e => erros.push(e.message)); await p.goto(URL_PAG); return p; };

  for (const c of CASOS) {
    const p = await page();
    for (const id of c.ativos) await p.click(`#chipsAtivos [data-ativo="${id}"]`);
    if (c.irritada) await p.check("#chkIrritada");
    if (c.sensivel) await p.check("#chkSensivel");
    await p.click("#btnVerificar");
    const geral = (await p.textContent("#resultado .veredito")) || "";
    const motivo = (await p.textContent("#resultado")).replace(/\s+/g, " ");
    checar(`${c.nome} → ${c.esperado}`, geral.includes(c.esperado), geral.trim());
    checar(`${c.nome}: mostra motivo`, motivo.length > 80);
    if (c.naoEsperado) checar(`${c.nome}: não aparece "${c.naoEsperado}"`, !motivo.includes(c.naoEsperado), motivo.slice(0, 160));
    await p.context().close();
  }

  // Lista INCI colada (sem clicar em nada)
  {
    const p = await page();
    await p.fill("#ingredientes", "Aqua, Glycerin, Glycolic Acid, Retinol, Sodium Hyaluronate, Citric Acid, Parfum");
    await p.click("#btnVerificar");
    const t = await p.textContent("#resultado");
    checar("INCI colado: reconhece retinol e ácido glicólico", /Retinol/.test(t) && /Ácido glicólico/.test(t));
    checar("INCI colado: ácido cítrico não vira AHA", !/cítrico/i.test(t));
    checar("INCI colado: resultado geral horários diferentes", /Resultado geral: Use em horários diferentes/.test(t));
    await p.context().close();
  }

  // Um ativo só: pede o segundo
  {
    const p = await page();
    await p.click('#chipsAtivos [data-ativo="retinol"]');
    await p.click("#btnVerificar");
    checar("1 ativo: pede pelo menos 2", /pelo menos 2 ativos/.test(await p.textContent("#resultado")));
    await p.context().close();
  }

  // Exemplos por link e lista de regras gerada do arquivo
  {
    const p = await page();
    const exemplos = await p.$$eval("#listaExemplos li", lis => lis.map(l => l.textContent));
    checar("página lista os exemplos com o resultado esperado", exemplos.length >= 5, exemplos.join(" | "));
    const regras = await p.textContent("#listaRegras");
    checar("lista de regras gerada com a versão", /Versão das regras: v\d+\.\d+\.\d+/.test(regras) && /retinoide \+ ácido esfoliante/.test(regras));
    await p.click("#listaExemplos li:first-child a");
    await p.waitForSelector("#resultado .veredito");
    checar("exemplo por link abre já verificado", /horários diferentes/.test(await p.textContent("#resultado .veredito")));
    checar("exemplo por link marca os botões", await p.getAttribute('#chipsAtivos [data-ativo="retinol"]', "aria-pressed") === "true");
    await p.context().close();
  }

  checar("sem erros de JavaScript", !erros.length, erros.join("; "));
  await browser.close();
  console.log(falhas.length ? `\n${falhas.length} falha(s)` : "\nTodos os testes do verificador passaram.");
  process.exit(falhas.length ? 1 : 0);
})();
