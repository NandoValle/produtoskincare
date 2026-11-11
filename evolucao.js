/* Evolução da pele — leitura dos dados locais e gráficos SVG. Tudo no aparelho. Idioma: <html lang>. */
(function () {
  "use strict";

  var LANG = (document.documentElement.lang || "pt-BR").toLowerCase();
  var L = LANG.indexOf("pt") === 0 ? "pt" : LANG.indexOf("es") === 0 ? "es" : "en";
  var LOCALE = L === "pt" ? "pt-BR" : L === "es" ? "es-ES" : "en-GB";

  var T = {
    pt: { grafico: "Gráfico da sua evolução ao longo do tempo", barras: "Dias com rotina completa por semana", de5: "de 5", min: "pior dia", max: "melhor dia",
      dia: "dia", doAcomp: "do acompanhamento", proximo: "próximo marco", em: "em", dias: "dias", semDados: "Sua curva começa no primeiro registro.", primeiroVs: "primeiro vs. agora" },
    en: { grafico: "Chart of your progress over time", barras: "Days with a complete routine, by week", de5: "of 5", min: "worst day", max: "best day",
      dia: "day", doAcomp: "of your follow-up", proximo: "next mark", em: "in", dias: "days", semDados: "Your curve starts with the first record.", primeiroVs: "first vs. now" },
    es: { grafico: "Gráfico de tu evolución en el tiempo", barras: "Días con rutina completa, por semana", de5: "de 5", min: "peor día", max: "mejor día",
      dia: "día", doAcomp: "del seguimiento", proximo: "próximo marco", em: "en", dias: "días", semDados: "Tu curva empieza con el primer registro.", primeiroVs: "primero vs. ahora" }
  }[L];

  var DIMS = [
    { id: "vico", cor: "#c97f92",
      rotulo: { pt: "Viço", en: "Radiance", es: "Luminosidad" },
      de: { pt: "opaca", en: "dull", es: "opaca" },
      para: { pt: "luminosa", en: "glowing", es: "luminosa" } },
    { id: "conforto", cor: "#3f6b55",
      rotulo: { pt: "Conforto", en: "Comfort", es: "Confort" },
      de: { pt: "irritada", en: "irritated", es: "irritada" },
      para: { pt: "calma", en: "calm", es: "tranquila" } },
    { id: "equilibrio", cor: "#b98a2f",
      rotulo: { pt: "Equilíbrio", en: "Balance", es: "Equilibrio" },
      de: { pt: "descontrolada", en: "unruly", es: "descontrolada" },
      para: { pt: "equilibrada", en: "balanced", es: "equilibrada" } },
    { id: "uniformidade", cor: "#5b6fa8",
      rotulo: { pt: "Uniformidade", en: "Evenness", es: "Uniformidad" },
      de: { pt: "manchada", en: "blotchy", es: "manchada" },
      para: { pt: "uniforme", en: "even", es: "uniforme" } }
  ].map(function (d) {
    return {
      id: d.id, cor: d.cor,
      rotulo: d.rotulo[L] || d.rotulo.pt,
      de: d.de[L] || d.de.pt,
      para: d.para[L] || d.para.pt
    };
  });

  var CICLOS = [28, 56, 84, 112, 168];
  var BD = "ps_diario_site", LOJA = "fotos";

  function abrirBD() {
    return new Promise(function (res, rej) {
      if (!window.indexedDB) { rej(new Error("sem indexedDB")); return; }
      var req = indexedDB.open(BD, 1);
      req.onupgradeneeded = function () {
        if (!req.result.objectStoreNames.contains(LOJA)) req.result.createObjectStore(LOJA, { keyPath: "id", autoIncrement: true });
      };
      req.onsuccess = function () { res(req.result); };
      req.onerror = function () { rej(req.error); };
    });
  }

  function operar(escrita, fn) {
    return abrirBD().then(function (bd) {
      return new Promise(function (res, rej) {
        var t = bd.transaction(LOJA, escrita ? "readwrite" : "readonly");
        var s = t.objectStore(LOJA);
        var saida = fn(s);
        t.oncomplete = function () { res(saida && saida.result !== undefined ? saida.result : saida); };
        t.onerror = function () { rej(t.error); };
      });
    });
  }

  function registros() {
    return operar(false, function (s) { return s.getAll(); }).then(function (lista) {
      return (lista || []).slice().sort(function (a, b) { return String(a.data).localeCompare(String(b.data)); });
    });
  }

  function salvarHoje(rec) {
    var hoje = dataHoje();
    return registros().then(function (lista) {
      var existente = null;
      for (var i = 0; i < lista.length; i++) { if (lista[i].data === hoje) { existente = lista[i]; break; } }
      if (existente) {
        var mesclado = {
          id: existente.id, data: hoje, criadoEm: existente.criadoEm, atualizadoEm: Date.now(),
          nota: rec.nota !== undefined ? rec.nota : existente.nota,
          foto: rec.foto !== undefined ? rec.foto : existente.foto,
          scores: rec.scores ? Object.assign({}, existente.scores || {}, rec.scores) : (existente.scores || null)
        };
        return operar(true, function (s) { return s.put(mesclado); }).then(function () { return mesclado; });
      }
      var novo = { data: hoje, nota: rec.nota || "", foto: rec.foto || null, scores: rec.scores || null, criadoEm: Date.now() };
      return operar(true, function (s) { return s.add(novo); }).then(function (id) { novo.id = id; return novo; });
    });
  }

  function remover(id) { return operar(true, function (s) { return s.delete(Number(id)); }); }

  function dataHoje() {
    var d = new Date();
    return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
  }

  function diffDias(a, b) { return Math.round((Date.parse(b + "T12:00:00") - Date.parse(a + "T12:00:00")) / 86400000); }

  function fmtData(iso) {
    return new Date(iso + "T12:00:00").toLocaleDateString(LOCALE, { day: "numeric", month: "long", year: "numeric" });
  }
  function fmtCurta(iso) {
    return new Date(iso + "T12:00:00").toLocaleDateString(LOCALE, { day: "2-digit", month: "2-digit" });
  }

  function mediaScores(s) {
    if (!s) return null;
    var v = [];
    DIMS.forEach(function (d) { if (typeof s[d.id] === "number") v.push(s[d.id]); });
    if (!v.length) return null;
    return v.reduce(function (a, b) { return a + b; }, 0) / v.length;
  }

  function analisar(regs, tracker) {
    regs = regs || [];
    tracker = tracker || {};
    var comNota = regs.filter(function (r) { return mediaScores(r.scores) !== null; });
    var serie = comNota.map(function (r) {
      return { data: r.data, media: mediaScores(r.scores), scores: r.scores };
    });
    var primeiro = comNota[0] || null, ultimo = comNota[comNota.length - 1] || null;
    var deltas = null;
    if (primeiro && ultimo && primeiro !== ultimo) {
      deltas = {};
      DIMS.forEach(function (d) {
        var a = primeiro.scores[d.id], b = ultimo.scores[d.id];
        if (typeof a === "number" && typeof b === "number") deltas[d.id] = b - a;
      });
    }
    var refData = (regs[0] || {}).data || dataHoje();
    var dias = diffDias(refData, dataHoje());
    var marcos = CICLOS.map(function (c) {
      var alvo = somaDias(refData, c);
      var atingido = diffDias(refData, dataHoje()) >= c;
      var ponto = null, melhor = Infinity;
      serie.forEach(function (p) {
        var dd = Math.abs(diffDias(alvo, p.data));
        if (dd < melhor && dd <= 14) { melhor = dd; ponto = p; }
      });
      return { dias: c, data: alvo, atingido: atingido, ponto: ponto, faltam: Math.max(0, c - dias) };
    });
    var constancia = constanciaSemanal(tracker);
    return {
      registros: regs, comNota: comNota, serie: serie, dias: dias,
      refData: refData, primeiro: primeiro, ultimo: ultimo, deltas: deltas,
      marcos: marcos, constancia: constancia,
      temDados: serie.length > 0, temAlgum: regs.length > 0
    };
  }

  function somaDias(iso, n) {
    var d = new Date(iso + "T12:00:00");
    d.setDate(d.getDate() + n);
    return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
  }

  function rotinaCompleta(r) {
    if (!r) return false;
    var m = ["m1", "m2", "m3", "m4"].every(function (id) { return r[id]; });
    var n = ["n1", "n2", "n3"].every(function (id) { return r[id]; });
    return m || n;
  }

  function constanciaSemanal(tracker) {
    var semanas = [];
    var hoje = new Date(dataHoje() + "T12:00:00");
    var inicio = new Date(hoje);
    var diaSem = (inicio.getDay() + 6) % 7; /* segunda = 0 */
    inicio.setDate(inicio.getDate() - diaSem - 7 * 7); /* 8 semanas, a atual por último */
    for (var w = 0; w < 8; w++) {
      var diasCom = 0, passados = 0;
      for (var d = 0; d < 7; d++) {
        var dt = new Date(inicio);
        dt.setDate(inicio.getDate() + w * 7 + d);
        if (dt > hoje) break;
        passados++;
        var iso = dt.getFullYear() + "-" + String(dt.getMonth() + 1).padStart(2, "0") + "-" + String(dt.getDate()).padStart(2, "0");
        if (rotinaCompleta(tracker[iso])) diasCom++;
      }
      if (passados > 0) {
        semanas.push({
          inicio: (function () { var x = new Date(inicio); x.setDate(inicio.getDate() + w * 7); return x.getFullYear() + "-" + String(x.getMonth() + 1).padStart(2, "0") + "-" + String(x.getDate()).padStart(2, "0"); })(),
          pct: Math.round(diasCom / passados * 100), diasCom: diasCom, passados: passados
        });
      }
    }
    return semanas;
  }

  /* ===== Gráfico de linha (autopercepção) ===== */
  function graficoSVG(a, opts) {
    opts = opts || {};
    var ativas = opts.ativas || { media: true };
    if (!a || a.serie.length === 0) return "";
    var W = 640, H = 250, padL = 40, padR = 16, padT = 18, padB = 36;
    var pw = W - padL - padR, ph = H - padT - padB;
    var serie = a.serie;
    var t0 = Date.parse(serie[0].data + "T12:00:00");
    var t1 = Date.parse(serie[serie.length - 1].data + "T12:00:00");
    if (t1 === t0) t1 = t0 + 86400000;
    function X(iso) { return padL + (Date.parse(iso + "T12:00:00") - t0) / (t1 - t0) * pw; }
    function Y(v) { return padT + (5 - v) / 4 * ph; }

    var s = [];
    s.push('<svg viewBox="0 0 ' + W + " " + H + '" width="100%" role="img" aria-label="' + T.grafico + '" style="display:block;height:auto">');
    /* grade */
    for (var v = 1; v <= 5; v++) {
      s.push('<line x1="' + padL + '" y1="' + Y(v).toFixed(1) + '" x2="' + (W - padR) + '" y2="' + Y(v).toFixed(1) + '" stroke="rgba(26,22,20,0.08)" stroke-width="1"/>');
      s.push('<text x="' + (padL - 10) + '" y="' + (Y(v) + 4).toFixed(1) + '" text-anchor="end" font-size="11" fill="#7a6e65">' + v + "</text>");
    }
    /* marcos de ciclo atingidos */
    a.marcos.forEach(function (mk) {
      if (!mk.atingido) return;
      var x = X(mk.data);
      if (x < padL || x > W - padR) return;
      s.push('<line x1="' + x.toFixed(1) + '" y1="' + padT + '" x2="' + x.toFixed(1) + '" y2="' + (H - padB) + '" stroke="#b4546a" stroke-width="1" stroke-dasharray="3 4" opacity="0.35"/>');
      s.push('<text x="' + x.toFixed(1) + '" y="' + (padT - 4) + '" text-anchor="middle" font-size="10" fill="#b4546a">' + mk.dias + "d</text>");
    });
    /* eixo x */
    var nTicks = Math.min(5, serie.length);
    for (var i = 0; i < nTicks; i++) {
      var idx = nTicks === 1 ? 0 : Math.round(i * (serie.length - 1) / (nTicks - 1));
      s.push('<text x="' + X(serie[idx].data).toFixed(1) + '" y="' + (H - padB + 18) + '" text-anchor="middle" font-size="11" fill="#7a6e65">' + fmtCurta(serie[idx].data) + "</text>");
    }
    /* área + linha composta */
    function pontos(fn) {
      return serie.map(function (p) { return X(p.data).toFixed(1) + "," + Y(fn(p)).toFixed(1); }).join(" ");
    }
    if (ativas.media) {
      if (serie.length > 1) {
        var pts = pontos(function (p) { return p.media; });
        s.push('<polygon points="' + padL + "," + (H - padB) + " " + pts + " " + (W - padR) + "," + (H - padB) + '" fill="rgba(180,84,106,0.08)"/>');
        s.push('<polyline points="' + pts + '" fill="none" stroke="#b4546a" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>');
      }
      serie.forEach(function (p) {
        s.push('<circle cx="' + X(p.data).toFixed(1) + '" cy="' + Y(p.media).toFixed(1) + '" r="4.5" fill="#fff" stroke="#b4546a" stroke-width="2"><title>' + fmtData(p.data) + " · " + p.media.toFixed(1) + " " + T.de5 + "</title></circle>");
      });
    }
    /* linhas por dimensão */
    DIMS.forEach(function (d) {
      if (!ativas[d.id]) return;
      var pts = pontos(function (p) { return p.scores[d.id]; });
      if (serie.length > 1) {
        s.push('<polyline points="' + pts + '" fill="none" stroke="' + d.cor + '" stroke-width="1.6" stroke-linejoin="round" opacity="0.9"/>');
      }
      serie.forEach(function (p) {
        if (typeof p.scores[d.id] !== "number") return;
        s.push('<circle cx="' + X(p.data).toFixed(1) + '" cy="' + Y(p.scores[d.id]).toFixed(1) + '" r="3" fill="' + d.cor + '"><title>' + d.rotulo + " · " + fmtData(p.data) + " · " + p.scores[d.id] + " " + T.de5 + "</title></circle>");
      });
    });
    s.push("</svg>");
    return s.join("");
  }

  /* ===== Barras de constância semanal ===== */
  function barrasSVG(a) {
    if (!a || !a.constancia.length) return "";
    var sem = a.constancia;
    var W = 640, H = 96, padB = 24, padT = 10;
    var bw = Math.min(56, (W - 20) / sem.length - 12);
    var gap = (W - 20 - bw * sem.length) / Math.max(1, sem.length - 1);
    var s = ['<svg viewBox="0 0 ' + W + " " + H + '" width="100%" role="img" aria-label="' + T.barras + '" style="display:block;height:auto">'];
    var base = H - padB;
    s.push('<line x1="10" y1="' + base + '" x2="' + (W - 10) + '" y2="' + base + '" stroke="rgba(26,22,20,0.12)" stroke-width="1"/>');
    sem.forEach(function (w, i) {
      var x = 10 + i * (bw + gap);
      var h = Math.max(2, (w.pct / 100) * (base - padT));
      s.push('<rect x="' + x.toFixed(1) + '" y="' + (base - h).toFixed(1) + '" width="' + bw.toFixed(1) + '" height="' + h.toFixed(1) + '" rx="5" fill="' + (w.pct >= 70 ? "#3f6b55" : w.pct >= 40 ? "#b4546a" : "#c9b8a8") + '" opacity="0.9"><title>' + fmtCurta(w.inicio) + " · " + w.diasCom + " / " + w.passados + "</title></rect>");
      s.push('<text x="' + (x + bw / 2).toFixed(1) + '" y="' + (base + 16) + '" text-anchor="middle" font-size="10" fill="#7a6e65">' + fmtCurta(w.inicio) + "</text>");
    });
    s.push("</svg>");
    return s.join("");
  }

  /* ===== Sparkline compacta (linha composta) ===== */
  function sparklineSVG(a) {
    if (!a || a.serie.length === 0) return "";
    var W = 320, H = 88, padL = 8, padR = 8, padT = 12, padB = 12;
    var pw = W - padL - padR, ph = H - padT - padB;
    var serie = a.serie;
    var t0 = Date.parse(serie[0].data + "T12:00:00");
    var t1 = Date.parse(serie[serie.length - 1].data + "T12:00:00");
    if (t1 === t0) t1 = t0 + 86400000;
    function X(iso) { return padL + (Date.parse(iso + "T12:00:00") - t0) / (t1 - t0) * pw; }
    function Y(v) { return padT + (5 - v) / 4 * ph; }
    var s = ['<svg viewBox="0 0 ' + W + " " + H + '" width="100%" style="display:block;max-width:340px;height:auto" role="img" aria-label="' + T.grafico + '">'];
    var pts = serie.map(function (p) { return X(p.data).toFixed(1) + "," + Y(p.media).toFixed(1); }).join(" ");
    if (serie.length > 1) {
      s.push('<polygon points="' + padL + "," + (H - padB) + " " + pts + " " + (W - padR) + "," + (H - padB) + '" fill="rgba(180,84,106,0.10)"/>');
      s.push('<polyline points="' + pts + '" fill="none" stroke="#b4546a" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>');
    }
    serie.forEach(function (p) {
      s.push('<circle cx="' + X(p.data).toFixed(1) + '" cy="' + Y(p.media).toFixed(1) + '" r="4" fill="#fff" stroke="#b4546a" stroke-width="2"><title>' + fmtData(p.data) + " · " + p.media.toFixed(1) + " " + T.de5 + "</title></circle>");
    });
    s.push("</svg>");
    return s.join("");
  }

  /* ===== Cartão-resumo reutilizável (home, tracker) ===== */
  function cartaoResumo(a) {
    if (!a || !a.temDados) {
      return '<p class="evo-sem">' + T.semDados + "</p>";
    }
    var deltas = "";
    if (a.deltas) {
      var partes = [];
      DIMS.forEach(function (d) {
        var v = a.deltas[d.id];
        if (typeof v !== "number" || v === 0) return;
        partes.push('<span class="evo-chip">' + d.rotulo + " " + (v > 0 ? "↑" : "↓") + " " + Math.abs(v) + "</span>");
      });
      if (partes.length) deltas = '<div class="evo-chips">' + partes.join("") + '<span class="evo-chip evo-chip-legenda">' + T.primeiroVs + "</span></div>";
    }
    var proximo = null;
    a.marcos.forEach(function (mk) { if (!mk.atingido && !proximo) proximo = mk; });
    var marcoHTML = proximo
      ? '<p class="evo-marco">' + T.proximo + " " + T.em + " " + proximo.faltam + " " + T.dias + " (" + T.dia + " " + proximo.dias + ")</p>"
      : "";
    return '<p class="evo-num">' + a.dias + ' <span class="evo-num-leg">' + T.dia + " " + T.doAcomp + "</span></p>" +
      sparklineSVG(a) + deltas + marcoHTML;
  }

  window.PSEvolucao = {
    DIMS: DIMS, CICLOS: CICLOS, idioma: L,
    abrirBD: abrirBD, registros: registros, salvarHoje: salvarHoje, remover: remover,
    dataHoje: dataHoje, diffDias: diffDias, fmtData: fmtData, fmtCurta: fmtCurta,
    mediaScores: mediaScores, analisar: analisar,
    graficoSVG: graficoSVG, barrasSVG: barrasSVG,
    sparklineSVG: sparklineSVG, cartaoResumo: cartaoResumo
  };
})();
