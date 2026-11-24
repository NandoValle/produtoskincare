/* "Ouvir este guia": lê o texto da página em voz alta com a voz do próprio aparelho (Web Speech API).
 * Nada é enviado a servidor nenhum e o texto continua todo na página — o áudio é só outro jeito de acompanhar.
 * Carregado pelo premium.js nas páginas de leitura (guias, artigos, fichas). Sem suporte no navegador, não aparece.
 */
(function () {
  "use strict";
  var fala = window.speechSynthesis;
  if (!fala || !window.SpeechSynthesisUtterance || window.PSOuvir) return;
  var main = document.querySelector("main");
  var h1 = main && main.querySelector("h1");
  if (!h1) return;

  var FORA = "nav,footer,form,script,style,noscript,button,select,figure,[hidden],[aria-hidden=true],.ig-top,.ig-foot,.ig-fontes,.ig-trilha,.ig-meta,.post-data,.ps-ouvir,.marca,.nav-tipos,.abas";
  var VELOCIDADES = [["0.8", "0,8×"], ["1", "1×"], ["1.25", "1,25×"], ["1.5", "1,5×"]];
  var CHAVE = "ps-ouvir-vel";

  // Cada bloco de texto vira um trecho; a linha de tabela é lida célula a célula.
  function trechos() {
    var lista = [];
    main.querySelectorAll("h1,h2,h3,h4,p,li,dt,dd,tr,summary").forEach(function (el) {
      if (el.closest(FORA)) return;
      if (el !== h1 && !(h1.compareDocumentPosition(el) & Node.DOCUMENT_POSITION_FOLLOWING)) return; // só do título em diante
      if (el.parentElement.closest("p,li,dd,tr")) return; // já lido dentro do bloco de fora
      if (!el.getClientRects().length) return; // escondido (aba fechada, <details> fechado)
      var texto;
      if (el.tagName === "TR") {
        texto = Array.prototype.map.call(el.cells, function (c) { return c.innerText.trim(); }).filter(Boolean).join(". ");
      } else {
        texto = el.innerText;
      }
      // Emoji e setas não são lidos: viram pausa ou somem.
      texto = String(texto || "").replace(/[\u2190-\u21FF]/g, ", ").replace(/[\u{1F000}-\u{1FAFF}\u{2600}-\u{27BF}\u{FE0F}\u{200D}]/gu, "").replace(/\s+/g, " ").replace(/^[,\s]+/, "").trim();
      if (texto.length < 2) return;
      if (/^H\d$/.test(el.tagName) && !/[.!?:]$/.test(texto)) texto += ".";
      lista.push({ el: el, texto: texto });
    });
    return lista;
  }

  // Frases longas travam a fala em alguns navegadores: corta em pedaços de até ~200 caracteres.
  function pedacos(texto) {
    var partes = texto.match(/[^.!?;:]+[.!?;:]*\s*/g) || [texto], saida = [], atual = "";
    partes.forEach(function (p) {
      while (p.length > 200) {
        var corte = p.lastIndexOf(" ", 200);
        if (corte < 80) corte = 200;
        if (atual) { saida.push(atual); atual = ""; }
        saida.push(p.slice(0, corte));
        p = p.slice(corte);
      }
      if ((atual + p).length > 200) { saida.push(atual); atual = p; } else atual += p;
    });
    if (atual.trim()) saida.push(atual);
    return saida.map(function (s) { return s.trim(); }).filter(Boolean);
  }

  function voz() {
    var vozes = fala.getVoices() || [];
    var br = vozes.filter(function (v) { return /^pt[-_]BR/i.test(v.lang); });
    var pt = vozes.filter(function (v) { return /^pt/i.test(v.lang); });
    var local = br.filter(function (v) { return v.localService; });
    return local[0] || br[0] || pt[0] || null;
  }

  var fila = [], pos = 0, sub = 0, tocando = false, marcado = null, velocidade = "1", sessao = 0;
  try { var salva = localStorage.getItem(CHAVE); if (salva && VELOCIDADES.some(function (v) { return v[0] === salva; })) velocidade = salva; } catch (e) {}

  var caixa = document.createElement("div");
  caixa.className = "ps-ouvir";
  caixa.setAttribute("role", "group");
  caixa.setAttribute("aria-label", "Ouvir este guia");
  var btn = document.createElement("button");
  btn.type = "button";
  btn.className = "ps-ouvir-btn";
  var parar = document.createElement("button");
  parar.type = "button";
  parar.className = "ps-ouvir-btn ps-ouvir-sec";
  parar.textContent = "Parar";
  parar.hidden = true;
  var rotulo = document.createElement("label");
  rotulo.className = "ps-ouvir-vel";
  rotulo.hidden = true;
  var rotuloTexto = document.createElement("span");
  rotuloTexto.textContent = "Velocidade";
  var sel = document.createElement("select");
  VELOCIDADES.forEach(function (v) {
    var o = document.createElement("option");
    o.value = v[0]; o.textContent = v[1];
    if (v[0] === velocidade) o.selected = true;
    sel.appendChild(o);
  });
  rotulo.appendChild(rotuloTexto);
  rotulo.appendChild(sel);
  var estado = document.createElement("p");
  estado.className = "ps-ouvir-nota";
  estado.setAttribute("role", "status");
  caixa.appendChild(btn);
  caixa.appendChild(parar);
  caixa.appendChild(rotulo);
  caixa.appendChild(estado);

  function desmarcar() { if (marcado) { marcado.classList.remove("ps-ouvindo"); marcado = null; } }
  function pintar() {
    var comecou = pos > 0 || sub > 0 || tocando;
    btn.textContent = tocando ? "⏸ Pausar" : (comecou ? "▶ Continuar" : "🔊 Ouvir este guia");
    btn.setAttribute("aria-pressed", String(tocando));
    parar.hidden = rotulo.hidden = !comecou;
  }

  function falar() {
    if (!tocando) return;
    if (pos >= fila.length) { encerrar("Fim do texto."); return; }
    var item = fila[pos];
    if (!item.partes) item.partes = pedacos(item.texto);
    if (sub >= item.partes.length) { pos += 1; sub = 0; falar(); return; }
    if (marcado !== item.el) { desmarcar(); marcado = item.el; marcado.classList.add("ps-ouvindo"); }
    var u = new SpeechSynthesisUtterance(item.partes[sub]);
    var v = voz();
    if (v) u.voice = v;
    u.lang = v ? v.lang : "pt-BR";
    u.rate = parseFloat(velocidade) || 1;
    var minha = sessao;
    u.onend = function () { if (minha !== sessao || !tocando) return; sub += 1; falar(); };
    u.onerror = function (ev) {
      if (minha !== sessao || !tocando) return;
      if (ev.error === "interrupted" || ev.error === "canceled") return;
      encerrar("Não deu para ler em voz alta neste navegador. O texto completo continua na página.");
    };
    fala.speak(u);
  }

  function tocar() {
    if (!fila.length) fila = trechos();
    if (!fila.length) { estado.textContent = "Não encontrei texto para ler nesta página."; return; }
    sessao += 1;
    fala.cancel();
    tocando = true;
    estado.textContent = voz() ? "" : "Este aparelho pode não ter voz em português instalada; a leitura usa a voz padrão.";
    pintar();
    falar();
  }
  // Pausar cancela a fala e guarda o ponto: o pause() nativo não funciona em vários celulares Android.
  function pausar() {
    sessao += 1;
    tocando = false;
    fala.cancel();
    pintar();
  }
  function encerrar(msg) {
    sessao += 1;
    tocando = false;
    fala.cancel();
    pos = 0; sub = 0; fila = [];
    desmarcar();
    estado.textContent = msg || "";
    pintar();
  }

  btn.addEventListener("click", function () {
    if (tocando) { pausar(); return; }
    if (pos === 0 && sub === 0 && window.PSAnalytics) window.PSAnalytics.evento("ouvir" + location.pathname, "Ouvir este guia");
    tocar();
  });
  parar.addEventListener("click", function () { encerrar(""); btn.focus(); });
  sel.addEventListener("change", function () {
    velocidade = sel.value;
    try { localStorage.setItem(CHAVE, velocidade); } catch (e) {}
    if (tocando) tocar(); // recomeça o trecho atual na velocidade nova
  });
  window.addEventListener("pagehide", function () { sessao += 1; fala.cancel(); });
  if (fala.addEventListener) fala.addEventListener("voiceschanged", function () {});
  fala.cancel(); // fala que ficou da página anterior

  pintar();
  var meta = main.querySelector(".ig-meta");
  var ancora = meta && !meta.closest("nav,footer,[hidden]") ? meta : h1;
  ancora.insertAdjacentElement("afterend", caixa);
  window.PSOuvir = { trechos: trechos, pedacos: pedacos };
})();
