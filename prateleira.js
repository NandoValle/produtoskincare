/* Minha prateleira: os produtos que a pessoa já tem, salvos só neste aparelho (localStorage).
 * Usado por /ferramentas/prateleira/ e /ferramentas/farmacia/. Precisa de /regras-ativos.js antes.
 *
 * Toda análise sai das regras de /regras-ativos.js:
 *  - conflitos: pares de ativos de produtos diferentes usados no mesmo período (manhã ou noite);
 *    "não combine" vale mesmo em períodos diferentes;
 *  - repetidos: o mesmo grupo de ativo em dois produtos no mesmo período;
 *  - o que falta: limpeza, hidratante e protetor solar.
 * Par sem regra cadastrada aparece como "sem regra cadastrada (não sabemos)", nunca como "pode usar junto".
 */
(function () {
  "use strict";
  var R = window.PSRegras;
  var CHAVE = "ps-prateleira-v1";
  var PASSOS = { limpeza: "Limpeza", tratamento: "Tratamento (sérum)", hidratacao: "Hidratante", protetor: "Protetor solar", outro: "Outro" };
  var PERIODOS = { manha: "manhã", noite: "noite" };
  var PESO = { ok: 0, sem_regra: 1, horarios: 2, nao: 3 };
  // Grupos em que ter dois produtos no mesmo período costuma ser repetição (não vale para hidratantes e filtro).
  var REPETICAO = { retinoide: 1, aha: 1, bha: 1, vitc: 1, bpo: 1, niacinamida: 1, azelaico: 1, clareador: 1 };
  var ESSENCIAIS = ["limpeza", "hidratacao", "protetor"];

  function ler() {
    try {
      var d = JSON.parse(localStorage.getItem(CHAVE) || "{}");
      d.itens = Array.isArray(d.itens) ? d.itens : [];
      d.sensivel = !!d.sensivel;
      return d;
    } catch (e) { return { itens: [], sensivel: false }; }
  }
  function salvar(d) { try { localStorage.setItem(CHAVE, JSON.stringify(d)); } catch (e) {} }

  function novoId() { return "p" + Date.now().toString(36) + Math.random().toString(36).slice(2, 6); }

  /* Item a partir de um produto do catálogo (/produtos.json). */
  function doCatalogo(p) {
    return {
      uid: novoId(), id: p.id, nome: p.nome, passo: p.passo || "outro",
      periodo: (p.periodo && p.periodo.length ? p.periodo : ["manha", "noite"]).slice(),
      texto: (p.ativos || []).join(", "), link: "/produtos/" + p.id + "/"
    };
  }

  /* Período sugerido para um produto de fora do catálogo, pelos ativos (só sugestão: a pessoa pode mudar). */
  function periodoSugerido(texto, passo) {
    if (passo === "protetor") return ["manha"];
    var classes = (R ? R.detectar(texto) : []).map(function (a) { return a.classe; });
    if (classes.indexOf("retinoide") >= 0 || classes.indexOf("aha") >= 0) return ["noite"];
    if (classes.indexOf("vitc") >= 0) return ["manha"];
    return ["manha", "noite"];
  }

  function ativosDe(item) {
    return R ? R.detectar([item.nome, item.texto].join(", ")) : [];
  }

  function usaEm(item, periodo) { return (item.periodo || []).indexOf(periodo) >= 0; }

  /* Pior resultado entre os ativos de dois produtos. */
  function compararItens(x, y, ctx) {
    var ax = ativosDe(x), ay = ativosDe(y), pior = null;
    ax.forEach(function (a) {
      ay.forEach(function (b) {
        if (a.id === b.id && a.classe !== "retinoide") return; // o mesmo ativo nos dois é repetição, não conflito
        var r = R.avaliarPar(a, b, ctx);
        r.a = a; r.b = b;
        if (!pior || PESO[r.resultado] > PESO[pior.resultado]) pior = r;
      });
    });
    return pior;
  }

  function analisar(itens, opcoes) {
    opcoes = opcoes || {};
    var ctx = { sensivel: !!opcoes.sensivel };
    var conflitos = [], repetidos = [], vistos = {};

    for (var i = 0; i < itens.length; i++) {
      for (var j = i + 1; j < itens.length; j++) {
        var x = itens[i], y = itens[j];
        var comuns = ["manha", "noite"].filter(function (p) { return usaEm(x, p) && usaEm(y, p); });
        var r = compararItens(x, y, ctx);
        if (!r || r.resultado === "ok") continue;
        // "Use em horários diferentes" e "sem regra" só pesam quando os dois caem no mesmo período.
        if (r.resultado !== "nao" && !comuns.length) continue;
        conflitos.push({ x: x, y: y, periodos: comuns, resultado: r.resultado, rotulo: R.ROTULOS[r.resultado],
          motivo: r.motivo, nota: r.nota || "", ativoX: r.a.nome, ativoY: r.b.nome, porSensibilidade: !!r.porSensibilidade });
      }
    }
    conflitos.sort(function (p, q) { return PESO[q.resultado] - PESO[p.resultado]; });

    ["manha", "noite"].forEach(function (per) {
      var porClasse = {};
      itens.forEach(function (it) {
        if (!usaEm(it, per)) return;
        var classes = {};
        ativosDe(it).forEach(function (a) { if (REPETICAO[a.classe]) classes[a.classe] = a; });
        Object.keys(classes).forEach(function (c) { (porClasse[c] = porClasse[c] || []).push(it); });
      });
      Object.keys(porClasse).forEach(function (c) {
        var lista = porClasse[c];
        if (lista.length < 2) return;
        var chave = c + "|" + lista.map(function (it) { return it.uid; }).sort().join(",");
        if (vistos[chave]) { vistos[chave].periodos.push(per); return; }
        vistos[chave] = { classe: c, nomeClasse: R.CLASSES[c] || c, itens: lista, periodos: [per] };
        repetidos.push(vistos[chave]);
      });
    });

    var passos = {};
    itens.forEach(function (it) { passos[it.passo] = true; });
    var faltando = ESSENCIAIS.filter(function (p) { return !passos[p]; });
    var classesTodas = {};
    itens.forEach(function (it) { ativosDe(it).forEach(function (a) { classesTodas[a.classe] = true; }); });
    var fotossensivel = !!(classesTodas.retinoide || classesTodas.aha || classesTodas.bha);

    return { conflitos: conflitos, repetidos: repetidos, faltando: faltando, fotossensivel: fotossensivel, versao: R.VERSAO };
  }

  window.PSPrateleira = {
    CHAVE: CHAVE, PASSOS: PASSOS, PERIODOS: PERIODOS, ESSENCIAIS: ESSENCIAIS,
    ler: ler, salvar: salvar, novoId: novoId, doCatalogo: doCatalogo, periodoSugerido: periodoSugerido,
    ativosDe: ativosDe, analisar: analisar, compararItens: compararItens
  };
})();
