/* Rótulos guardados: a lista de ingredientes (INCI) de um frasco, com data e lote, salva só neste aparelho,
 * e a comparação entre duas listas. Usado por /ferramentas/reformulacao/.
 *
 * A comparação é de texto contra texto: diz o que está numa lista e não está na outra, e o que mudou de posição.
 * Não diz por que mudou nem se a mudança importa para a pele. Leitura por foto troca letras: nomes quase iguais
 * entram como "parecidos", para a pessoa conferir no frasco: não são contados como troca nem como iguais.
 */
(function (raiz) {
  "use strict";
  var CHAVE = "ps-rotulos-v1";

  function semAcento(s) { return s.normalize ? s.normalize("NFD").replace(/[̀-ͯ]/g, "") : s; }

  /* Texto do rótulo -> lista de ingredientes, na ordem do rótulo. Cada item: { nome, chaves }.
   * "chaves" são as formas de comparar: o nome inteiro e cada parte separada por barra (AQUA / WATER / EAU). */
  function listar(texto) {
    var t = String(texto || "").replace(/\r?\n/g, " ");
    var m = t.match(/(ingredient[se]s?|ingredientes|composi[cç][aã]o|inci)\s*[:\-]/i);
    if (m) t = t.slice(m.index + m[0].length);
    t = t.replace(/(\d),(\d)/g, "$1\u0001$2");                 // vírgula dentro de nome: 1,2-HEXANEDIOL
    var vistos = {}, saida = [];
    t.split(/[,;•·|]/).forEach(function (parte) {
      var nome = parte.replace(/\u0001/g, ",").replace(/\[[^\]]*\]/g, " ").replace(/[*.]+\s*$/g, "").replace(/^[\s*.\-]+/, "").replace(/\s+/g, " ").trim();
      if (nome.length < 2 || nome.length > 90) return;
      var limpo = semAcento(nome).toUpperCase();
      var inteiro = limpo.replace(/[^A-Z0-9]/g, "");
      if (inteiro.length < 2 || vistos[inteiro]) return;
      vistos[inteiro] = 1;
      var chaves = [inteiro];
      limpo.split("/").forEach(function (p) {
        var k = p.replace(/\([^)]*\)/g, "").replace(/[^A-Z0-9]/g, "");
        if (k.length >= 3 && chaves.indexOf(k) < 0) chaves.push(k);
      });
      saida.push({ nome: limpo.replace(/\s*\/\s*/g, " / "), chaves: chaves });
    });
    return saida;
  }

  function mesmo(a, b) { return a.chaves.some(function (k) { return b.chaves.indexOf(k) >= 0; }); }

  function distancia(a, b, teto) {
    if (Math.abs(a.length - b.length) > teto) return teto + 1;
    var ant = [], i, j;
    for (j = 0; j <= b.length; j++) ant[j] = j;
    for (i = 1; i <= a.length; i++) {
      var atual = [i], menor = i;
      for (j = 1; j <= b.length; j++) {
        atual[j] = Math.min(ant[j] + 1, atual[j - 1] + 1, ant[j - 1] + (a.charCodeAt(i - 1) === b.charCodeAt(j - 1) ? 0 : 1));
        if (atual[j] < menor) menor = atual[j];
      }
      if (menor > teto) return teto + 1;
      ant = atual;
    }
    return ant[b.length];
  }

  /* Compara a lista anterior (A) com a nova (B).
   * iguais: [{ nome, de, para }]  (posições, começando em 1)
   * parecidos: [{ antes, agora, de, para }]  nomes quase iguais: pode ser erro de leitura ou outro ingrediente
   *            de nome próximo (METHYLPARABEN x ETHYLPARABEN). A página manda conferir no frasco.
   * saiu: [{ nome, de }]   entrou: [{ nome, para }]
   * moveu: itens de "iguais" que mudaram 3 ou mais posições entre os ingredientes comuns */
  function comparar(textoA, textoB) {
    var A = listar(textoA), B = listar(textoB);
    var usadoB = {}, iguais = [], parecidos = [], sobraA = [];
    A.forEach(function (a, i) {
      for (var j = 0; j < B.length; j++) {
        if (!usadoB[j] && mesmo(a, B[j])) { usadoB[j] = 1; iguais.push({ nome: B[j].nome, de: i + 1, para: j + 1 }); return; }
      }
      sobraA.push({ item: a, pos: i + 1 });
    });
    var saiu = [];
    sobraA.forEach(function (s) {
      var k = s.item.chaves[0], teto = Math.min(3, Math.max(1, Math.floor(k.length * 0.2))), melhor = -1, melhorD = teto + 1;
      for (var j = 0; j < B.length; j++) {
        if (usadoB[j]) continue;
        var d = distancia(k, B[j].chaves[0], teto);
        if (d < melhorD) { melhorD = d; melhor = j; }
      }
      if (melhor >= 0) { usadoB[melhor] = 1; parecidos.push({ antes: s.item.nome, agora: B[melhor].nome, de: s.pos, para: melhor + 1 }); }
      else saiu.push({ nome: s.item.nome, de: s.pos });
    });
    var entrou = [];
    B.forEach(function (b, j) { if (!usadoB[j]) entrou.push({ nome: b.nome, para: j + 1 }); });

    // Posição relativa só entre os ingredientes que estão nas duas listas (quem entrou ou saiu não conta como deslocamento).
    var comuns = iguais.concat(parecidos.map(function (p) { return { nome: p.agora, de: p.de, para: p.para }; }));
    var ordemA = comuns.slice().sort(function (x, y) { return x.de - y.de; });
    var ordemB = comuns.slice().sort(function (x, y) { return x.para - y.para; });
    var moveu = [];
    comuns.forEach(function (c) {
      var ra = ordemA.indexOf(c) + 1, rb = ordemB.indexOf(c) + 1;
      if (Math.abs(ra - rb) >= 3) moveu.push({ nome: c.nome, de: c.de, para: c.para });
    });
    moveu.sort(function (x, y) { return x.para - y.para; });

    return { totalA: A.length, totalB: B.length, iguais: iguais, parecidos: parecidos, saiu: saiu, entrou: entrou, moveu: moveu,
      comparavel: A.length >= 3 && B.length >= 3,
      mesmaLista: A.length >= 3 && B.length >= 3 && !saiu.length && !entrou.length && !parecidos.length,
      soConferir: A.length >= 3 && B.length >= 3 && !saiu.length && !entrou.length && parecidos.length > 0 };
  }

  /* ---- guardados neste aparelho ---- */
  function ler() {
    try { var d = JSON.parse(localStorage.getItem(CHAVE) || "[]"); return Array.isArray(d) ? d : []; } catch (e) { return []; }
  }
  function gravar(l) { try { localStorage.setItem(CHAVE, JSON.stringify(l)); return true; } catch (e) { return false; } }
  function chaveProduto(nome) { return semAcento(String(nome || "")).toUpperCase().replace(/[^A-Z0-9]/g, ""); }
  function guardar(r) {
    var l = ler();
    var novo = { id: "r" + Date.now().toString(36) + Math.random().toString(36).slice(2, 6), produto: String(r.produto || "").trim().slice(0, 120),
      data: r.data, lote: String(r.lote || "").trim().slice(0, 40), texto: String(r.texto || "").trim().slice(0, 6000), guardadoEm: Date.now() };
    l.push(novo);
    return gravar(l) ? novo : null;
  }
  function remover(id) { return gravar(ler().filter(function (r) { return r.id !== id; })); }
  /* Rótulo guardado mais recente do mesmo produto, anterior ao informado. */
  function anteriorDe(rotulo) {
    var k = chaveProduto(rotulo.produto);
    var outros = ler().filter(function (r) { return r.id !== rotulo.id && chaveProduto(r.produto) === k; });
    outros.sort(function (a, b) { return a.data < b.data ? 1 : a.data > b.data ? -1 : b.guardadoEm - a.guardadoEm; });
    return outros[0] || null;
  }

  var api = { CHAVE: CHAVE, listar: listar, comparar: comparar, ler: ler, guardar: guardar, remover: remover, anteriorDe: anteriorDe, chaveProduto: chaveProduto };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else raiz.PSRotulos = api;
})(typeof window !== "undefined" ? window : this);
