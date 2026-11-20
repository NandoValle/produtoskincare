/* Busca inteligente por ingrediente/produto — Produto Skincare
   Motor de busca com autocomplete: normalização sem acento, sinônimos de
   ativos (BHA → ácido salicílico), tolerância a erro de digitação e
   sugestões navegáveis por teclado. Fonte de dados: /produtos.json e
   /ingredientes/ingredientes.json (mesmos do provador). */
(function () {
  "use strict";

  // ---------- dados ----------
  var PRODUTOS = [];
  var INGREDIENTES = [];
  var CARREGADO = false;

  // sinônimos/expansões: cada grupo é um conjunto de termos equivalentes
  var GRUPOS_SINONIMO = [
    ["bha", "ácido salicílico", "salicílico", "salicilico"],
    ["aha", "ácido mandélico", "mandélico", "mandelico", "ácido glicólico", "glicólico", "ácido láctico", "láctico"],
    ["vitamina c", "ácido ascórbico", "ascórbico", "ascorbico"],
    ["vitamina a", "retinol", "retinoide", "retinoides"],
    ["b3", "niacinamida"],
    ["b5", "pantenol", "dexpantenol"],
    ["ha", "ácido hialurônico", "hialurônico", "hialuronico"],
    ["spf", "fps", "protetor solar", "protetor"],
    ["ceramida", "ceramidas"],
    ["peptídeo", "peptideo", "peptídeos", "peptideos", "peptídeo de cobre", "cobre"],
    ["ácido azelaico", "azelaico"],
    ["ácido ferúlico", "ferulico", "ferúlico"],
    ["ácido tranexâmico", "tranexamico", "tranexâmico"],
    ["zinco", "zinc"],
    ["argila", "máscara de argila"],
    ["karité", "karite", "manteiga de karité"],
    ["ureia"]
  ];
  var MAPA_SINONIMO = {};
  GRUPOS_SINONIMO.forEach(function (g) {
    g.forEach(function (t) {
      if (!MAPA_SINONIMO[t]) MAPA_SINONIMO[t] = [];
      g.forEach(function (o) { if (o !== t && MAPA_SINONIMO[t].indexOf(o) < 0) MAPA_SINONIMO[t].push(o); });
    });
  });

  var GUIAS_PELE = [
    { chave: "oleosa", nome: "Pele oleosa", url: "/pele/oleosa/", dica: "brilho, poros, cravos" },
    { chave: "seca", nome: "Pele seca", url: "/pele/seca/", dica: "repuxamento, descamação" },
    { chave: "mista", nome: "Pele mista", url: "/pele/mista/", dica: "zona T oleosa, bochechas secas" },
    { chave: "normal", nome: "Pele normal", url: "/pele/normal/", dica: "equilibrada" }
  ];

  var POPULARES = ["niacinamida", "retinol", "vitamina C", "ácido hialurônico", "protetor solar", "cerave", "ácido salicílico", "ceramidas"];

  // ---------- texto ----------
  function norm(s) {
    return String(s || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim();
  }

  // distância de edição simples (limite 1) para tolerar erro de digitação
  function edicao1(a, b) {
    if (Math.abs(a.length - b.length) > 1) return false;
    if (a === b) return true;
    var i = 0, j = 0, dif = 0;
    while (i < a.length && j < b.length) {
      if (a[i] === b[j]) { i++; j++; continue; }
      if (++dif > 1) return false;
      if (a.length > b.length) i++;
      else if (a.length < b.length) j++;
      else { i++; j++; }
    }
    return true;
  }

  function expandir(termo) {
    var t = norm(termo);
    var saida = [t];
    Object.keys(MAPA_SINONIMO).forEach(function (k) {
      // termos curtos (ha, b3, b5…) só casam por igualdade — "bha" não deve virar "ha"
      var casa = k.length <= 3 ? (t === k) : (t.indexOf(k) >= 0 || k.indexOf(t) >= 0);
      if (casa) {
        MAPA_SINONIMO[k].forEach(function (s) { if (saida.indexOf(s) < 0) saida.push(s); });
      }
    });
    return saida;
  }

  // pontuação de um item contra os termos expandidos
  function pontuar(alvo, termos, pesos) {
    var melhor = 0;
    termos.forEach(function (t) {
      if (!t) return;
      if (alvo === t) melhor = Math.max(melhor, pesos.exato);
      else if (alvo.indexOf(t) === 0) melhor = Math.max(melhor, pesos.prefixo);
      else if (alvo.indexOf(t) >= 0) melhor = Math.max(melhor, pesos.contem);
      else if (t.length >= 4) {
        // tolerância a erro de digitação em palavras
        alvo.split(/\s+/).forEach(function (p) {
          if (p.length >= 3 && edicao1(p, t)) melhor = Math.max(melhor, pesos.fuzzy);
        });
      }
    });
    return melhor;
  }

  function buscar(termo) {
    var termos = expandir(termo);
    var resIng = [];
    var resProd = [];
    var resGuias = [];

    INGREDIENTES.forEach(function (ing) {
      var s = 0;
      s = Math.max(s, pontuar(norm(ing.nome), termos, { exato: 100, prefixo: 80, contem: 60, fuzzy: 45 }));
      s = Math.max(s, pontuar(norm(ing.slug.replace(/-/g, " ")), termos, { exato: 100, prefixo: 75, contem: 55, fuzzy: 40 }));
      s = Math.max(s, pontuar(norm(ing.resumo), termos, { exato: 40, prefixo: 25, contem: 22, fuzzy: 0 }) * 0.5);
      if (s > 0) resIng.push({ item: ing, score: s });
    });

    PRODUTOS.forEach(function (p) {
      var s = 0;
      s = Math.max(s, pontuar(norm(p.nome), termos, { exato: 100, prefixo: 80, contem: 60, fuzzy: 45 }));
      s = Math.max(s, pontuar(norm(p.marca), termos, { exato: 90, prefixo: 70, contem: 50, fuzzy: 35 }));
      s = Math.max(s, pontuar(norm(p.grupo || ""), termos, { exato: 70, prefixo: 55, contem: 40, fuzzy: 25 }));
      s = Math.max(s, pontuar(norm((p.ativos || []).join(" ")), termos, { exato: 85, prefixo: 70, contem: 55, fuzzy: 35 }));
      s = Math.max(s, pontuar(norm(p.porque || ""), termos, { exato: 35, prefixo: 22, contem: 20, fuzzy: 0 }) * 0.5);
      // tipo de pele e passo da rotina
      termos.forEach(function (t) {
        if (["oleosa", "seca", "mista", "normal", "sensivel", "sensível"].indexOf(t) >= 0) {
          var tt = t === "sensível" ? "sensivel" : t;
          if ((p.tipos || []).indexOf(tt) >= 0 || (p.tipos || []).indexOf("todos") >= 0) s = Math.max(s, 45);
        }
        if (["limpeza", "tratamento", "hidratacao", "hidratação", "protetor"].indexOf(t) >= 0) {
          var pp = t === "hidratação" ? "hidratacao" : t;
          if (norm(p.passo) === pp) s = Math.max(s, 45);
        }
      });
      if (s > 0) resProd.push({ item: p, score: s });
    });

    GUIAS_PELE.forEach(function (g) {
      if (pontuar(norm(g.nome) + " " + norm(g.dica), termos, { exato: 100, prefixo: 80, contem: 60, fuzzy: 30 }) > 0) {
        resGuias.push({ item: g, score: 90 });
      }
    });

    resIng.sort(function (a, b) { return b.score - a.score; });
    resProd.sort(function (a, b) { return b.score - a.score; });
    resGuias.sort(function (a, b) { return b.score - a.score; });
    return { ingredientes: resIng, produtos: resProd, guias: resGuias };
  }

  // ---------- UI ----------
  var el = function (id) { return document.getElementById(id); };

  function fmtPreco(v) {
    if (v == null) return "";
    return "R$ " + Number(v).toFixed(2).replace(".", ",");
  }

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function cardIngrediente(ing) {
    return '<a class="bs-card" href="' + esc(ing.url) + '">' +
      '<span class="bs-tag bs-tag-ing">Ingrediente</span>' +
      '<strong>' + esc(ing.nome) + "</strong>" +
      '<span class="bs-sub">Evidência ' + esc(ing.evidencia) + "</span>" +
      '<span class="bs-desc">' + esc(ing.resumo) + "</span>" +
      '<span class="bs-ir">Ver ficha →</span></a>';
  }

  function cardProduto(p) {
    var ativos = (p.ativos || []).slice(0, 3).join(" · ");
    return '<a class="bs-card" href="/produtos/' + esc(p.id) + '/">' +
      '<span class="bs-tag bs-tag-prod">Produto</span>' +
      '<strong>' + esc(p.nome) + "</strong>" +
      '<span class="bs-sub">' + esc(p.marca) + (p.preco != null ? " · " + esc(fmtPreco(p.preco)) : "") +
      (p.avaliacao ? " · " + esc(p.avaliacao) + "★" : "") + "</span>" +
      (ativos ? '<span class="bs-desc">Ativos: ' + esc(ativos) + "</span>" : "") +
      '<span class="bs-ir">Ver produto →</span></a>';
  }

  function cardGuia(g) {
    return '<a class="bs-card" href="' + esc(g.url) + '">' +
      '<span class="bs-tag bs-tag-guia">Guia</span>' +
      "<strong>" + esc(g.nome) + "</strong>" +
      '<span class="bs-sub">' + esc(g.dica) + "</span>" +
      '<span class="bs-ir">Abrir guia →</span></a>';
  }

  function renderResultados(termo) {
    var alvo = el("bs-resultados");
    if (!alvo) return;
    if (!termo || !termo.trim()) {
      alvo.innerHTML = '<p class="bs-vazio">Digite um ingrediente (niacinamida, retinol…), um produto (CeraVe…) ou algo como <em>protetor solar</em> ou <em>pele oleosa</em>.</p>';
      return;
    }
    var r = buscar(termo);
    var html = "";
    var total = r.ingredientes.length + r.produtos.length + r.guias.length;

    if (total === 0) {
      alvo.innerHTML = '<div class="bs-card bs-card-aviso"><strong>Nada encontrado para "' + esc(termo) + '"</strong>' +
        '<span class="bs-desc">Tente o nome de um ativo (niacinamida, ácido salicílico), uma marca (CeraVe, Eucerin) ' +
        "ou um passo da rotina (limpeza, protetor). Se preferir, o catálogo completo está em " +
        '<a href="/produtos/">/produtos/</a>.</span></div>';
      return;
    }

    html += '<p class="bs-contagem">' + total + " resultado" + (total > 1 ? "s" : "") + ' para "' + esc(termo) + '"</p>';

    if (r.ingredientes.length) {
      html += '<h2 class="bs-secao">Ingredientes</h2><div class="bs-grade">';
      r.ingredientes.slice(0, 6).forEach(function (x) { html += cardIngrediente(x.item); });
      html += "</div>";
    }
    if (r.produtos.length) {
      html += '<h2 class="bs-secao">Produtos</h2><div class="bs-grade">';
      r.produtos.slice(0, 12).forEach(function (x) { html += cardProduto(x.item); });
      html += "</div>";
    }
    if (r.guias.length) {
      html += '<h2 class="bs-secao">Guias</h2><div class="bs-grade">';
      r.guias.forEach(function (x) { html += cardGuia(x.item); });
      html += "</div>";
    }
    alvo.innerHTML = html;
  }

  // ---------- autocomplete ----------
  var SUGESTOES_ATIVAS = -1;

  function renderSugestoes(termo) {
    var painel = el("bs-sugestoes");
    if (!painel) return;
    if (!termo || termo.trim().length < 1) {
      painel.hidden = true;
      painel.innerHTML = "";
      SUGESTOES_ATIVAS = -1;
      return;
    }
    var r = buscar(termo);
    var itens = [];
    r.ingredientes.slice(0, 3).forEach(function (x) {
      itens.push({ tipo: "Ingrediente", nome: x.item.nome, sub: "evidência " + x.item.evidencia, url: x.item.url });
    });
    r.produtos.slice(0, 4).forEach(function (x) {
      itens.push({
        tipo: "Produto", nome: x.item.nome,
        sub: x.item.marca + (x.item.preco != null ? " · " + fmtPreco(x.item.preco) : ""),
        url: "/produtos/" + x.item.id + "/"
      });
    });
    r.guias.slice(0, 1).forEach(function (x) {
      itens.push({ tipo: "Guia", nome: x.item.nome, sub: x.item.dica, url: x.item.url });
    });

    if (!itens.length) {
      painel.hidden = true;
      painel.innerHTML = "";
      SUGESTOES_ATIVAS = -1;
      return;
    }

    var html = "";
    itens.slice(0, 8).forEach(function (it, i) {
      html += '<li class="bs-sug" role="option" id="bs-sug-' + i + '" aria-selected="false" data-url="' + esc(it.url) + '">' +
        '<span class="bs-sug-tipo">' + esc(it.tipo) + "</span>" +
        "<span><strong>" + esc(it.nome) + '</strong><span class="bs-sug-sub">' + esc(it.sub) + "</span></span></li>";
    });
    painel.innerHTML = html;
    painel.hidden = false;
    SUGESTOES_ATIVAS = -1;

    Array.prototype.forEach.call(painel.querySelectorAll(".bs-sug"), function (li) {
      li.addEventListener("mousedown", function (e) {
        e.preventDefault();
        window.location.href = li.getAttribute("data-url");
      });
    });
  }

  function moverSugestao(delta) {
    var painel = el("bs-sugestoes");
    if (!painel || painel.hidden) return;
    var itens = painel.querySelectorAll(".bs-sug");
    if (!itens.length) return;
    SUGESTOES_ATIVAS = (SUGESTOES_ATIVAS + delta + itens.length) % itens.length;
    Array.prototype.forEach.call(itens, function (li, i) {
      var sel = i === SUGESTOES_ATIVAS;
      li.setAttribute("aria-selected", sel ? "true" : "false");
      li.classList.toggle("bs-sug-ativa", sel);
      if (sel) li.scrollIntoView({ block: "nearest" });
    });
  }

  // ---------- ligação ----------
  function iniciar() {
    var campo = el("bs-campo");
    var painel = el("bs-sugestoes");
    if (!campo) return;

    // chips populares
    var chips = el("bs-chips");
    if (chips) {
      POPULARES.forEach(function (t) {
        var b = document.createElement("button");
        b.type = "button";
        b.className = "bs-chip";
        b.textContent = t;
        b.addEventListener("click", function () {
          campo.value = t;
          renderSugestoes("");
          painel.hidden = true;
          renderResultados(t);
          campo.focus();
        });
        chips.appendChild(b);
      });
    }

    var debounce;
    campo.addEventListener("input", function () {
      clearTimeout(debounce);
      debounce = setTimeout(function () {
        renderSugestoes(campo.value);
        renderResultados(campo.value);
      }, 120);
    });

    campo.addEventListener("keydown", function (e) {
      if (e.key === "ArrowDown") { e.preventDefault(); moverSugestao(1); }
      else if (e.key === "ArrowUp") { e.preventDefault(); moverSugestao(-1); }
      else if (e.key === "Escape") {
        if (painel && !painel.hidden) { painel.hidden = true; SUGESTOES_ATIVAS = -1; }
      } else if (e.key === "Enter") {
        var ativo = painel && !painel.hidden ? painel.querySelector(".bs-sug-ativa") : null;
        if (ativo) {
          e.preventDefault();
          window.location.href = ativo.getAttribute("data-url");
        } else {
          e.preventDefault();
          renderSugestoes("");
          if (painel) painel.hidden = true;
          renderResultados(campo.value);
        }
      }
    });

    campo.addEventListener("blur", function () {
      setTimeout(function () { if (painel) painel.hidden = true; }, 150);
    });

    // busca inicial via ?q=
    var q = new URLSearchParams(window.location.search).get("q");
    if (q) {
      campo.value = q;
      renderResultados(q);
    } else {
      renderResultados("");
    }

    // formulário sem JS ainda funciona: GET /ferramentas/busca/?q=...
    var form = el("bs-form");
    if (form) {
      form.addEventListener("submit", function (e) {
        e.preventDefault();
        renderSugestoes("");
        painel.hidden = true;
        renderResultados(campo.value);
      });
    }
  }

  // carrega dados (mesmos JSONs do provador)
  function carregar() {
    var pProd = fetch("/produtos.json", { cache: "no-cache" })
      .then(function (r) { return r.ok ? r.json() : { produtos: [] }; })
      .then(function (d) { PRODUTOS = d.produtos || []; })
      .catch(function () { PRODUTOS = []; });
    var pIng = fetch("/ingredientes/ingredientes.json", { cache: "no-cache" })
      .then(function (r) { return r.ok ? r.json() : []; })
      .then(function (l) { INGREDIENTES = l || []; })
      .catch(function () { INGREDIENTES = []; });
    Promise.all([pProd, pIng]).then(function () {
      CARREGADO = true;
      iniciar();
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", carregar);
  } else {
    carregar();
  }
})();
