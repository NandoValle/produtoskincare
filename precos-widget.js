/*
 * precos-widget.js — selo de bom preço, custo por dia, mini-gráfico e alerta local.
 *
 * Uso na página do produto (ver snippet-produto.html):
 *   <div class="ps-precos" data-precos-id="cerave-gel-limpeza">…fallback sem JS…</div>
 *   <script src="/precos-widget.js" defer></script>
 *
 * O widget lê /precos.json (gerado por gerar-precos.mjs), aprimora o bloco e guarda o
 * alerta de preço só no aparelho (localStorage) — sem cadastro, sem servidor.
 * Sem JavaScript ou sem /precos.json, o fallback estático dentro do bloco continua no ar.
 */
(function () {
  "use strict";

  var ROTULO = {
    "otimo": "🟢 ótimo preço", "bom": "🔵 bom preço", "justo": "⚪ preço justo",
    "alto": "🔴 caro agora", "sem-historico": "➖ histórico em construção",
    "desatualizado": "⏸ preço não conferido recentemente"
  };
  var CSS = ".ps-selo{display:inline-block;padding:.15em .6em;border-radius:999px;font-size:.85em}" +
    ".ps-selo-otimo{background:#e7f6e9;color:#1c6b2c}.ps-selo-bom{background:#e8f0fb;color:#1c4d8f}" +
    ".ps-selo-justo{background:#f0f0f0;color:#555}.ps-selo-alto{background:#fdeaea;color:#9c2020}" +
    ".ps-selo-sem-historico{background:#f5f1e6;color:#8a6d1a}.ps-selo-desatualizado{background:#f0f0f0;color:#777}" +
    ".ps-precos{font-size:.95em}.ps-precos-linha{margin:.3em 0}" +
    ".ps-precos-alerta{margin-top:.6em;padding:.6em;border:1px solid #ddd;border-radius:8px}" +
    ".ps-precos-aviso{margin-top:.6em;padding:.6em;border:1px solid #c9e3c9;background:#f2faf2;border-radius:8px}" +
    ".ps-precos input[type=number]{width:7em;padding:.3em}";

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function brl(cents) { return "R$ " + (cents / 100).toFixed(2).replace(".", ","); }
  function dataBR(iso) { return iso ? iso.split("-").reverse().join("/") : "—"; }

  // Quantos dias faz que o preço foi conferido. Acima de FRESCO_DIAS ele deixa de ser
  // apresentado como preço de agora e passa a ser "último preço registrado": o site confere
  // em lote, e um número de semanas atrás em negrito se lê como oferta do dia.
  var FRESCO_DIAS = 7;
  function diasDesde(iso) {
    if (!iso) return null;
    var t = Date.parse(iso + "T00:00:00Z");
    if (isNaN(t)) return null;
    return Math.floor((Date.now() - t) / 86400000);
  }
  // URL de BUSCA (lista de resultados) em vez da página de uma oferta. Nesses casos o
  // visitante não tem como conferir o preço que o site registrou: o link cai numa busca,
  // onde o valor e a variante mudam. Então o rótulo diz "procurar" e o preço vem com a
  // ressalva. Em 24/11/2026 eram 8 dos 26 produtos do precos.json (6 Shopee, 2 Amazon).
  var RE_BUSCA = /[/?](?:search\?keyword|s\?k=)|[?&]keyword=|\/busca/i;
  function ehBusca(url) { return !!url && RE_BUSCA.test(url); }

  function fresco(p) {
    var d = p.current ? diasDesde(p.current.checked_at) : null;
    return d !== null && d <= FRESCO_DIAS;
  }

  function sparkline(series, alt) {
    if (!series || series.length < 2) return "";
    var w = 160, h = 40, pad = 4;
    var xs = series.map(function (p, i) { return pad + (i * (w - 2 * pad)) / (series.length - 1); });
    var vals = series.map(function (p) { return p[1]; });
    var min = Math.min.apply(null, vals), max = Math.max.apply(null, vals);
    var span = max - min || 1;
    var ys = vals.map(function (v) { return h - pad - ((v - min) * (h - 2 * pad)) / span; });
    var d = xs.map(function (x, i) { return (i ? "L" : "M") + x.toFixed(1) + " " + ys[i].toFixed(1); }).join(" ");
    return '<svg width="' + w + '" height="' + h + '" viewBox="0 0 ' + w + " " + h + '" role="img" aria-label="' + esc(alt) + '">' +
      '<path d="' + d + '" fill="none" stroke="#1c4d8f" stroke-width="2"/>' +
      '<circle cx="' + xs[xs.length - 1].toFixed(1) + '" cy="' + ys[ys.length - 1].toFixed(1) + '" r="3" fill="#1c4d8f"/></svg>';
  }

  function renderizar(bloco, p) {
    var partes = [];
    partes.push('<p class="ps-precos-linha"><span class="ps-selo ps-selo-' + p.badge + '" title="' + esc(p.badge_motivo) + '">' +
      ROTULO[p.badge] + "</span></p>");
    if (p.current) {
      var dias = diasDesde(p.current.checked_at);
      var busca = ehBusca(p.current.url);
      var naLoja = p.current.url
        ? ' · <a href="' + esc(p.current.url) + '" rel="nofollow sponsored">' +
          (busca ? "procurar na loja" : "ver na loja") + "</a>"
        : "";
      var obs = p.n_observations + " observaç" + (p.n_observations === 1 ? "ão" : "ões");
      if (fresco(p)) {
        partes.push('<p class="ps-precos-linha"><strong>' + brl(p.current.price_cents) + "</strong>" +
          (p.current.promo ? " <em>(promoção)</em>" : "") +
          " · conferido em " + dataBR(p.current.checked_at) + " · " + obs + naLoja + "</p>");
      } else {
        // Preço antigo: não vai em negrito nem sozinho, para não passar por oferta de agora.
        partes.push('<p class="ps-precos-linha">Último preço registrado: ' + brl(p.current.price_cents) +
          (p.current.promo ? " (em promoção na ocasião)" : "") +
          ", em " + dataBR(p.current.checked_at) +
          (dias === null ? "" : " — " + (dias === 1 ? "há 1 dia" : "há " + dias + " dias")) +
          " · " + obs + naLoja + "</p>");
        partes.push('<p class="ps-precos-linha ig-nota">Não é o preço de hoje: confira na loja antes de comprar.</p>');
      }
      if (busca) {
        partes.push('<p class="ps-precos-linha ig-nota">O link abre uma busca na loja, não uma oferta fixa: confirme a marca, o tamanho e o preço no anúncio que escolher.</p>');
      }
    }
    if (p.custo) {
      partes.push('<p class="ps-precos-linha">≈ <strong>' + brl(p.custo.custo_dia_cents) + "/dia</strong>" +
        " · rende ~" + p.custo.rendimento_dias + " dias" +
        ' <span class="ig-nota">(estimativa com ' + p.custo.dose_ml_dia + " ml/dia)</span></p>");
    }
    var janela = p.window_days || 90;
    var alt = "Preço nos últimos " + janela + " dias: de " + brl(p.min_cents) + " a " + brl(p.max_cents);
    var svg = sparkline(p.series, alt);
    if (svg) partes.push('<p class="ps-precos-linha">' + svg + "</p>");

    // alerta local (sem cadastro)
    var chave = "ps-alerta-preco:" + p.product_id;
    var salvo = null;
    try { salvo = JSON.parse(localStorage.getItem(chave) || "null"); } catch (e) {}
    // O aviso só sai com conferência recente. Com um preço de semanas atrás, dizer "o preço
    // atual está abaixo do seu alvo" é mandar a pessoa comprar com base num número que o site
    // não conferiu — o alerta ficava disparando sozinho em todo produto sem conferência nova.
    if (salvo && p.current && p.current.price_cents <= salvo.cents && fresco(p)) {
      partes.push('<div class="ps-precos-aviso" role="status">🔔 Seu alerta: o preço conferido em ' +
        dataBR(p.current.checked_at) + " (" + brl(p.current.price_cents) +
        ") está abaixo do alvo que você escolheu (" + brl(salvo.cents) + ")." +
        ' <button type="button" data-alerta-remover>remover alerta</button></div>');
    } else if (salvo && p.current && p.current.price_cents <= salvo.cents) {
      partes.push('<div class="ps-precos-aviso" role="status">🔔 Seu alerta está guardado (' +
        brl(salvo.cents) + "). O último preço registrado, de " + dataBR(p.current.checked_at) +
        ", já estava abaixo dele, mas é antigo: o aviso volta quando houver conferência nova." +
        ' <button type="button" data-alerta-remover>remover alerta</button></div>');
    }
    partes.push('<div class="ps-precos-alerta"><form data-alerta-form>' +
      '<label>Avise-me se cair abaixo de <input type="number" min="1" step="0.01" value="' +
      (salvo ? (salvo.cents / 100).toFixed(2) : (p.current ? (p.current.price_cents / 100 * 0.9).toFixed(2) : "")) +
      '"> R$</label> <button type="submit">guardar alerta</button>' +
      '</form><p class="ig-nota">O alerta fica só neste aparelho, sem cadastro. Ao voltar ao site, se o preço tiver atingido o valor, o aviso aparece.</p></div>');

    bloco.innerHTML = partes.join("");
    var form = bloco.querySelector("[data-alerta-form]");
    if (form) {
      form.addEventListener("submit", function (e) {
        e.preventDefault();
        var v = parseFloat(form.querySelector("input").value);
        if (!(v > 0)) return;
        try { localStorage.setItem(chave, JSON.stringify({ cents: Math.round(v * 100) })); } catch (e2) {}
        form.querySelector("button").textContent = "alerta guardado ✓";
      });
    }
    var remover = bloco.querySelector("[data-alerta-remover]");
    if (remover) {
      remover.addEventListener("click", function () {
        try { localStorage.removeItem(chave); } catch (e2) {}
        renderizar(bloco, p);
      });
    }
  }

  function iniciar() {
    if (!document.querySelector("[data-precos-id]")) return;
    var estilo = document.createElement("style");
    estilo.textContent = CSS;
    document.head.appendChild(estilo);
    fetch("/precos.json", { credentials: "same-origin" }).then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    }).then(function (dados) {
      document.querySelectorAll("[data-precos-id]").forEach(function (bloco) {
        var p = dados.produtos[bloco.getAttribute("data-precos-id")];
        if (p) renderizar(bloco, p);
      });
    }).catch(function () { /* fallback estático permanece */ });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", iniciar);
  else iniciar();
})();
