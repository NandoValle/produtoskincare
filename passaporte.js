/* Passaporte da Pele: resumo do acompanhamento dentro de um link, para mostrar na consulta.
 *
 * O resumo vai inteiro no trecho depois do "#" do endereço. Esse trecho não é enviado ao servidor:
 * o navegador de quem abre o link lê e monta a página ali mesmo. Não há cadastro nem cópia no site.
 * Fotos não entram (não cabem num QR Code).
 *
 * Usado por /ferramentas/relatorio/ (monta e mostra o QR) e /ferramentas/passaporte/ (lê e mostra).
 *
 * Formato (versão 1), em JSON compacto:
 *   v: 1
 *   g: data em que foi gerado (AAAA-MM-DD)
 *   t: tipo de pele escolhido no guia de rotina (opcional)
 *   c: [manhãs completas, noites completas, dias com registro] nos últimos 30 dias
 *   b: data-base das notas; s: [[dias desde b, viço, conforto, equilíbrio, uniformidade], ...] (0 = sem nota)
 *   p: [[nome do produto, 1 manhã | 2 noite | 3 os dois, passo], ...] da Minha prateleira
 *   n: [[data, texto], ...] observações escritas pela pessoa
 * No endereço: "1d." + JSON comprimido (deflate) em base64url, ou "1j." + JSON em base64url.
 */
