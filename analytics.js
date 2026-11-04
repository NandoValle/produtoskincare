/* Estatística de visitas sem cookies (GoatCounter) e contagem de cliques nos links de loja.
 *
 * DESLIGADA até você preencher GOATCOUNTER_CODIGO:
 * 1. Crie uma conta em https://www.goatcounter.com (o "code" é o subdomínio, ex.: produtoskincare).
 * 2. Preencha o código abaixo e publique.
 * Nada é enviado enquanto o código estiver vazio. GoatCounter não usa cookies
 * e não guarda o IP completo (confira a política atual no site deles).
 */
(function () {
  "use strict";
  var GOATCOUNTER_CODIGO = ""; // ex.: "produtoskincare"

  var ativo = !!GOATCOUNTER_CODIGO;
  var fila = [];

  function enviar(caminho, titulo) {
    if (!ativo) return;
    var gc = window.goatcounter;
    if (gc && gc.count) gc.count({ path: caminho, title: titulo || caminho, event: true });
    else fila.push([caminho, titulo]);
  }

  window.PSAnalytics = {
    ativo: ativo,
    evento: function (nome, titulo) { enviar(String(nome).replace(/^\/+/, ""), titulo); }
  };

  if (ativo) {
    window.goatcounter = window.goatcounter || {};
    var s = document.createElement("script");
    s.async = true;
    s.src = "https://gc.zgo.at/count.js";
    s.setAttribute("data-goatcounter", "https://" + GOATCOUNTER_CODIGO + ".goatcounter.com/count");
    s.onload = function () { fila.splice(0).forEach(function (f) { enviar(f[0], f[1]); }); };
    document.head.appendChild(s);
  }

  var LOJAS = [
    [/(^|\.)amazon\.com\.br$|(^|\.)amzn\.to$|^link\.amazon$/, "amazon"],
    [/(^|\.)shopee\.com\.br$/, "shopee"],
    [/(^|\.)mercadolivre\.com\.br$|(^|\.)mercadolibre\.com$/, "mercadolivre"],
    [/(^|\.)tiktok\.com$/, "tiktok"]
  ];
  function loja(url) {
    try {
      var h = new URL(url, location.href).hostname.toLowerCase();
      for (var i = 0; i < LOJAS.length; i++) if (LOJAS[i][0].test(h)) return LOJAS[i][1];
    } catch (e) {}
    return null;
  }
  function slug(t) {
    return String(t || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "")
      .replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 60) || "sem-nome";
  }

  // Um clique em link de loja vira o evento "clique/<loja>/<página>/<produto>".
  document.addEventListener("click", function (ev) {
    var a = ev.target.closest && ev.target.closest("a[href]");
    if (!a) return;
    var l = loja(a.href);
    if (!l) return;
    var pagina = slug(location.pathname) || "inicio";
    var produto = a.getAttribute("data-produto") || a.textContent;
    enviar("clique/" + l + "/" + pagina + "/" + slug(produto), "Clique " + l + ": " + String(produto).trim().slice(0, 80));
  }, true);
})();
