/* Cartão para Stories (1080x1920), desenhado no próprio aparelho.
 * Nada é enviado ao site: a imagem é gerada num <canvas> e vai para o
 * compartilhamento do celular (Instagram, WhatsApp...) ou é baixada.
 *
 * Uso:
 *   PSCartao.montar(elemento, function () {
 *     return { rotulo, titulo, linhas: ["...", "..."], rodape, arquivo };
 *   }, { evento: "prateleira/cartao" });
 */
(function () {
  "use strict";
  var W = 1080, H = 1920, M = 96;
  var COR = { fundo: "#f7f8f7", papel: "#fdfefd", tinta: "#252b2a", suave: "#39413f", linha: "#dce1de", rosa: "#9b405b", rosaClaro: "#f6e9ee" };
  var DISPLAY = "'Cormorant Garamond', Georgia, serif", CORPO = "Manrope, 'Segoe UI', Arial, sans-serif";

  function quebrar(ctx, texto, largura) {
    var linhas = [], atual = "";
    String(texto).split(/\s+/).forEach(function (p) {
      var t = atual ? atual + " " + p : p;
      if (ctx.measureText(t).width <= largura || !atual) atual = t;
      else { linhas.push(atual); atual = p; }
    });
    if (atual) linhas.push(atual);
    return linhas;
  }

  function desenhar(d) {
    var c = document.createElement("canvas"); c.width = W; c.height = H;
    var ctx = c.getContext("2d");
    ctx.fillStyle = COR.fundo; ctx.fillRect(0, 0, W, H);
    ctx.textBaseline = "top";
    // marca
    ctx.font = "500 52px " + DISPLAY; ctx.fillStyle = COR.tinta; ctx.fillText("produto", M, 120);
    var w = ctx.measureText("produto").width; ctx.fillStyle = COR.rosa; ctx.fillText("skincare", M + w, 120);
    var y = 330;
    if (d.rotulo) {
      ctx.font = "600 34px " + CORPO;
      var rw = ctx.measureText(d.rotulo.toUpperCase()).width + 64;
      ctx.fillStyle = COR.rosaClaro; arredondado(ctx, M, y, rw, 70, 35); ctx.fill();
      ctx.fillStyle = COR.rosa; ctx.fillText(d.rotulo.toUpperCase(), M + 32, y + 17);
      y += 120;
    }
    ctx.font = "500 112px " + DISPLAY; ctx.fillStyle = COR.tinta;
    quebrar(ctx, d.titulo || "", W - 2 * M).slice(0, 4).forEach(function (l) { ctx.fillText(l, M, y); y += 118; });
    y += 40;
    // caixa com as linhas
    var linhas = (d.linhas || []).slice(0, 8);
    if (linhas.length) {
      ctx.font = "400 42px " + CORPO;
      var blocos = linhas.map(function (l) { return quebrar(ctx, l, W - 2 * M - 80).slice(0, 3); });
      var altura = blocos.reduce(function (s, b) { return s + b.length * 56 + 28; }, 40);
      altura = Math.min(altura, H - y - 330);
      ctx.fillStyle = COR.papel; ctx.strokeStyle = COR.linha; ctx.lineWidth = 3;
      arredondado(ctx, M, y, W - 2 * M, altura, 36); ctx.fill(); ctx.stroke();
      ctx.save(); ctx.beginPath(); ctx.rect(M, y, W - 2 * M, altura); ctx.clip();
      var yy = y + 40; ctx.fillStyle = COR.suave;
      blocos.forEach(function (b) { b.forEach(function (l) { ctx.fillText(l, M + 40, yy); yy += 56; }); yy += 28; });
      ctx.restore();
    }
    // rodapé
    ctx.font = "400 34px " + CORPO; ctx.fillStyle = COR.suave;
    if (d.rodape) quebrar(ctx, d.rodape, W - 2 * M).slice(0, 2).forEach(function (l, i) { ctx.fillText(l, M, H - 300 + i * 46); });
    ctx.fillStyle = COR.rosa; arredondado(ctx, M, H - 190, W - 2 * M, 100, 50); ctx.fill();
    ctx.fillStyle = "#fff";
    var url = "produtoskincare.com.br" + (d.caminho || ""), tam = 40;
    do { ctx.font = "600 " + tam + "px " + CORPO; tam -= 2; } while (ctx.measureText(url).width > W - 2 * M - 70 && tam > 20);
    ctx.fillText(url, (W - ctx.measureText(url).width) / 2, H - 160);
    return c;
  }

  function arredondado(ctx, x, y, w, h, r) {
    ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath();
  }

  function gerar(dados) {
    var pronto = document.fonts && document.fonts.load
      ? Promise.all([document.fonts.load("500 112px 'Cormorant Garamond'"), document.fonts.load("400 42px Manrope"), document.fonts.load("600 40px Manrope")]).catch(function () {})
      : Promise.resolve();
    return pronto.then(function () {
      var c = desenhar(dados);
      return new Promise(function (ok) { c.toBlob(function (b) { ok(b); }, "image/png"); });
    });
  }

  function montar(alvo, obter, opcoes) {
    if (!alvo) return;
    opcoes = opcoes || {};
    alvo.innerHTML = '<div class="psc"><button type="button" class="ft-btn ft-sec psc-btn">📸 Cartão para os Stories</button>' +
      '<p class="ig-nota psc-nota">Gera uma imagem no seu aparelho para postar nos Stories ou mandar no WhatsApp. Nada é enviado ao site.</p></div>';
    var btn = alvo.querySelector(".psc-btn"), nota = alvo.querySelector(".psc-nota");
    btn.addEventListener("click", function () {
      var dados = obter();
      if (!dados) return;
      btn.disabled = true;
      gerar(dados).then(function (blob) {
        btn.disabled = false;
        if (!blob) { nota.textContent = "Não deu para gerar a imagem neste navegador."; return; }
        var nome = (dados.arquivo || "produtoskincare") + ".png";
        var arquivo = typeof File === "function" ? new File([blob], nome, { type: "image/png" }) : null;
        try { if (window.PSAnalytics && opcoes.evento) PSAnalytics.evento(opcoes.evento); } catch (e) {}
        if (arquivo && navigator.canShare && navigator.canShare({ files: [arquivo] })) {
          navigator.share({ files: [arquivo], title: dados.titulo || "Produto Skincare" }).catch(function () {});
          return;
        }
        var a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = nome;
        document.body.appendChild(a); a.click(); a.remove();
        setTimeout(function () { URL.revokeObjectURL(a.href); }, 4000);
        nota.textContent = "Imagem baixada. Abra o Instagram ou o WhatsApp e escolha a foto da galeria.";
      }).catch(function () { btn.disabled = false; nota.textContent = "Não deu para gerar a imagem neste navegador."; });
    });
  }

  // A fonte de título usa algarismos antigos ("1" parece "I"): nos títulos, números por extenso.
  var EXTENSO = ["zero", "um", "dois", "três", "quatro", "cinco", "seis", "sete", "oito", "nove", "dez", "onze", "doze"];
  function extenso(n, feminino) {
    if (n === 1 && feminino) return "uma";
    if (n === 2 && feminino) return "duas";
    return EXTENSO[n] || String(n);
  }

  window.PSCartao = { montar: montar, gerar: gerar, extenso: extenso };
})();