(function (raiz) {
  "use strict";
  var DIMS = ["vico", "conforto", "equilibrio", "uniformidade"];
  var PASSOS = ["limpeza", "tratamento", "hidratacao", "protetor", "outro"];
  var LIMITE = 1150;          // caracteres do endereço inteiro: acima disso o QR fica difícil de ler na tela
  var RE_DATA = /^\d{4}-\d{2}-\d{2}$/;

  function diff(a, b) { return Math.round((Date.parse(b + "T12:00:00") - Date.parse(a + "T12:00:00")) / 86400000); }
  function soma(iso, n) {
    var d = new Date(Date.parse(iso + "T12:00:00") + n * 86400000);
    return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
  }
  function nota15(x) { x = Math.round(Number(x)); return x >= 1 && x <= 5 ? x : 0; }
  function limpo(s, max) { s = String(s == null ? "" : s).replace(/\s+/g, " ").trim(); return s.length > max ? s.slice(0, max - 1) + "…" : s; }

  /* Monta o resumo a partir dos dados do aparelho.
   * fonte = { hoje, pele, tracker (rotina_tracker), registros (diário), notas (rotina_notas), prateleira (ps-prateleira-v1) } */
  function montar(fonte) {
    var hoje = fonte.hoje, r = { v: 1, g: hoje };
    if (/^[a-z]{3,12}$/.test(fonte.pele || "")) r.t = fonte.pele;

    var tracker = fonte.tracker || {}, m = 0, n = 0, d = 0;
    Object.keys(tracker).sort().slice(-30).forEach(function (dia) {
      var x = tracker[dia] || {};
      var cm = ["m1", "m2", "m3", "m4"].every(function (id) { return x[id]; });
      var cn = ["n1", "n2", "n3"].every(function (id) { return x[id]; });
      if (cm || cn) d++;
      if (cm) m++;
      if (cn) n++;
    });
    r.c = [m, n, d];

    var regs = (fonte.registros || []).filter(function (x) { return x && RE_DATA.test(x.data || ""); });
    var comNota = regs.filter(function (x) { return x.scores && DIMS.some(function (id) { return nota15(x.scores[id]); }); });
    if (comNota.length) {
      r.b = comNota[0].data;
      r.s = comNota.map(function (x) {
        return [diff(r.b, x.data)].concat(DIMS.map(function (id) { return nota15(x.scores[id]); }));
      });
    }

    var itens = (fonte.prateleira && fonte.prateleira.itens) || [];
    var p = itens.filter(function (i) { return i && i.nome; }).map(function (i) {
      var per = i.periodo || [];
      var cod = (per.indexOf("manha") >= 0 ? 1 : 0) + (per.indexOf("noite") >= 0 ? 2 : 0);
      return [limpo(i.nome, 60), cod || 3, Math.max(0, PASSOS.indexOf(i.passo))];
    });
    if (p.length) r.p = p;

    var obs = [];
    (fonte.notas || []).forEach(function (x) { if (x && RE_DATA.test(x.data || "") && x.texto) obs.push([x.data, limpo(x.texto, 160)]); });
    regs.forEach(function (x) { if (x.nota) obs.push([x.data, limpo(x.nota, 160)]); });
    obs.sort(function (a, b) { return a[0] < b[0] ? 1 : a[0] > b[0] ? -1 : 0; });   // mais recente primeiro
    if (obs.length) r.n = obs;
    return r;
  }

  function temDados(r) { return !!(r && ((r.s && r.s.length) || (r.p && r.p.length) || (r.n && r.n.length) || (r.c && r.c[2] > 0))); }

  /* ---- base64url e compressão ---- */
  function b64(bytes) {
    var s = "";
    for (var i = 0; i < bytes.length; i++) s += String.fromCharCode(bytes[i]);
    return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  }
  function deB64(txt) {
    txt = txt.replace(/-/g, "+").replace(/_/g, "/");
    while (txt.length % 4) txt += "=";
    var s = atob(txt), out = new Uint8Array(s.length);
    for (var i = 0; i < s.length; i++) out[i] = s.charCodeAt(i);
    return out;
  }
  function passar(bytes, fluxo) {
    return new Response(new Blob([bytes]).stream().pipeThrough(fluxo)).arrayBuffer().then(function (b) { return new Uint8Array(b); });
  }

  function codificar(r) {
    var bytes = new TextEncoder().encode(JSON.stringify(r));
    if (typeof CompressionStream === "undefined") return Promise.resolve("1j." + b64(bytes));
    return passar(bytes, new CompressionStream("deflate-raw")).then(function (c) {
      return c.length < bytes.length ? "1d." + b64(c) : "1j." + b64(bytes);
    }).catch(function () { return "1j." + b64(bytes); });
  }

  function decodificar(txt) {
    txt = String(txt || "").replace(/^#/, "");
    var tipo = txt.slice(0, 3), corpo = txt.slice(3);
    if ((tipo !== "1d." && tipo !== "1j.") || !/^[A-Za-z0-9_-]+$/.test(corpo) || corpo.length > 6000) return Promise.reject(new Error("formato"));
    var bytes;
    try { bytes = deB64(corpo); } catch (e) { return Promise.reject(e); }
    var pronto = tipo === "1j." ? Promise.resolve(bytes)
      : (typeof DecompressionStream === "undefined" ? Promise.reject(new Error("sem-descompressao")) : passar(bytes, new DecompressionStream("deflate-raw")));
    return pronto.then(function (b) {
      if (b.length > 20000) throw new Error("tamanho");
      return validar(JSON.parse(new TextDecoder().decode(b)));
    });
  }

  /* O link pode ter sido montado por qualquer pessoa: só passa o que tem o formato esperado. */
  function validar(x) {
    if (!x || x.v !== 1 || !RE_DATA.test(x.g || "")) throw new Error("formato");
    var r = { v: 1, g: x.g };
    if (typeof x.t === "string" && /^[a-z]{3,12}$/.test(x.t)) r.t = x.t;
    function int(v, max) { v = Math.round(Number(v)); return v >= 0 && v <= max ? v : 0; }
    if (Array.isArray(x.c)) r.c = [int(x.c[0], 30), int(x.c[1], 30), int(x.c[2], 30)];
    if (Array.isArray(x.s) && RE_DATA.test(x.b || "")) {
      r.b = x.b;
      r.s = x.s.filter(Array.isArray).slice(0, 400).map(function (l) {
        return [int(l[0], 4000), nota15(l[1]), nota15(l[2]), nota15(l[3]), nota15(l[4])];
      });
    }
    if (Array.isArray(x.p)) r.p = x.p.filter(Array.isArray).slice(0, 40).map(function (l) {
      return [limpo(l[0], 60), int(l[1], 3) || 3, int(l[2], 4)];
    }).filter(function (l) { return l[0]; });
    if (Array.isArray(x.n)) r.n = x.n.filter(function (l) { return Array.isArray(l) && RE_DATA.test(l[0] || ""); }).slice(0, 60).map(function (l) {
      return [l[0], limpo(l[1], 160)];
    }).filter(function (l) { return l[1]; });
    return r;
  }

  /* Registros do diário reconstruídos, no formato que /evolucao.js lê. */
  function registros(r) {
    return (r.s || []).map(function (l) {
      var scores = {};
      DIMS.forEach(function (id, i) { if (l[i + 1]) scores[id] = l[i + 1]; });
      return { data: soma(r.b, l[0]), scores: scores };
    });
  }

  /* Encolhe o resumo até o endereço caber no QR. Devolve { url, resumo, cortes }.
   * Ordem dos cortes: observações mais antigas, pontos intermediários da curva, produtos além de 12. */
  function link(base, resumo) {
    var r = JSON.parse(JSON.stringify(resumo));
    var cortes = { notas: 0, pontos: 0, produtos: 0 };
    function tentar() {
      return codificar(r).then(function (cod) {
        var url = base + "#" + cod;
        if (url.length <= LIMITE) return { url: url, resumo: r, cortes: cortes };
        if (r.n && r.n.length > 3) { r.n.pop(); cortes.notas++; return tentar(); }
        if (r.s && r.s.length > 12) {                       // tira um ponto sim, um não; mantém o primeiro e o último
          var antes = r.s.length;
          r.s = r.s.filter(function (_, i) { return i === 0 || i === antes - 1 || i % 2 === 0; });
          cortes.pontos += antes - r.s.length; return tentar();
        }
        if (r.p && r.p.length > 12) { r.p.pop(); cortes.produtos++; return tentar(); }
        if (r.n && r.n.length) { r.n.pop(); cortes.notas++; if (!r.n.length) delete r.n; return tentar(); }
        if (r.p && r.p.length > 4) { r.p.pop(); cortes.produtos++; return tentar(); }
        if (r.s && r.s.length > 2) { r.s.splice(1, 1); cortes.pontos++; return tentar(); }
        return { url: url, resumo: r, cortes: cortes };
      });
    }
    return tentar();
  }

  var api = { DIMS: DIMS, PASSOS: PASSOS, LIMITE: LIMITE, montar: montar, temDados: temDados, codificar: codificar,
    decodificar: decodificar, validar: validar, registros: registros, link: link };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else raiz.PSPassaporte = api;
})(typeof window !== "undefined" ? window : this);
