/* Canais de contato, redes sociais e newsletter do site.
 *
 * Tudo fica DESLIGADO enquanto os campos abaixo estiverem vazios: nada aparece
 * na página e nada é enviado. Preencha só o que você tiver e publique.
 *
 * Onde aparece:
 * - Rodapé de todas as páginas: link "Contato" e links das redes sociais.
 * - Antes do rodapé: caixa de newsletter (se newsletter_form ou newsletter_link estiver preenchido).
 * - Onde a página tiver <div data-ps-ebook></div>: bloco do e-book grátis (resultado do provador, comparativos).
 * - Canto da tela: convite da newsletter, uma vez por visitante (veja "convite" abaixo).
 * - Página /contato/: lista dos canais e o formulário "Sugira um produto".
 * - Qualquer <form data-ps-enviar="Assunto">: envia a resposta pelo e-mail ou WhatsApp de quem escreve.
 */
(function () {
  "use strict";
  var CANAIS = {
    email: "contato@produtoskincare.com.br",
    whatsapp: "",         // número com DDD, só dígitos, ex.: "31912345678"
    // Botão flutuante "Dúvida? WhatsApp" em todas as páginas. Só aparece com o número acima preenchido.
    whatsapp_botao: true,
    // true = quem responde nesse número é uma IA. O botão e a mensagem inicial avisam isso.
    whatsapp_ia: true,
    instagram: "",        // usuário, sem @
    tiktok: "",           // usuário, sem @
    youtube: "",          // handle, sem @

    // Newsletter: preencha UM dos dois.
    // 1) newsletter_form: endereço "action" do formulário de inscrição do seu serviço
    //    (Buttondown, Brevo, Mailchimp, MailerLite…). O e-mail vai direto para o serviço.
    //    Buttondown: "https://buttondown.com/api/emails/embed-subscribe/SEU-USUARIO"
    newsletter_form: "https://buttondown.com/api/emails/embed-subscribe/produtoskincare",
    newsletter_campo: "email",  // nome do campo de e-mail que o serviço espera
    // Campos ocultos que o serviço pede junto com o e-mail. O Buttondown pede { embed: "1" }.
    newsletter_ocultos: { embed: "1" },
    // 2) newsletter_link: link de inscrição (Substack, canal do WhatsApp, canal do Telegram).
    newsletter_link: "",
    newsletter_servico: "Buttondown", // nome do serviço, para o aviso de privacidade. Ex.: "Buttondown"
    newsletter_nome: "Achados da semana",
    newsletter_descricao: "Um e-mail curto com produtos que baixaram de preço, achados novos e um guia da semana. Sem spam.",

    // E-book grátis para quem assina (o mesmo da página /newsletter/). Vazio = não é citado em lugar nenhum.
    ebook_pdf: "/newsletter/rotina-basica-por-tipo-de-pele.pdf",
    ebook_nome: "Rotina básica por tipo de pele",
    ebook_convite: "PDF de 11 páginas com a rotina de manhã e de noite. Junto vem a newsletter, um e-mail curto por semana.",
    ebook_descricao: "PDF de 11 páginas com a rotina de manhã e de noite para pele oleosa, seca, mista e normal. Junto vem a newsletter, um e-mail curto por semana.",

    // Convite da newsletter: cartão no canto da tela, que não cobre a página nem trava a leitura.
    // Aparece uma vez por visitante, depois de convite_segundos na página ou de convite_rolagem da página rolada.
    // false = desligado. Não aparece nas páginas de convite_fora nem onde já existe um bloco do e-book.
    convite: true,
    convite_segundos: 45,
    convite_rolagem: 0.6,
    convite_fora: ["/newsletter/", "/provador/", "/pergunte/", "/contato/", "/privacidade/", "/termos/", "/en/", "/es/"]
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
    ".psc-news{max-width:720px;margin:48px auto 0;padding:24px;border:1px solid var(--linha,#E4DBCE);border-radius:var(--raio,16px);background:var(--papel,#fff);display:flex;flex-direction:column;gap:12px}" +
    ".psc-news h2{font-size:1.6rem;margin:0}.psc-news p{margin:0}" +
    ".psc-news form{display:flex;flex-wrap:wrap;gap:8px}" +
    ".psc-news input[type=email]{flex:1 1 220px;min-width:0;max-width:100%;min-height:48px;padding:0 14px;border-radius:12px;border:1px solid var(--linha-2,#D3C7B6);background:var(--papel,#fff);color:var(--tinta,#17120E)}" +
    ".psc-btn{display:inline-flex;align-items:center;justify-content:center;min-height:48px;padding:0 22px;border-radius:999px;border:0;background:var(--rosa,#755728);color:var(--sobre-rosa,#fff);font-weight:600;text-decoration:none;cursor:pointer}" +
    "#psc-wa{position:fixed;left:16px;bottom:16px;z-index:90;display:flex;flex-direction:column;gap:2px;padding:10px 18px;border-radius:999px;background:#1f7a4d;color:#fff;text-decoration:none;line-height:1.25;box-shadow:0 8px 24px #17120e33}" +
    "#psc-wa strong{font-size:14px;font-weight:600}#psc-wa span{font-size:11px;opacity:.92}" +
    "#psc-wa:hover{background:#18643f}#psc-wa:focus-visible{outline:2px solid var(--tinta,#17120E);outline-offset:2px}" +
    "@media print{#psc-wa{display:none}}" +
    ".psc-nota{font-size:.84rem;color:var(--suave,#596360)}" +
    ".psc-ebook{margin:28px 0}" +
    ".psc-rotulo{font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;font-weight:600;color:var(--rosa,#755728)}" +
    "#psc-convite{position:fixed;right:16px;bottom:84px;z-index:91;width:min(360px,calc(100vw - 24px));margin:0;padding:20px 20px 18px;gap:10px;box-shadow:0 18px 48px #17120e33;animation:psc-sobe .3s ease}" +
    "#psc-convite h2{font-size:1.35rem;padding-right:36px}" +
    ".psc-fechar{position:absolute;top:6px;right:6px;width:44px;height:44px;border:0;background:none;color:var(--suave,#596360);font-size:1.6rem;line-height:1;cursor:pointer;border-radius:50%}" +
    ".psc-fechar:hover{color:var(--tinta,#17120E)}.psc-fechar:focus-visible{outline:2px solid var(--rosa,#755728);outline-offset:-4px}" +
    "@keyframes psc-sobe{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}" +
    "#psc-convite p{font-size:.94rem}#psc-convite .psc-nota{font-size:.8rem}" +
    "@media(max-width:560px){#psc-convite{right:12px;left:12px;bottom:72px;width:auto;padding:14px 16px;gap:6px}#psc-convite h2{font-size:1.2rem}" +
    "#psc-convite form label{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}" +
    "#psc-convite input[type=email]{flex:1 1 120px}#psc-convite .psc-btn{padding:0 16px;white-space:nowrap}}" +
    "@media(prefers-reduced-motion:reduce){#psc-convite{animation:none}}" +
    "@media print{#psc-convite,.psc-ebook{display:none}}" +
    ".psc-canais{list-style:none;padding:0;margin:0;display:grid;gap:10px}" +
    ".psc-canais a{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;padding:14px 16px;border:1px solid var(--linha,#E4DBCE);border-radius:12px;text-decoration:none;color:var(--tinta,#17120E);background:var(--papel,#fff)}" +
    ".psc-canais a:hover{border-color:var(--rosa,#755728)}.psc-canais span{color:var(--suave,#596360);overflow-wrap:anywhere}";

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

  // Botão flutuante do WhatsApp (canto inferior esquerdo; o direito é do "Som do sonho").
  function botaoWhatsApp() {
    if (vazio(CANAIS.whatsapp) || !CANAIS.whatsapp_botao) return;
    if (document.body.hasAttribute("data-sem-whatsapp") || document.getElementById("psc-wa")) return;
    var titulo = (document.querySelector("h1") || {}).textContent || document.title || "";
    titulo = titulo.replace(/\s+/g, " ").trim().slice(0, 90);
    var texto = "Olá! Vim pelo site Produto Skincare" + (titulo ? " (página: " + titulo + ")" : "") + ". Minha dúvida: ";
    var a = el("a", { id: "psc-wa", href: linkWa(texto), target: "_blank", rel: "noopener",
      "aria-label": CANAIS.whatsapp_ia ? "Tirar dúvida no WhatsApp, com resposta por inteligência artificial" : "Tirar dúvida no WhatsApp" });
    a.appendChild(el("strong", null, "Dúvida? WhatsApp"));
    if (CANAIS.whatsapp_ia) a.appendChild(el("span", null, "Resposta por IA · não é consulta"));
    a.addEventListener("click", function () { contar("contato/whatsapp-botao"); });
    document.body.appendChild(a);
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

  var temEbook = !vazio(CANAIS.newsletter_form) && !vazio(CANAIS.ebook_pdf);
  var CHAVE_CONVITE = "ps_convite_news";

  // O site lembra, só neste aparelho, que o convite já apareceu ou que a pessoa já assinou.
  function lembrarConvite() { try { localStorage.setItem(CHAVE_CONVITE, "1"); } catch (e) {} }

  // Formulário de inscrição. `sufixo` deixa os ids únicos quando há mais de um na página.
  function formularioNews(sufixo, evento, textoBotao) {
    var f = el("form", { action: CANAIS.newsletter_form.trim(), method: "post", target: "_blank" });
    var id = "psc-email" + sufixo;
    var lbl = el("label", { "for": id, "class": "psc-nota" }, "Seu e-mail");
    lbl.style.flexBasis = "100%";
    f.appendChild(lbl);
    f.appendChild(el("input", { id: id, type: "email", name: CANAIS.newsletter_campo || "email", required: "", autocomplete: "email", placeholder: "voce@exemplo.com" }));
    var ocultos = CANAIS.newsletter_ocultos || {};
    Object.keys(ocultos).forEach(function (k) {
      f.appendChild(el("input", { type: "hidden", name: k, value: String(ocultos[k]) }));
    });
    f.appendChild(el("button", { type: "submit", "class": "psc-btn" }, textoBotao || "Quero receber"));
    var pronto = null;
    if (temEbook) {
      pronto = el("p", { "class": "psc-nota", role: "status", hidden: "" }, "Inscrição enviada (a confirmação abriu em outra aba). ");
      pronto.style.flexBasis = "100%";
      pronto.appendChild(el("a", { href: CANAIS.ebook_pdf, download: "" }, "Baixar o e-book (PDF)"));
      f.appendChild(pronto);
    }
    f.addEventListener("submit", function () {
      contar(evento);
      lembrarConvite();
      if (pronto) pronto.hidden = false;
    });
    return f;
  }

  function notaPrivacidade(curta) {
    var servico = CANAIS.newsletter_servico ? " (" + CANAIS.newsletter_servico + ")" : "";
    var p = el("p", { "class": "psc-nota" }, curta ?
      "Seu e-mail vai direto para o serviço de envio" + servico + ". Dá para cancelar em qualquer e-mail. " :
      "Seu e-mail vai direto para o serviço de envio da newsletter" + servico +
      ", só para mandar a newsletter. Dá para cancelar em qualquer e-mail. ");
    p.appendChild(el("a", { href: "/privacidade/" }, "Privacidade"));
    return p;
  }

  function caixaNewsletter() {
    var caixa = el("section", { "class": "psc-news", "aria-labelledby": "psc-news-t" });
    caixa.appendChild(el("h2", { id: "psc-news-t" }, CANAIS.newsletter_nome || "Novidades"));
    caixa.appendChild(el("p", null, CANAIS.newsletter_descricao));
    if (!vazio(CANAIS.newsletter_form)) {
      if (temEbook) {
        var brinde = el("p", null, "Quem assina também recebe o e-book grátis ");
        brinde.appendChild(el("a", { href: "/newsletter/" }, CANAIS.ebook_nome));
        brinde.appendChild(document.createTextNode(" (PDF)."));
        caixa.appendChild(brinde);
      }
      caixa.appendChild(formularioNews("", "newsletter/inscricao"));
      caixa.appendChild(notaPrivacidade());
    } else {
      var servico = CANAIS.newsletter_servico ? " (" + CANAIS.newsletter_servico + ")" : "";
      var a = el("a", { href: CANAIS.newsletter_link.trim(), "class": "psc-btn", target: "_blank", rel: "noopener" }, "Quero receber");
      a.addEventListener("click", function () { contar("newsletter/link"); });
      var p = el("p"); p.appendChild(a); caixa.appendChild(p);
      var nota = el("p", { "class": "psc-nota" }, "A inscrição é feita no próprio serviço" + servico + ", sob as regras dele. ");
      nota.appendChild(el("a", { href: "/privacidade/" }, "Privacidade"));
      caixa.appendChild(nota);
    }
    return caixa;
  }

  // Bloco do e-book grátis, no meio do conteúdo: entra em todo elemento com data-ps-ebook.
  // O valor do atributo escolhe o nível do título (data-ps-ebook="h3"); o padrão é h2.
  function blocoEbook(alvo, n) {
    var nivel = /^h[2-4]$/.test(alvo.getAttribute("data-ps-ebook") || "") ? alvo.getAttribute("data-ps-ebook") : "h2";
    var idT = "psc-ebook-t" + n;
    var caixa = el("section", { "class": "psc-news psc-ebook", "aria-labelledby": idT });
    caixa.appendChild(el("p", { "class": "psc-rotulo" }, "E-book grátis"));
    caixa.appendChild(el(nivel, { id: idT }, CANAIS.ebook_nome));
    caixa.appendChild(el("p", null, CANAIS.ebook_descricao));
    caixa.appendChild(formularioNews("-ebook" + n, "newsletter/inscricao-ebook", "Quero o e-book"));
    caixa.appendChild(notaPrivacidade());
    alvo.appendChild(caixa);
  }

  function newsletter() {
    if (!temNews || document.body.hasAttribute("data-sem-newsletter")) return;
    var blocos = temEbook ? document.querySelectorAll("[data-ps-ebook]") : [];
    for (var i = 0; i < blocos.length; i++) blocoEbook(blocos[i], i + 1);
    // Página que já tem o bloco do e-book não repete a caixa antes do rodapé.
    if (blocos.length) return;
    var alvo = document.querySelector("[data-ps-newsletter]");
    if (alvo) { alvo.appendChild(caixaNewsletter()); return; }
    var r = document.querySelector("footer.ps-rodape");
    if (r && r.parentNode) r.parentNode.insertBefore(caixaNewsletter(), r);
  }

  // Convite da newsletter: cartão no canto, sem cobrir a página e sem roubar o foco.
  function convite() {
    if (!CANAIS.convite || !temEbook || document.body.hasAttribute("data-sem-newsletter")) return;
    if (document.querySelector("[data-ps-ebook]")) return;
    var caminho = location.pathname;
    if ((CANAIS.convite_fora || []).some(function (p) { return caminho.indexOf(p) === 0; })) return;
    // Sem armazenamento local não dá para garantir "uma vez só": melhor não mostrar.
    try { if (localStorage.getItem(CHAVE_CONVITE)) return; } catch (e) { return; }

    var aberto = null, feito = false;
    function fechar(motivo) {
      if (!aberto) return;
      aberto.remove(); aberto = null;
      document.removeEventListener("keydown", tecla);
      if (motivo) contar("newsletter/convite-" + motivo);
    }
    function tecla(ev) { if (ev.key === "Escape") fechar("fechou"); }
    function abrir() {
      if (feito) return;
      // Quem está digitando (busca, quiz, ferramenta) não é interrompido: tenta de novo depois.
      var foco = document.activeElement;
      if (foco && /^(INPUT|TEXTAREA|SELECT)$/.test(foco.tagName)) { setTimeout(abrir, 15000); return; }
      try { if (localStorage.getItem(CHAVE_CONVITE)) { feito = true; return; } } catch (e) { return; }
      // Com a caixa de newsletter do fim da página à vista, o convite seria repetição.
      var caixa = document.getElementById("psc-news-t");
      if (caixa) {
        var q = caixa.parentNode.getBoundingClientRect();
        if (q.top < innerHeight && q.bottom > 0) return;
      }
      feito = true;
      removeEventListener("scroll", rolou);
      lembrarConvite();
      var c = el("section", { id: "psc-convite", "class": "psc-news", role: "dialog", "aria-labelledby": "psc-convite-t" });
      var x = el("button", { type: "button", "class": "psc-fechar", "aria-label": "Fechar convite" }, "×");
      x.addEventListener("click", function () { fechar("fechou"); });
      c.appendChild(x);
      c.appendChild(el("p", { "class": "psc-rotulo" }, "E-book grátis"));
      c.appendChild(el("h2", { id: "psc-convite-t" }, CANAIS.ebook_nome));
      c.appendChild(el("p", null, CANAIS.ebook_convite || CANAIS.ebook_descricao));
      var f = formularioNews("-convite", "newsletter/inscricao-convite", "Quero o e-book");
      c.appendChild(f);
      c.appendChild(notaPrivacidade(true));
      document.body.appendChild(c);
      aberto = c;
      document.addEventListener("keydown", tecla);
      contar("newsletter/convite-visto");
    }
    function rolou() {
      var alt = document.documentElement.scrollHeight - innerHeight;
      if (alt > 0 && scrollY / alt >= (CANAIS.convite_rolagem || 0.6)) abrir();
    }
    setTimeout(abrir, (CANAIS.convite_segundos || 45) * 1000);
    addEventListener("scroll", rolou, { passive: true });
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

  // Formulários "data-ps-enviar": a resposta sai do aplicativo de e-mail ou do WhatsApp de quem
  // escreve. O site não recebe nem guarda nada. O valor do atributo é o assunto da mensagem;
  // cada campo com "name" entra no texto, com o rótulo de "data-rotulo".
  function formularios() {
    var podeWa = !vazio(CANAIS.whatsapp), podeMail = !vazio(CANAIS.email);
    Array.prototype.forEach.call(document.querySelectorAll("form[data-ps-enviar]"), function (form) {
      if (!podeWa && !podeMail) return;
      form.hidden = false;
      var assunto = form.getAttribute("data-ps-enviar") + " — Produto Skincare";
      var evento = form.getAttribute("data-evento") || "formulario";
      var texto = function () {
        var linhas = [], vistos = {};
        Array.prototype.forEach.call(form.elements, function (el) {
          if (!el.name || vistos[el.name]) return;
          var valor;
          if (el.type === "radio" || el.type === "checkbox") {
            var marcados = form.querySelectorAll('[name="' + el.name + '"]:checked');
            valor = Array.prototype.map.call(marcados, function (m) { return m.value; }).join(", ");
          } else valor = String(el.value || "").trim();
          vistos[el.name] = true;
          if (!valor) return;
          linhas.push((el.getAttribute("data-rotulo") || el.name) + ":\n" + valor);
        });
        return assunto + "\n\n" + linhas.join("\n\n");
      };
      form.addEventListener("submit", function (ev) { ev.preventDefault(); });
      Array.prototype.forEach.call(form.querySelectorAll("[data-via]"), function (b) {
        var via = b.getAttribute("data-via");
        b.hidden = via === "whatsapp" ? !podeWa : !podeMail;
        b.addEventListener("click", function () {
          if (!form.reportValidity()) return;
          if (via === "whatsapp") window.open(linkWa(texto()), "_blank", "noopener");
          else location.href = linkMail(assunto, texto());
          contar(evento + "-" + via);
          var ok = form.querySelector("[data-ps-enviado]");
          if (ok) ok.hidden = false;
        });
      });
    });
  }

  function iniciar() {
    if (!temContato && !temNews) return;
    estilo();
    rodape();
    botaoWhatsApp();
    newsletter();
    convite();
    paginaContato();
    formularios();
  }

  window.PSCanais = { ativo: temContato || temNews, temContato: temContato, temNewsletter: temNews, linkWhatsApp: linkWa };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", iniciar);
  else iniciar();
})();
