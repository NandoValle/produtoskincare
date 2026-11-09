/* Canais de contato, redes sociais e newsletter do site.
 *
 * Tudo fica DESLIGADO enquanto os campos abaixo estiverem vazios: nada aparece
 * na página e nada é enviado. Preencha só o que você tiver e publique.
 *
 * Onde aparece:
 * - Rodapé de todas as páginas: link "Contato" e links das redes sociais.
 * - Antes do rodapé: caixa de newsletter (se newsletter_form ou newsletter_link estiver preenchido).
 * - Página /contato/: lista dos canais e o formulário "Sugira um produto".
 */
(function () {
  "use strict";
  var CANAIS = {
    email: "contato@produtoskincare.com.br",
    whatsapp: "",         // número com DDD, só dígitos, ex.: "31912345678"
    instagram: "",        // usuário, sem @
    tiktok: "",           // usuário, sem @
    youtube: "",          // handle, sem @

    // Newsletter: preencha UM dos dois.
    // 1) newsletter_form: endereço "action" do formulário de inscrição do seu serviço
    //    (Buttondown, Brevo, Mailchimp, MailerLite…). O e-mail vai direto para o serviço.
    newsletter_form: "",
    newsletter_campo: "email",  // nome do campo de e-mail que o serviço espera
    // 2) newsletter_link: link de inscrição (Substack, canal do WhatsApp, canal do Telegram).
    newsletter_link: "",
    newsletter_servico: "",     // nome do serviço, para o aviso de privacidade. Ex.: "Buttondown"
    newsletter_nome: "Achados da semana",
    newsletter_descricao: "Um e-mail curto com produtos que baixaram de preço, achados novos e um guia da semana. Sem spam."
  };

  function vazio(v) { return !String(v || "").trim(); }
  var temContato = !vazio(CANAIS.email) || !vazio(CANAIS.whatsapp) || !vazio(CANAIS.instagram) || !vazio(CANAIS.tiktok) || !vazio(CANAIS.youtube);
  var temNews = !vazio(CANAIS.newsletter_form) || !vazio(CANAIS.newsletter_link);

  function soDigitos(v) { return String(v || "").replace(/\D/g, ""); }
  function linkWa(texto) {
    var d = soDigitos(CANAIS.whatsapp);
    if (d.length === 10 || d.length === 11) d = "55" + d;
    return "https://wa.me/" + d + (texto ? "?text=" + encodeURIComponent(texto) : "");
  }
  function linkMail(assunto, corpo) {
    return "mailto:" + CANAIS.email.trim() + "?subject=" + encodeURIComponent(assunto || "") +
      (corpo ? "&body=" + encodeURIComponent(corpo) : "");
  }
  function usuario(v) { return String(v || "").trim().replace(/^@/, ""); }

  function lista() {
    var l = [];
    if (!vazio(CANAIS.whatsapp)) l.push({ id: "whatsapp", nome: "WhatsApp", url: linkWa("Olá! Vim pelo site Produto Skincare."), rotulo: "Conversar no WhatsApp" });
    if (!vazio(CANAIS.email)) l.push({ id: "email", nome: "E-mail", url: linkMail("Contato pelo site"), rotulo: CANAIS.email.trim() });
    if (!vazio(CANAIS.instagram)) l.push({ id: "instagram", nome: "Instagram", url: "https://www.instagram.com/" + encodeURIComponent(usuario(CANAIS.instagram)) + "/", rotulo: "@" + usuario(CANAIS.instagram) });
    if (!vazio(CANAIS.tiktok)) l.push({ id: "tiktok", nome: "TikTok", url: "https://www.tiktok.com/@" + encodeURIComponent(usuario(CANAIS.tiktok)), rotulo: "@" + usuario(CANAIS.tiktok) });
    if (!vazio(CANAIS.youtube)) l.push({ id: "youtube", nome: "YouTube", url: "https://www.youtube.com/@" + encodeURIComponent(usuario(CANAIS.youtube)), rotulo: "@" + usuario(CANAIS.youtube) });
    return l;
  }

  var CSS = ".psc-redes{display:flex;flex-wrap:wrap;gap:8px 16px;margin-top:20px;padding:0;list-style:none}" +
    ".psc-redes a{font-size:14px}" +
    ".psc-news{max-width:720px;margin:48px auto 0;padding:24px;border:1px solid var(--linha,#dce1de);border-radius:var(--raio,16px);background:var(--papel,#fff);display:flex;flex-direction:column;gap:12px}" +
    ".psc-news h2{font-size:1.6rem;margin:0}.psc-news p{margin:0}" +
    ".psc-news form{display:flex;flex-wrap:wrap;gap:8px}" +
    ".psc-news input[type=email]{flex:1 1 220px;min-height:48px;padding:0 14px;border-radius:12px;border:1px solid var(--linha-2,#c8d0cb);background:var(--papel,#fff);color:var(--tinta,#252b2a)}" +
    ".psc-btn{display:inline-flex;align-items:center;justify-content:center;min-height:48px;padding:0 22px;border-radius:999px;border:0;background:var(--rosa,#9b405b);color:#fff;font-weight:600;text-decoration:none;cursor:pointer}" +
    "@media(prefers-color-scheme:dark){.psc-btn{color:#28131b}}html[data-tema=claro] .psc-btn{color:#fff}html[data-tema=escuro] .psc-btn{color:#28131b}" +
    ".psc-nota{font-size:.84rem;color:var(--suave,#596360)}" +
    ".psc-canais{list-style:none;padding:0;margin:0;display:grid;gap:10px}" +
    ".psc-canais a{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;padding:14px 16px;border:1px solid var(--linha,#dce1de);border-radius:12px;text-decoration:none;color:var(--tinta,#252b2a);background:var(--papel,#fff)}" +
    ".psc-canais a:hover{border-color:var(--rosa,#9b405b)}.psc-canais span{color:var(--suave,#596360);overflow-wrap:anywhere}";

  function estilo() {
    if (document.getElementById("psc-css")) return;
    var s = document.createElement("style");
    s.id = "psc-css";
    s.textContent = CSS;
    document.head.appendChild(s);
  }

  function el(tag, attrs, texto) {
    var n = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) { n.setAttribute(k, attrs[k]); });
    if (texto != null) n.textContent = texto;
    return n;
  }

  function contar(nome) {
    try { if (window.PSAnalytics) window.PSAnalytics.evento(nome); } catch (e) {}
  }

  function rodape() {
    var r = document.querySelector("footer.ps-rodape");
    if (!r || !temContato) return;
    var links = r.querySelector(".ps-rodape-links");
    if (links && !links.querySelector('a[href="/contato/"]')) {
      links.insertBefore(el("a", { href: "/contato/" }, "Contato"), links.firstChild);
    }
    var marca = r.querySelector(".ps-rodape-marca");
    var redes = lista().filter(function (c) { return c.id !== "email" && c.id !== "whatsapp"; });
    if (marca && redes.length && !marca.querySelector(".psc-redes")) {
      var ul = el("ul", { "class": "psc-redes", "aria-label": "Redes sociais" });
      redes.forEach(function (c) {
        var li = el("li");
        li.appendChild(el("a", { href: c.url, target: "_blank", rel: "noopener me" }, c.nome));
        ul.appendChild(li);
      });
      marca.appendChild(ul);
    }
  }

  function caixaNewsletter() {
    var caixa = el("section", { "class": "psc-news", "aria-labelledby": "psc-news-t" });
    caixa.appendChild(el("h2", { id: "psc-news-t" }, CANAIS.newsletter_nome || "Novidades"));
    caixa.appendChild(el("p", null, CANAIS.newsletter_descricao));
    var servico = CANAIS.newsletter_servico ? " (" + CANAIS.newsletter_servico + ")" : "";
    if (!vazio(CANAIS.newsletter_form)) {
      var f = el("form", { action: CANAIS.newsletter_form.trim(), method: "post", target: "_blank" });
      var id = "psc-email";
      var lbl = el("label", { "for": id, "class": "psc-nota" }, "Seu e-mail");
      lbl.style.flexBasis = "100%";
      f.appendChild(lbl);
      f.appendChild(el("input", { id: id, type: "email", name: CANAIS.newsletter_campo || "email", required: "", autocomplete: "email", placeholder: "voce@exemplo.com" }));
      f.appendChild(el("button", { type: "submit", "class": "psc-btn" }, "Quero receber"));
      f.addEventListener("submit", function () { contar("newsletter/inscricao"); });
      caixa.appendChild(f);
      caixa.appendChild(el("p", { "class": "psc-nota" },
        "Seu e-mail vai direto para o serviço de envio da newsletter" + servico +
        ", só para mandar a newsletter. Dá para cancelar em qualquer e-mail."));
    } else {
      var a = el("a", { href: CANAIS.newsletter_link.trim(), "class": "psc-btn", target: "_blank", rel: "noopener" }, "Quero receber");
      a.addEventListener("click", function () { contar("newsletter/link"); });
      var p = el("p"); p.appendChild(a); caixa.appendChild(p);
      caixa.appendChild(el("p", { "class": "psc-nota" }, "A inscrição é feita no próprio serviço" + servico + ", sob as regras dele."));
    }
    var priv = caixa.querySelector(".psc-nota:last-child");
    if (priv) {
      priv.appendChild(document.createTextNode(" "));
      priv.appendChild(el("a", { href: "/privacidade/" }, "Privacidade"));
    }
    return caixa;
  }

  function newsletter() {
    if (!temNews || document.body.hasAttribute("data-sem-newsletter")) return;
    var alvo = document.querySelector("[data-ps-newsletter]");
    if (alvo) { alvo.appendChild(caixaNewsletter()); return; }
    var r = document.querySelector("footer.ps-rodape");
    if (r && r.parentNode) r.parentNode.insertBefore(caixaNewsletter(), r);
  }

  // Página /contato/
  function paginaContato() {
    var alvo = document.querySelector("[data-ps-canais]");
    if (alvo) {
      var l = lista();
      if (l.length) {
        var ul = el("ul", { "class": "psc-canais" });
        l.forEach(function (c) {
          var li = el("li");
          var a = el("a", { href: c.url, target: c.id === "email" ? "_self" : "_blank", rel: "noopener" });
          a.appendChild(el("strong", null, c.nome));
          a.appendChild(el("span", null, c.rotulo));
          a.addEventListener("click", function () { contar("contato/" + c.id); });
          li.appendChild(a); ul.appendChild(li);
        });
        alvo.innerHTML = "";
        alvo.appendChild(ul);
      }
    }
    var form = document.querySelector("[data-ps-sugerir]");
    if (form) {
      var podeWa = !vazio(CANAIS.whatsapp), podeMail = !vazio(CANAIS.email);
      if (!podeWa && !podeMail) return;
      form.hidden = false;
      var bWa = form.querySelector("[data-via=whatsapp]"), bMail = form.querySelector("[data-via=email]");
      if (bWa) bWa.hidden = !podeWa;
      if (bMail) bMail.hidden = !podeMail;
      var montarTexto = function () {
        var tipo = (form.querySelector("[name=tipo]:checked") || {}).value || "Sugestão";
        var msg = (form.querySelector("[name=mensagem]") || {}).value || "";
        var pagina = (form.querySelector("[name=pagina]") || {}).value || "";
        return tipo + " — Produto Skincare\n\n" + msg.trim() + (pagina.trim() ? "\n\nPágina: " + pagina.trim() : "");
      };
      form.addEventListener("submit", function (ev) { ev.preventDefault(); });
      if (bWa) bWa.addEventListener("click", function () {
        if (!form.reportValidity()) return;
        window.open(linkWa(montarTexto()), "_blank", "noopener");
        contar("contato/sugestao-whatsapp");
      });
      if (bMail) bMail.addEventListener("click", function () {
        if (!form.reportValidity()) return;
        var tipo = (form.querySelector("[name=tipo]:checked") || {}).value || "Sugestão";
        location.href = linkMail(tipo + " — Produto Skincare", montarTexto());
        contar("contato/sugestao-email");
      });
    }
  }

  function iniciar() {
    if (!temContato && !temNews) return;
    estilo();
    rodape();
    newsletter();
    paginaContato();
  }

  window.PSCanais = { ativo: temContato || temNews, temContato: temContato, temNewsletter: temNews, linkWhatsApp: linkWa };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", iniciar);
  else iniciar();
})();
