/* Lojas de afiliado do produtoskincare.com.br
 * Um produto pode ter várias lojas. Cada loja em produtos.json fica assim:
 *   "lojas": [
 *     { "loja": "amazon", "url": "https://www.amazon.com.br/dp/ASIN" },
 *     { "loja": "shopee", "url": "https://shopee.com.br/search?keyword=...", "afiliado": "" },
 *     { "loja": "mercadolivre", "url": "https://lista.mercadolivre.com.br/...", "afiliado": "" }
 *   ]
 * "url" é o endereço normal da loja. "afiliado" é o link gerado no painel de afiliados
 * (Shopee ou Mercado Livre). Quando "afiliado" estiver preenchido, ele é usado no lugar de "url".
 * Na Amazon a tag abaixo é aplicada sozinha em qualquer link amazon.com.br.
 */
(function () {
  const CONFIG = {
    amazon:       { nome: "Amazon", em: "na", tag: "produtoskincare-20" },
    shopee:       { nome: "Shopee", em: "na" },        // link de afiliado: preencher "afiliado" em cada produto
    mercadolivre: { nome: "Mercado Livre", em: "no" }, // link de afiliado: preencher "afiliado" em cada produto
    tiktok:       { nome: "TikTok Shop", em: "no" }
  };
  const ORDEM = ["amazon", "mercadolivre", "shopee", "tiktok"];

  function comTagAmazon(url) {
    try {
      const u = new URL(url);
      if (!/(^|\.)amazon\.com\.br$/.test(u.hostname)) return url;
      // corrige links antigos do tipo "?k=busca?tag=..." (dois "?")
      const k = u.searchParams.get("k");
      if (k && k.includes("?tag=")) u.searchParams.set("k", k.split("?tag=")[0]);
      u.searchParams.set("tag", CONFIG.amazon.tag);
      return u.toString();
    } catch (e) { return url; }
  }

  function busca(loja, termo) {
    const t = String(termo || "").trim();
    if (!t) return "";
    if (loja === "shopee") return "https://shopee.com.br/search?keyword=" + encodeURIComponent(t);
    if (loja === "mercadolivre") {
      const slug = t.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase()
        .replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
      return "https://lista.mercadolivre.com.br/" + slug;
    }
    if (loja === "amazon") return "https://www.amazon.com.br/s?k=" + encodeURIComponent(t);
    return "";
  }

  // Lista as lojas de um produto, já com o link final (afiliado quando houver).
  function lojasDoProduto(p) {
    let lista = Array.isArray(p.lojas) && p.lojas.length ? p.lojas.slice() : [];
    if (!lista.length) {
      if (p.link) lista.push({ loja: p.plataforma || "", url: p.link });
      ["shopee", "mercadolivre"].forEach(l => {
        if (!lista.some(x => x.loja === l)) lista.push({ loja: l, url: busca(l, p.nome), busca: true });
      });
    }
    return lista
      .filter(x => x && (x.afiliado || x.url))
      .map(x => {
        let url = x.afiliado || x.url;
        if (x.loja === "amazon") url = comTagAmazon(url);
        return {
          loja: x.loja,
          nome: (CONFIG[x.loja] && CONFIG[x.loja].nome) || "loja",
          em: (CONFIG[x.loja] && CONFIG[x.loja].em) || "na",
          url,
          principal: x.loja === p.plataforma,
          busca: !!x.busca || /\/search\?|lista\.mercadolivre|\/s\?k=/.test(x.url || "")
        };
      })
      .sort((a, b) => (b.principal - a.principal) || (ORDEM.indexOf(a.loja) - ORDEM.indexOf(b.loja)));
  }

  window.LOJAS = { CONFIG, lojasDoProduto, comTagAmazon, busca };
})();
