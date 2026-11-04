/* Receber resultados por WhatsApp e e-mail, sem servidor.
 * O envio sai do WhatsApp ou do e-mail da própria pessoa: o site não recebe
 * nem guarda número, endereço ou resultado.
 *
 * Uso:
 *   PSEnviar.montar(elemento, () => ({ assunto, texto, url }), { lembretes: [...] })
 * `texto` é o resultado em texto simples; `url` é o link para reabrir o resultado.
 * `lembretes` (opcional) gera um arquivo .ics para a agenda: [{ titulo, descricao, inicio: Date, diario: bool }]
 */
(function () {
  "use strict";
  var LIMITE_EMAIL = 1800; // alguns apps de e-mail cortam links mailto muito longos

  var CSS = ".pse{background:var(--papel,#fff);border:1px solid var(--linha,#dce1de);border-radius:var(--raio,16px);padding:18px;margin:20px 0;display:flex;flex-direction:column;gap:14px}" +
    ".pse h3{margin:0;font-size:1.3rem}.pse p{margin:0}" +
    ".pse-nota{font-size:.84rem;color:var(--suave,#596360)}" +
    ".pse-linha{display:flex;flex-wrap:wrap;gap:8px;align-items:center}" +
    ".pse-linha input{flex:1 1 200px;min-height:46px;padding:0 14px;border-radius:12px;border:1px solid var(--linha-2,#c8d0cb);background:var(--papel,#fff);color:var(--tinta,#252b2a);font:inherit}" +
    ".pse-btn{min-height:46px;padding:0 18px;border-radius:999px;border:0;font:inherit;font-weight:600;cursor:pointer;display:inline-flex;align-items:center;gap:8px;text-decoration:none}" +
    ".pse-wa{background:#1f7a4d;color:#fff}.pse-mail{background:var(--rosa,#9b405b);color:#fff}" +
    ".pse-sec{background:transparent;color:var(--tinta,#252b2a);border:1px solid var(--linha-2,#c8d0cb)}" +
    ".pse-btn:hover{filter:brightness(.93)}" +
    ".pse label{font-weight:600;font-size:.92rem;display:block;margin-bottom:6px}" +
    ".pse-ok{font-size:.86rem;color:var(--verde,#375d4e);min-height:1.2em}";

  function estilo() {
    if (document.getElementById("pse-css")) return;
    var s = document.createElement("style");
    s.id = "pse-css";
    s.textContent = CSS;
    document.head.appendChild(s);
  }

  function contar(evento) {
    try { if (window.PSAnalytics) window.PSAnalytics.evento(evento); } catch (e) {}
  }

  function soDigitos(v) { return String(v || "").replace(/\D/g, ""); }

  function linkWhatsApp(numero, texto) {
    var d = soDigitos(numero);
    if (d.length === 10 || d.length === 11) d = "55" + d; // DDD + número, sem o 55
    var base = d.length >= 12 ? "https://wa.me/" + d : "https://wa.me/";
    return base + "?text=" + encodeURIComponent(texto);
  }

  function linkEmail(email, assunto, texto, url) {
    var corpo = texto;
    if (corpo.length > LIMITE_EMAIL) {
      corpo = corpo.slice(0, LIMITE_EMAIL).replace(/\s+\S*$/, "") + "\n\n(continua no link abaixo)\n" + (url || "");
    }
    var para = String(email || "").trim();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(para)) para = "";
    return "mailto:" + encodeURIComponent(para).replace(/%40/g, "@") +
      "?subject=" + encodeURIComponent(assunto) + "&body=" + encodeURIComponent(corpo);
  }

  function dataICS(d) {
    function p(n) { return String(n).padStart(2, "0"); }
    return d.getFullYear() + p(d.getMonth() + 1) + p(d.getDate()) + "T" + p(d.getHours()) + p(d.getMinutes()) + "00";
  }
  function escICS(t) { return String(t || "").replace(/\\/g, "\\\\").replace(/\n/g, "\\n").replace(/([,;])/g, "\\$1"); }

  function baixarICS(lembretes, nomeArquivo) {
    var agora = new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d+/, ""); // UTC, ex.: 20261104T093000Z
    var linhas = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Produto Skincare//Lembretes//PT-BR", "CALSCALE:GREGORIAN"];
    lembretes.forEach(function (l, i) {
      var fim = new Date(l.inicio.getTime() + 10 * 60000);
      linhas.push("BEGIN:VEVENT",
        "UID:" + agora + "-" + i + "@produtoskincare.com.br",
        "DTSTAMP:" + agora,
        "DTSTART:" + dataICS(l.inicio),
        "DTEND:" + dataICS(fim),
        "SUMMARY:" + escICS(l.titulo),
        "DESCRIPTION:" + escICS(l.descricao));
      if (l.diario) linhas.push("RRULE:FREQ=DAILY");
      linhas.push("BEGIN:VALARM", "ACTION:DISPLAY", "DESCRIPTION:" + escICS(l.titulo), "TRIGGER:PT0M", "END:VALARM", "END:VEVENT");
    });
    linhas.push("END:VCALENDAR");
    var blob = new Blob([linhas.join("\r\n")], { type: "text/calendar;charset=utf-8" });
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = nomeArquivo || "lembretes-skincare.ics";
    document.body.appendChild(a);
    a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
  }

  function el(tag, attrs, texto) {
    var n = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) { n.setAttribute(k, attrs[k]); });
    if (texto != null) n.textContent = texto;
    return n;
  }

  var contador = 0;
  function montar(alvo, obterConteudo, opcoes) {
    if (!alvo) return;
    estilo();
    opcoes = opcoes || {};
    contador += 1;
    var id = "pse" + contador;
    var caixa = el("section", { "class": "pse", "aria-labelledby": id + "-t" });
    caixa.appendChild(el("h3", { id: id + "-t" }, opcoes.titulo || "Receber este resultado"));
    caixa.appendChild(el("p", { "class": "pse-nota" },
      "O envio sai do seu WhatsApp ou do seu e-mail. O site não recebe nem guarda seu número, seu endereço ou seu resultado."));

    // WhatsApp
    var bWa = el("div");
    bWa.appendChild(el("label", { "for": id + "-tel" }, "Seu WhatsApp (opcional, com DDD)"));
    var lWa = el("div", { "class": "pse-linha" });
    var tel = el("input", { id: id + "-tel", type: "tel", inputmode: "tel", autocomplete: "tel-national", placeholder: "Ex.: 11 91234-5678" });
    var btWa = el("button", { type: "button", "class": "pse-btn pse-wa" }, "Enviar no WhatsApp");
    lWa.appendChild(tel); lWa.appendChild(btWa); bWa.appendChild(lWa);
    caixa.appendChild(bWa);

    // E-mail
    var bEm = el("div");
    bEm.appendChild(el("label", { "for": id + "-mail" }, "Seu e-mail (opcional)"));
    var lEm = el("div", { "class": "pse-linha" });
    var mail = el("input", { id: id + "-mail", type: "email", inputmode: "email", autocomplete: "email", placeholder: "voce@exemplo.com" });
    var btEm = el("button", { type: "button", "class": "pse-btn pse-mail" }, "Enviar por e-mail");
    lEm.appendChild(mail); lEm.appendChild(btEm); bEm.appendChild(lEm);
    caixa.appendChild(bEm);

    var extras = el("div", { "class": "pse-linha" });
    var btCop = el("button", { type: "button", "class": "pse-btn pse-sec" }, "Copiar texto");
    extras.appendChild(btCop);
    var btIcs = null;
    if (typeof opcoes.lembretes === "function" || (opcoes.lembretes && opcoes.lembretes.length)) {
      btIcs = el("button", { type: "button", "class": "pse-btn pse-sec" }, "Lembretes na agenda (.ics)");
      extras.appendChild(btIcs);
    }
    caixa.appendChild(extras);
    var ok = el("p", { "class": "pse-ok", role: "status" });
    caixa.appendChild(ok);
    if (btIcs) caixa.appendChild(el("p", { "class": "pse-nota" }, opcoes.notaLembretes ||
      "O arquivo .ics abre no Google Agenda, no Calendário do iPhone e no Outlook. Os lembretes ficam só na sua agenda."));

    function conteudo() {
      var c = obterConteudo() || {};
      var texto = (c.texto || "").trim();
      if (c.url) texto += "\n\nVer de novo: " + c.url;
      return { assunto: c.assunto || "Meu resultado no Produto Skincare", texto: texto, url: c.url || location.href };
    }

    btWa.addEventListener("click", function () {
      var c = conteudo();
      window.open(linkWhatsApp(tel.value, c.texto), "_blank", "noopener");
      contar("enviar/whatsapp");
    });
    btEm.addEventListener("click", function () {
      var c = conteudo();
      location.href = linkEmail(mail.value, c.assunto, c.texto, c.url);
      contar("enviar/email");
    });
    btCop.addEventListener("click", function () {
      var c = conteudo();
      var pronto = function () { ok.textContent = "Texto copiado. Cole onde quiser."; };
      if (navigator.clipboard) {
        navigator.clipboard.writeText(c.texto).then(pronto, function () { ok.textContent = "Não deu para copiar automaticamente."; });
      }
      contar("enviar/copiar");
    });
    if (btIcs) btIcs.addEventListener("click", function () {
      var l = typeof opcoes.lembretes === "function" ? opcoes.lembretes() : opcoes.lembretes;
      baixarICS(l, opcoes.arquivoICS);
      ok.textContent = "Arquivo de lembretes baixado. Abra-o para adicionar à sua agenda.";
      contar("enviar/agenda");
    });

    alvo.appendChild(caixa);
    return caixa;
  }

  window.PSEnviar = { montar: montar, linkWhatsApp: linkWhatsApp, linkEmail: linkEmail, baixarICS: baixarICS };
})();
