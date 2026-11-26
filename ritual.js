/* "Você já tem este ativo em casa?" nas fichas de ativos (/ativos/<slug>/ e /ingredientes/<slug>/).
 *
 * Lê a Minha prateleira (/ferramentas/prateleira/), que fica salva só neste aparelho
 * (localStorage, chave ps-prateleira-v1), e diz se algum produto anotado ali traz o ativo
 * desta ficha. Nada é enviado a servidor nenhum. O reconhecimento do ativo usa as mesmas
 * regras do verificador (/regras-ativos.js), carregadas só quando a prateleira tem itens.
 *
 * O bloco é posto na página por _scripts/decisao_ficha.py: <div data-ritual="Nome, INCI" hidden>.
 * Sem JavaScript ele continua oculto e a ficha fica como sempre foi.
 */
(function () {
  "use strict";
  var alvo = document.querySelector("[data-ritual]");
  var dd = alvo && alvo.querySelector("dd");
  if (!dd) return;

  var PASSOS = { limpeza: "limpeza", tratamento: "tratamento", hidratacao: "hidratante", protetor: "protetor solar", outro: "outro passo" };
  var PERIODOS = { manha: "manhã", noite: "noite" };
  var PRATELEIRA = "/ferramentas/prateleira/";

  var itens = [];
  try {
    var d = JSON.parse(localStorage.getItem("ps-prateleira-v1") || "{}");
    if (d && Array.isArray(d.itens)) itens = d.itens;
  } catch (e) { return; } // sem acesso ao armazenamento (aba privada, bloqueio): a ficha fica como está

  function p(texto, forte) {
    var el = document.createElement("p");
    if (forte) { var b = document.createElement("b"); b.textContent = forte + " "; el.appendChild(b); }
    el.appendChild(document.createTextNode(texto));
    return el;
  }
  function link(texto) {
    var el = document.createElement("p"), a = document.createElement("a");
    a.href = PRATELEIRA; a.textContent = texto;
    el.appendChild(a);
    return el;
  }
  function mostrar(nos) {
    dd.textContent = "";
    nos.forEach(function (n) { dd.appendChild(n); });
    alvo.hidden = false;
  }
  function plural(n, um, varios) { return n + " " + (n === 1 ? um : varios); }

  if (!itens.length) {
    mostrar([
      p("Ainda não dá para saber: a sua prateleira neste aparelho está vazia. Anote o que você já tem em casa (fica salvo só aqui, sem cadastro) e esta ficha passa a dizer se você já tem este ativo antes de comprar outro."),
      link("Montar minha prateleira")
    ]);
    return;
  }

  function comparar(R) {
    var meus = R.detectar(alvo.getAttribute("data-ritual") || "").map(function (a) { return a.id; });
    if (!meus.length) {
      mostrar([
        p("O verificador do site não reconhece este ativo pelo nome, então não dá para comparar com a sua prateleira. Confira no rótulo dos seus produtos."),
        link("Ver minha prateleira")
      ]);
      return;
    }
    var achados = itens.filter(function (it) {
      return R.detectar((it.nome || "") + ", " + (it.texto || "")).some(function (a) { return meus.indexOf(a.id) >= 0; });
    });
    if (!achados.length) {
      mostrar([
        p("Nenhum dos " + plural(itens.length, "produto", "produtos") + " da sua prateleira cita este ativo. Isso vale para o que foi anotado: se um produto foi salvo sem a lista de ativos, confira o rótulo.", "Não encontramos."),
        link("Ver minha prateleira")
      ]);
      return;
    }
    var ul = document.createElement("ul");
    achados.forEach(function (it) {
      var li = document.createElement("li");
      var quando = (Array.isArray(it.periodo) ? it.periodo : []).map(function (x) { return PERIODOS[x]; }).filter(Boolean).join(" e ");
      li.textContent = (it.nome || "Produto sem nome") + " (" + (PASSOS[it.passo] || PASSOS.outro) + (quando ? ", uso de " + quando : "") + ")";
      ul.appendChild(li);
    });
    mostrar([
      p("Na sua prateleira, " + plural(achados.length, "produto traz", "produtos trazem") + " este ativo:", "Sim."),
      ul,
      p("Antes de comprar outro, vale usar o que já está em casa. A prateleira mostra se ele combina com o resto da sua rotina."),
      link("Ver minha prateleira")
    ]);
  }

  if (window.PSRegras) { comparar(window.PSRegras); return; }
  var s = document.createElement("script");
  s.src = "/regras-ativos.js";
  s.onload = function () { if (window.PSRegras) comparar(window.PSRegras); };
  document.head.appendChild(s);
})();
