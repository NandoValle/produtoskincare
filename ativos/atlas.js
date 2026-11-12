/* Atlas dos Ativos (/ativos/): busca por objetivo, filtros, comparador, passaporte, mapa da pele
 * e leitor de rótulo. Os dados vêm de /ativos/atlas-dados.js (gerado por _scripts/gerar_atlas.py)
 * e as combinações, de /regras-ativos.js (as mesmas regras do verificador de ingredientes).
 * Nada aqui cria informação: o script só cruza o que já está nessas duas fontes.
 * Sem JavaScript a página continua sendo a lista completa, por categoria.
 */
(function () {
  "use strict";
  var D = window.ATLAS;
  var raiz = document.querySelector("main.atlas");
  if (!D || !raiz) return;
  var R = window.PSRegras || null;
  var $ = function (s) { return raiz.querySelector(s); };
  var $$ = function (s) { return Array.prototype.slice.call(raiz.querySelectorAll(s)); };

  var POR_ID = {};
  var TOTAL = D.ativos.length;
  var EV_N = { forte: 3, moderada: 2, emergente: 1, "": 0 };
  var IRRITA = ["baixa", "moderada", "alta"];
  var NIVEL = { 1: "iniciante", 2: "intermediário", 3: "avançado" };
  var TURNO = { manha: "De manhã", noite: "À noite", ambos: "De manhã ou à noite" };
  var GEST = {
    evitar: "Evitar na gestação e na amamentação.",
    consultar: "Consulte seu médico antes de usar na gestação.",
    compativel: "Costuma ser considerado compatível com a gestação. Confirme com seu médico.",
    "": "O guia não traz orientação de gestação para este ativo. Pergunte ao seu médico."
  };
  var CLASSES = ["retinoide", "aha", "bha", "vitc", "bpo", "niacinamida", "azelaico", "clareador", "hidratante", "antioxidante", "filtro", "irritada"];
  var ROTULO_CLASSE = {
    retinoide: "retinoides (retinol, retinal, tretinoína, adapaleno)", aha: "ácidos AHA (glicólico, lático, mandélico)",
    bha: "ácido salicílico (BHA)", vitc: "vitamina C", bpo: "peróxido de benzoíla", niacinamida: "niacinamida",
    azelaico: "ácido azelaico", clareador: "clareadores suaves (ácido tranexâmico, alfa-arbutina)",
    hidratante: "hidratantes e calmantes", antioxidante: "antioxidantes e peptídeos", filtro: "protetor solar",
    irritada: "a pele irritada"
  };
  var VEREDITO = { ok: "Pode usar junto", horarios: "Use em horários diferentes", nao: "Não combine", sem_regra: "Sem regra cadastrada: não sabemos" };
  var PARADAS = " a o as os e de da do das dos para pra com sem em no na nos nas um uma que eu tenho minha meu pele quero como muito muita estou sou tratar melhorar ativo ativos qual quais melhor melhores tem ter tipo sobre ";
  var FILTROS = {
    evid: { rotulo: "evidência avaliada", f: function (a) { return !!a.ev; } },
    gest: { rotulo: "compatível na gestação", f: function (a) { return a.gest === "compativel"; } },
    semrx: { rotulo: "sem receita", f: function (a) { return !a.rx; } },
    sensivel: { rotulo: "pele sensível", f: function (a) { return a.irrita === 0 && (!a.pele.length || a.pele.indexOf("sensivel") >= 0); } },
    iniciante: { rotulo: "para iniciantes", f: function (a) { return a.nivel === 1; } },
    manha: { rotulo: "uso de manhã", f: function (a) { return a.turno === "manha" || a.turno === "ambos"; } }
  };

  function norm(s) {
    return String(s == null ? "" : s).normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
  }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; });
  }
  function lista(arr) {
    if (arr.length < 2) return arr.join("");
    return arr.slice(0, -1).join(", ") + " e " + arr[arr.length - 1];
  }
  function dataLonga(iso) {
    var m = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"];
    var p = String(iso).split("-");
    return p.length === 3 ? parseInt(p[2], 10) + " de " + m[parseInt(p[1], 10) - 1] + " de " + p[0] : "";
  }
  function barra(n, tipo, vazia) {
    var h = '<span class="at-barra ' + tipo + (vazia ? " vazia" : "") + '" aria-hidden="true">';
    for (var k = 0; k < 3; k++) h += k < n ? '<i class="on"></i>' : "<i></i>";
    return h + "</span>";
  }
  function medEv(a) { return barra(EV_N[a.ev], "ev", !a.ev) + '<span class="at-valor">' + (a.ev || "ainda não avaliada") + "</span>"; }
  function medIr(a) { return barra(a.irrita + 1, "ir") + '<span class="at-valor">' + IRRITA[a.irrita] + "</span>"; }
  function medNv(a) { return barra(a.nivel, "nv") + '<span class="at-valor">' + NIVEL[a.nivel] + "</span>"; }
  function objetivos(a) { return a.c.map(function (o) { return D.objetivos[o].toLowerCase(); }); }
  function peles(a) {
    return a.pele.length ? "Pele " + lista(a.pele.map(function (p) { return D.peles[p]; })) : "Todos os tipos de pele";
  }

  D.ativos.forEach(function (a, i) {
    POR_ID[a.id] = a;
    a._ordem = i;
    a._nome = norm(a.nome);
    a._texto = " " + [a._nome, norm(a.n), norm(a.inci)].join(" ") + " ";
    a._cat = " " + norm(a.cat) + " ";
    a._cartao = document.getElementById("a-" + a.id);
  });

  var S = { q: "", rotulo: "", tema: "", filtros: {}, ordem: "padrao", comp: [] };
  var el = {
    busca: $("#at-busca"), q: $("#at-q"), rotulo: $("#at-rotulo"), inci: $("#at-inci"), painel: $("#at-painel"),
    ordem: $("#at-ordem"), limpar: $("#at-limpar"), contagem: $("#at-contagem"), avisoGest: $("#at-aviso-gest"),
    res: $("#at-resultados"), resT: $("#at-res-t"), resNota: $("#at-res-nota"), resLista: $("#at-res-lista"),
    resVazio: $("#at-res-vazio"), cats: $("#at-categorias"), prontas: $("#at-prontas")
  };

  /* ===== BUSCA ===== */
  /* Peso de um objetivo pela posição na lista do ativo (a primeira é o objetivo principal). */
  function peso(i) { return i === 0 ? 34 : i === 1 ? 28 : i < 4 ? 18 : 10; }
  function interpretar(q) {
    var nq = norm(q), resto = " " + nq + " ";
    var out = { nq: nq, objs: [], peles: [], filtros: [], texto: "" };
    function casar(mapa, destino) {
      Object.keys(mapa).forEach(function (id) {
        var achou = false;
        mapa[id].forEach(function (termo) {
          if ((" " + nq + " ").indexOf(" " + termo + " ") >= 0) { achou = true; resto = resto.split(" " + termo + " ").join(" "); }
          else if (nq.length >= 4 && nq.indexOf(" ") < 0 && termo.indexOf(nq) === 0) { achou = true; resto = " "; }
        });
        if (achou && destino.indexOf(id) < 0) destino.push(id);
      });
    }
    casar(D.vocabulario.peles, out.peles);
    casar(D.vocabulario.objetivos, out.objs);
    casar(D.vocabulario.filtros, out.filtros);
    out.texto = resto.split(" ").filter(function (t) { return t && PARADAS.indexOf(" " + t + " ") < 0; }).join(" ");
    return out;
  }

  function buscar(q) {
    var I = interpretar(q);
    var sens = I.peles.indexOf("sensivel") >= 0 || I.objs.indexOf("sensibilidade") >= 0;
    var porNome = {}, algumInteiro = false;
    if (I.nq) {
      D.ativos.forEach(function (a) {
        var frase = I.texto || I.nq;
        if (a._texto.indexOf(" " + frase) >= 0) { porNome[a.id] = { p: a._nome.indexOf(frase) === 0 ? 130 : 100, tipo: "nome" }; algumInteiro = true; }
        else if (frase.length >= 4 && a._cat.indexOf(" " + frase) >= 0) { porNome[a.id] = { p: 60, tipo: "cat" }; algumInteiro = true; }
      });
      if (!algumInteiro && I.texto) {
        var tokens = I.texto.split(" ").filter(function (t) { return t.length >= 3; });
        D.ativos.forEach(function (a) {
          var n = tokens.filter(function (t) { return a._texto.indexOf(" " + t) >= 0; }).length;
          if (n) porNome[a.id] = { p: 40 * n, tipo: "nome" };
        });
      }
    }
    var itens = [];
    D.ativos.forEach(function (a) {
      var pontos = 0, motivos = [], base = false;
      var pn = porNome[a.id];
      if (pn) {
        base = true; pontos += pn.p;
        motivos.push(pn.tipo === "cat" ? "faz parte da categoria <b>" + esc(a.cat) + "</b>"
          : "o nome combina com a busca (no rótulo: <b>" + esc(a.inci) + "</b>)");
      }
      I.objs.forEach(function (o) {
        var i = a.c.indexOf(o);
        if (i < 0) return;
        base = true; pontos += peso(i);
        motivos.push("costuma ser indicado para <b>" + esc(D.objetivos[o].toLowerCase()) + "</b>" + (i === 0 ? " (é o objetivo principal dele)" : ""));
      });
      if (!base) return;
      I.peles.forEach(function (p) {
        if (!a.pele.length) { pontos += 4; motivos.push("serve para todos os tipos de pele"); }
        else if (a.pele.indexOf(p) >= 0) { pontos += 8; motivos.push("é indicado para pele <b>" + esc(D.peles[p]) + "</b>"); }
        else { pontos -= 12; motivos.push("atenção: não costuma ser a primeira escolha para pele " + esc(D.peles[p])); }
      });
      if (sens) {
        if (a.irrita === 0) { pontos += 6; motivos.push("a chance de irritar é baixa"); }
        if (a.irrita === 2) { pontos -= 25; motivos.push("atenção: pode irritar bastante"); }
      }
      pontos += EV_N[a.ev] * 2;
      if (a.rx) pontos -= 5;
      itens.push({ a: a, pontos: pontos, motivos: motivos.filter(function (m, k) { return motivos.indexOf(m) === k; }) });
    });
    return { itens: itens, I: I };
  }

  /* ===== LEITOR DE RÓTULO ===== */
  function lerRotulo(texto) {
    var t = " " + norm(texto) + " ";
    var itens = [];
    D.ativos.forEach(function (a) {
      var pos = -1, achado = "";
      a.rot.forEach(function (termo) {
        var p = t.indexOf(" " + termo + " ");
        if (p >= 0 && (pos < 0 || p < pos)) { pos = p; achado = termo; }
      });
      if (pos >= 0) itens.push({ a: a, pontos: -pos, motivos: ["reconhecido na lista como <b>" + esc(achado) + "</b>"] });
    });
    return itens;
  }

  /* ===== RENDER ===== */
  function passa(a, implicitos) {
    var chaves = Object.keys(S.filtros).concat(implicitos || []);
    return chaves.every(function (k) { return FILTROS[k].f(a); });
  }
  function comparador(modo) {
    var nome = function (x, y) { return x.nome.localeCompare(y.nome, "pt"); };
    if (S.ordem === "evid") return function (x, y) { return EV_N[y.a.ev] - EV_N[x.a.ev] || nome(x.a, y.a); };
    if (S.ordem === "irrita") return function (x, y) { return x.a.irrita - y.a.irrita || nome(x.a, y.a); };
    if (S.ordem === "az") return function (x, y) { return nome(x.a, y.a); };
    if (modo === "cats") return function (x, y) { return x.a._ordem - y.a._ordem; };
    return function (x, y) { return y.pontos - x.pontos || EV_N[y.a.ev] - EV_N[x.a.ev] || nome(x.a, y.a); };
  }
  function clonar(item) {
    var li = item.a._cartao.cloneNode(true);
    li.removeAttribute("id");
    li.hidden = false;
    if (item.motivos.length) {
      var p = document.createElement("p");
      p.className = "at-porque";
      p.innerHTML = "<b>Por que apareceu:</b> " + item.motivos.join("; ") + ".";
      li.insertBefore(p, li.querySelector(".at-medidores"));
    }
    return li;
  }

  function render(foco) {
    var modo = S.rotulo ? "rotulo" : S.q ? "busca" : S.tema ? "tema" : "cats";
    var nFiltros = Object.keys(S.filtros).length;
    var contexto = "", nota = "", implicitos = [], vistos = 0;

    if (modo === "cats") {
      el.res.hidden = true;
      el.cats.hidden = false;
      var ordenar = comparador("cats");
      $$("#at-categorias .at-cat").forEach(function (sec) {
        var ul = sec.querySelector(".at-grade"), n = 0;
        var itens = Array.prototype.slice.call(ul.children).map(function (li) { return { a: POR_ID[li.getAttribute("data-id")], li: li }; });
        itens.sort(ordenar).forEach(function (it) {
          var ok = passa(it.a);
          it.li.hidden = !ok;
          if (ok) n++;
          ul.appendChild(it.li);
        });
        sec.hidden = n === 0;
        vistos += n;
      });
      contexto = nFiltros ? "Mostrando " + vistos + " de " + TOTAL + " ativos" : TOTAL + " ativos em " + $$("#at-categorias .at-cat").length + " categorias";
    } else {
      var itens, titulo;
      if (modo === "rotulo") {
        itens = lerRotulo(S.rotulo);
        titulo = "Ativos reconhecidos no rótulo";
        nota = "Reconhecemos " + itens.length + " dos " + TOTAL + " ativos do atlas nesta lista. Ingredientes que não estão no atlas não aparecem. " +
          "A lista não mostra a concentração e não comprova eficácia nem segurança da fórmula. Para ver se combinam entre si, use o " +
          '<a href="/ferramentas/ingredientes/">verificador de ingredientes</a>.';
      } else if (modo === "busca") {
        var b = buscar(S.q);
        itens = b.itens;
        implicitos = b.I.filtros.map(function (f) { return f === "gestacao" ? "gest" : f === "sem-receita" ? "semrx" : f; })
          .filter(function (f) { return FILTROS[f] && !S.filtros[f]; });
        titulo = "Resultado para “" + S.q + "”";
        if (implicitos.length) nota = "A busca aplicou o filtro: " + lista(implicitos.map(function (f) { return FILTROS[f].rotulo; })) + ".";
        if (!itens.length && implicitos.length) {
          itens = D.ativos.map(function (a) { return { a: a, pontos: EV_N[a.ev], motivos: [] }; });
        }
      } else {
        var tema = D.temas.filter(function (t) { return t.id === S.tema; })[0];
        itens = [];
        D.ativos.forEach(function (a) {
          var melhor = -1, nomes = [];
          tema.objetivos.forEach(function (o) {
            var i = a.c.indexOf(o);
            if (i < 0) return;
            nomes.push("<b>" + esc(D.objetivos[o].toLowerCase()) + "</b>" + (i === 0 ? " (objetivo principal)" : ""));
            if (melhor < 0 || i < melhor) melhor = i;
          });
          if (melhor >= 0) itens.push({ a: a, pontos: peso(melhor) + EV_N[a.ev] * 2 - (a.rx ? 5 : 0), motivos: ["costuma ser indicado para " + lista(nomes)] });
        });
        titulo = "Mapa da pele: " + tema.titulo.toLowerCase();
      }
      var antes = itens.length;
      itens = itens.filter(function (it) { return passa(it.a, implicitos); }).sort(comparador(modo));
      vistos = itens.length;
      el.resT.textContent = titulo;
      el.resNota.innerHTML = nota;
      el.resNota.hidden = !nota;
      el.resLista.textContent = "";
      itens.forEach(function (it) { el.resLista.appendChild(clonar(it)); });
      el.resVazio.hidden = vistos > 0;
      if (!vistos) {
        el.resVazio.innerHTML = antes
          ? "<p>Nenhum ativo passa pelos filtros marcados. Desmarque um filtro para ver os " + antes + " encontrados.</p>"
          : modo === "rotulo"
            ? "<p>Não reconhecemos nenhum dos " + TOTAL + " ativos do atlas nesta lista. Confira se ela está em formato INCI (nomes em inglês, separados por vírgula).</p>"
            : "<p>Não encontramos “" + esc(S.q) + "” entre os " + TOTAL + " ativos do atlas.</p><p>Tente o nome que aparece no rótulo ou um objetivo, como manchas, acne, rugas ou pele sensível. Para uma pergunta mais aberta, use o <a href=\"/pergunte/\">Pergunte à IA</a>.</p>";
      }
      el.res.hidden = false;
      el.cats.hidden = true;
      contexto = vistos + (vistos === 1 ? " ativo" : " ativos") + (modo === "rotulo" ? " reconhecidos" : " de " + TOTAL);
    }

    el.prontas.hidden = modo !== "cats";
    if (nFiltros) contexto += " · filtros: " + lista(Object.keys(S.filtros).map(function (k) { return FILTROS[k].rotulo; }));
    el.contagem.textContent = contexto;
    el.avisoGest.hidden = !(S.filtros.gest || implicitos.indexOf("gest") >= 0);
    el.limpar.hidden = modo === "cats" && !nFiltros && S.ordem === "padrao";
    $$("[data-filtro]").forEach(function (b) { b.setAttribute("aria-pressed", S.filtros[b.getAttribute("data-filtro")] ? "true" : "false"); });
    sincronizarComparar();
    if (foco && modo !== "cats") {
      el.res.scrollIntoView({ block: "start", behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
      el.resT.focus({ preventScroll: true });
    }
  }

  /* ===== COMBINAÇÕES (regras do verificador) ===== */
  function combinacoes(a) {
    if (!R) return "<p>As regras de combinação não carregaram. Use o <a href=\"/ferramentas/ingredientes/\">verificador de ingredientes</a>.</p>";
    if (!a.classe) {
      return "<p>O <a href=\"/ferramentas/ingredientes/\">verificador de ingredientes</a> ainda não tem regra de combinação para este ativo, então não sabemos dizer com o que ele combina. Na dúvida, use em horários diferentes dos ativos mais fortes e introduza um ativo novo por vez.</p>";
    }
    var grupos = {}, ordem = [];
    CLASSES.forEach(function (c) {
      var r = R.avaliarPar({ classe: a.classe }, { classe: c });
      if (c === a.classe && (r.regra === "sem-regra" || r.regra.indexOf("neutra-") === 0)) return;
      var rot = c === a.classe ? "outro ativo da mesma família" : ROTULO_CLASSE[c];
      var chave = r.resultado + "|" + r.motivo + "|" + r.nota;
      if (!grupos[chave]) { grupos[chave] = { r: r, com: [] }; ordem.push(chave); }
      grupos[chave].com.push(rot);
    });
    var peso = { nao: 0, horarios: 1, sem_regra: 2, ok: 3 };
    ordem.sort(function (x, y) { return peso[grupos[x].r.resultado] - peso[grupos[y].r.resultado]; });
    return '<ul class="at-combina">' + ordem.map(function (k) {
      var g = grupos[k];
      return '<li class="' + g.r.resultado + '"><span class="at-veredito">' + VEREDITO[g.r.resultado] + "</span><b>Com " + esc(lista(g.com)) + ":</b> " +
        esc(g.r.motivo) + (g.r.nota ? " <i>" + esc(g.r.nota) + "</i>" : "") + "</li>";
    }).join("") + '</ul><p class="ig-nota">Regras do <a href="/ferramentas/ingredientes/">verificador de ingredientes</a>, versão ' + esc(D.regras) + ". São orientações de uso comuns, sem citação de estudo.</p>";
  }
  function parDeAtivos(a, b) {
    var titulo = "<b>" + esc(a.nome) + " com " + esc(b.nome) + ":</b> ";
    if (!R || !a.classe || !b.classe) {
      var sem = [a, b].filter(function (x) { return !x.classe; }).map(function (x) { return x.nome; });
      return '<li class="sem_regra"><span class="at-veredito">' + VEREDITO.sem_regra + "</span>" + titulo +
        "o verificador ainda não tem regra de combinação para " + esc(lista(sem)) + ". Isso não quer dizer que é seguro usar junto: na dúvida, use em horários diferentes e introduza um ativo novo por vez.</li>";
    }
    var r = R.avaliarPar({ classe: a.classe }, { classe: b.classe });
    return '<li class="' + r.resultado + '"><span class="at-veredito">' + VEREDITO[r.resultado] + "</span>" + titulo + esc(r.motivo) + (r.nota ? " <i>" + esc(r.nota) + "</i>" : "") + "</li>";
  }

  /* ===== JANELAS ===== */
  var janela = null, voltarFoco = null;
  function abrirJanela(titulo, sub, corpo, larga, hash) {
    fecharJanela(true);
    voltarFoco = document.activeElement;
    janela = document.createElement("dialog");
    janela.className = "at-janela" + (larga ? " larga" : "");
    janela.setAttribute("aria-labelledby", "at-janela-t");
    janela.innerHTML = '<div class="at-janela-dentro"><div class="at-janela-topo"><div><h2 id="at-janela-t" tabindex="-1">' + titulo + "</h2>" +
      (sub ? "<p>" + sub + "</p>" : "") + '</div><button type="button" class="at-fechar" data-fechar>Fechar</button></div>' +
      '<div class="at-janela-corpo">' + corpo + "</div></div>";
    raiz.appendChild(janela);
    /* Fecha por conta própria: o evento "close" do <dialog> nem sempre chega (aba em segundo plano). */
    var esta = janela;
    esta.addEventListener("cancel", function (e) { e.preventDefault(); if (janela === esta) fecharJanela(); });
    esta.addEventListener("close", function () { if (janela === esta) fecharJanela(); });
    esta.addEventListener("click", function (e) { if (e.target === esta && janela === esta) fecharJanela(); });
    if (janela.showModal) janela.showModal(); else janela.setAttribute("open", "");
    janela.querySelector("#at-janela-t").focus();
    if (hash) history.replaceState(null, "", "#" + hash);
  }
  function fecharJanela(silencioso) {
    if (!janela) return;
    var j = janela;
    janela = null;
    if (j.open && j.close) j.close();
    j.remove();
    if (silencioso) return;
    if (/^#(ativo|comparar)=/.test(location.hash)) history.replaceState(null, "", location.pathname + location.search);
    if (voltarFoco && document.contains(voltarFoco)) voltarFoco.focus();
  }

  function abrirPassaporte(id) {
    var a = POR_ID[id];
    if (!a) return;
    var cuidados = [];
    if (a.rx) cuidados.push("É medicamento: só use com prescrição.");
    if (a.sol) cuidados.push("Aumenta a sensibilidade ao sol: protetor solar todas as manhãs é parte do uso.");
    cuidados.push(a.irrita === 2 ? "Pode irritar bastante no início. Introduza um ativo novo por vez."
      : a.irrita === 1 ? "Pode irritar um pouco no início. Comece devagar e observe a pele." : "A chance de irritar é baixa, mas faça um teste numa área pequena antes.");
    cuidados.push(GEST[a.gest]);
    var estudos = a.ev
      ? '<p><span class="at-selo ok">Evidência ' + esc(a.ev) + "</span></p><p>" + esc(a.evm) + '</p><p><a href="' + a.url + '#o-que-faz">O que os estudos sugerem</a> · <a href="' + a.url + '#fontes">Fontes</a></p>'
      : "<p><b>Evidência ainda não avaliada.</b> O site ainda não avaliou os estudos deste ativo. A ficha resume orientações de uso comuns em dermatologia cosmética e não cita estudos. Isso não diz se o ativo funciona ou não.</p>";
    var corpo =
      '<dl class="at-pass-med"><div><dt>Evidência</dt><dd>' + medEv(a) + "</dd></div><div><dt>Irritação</dt><dd>" + medIr(a) + "</dd></div><div><dt>Nível</dt><dd>" + medNv(a) + "</dd></div></dl>" +
      "<section><h3>Para que é usado</h3><p>" + esc(a.d) + "</p><p>Objetivos, do mais ao menos comum: " + esc(lista(objetivos(a))) + ".</p></section>" +
      "<section><h3>O que os estudos mostram</h3>" + estudos + "</section>" +
      "<section><h3>Para quem</h3><p>" + esc(peles(a)) + ". Nível " + NIVEL[a.nivel] + ".</p></section>" +
      "<section><h3>Como usar</h3><ul><li><b>Quando:</b> " + TURNO[a.turno].toLowerCase() + ".</li><li><b>Concentração usual:</b> " + esc(a.conc) + ".</li>" +
      (a.dica ? "<li><b>Dica:</b> " + esc(a.dica) + "</li>" : "") + "</ul></section>" +
      "<section><h3>Cuidados</h3><ul>" + cuidados.map(function (c) { return "<li>" + esc(c) + "</li>"; }).join("") + "</ul></section>" +
      "<section><h3>Combinações</h3>" + combinacoes(a) + "</section>" +
      "<section><h3>Fontes e revisão</h3><p>" + (a.ev ? "Esta ficha tem estudos e fontes listados." : "Esta ficha não cita estudos.") +
      (a.rev ? " Última revisão da ficha: " + dataLonga(a.rev) + "." : "") + '</p><p class="at-acoes"><a class="at-bt cheio" href="' + a.url + '">Abrir a ficha completa</a>' +
      '<button type="button" class="at-bt" data-comparar="' + a.id + '" aria-pressed="false">Comparar</button>' +
      '<a class="at-bt" href="/ferramentas/ativos/#ativo=' + a.id + '">Ver no guia, com produtos</a></p></section>';
    abrirJanela(esc(a.n), "No rótulo (INCI): " + esc(a.inci) + " · " + esc(a.cat), corpo, false, "ativo=" + a.id);
    sincronizarComparar();
  }

  function abrirComparador(ids) {
    var as = ids.map(function (i) { return POR_ID[i]; }).filter(Boolean).slice(0, 3);
    if (as.length < 2) return;
    function linha(rotulo, f) { return "<tr><th scope=\"row\">" + rotulo + "</th>" + as.map(function (a) { return "<td>" + f(a) + "</td>"; }).join("") + "</tr>"; }
    var pares = [];
    for (var i = 0; i < as.length; i++) for (var j = i + 1; j < as.length; j++) pares.push(parDeAtivos(as[i], as[j]));
    var corpo = '<div class="at-rolagem"><table class="at-tabela" style="--n:' + as.length + '"><thead><tr><td></td>' +
      as.map(function (a) { return '<th scope="col">' + esc(a.nome) + "<small>" + esc(a.inci) + "</small></th>"; }).join("") + "</tr></thead><tbody>" +
      linha("Objetivos", function (a) { return "<ul>" + objetivos(a).map(function (o) { return "<li>" + esc(o) + "</li>"; }).join("") + "</ul>"; }) +
      linha("Evidência", function (a) { return medEv(a) + (a.ev ? "<br><small>" + esc(a.evm) + "</small>" : "<br><small>O site ainda não avaliou os estudos.</small>"); }) +
      linha("Irritação", medIr) +
      linha("Nível", medNv) +
      linha("Para quem", function (a) { return esc(peles(a)); }) +
      linha("Quando", function (a) { return TURNO[a.turno]; }) +
      linha("Concentração usual", function (a) { return esc(a.conc); }) +
      linha("Gestação", function (a) { return esc(GEST[a.gest]); }) +
      linha("Sol", function (a) { return a.sol ? "Aumenta a sensibilidade ao sol" : "Sem alerta de sol no guia"; }) +
      linha("Receita", function (a) { return a.rx ? "Medicamento: só com prescrição" : "Uso cosmético, sem receita"; }) +
      linha("Limites e dica", function (a) { return esc(a.dica || "Sem observação no guia."); }) +
      linha("Ficha", function (a) { return '<a href="' + a.url + '">Abrir a ficha</a>' + (a.rev ? "<br><small>Revisada em " + dataLonga(a.rev) + "</small>" : ""); }) +
      "</tbody></table></div>" +
      "<section><h3>Dá para usar juntos?</h3><ul class=\"at-combina\">" + pares.join("") + "</ul>" +
      '<p class="ig-nota">Regras do <a href="/ferramentas/ingredientes/">verificador de ingredientes</a>, versão ' + esc(D.regras) + ". Orientações de uso comuns, sem citação de estudo. Preço não entra na comparação: o atlas não tem esse dado por ativo.</p></section>" +
      '<p class="at-acoes"><button type="button" class="at-bt" data-copiar-link>Copiar o link desta comparação</button></p>';
    abrirJanela("Comparação lado a lado", esc(lista(as.map(function (a) { return a.nome; }))), corpo, true, "comparar=" + as.map(function (a) { return a.id; }).join(","));
  }

  /* ===== BANDEJA DO COMPARADOR ===== */
  var bandeja = document.createElement("div");
  bandeja.className = "at-bandeja";
  bandeja.setAttribute("role", "region");
  bandeja.setAttribute("aria-label", "Comparador");
  bandeja.hidden = true;
  raiz.appendChild(bandeja);
  function sincronizarComparar(aviso) {
    $$("[data-comparar]").forEach(function (b) {
      var dentro = S.comp.indexOf(b.getAttribute("data-comparar")) >= 0;
      b.setAttribute("aria-pressed", dentro ? "true" : "false");
      b.textContent = dentro ? "No comparador" : "Comparar";
    });
    bandeja.hidden = !S.comp.length;
    raiz.classList.toggle("com-bandeja", !!S.comp.length);
    if (!S.comp.length) return;
    bandeja.innerHTML = '<p role="status">' + (aviso || "Comparar " + S.comp.length + " de 3") + "</p><ul>" +
      S.comp.map(function (id) { return '<li><button type="button" class="at-chip" data-tirar="' + id + '" aria-label="Tirar ' + esc(POR_ID[id].nome) + ' do comparador">' + esc(POR_ID[id].nome) + ' <span aria-hidden="true">×</span></button></li>'; }).join("") +
      '</ul><button type="button" class="at-bt cheio" data-abrir-comparador' + (S.comp.length < 2 ? " disabled" : "") + ">" +
      (S.comp.length < 2 ? "Escolha mais um" : "Comparar agora") + "</button>";
  }
  function alternarComparar(id) {
    var i = S.comp.indexOf(id), aviso = "";
    if (i >= 0) S.comp.splice(i, 1);
    else if (S.comp.length >= 3) aviso = "O máximo é 3. Tire um para trocar.";
    else S.comp.push(id);
    sincronizarComparar(aviso);
  }

  /* ===== MAPA DA PELE ===== */
  function escolherTema(id) {
    $$(".at-tema").forEach(function (p) { p.hidden = p.getAttribute("data-tema") !== id; });
    $$(".at-temas [data-tema]").forEach(function (b) { b.setAttribute("aria-pressed", b.getAttribute("data-tema") === id ? "true" : "false"); });
    $$(".at-zona").forEach(function (z) { z.classList.toggle("ativa", z.getAttribute("data-tema") === id); });
  }

  /* ===== EVENTOS ===== */
  function limparModo() { S.q = ""; S.rotulo = ""; S.tema = ""; }
  raiz.addEventListener("click", function (e) {
    var t = e.target.closest ? e.target.closest("button,[data-tema]") : null;
    if (!t || !raiz.contains(t)) return;
    var v;
    if ((v = t.getAttribute("data-passaporte"))) abrirPassaporte(v);
    else if ((v = t.getAttribute("data-comparar"))) alternarComparar(v);
    else if ((v = t.getAttribute("data-tirar"))) alternarComparar(v);
    else if (t.hasAttribute("data-abrir-comparador")) abrirComparador(S.comp);
    else if ((v = t.getAttribute("data-comparacao"))) abrirComparador(v.split(","));
    else if (t.hasAttribute("data-fechar")) fecharJanela();
    else if (t.hasAttribute("data-copiar-link")) {
      var link = location.href;
      if (navigator.clipboard) navigator.clipboard.writeText(link).then(function () { t.textContent = "Link copiado"; }, function () { t.textContent = link; });
      else t.textContent = link;
    }
    else if ((v = t.getAttribute("data-filtro"))) { if (S.filtros[v]) delete S.filtros[v]; else S.filtros[v] = 1; render(); }
    else if ((v = t.getAttribute("data-q"))) { limparModo(); S.q = v; el.q.value = v; render(true); }
    else if ((v = t.getAttribute("data-ver-tema"))) { limparModo(); S.tema = v; el.q.value = ""; render(true); }
    else if ((v = t.getAttribute("data-tema"))) escolherTema(v);
    else if (t === el.limpar) {
      limparModo(); S.filtros = {}; S.ordem = "padrao"; el.ordem.value = "padrao"; el.q.value = ""; el.inci.value = "";
      render(); el.q.focus();
    }
    else if (t.id === "at-ler") { limparModo(); S.rotulo = el.inci.value.trim(); el.q.value = ""; render(!!S.rotulo); }
  });
  el.busca.addEventListener("submit", function (e) {
    e.preventDefault();
    limparModo(); S.q = el.q.value.trim();
    render(!!S.q);
  });
  var espera = 0;
  el.q.addEventListener("input", function () {
    clearTimeout(espera);
    espera = setTimeout(function () { limparModo(); S.q = el.q.value.trim(); render(); }, 160);
  });
  el.ordem.addEventListener("change", function () { S.ordem = el.ordem.value; render(); });

  function lerHash() {
    var m = /^#(ativo|comparar|q|tema)=(.+)$/.exec(location.hash);
    if (!m) return;
    var v;
    try { v = decodeURIComponent(m[2]); } catch (err) { return; }
    if (m[1] === "ativo") abrirPassaporte(v);
    else if (m[1] === "comparar") abrirComparador(v.split(","));
    else if (m[1] === "q") { limparModo(); S.q = v.slice(0, 80); el.q.value = S.q; render(true); }
    else if (m[1] === "tema" && D.temas.some(function (t) { return t.id === v; })) { escolherTema(v); limparModo(); S.tema = v; render(true); }
  }
  window.addEventListener("hashchange", lerHash);

  /* O site tem cabeçalho fixo: o painel de filtros gruda logo abaixo dele. */
  function medirTopo() {
    var topo = document.querySelector(".ps-topo");
    var fixo = topo && getComputedStyle(topo).position === "sticky";
    raiz.style.setProperty("--at-topo", (fixo ? topo.offsetHeight : 0) + "px");
  }
  window.addEventListener("resize", medirTopo);
  window.addEventListener("load", medirTopo);

  /* ===== LIGAR ===== */
  medirTopo();
  raiz.classList.add("atlas-js");
  [el.busca, el.rotulo, el.painel, el.prontas, $(".at-temas")].forEach(function (x) { if (x) x.hidden = false; });
  escolherTema("barreira");
  render();
  lerHash();
})();
