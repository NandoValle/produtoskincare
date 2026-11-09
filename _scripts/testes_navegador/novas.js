// Ferramentas novas: "Posso usar junto?", prateleira, modo farmácia, equivalente e modo 12 semanas.
// Uso: node novas.js http://127.0.0.1:8765
const { chromium } = require("playwright");
const path = require("path");
const fs = require("fs");
const os = require("os");
const BASE = process.argv[2] || "http://127.0.0.1:8765";
const falhas = [];
function checar(nome, ok, extra) { console.log(`${ok ? "OK   " : "FALHA"} ${nome}${extra ? " — " + extra : ""}`); if (!ok) falhas.push(nome); }
const texto = async (p, sel) => ((await p.textContent(sel)) || "").replace(/\s+/g, " ");

(async () => {
  const browser = await chromium.launch();
  const erros = [];
  async function abrir(url, prep) {
    const ctx = await browser.newContext();
    const p = await ctx.newPage();
    p.on("pageerror", e => erros.push(url + ": " + e.message));
    if (prep) await p.addInitScript(prep);
    await p.goto(BASE + url);
    return p;
  }

  // 1. Páginas "Posso usar X com Y?" saem das mesmas regras do verificador
  for (const [url, esperado] of [["/combina/retinol-com-vitamina-c/", "Use em horários diferentes"],
    ["/combina/vitamina-c-com-niacinamida/", "Pode usar junto"], ["/combina/dois-retinoides/", "Não combine"],
    ["/combina/acido-glicolico-com-pele-irritada/", "Não combine"]]) {
    const p = await abrir(url);
    const v = await texto(p, ".cb-veredito");
    checar(`${url} → ${esperado}`, v.includes(esperado), v);
    await p.context().close();
  }
  {
    const p = await abrir("/combina/");
    const n = await p.locator('a[href^="/combina/"][href$="/"]').count();
    checar("índice /combina/ lista as combinações", n >= 20, n + " links");
    checar("índice não tem par sem regra", !(await texto(p, "main")).includes("ácido azelaico com ácido salicílico"));
    await p.context().close();
  }

  // 2. Prateleira: retinol (catálogo) + ácido glicólico (fora do catálogo), os dois à noite
  {
    const p = await abrir("/ferramentas/prateleira/");
    await p.fill("#pr-busca", "rn-0,3");
    await p.click('#pr-sugestoes [data-id="principia-rn03"]');
    await p.click("#pr-outro summary");
    await p.fill("#pr-nome", "Tônico glicólico X");
    await p.fill("#pr-texto", "Aqua, Glycolic Acid 7%, Glycerin");
    await p.dispatchEvent("#pr-texto", "change");
    checar("prateleira sugere a noite para ácido", !(await p.isChecked("#pr-manha")) && await p.isChecked("#pr-noite"));
    await p.click("#pr-adicionar");
    const a = await texto(p, "#pr-analise");
    checar("prateleira: retinol + glicólico à noite → horários diferentes", a.includes("Use em horários diferentes"), a.slice(0, 160));
    checar("prateleira: aponta que falta protetor", a.includes("Falta: Protetor solar"));
    checar("prateleira: sugere protetor do catálogo", (await p.locator('#pr-analise a[href^="/produtos/"]').count()) > 0);
    // Tirar o glicólico da noite e pôr de manhã resolve o conflito
    const item = p.locator(".ft-item", { hasText: "Tônico glicólico X" });
    await item.locator('[data-per="manha"]').check();
    await item.locator('[data-per="noite"]').uncheck();
    const b = await texto(p, "#pr-analise");
    checar("prateleira: em períodos diferentes, sem conflito", b.includes("Nenhum conflito"), b.slice(0, 160));
    await p.reload();
    checar("prateleira fica salva no aparelho", (await p.locator(".ft-item").count()) === 2);
    await p.context().close();
  }

  // 3. Par sem regra na prateleira: "não sabemos", nunca "pode usar junto"
  {
    const prep = () => localStorage.setItem("ps-prateleira-v1", JSON.stringify({ sensivel: false, itens: [
      { uid: "a", nome: "Azelaico", passo: "tratamento", periodo: ["noite"], texto: "ácido azelaico 10%" },
      { uid: "b", nome: "Salicílico", passo: "tratamento", periodo: ["noite"], texto: "ácido salicílico 2%" }] }));
    const p = await abrir("/ferramentas/prateleira/", prep);
    const a = await texto(p, "#pr-analise");
    checar("prateleira: azelaico + salicílico → sem regra", a.includes("Sem regra cadastrada") && !a.includes("Pode usar junto"), a.slice(0, 160));
    await p.context().close();
  }

  // 4. Modo farmácia: produto da loja contra a prateleira
  {
    const prep = () => localStorage.setItem("ps-prateleira-v1", JSON.stringify({ sensivel: false, itens: [
      { uid: "a", id: "principia-rn03", nome: "Principia RN-0,3 Retinol", passo: "tratamento", periodo: ["noite"], texto: "retinol 0,3%" },
      { uid: "b", nome: "Sérum de niacinamida", passo: "tratamento", periodo: ["manha", "noite"], texto: "niacinamida 10%" }] }));
    const p = await abrir("/ferramentas/farmacia/", prep);
    checar("farmácia mostra a prateleira", (await texto(p, "#fa-prateleira")).includes("2 produtos"));
    await p.fill("#fa-texto", "Aqua, Lactic Acid 10%, Niacinamide");
    await p.dispatchEvent("#fa-texto", "change");
    await p.click("#fa-verificar");
    const r = await texto(p, "#fa-resultado");
    checar("farmácia: ácido lático x retinol → horários diferentes", r.includes("Com Principia RN-0,3 Retinol: Use em horários diferentes"), r.slice(0, 200));
    checar("farmácia: avisa niacinamida repetida", r.includes("Repete niacinamida"));
    checar("farmácia: preenche passo que falta? não (é tratamento)", !r.includes("Preenche um passo"));
    await p.click("#fa-adicionar");
    checar("farmácia: adiciona à prateleira", (await texto(p, "#fa-prateleira")).includes("3 produtos"));
    await p.context().close();
  }

  // 5. Equivalente mais barato
  {
    const p = await abrir("/ferramentas/equivalente/?produto=principia-niacinamida");
    await p.waitForSelector("#eq-resultado .ft-item");
    const r = await texto(p, "#eq-resultado");
    checar("equivalente: Principia niacinamida → The Ordinary, mesma concentração", r.includes("The Ordinary") && r.includes("mesmos ativos e concentração"), r.slice(0, 220));
    checar("equivalente: mostra quanto a menos", r.includes("a menos"));
    await p.fill("#eq-busca", "retinol b3");
    await p.click("#eq-sugestoes [data-i]");
    const r2 = await texto(p, "#eq-resultado");
    checar("equivalente: Retinol B3 → opções com retinol e niacinamida", r2.includes("Equivalentes de La Roche-Posay Retinol B3"), r2.slice(0, 200));
    checar("equivalente: produto de referência não aparece como equivalente de si mesmo", (await p.locator('#eq-resultado a[href="/produtos/lrp-retinol-b3/"]').count()) === 0);
    await p.context().close();
  }

  // 6. Modo 12 semanas: plano, .ics e diário de fotos (IndexedDB)
  {
    const p = await abrir("/ferramentas/12-semanas/");
    await p.selectOption("#sm-ativo", "retinoide");
    await p.click("#sm-salvar");
    checar("12 semanas: tabela com as etapas", (await p.locator("#sm-tabela tr").count()) === 4);
    checar("12 semanas: mostra a semana atual", (await texto(p, "#sm-agora")).includes("semana 1"));
    const [download] = await Promise.all([p.waitForEvent("download"), p.click("#sm-ics")]);
    const ics = fs.readFileSync(await download.path(), "utf8");
    checar("12 semanas: .ics com 12 lembretes", (ics.match(/BEGIN:VEVENT/g) || []).length === 12);
    const foto = path.join(os.tmpdir(), "ps-teste-foto.png");
    fs.writeFileSync(foto, Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAIAAAADCAIAAAA2iEnWAAAAEklEQVR4nGP4z8DwHwyBNAMDAFOpBfvk8QR5AAAAAElFTkSuQmCC", "base64"));
    await p.selectOption("#sm-reacao", "forte");
    await p.setInputFiles("#sm-arquivo", foto);
    await p.waitForSelector("#sm-galeria .ft-foto");
    checar("12 semanas: foto entra no diário", (await p.locator("#sm-galeria .ft-foto").count()) === 1);
    checar("12 semanas: reação forte mostra orientação", (await texto(p, "#sm-alerta")).includes("procure um dermatologista"));
    await p.reload();
    await p.waitForSelector("#sm-galeria .ft-foto");
    checar("12 semanas: foto continua depois de recarregar", (await p.locator("#sm-galeria .ft-foto").count()) === 1);
    await p.context().close();
  }

  // 7. Índice de ferramentas e menu
  {
    const p = await abrir("/ferramentas/");
    checar("índice /ferramentas/ tem as 4 ferramentas novas", (await p.locator('.ft-cards a[href="/ferramentas/prateleira/"], .ft-cards a[href="/ferramentas/farmacia/"], .ft-cards a[href="/ferramentas/equivalente/"], .ft-cards a[href="/ferramentas/12-semanas/"]').count()) === 4);
    await p.context().close();
  }

  checar("sem erros de JavaScript", !erros.length, erros.join(" | "));
  await browser.close();
  process.exit(falhas.length ? 1 : 0);
})();
