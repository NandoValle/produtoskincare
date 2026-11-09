/* Leitura do rótulo por foto, no próprio aparelho (Tesseract.js, carregado do jsDelivr só quando a pessoa usa).
 * A foto não é enviada a nenhum servidor. Na primeira vez, o leitor baixa cerca de 7 MB.
 *
 * Uso: PSOcr.ligar(inputFile, elementoStatus, function (texto) { ... })
 * O texto devolvido já vem limpo (começa depois de "Ingredientes:", sem quebras de linha).
 * É a mesma leitura de /ferramentas/ingredientes/.
 */
(function () {
  "use strict";
  var VERSAO = "6.0.1";

  function carregarScript(src) {
    return new Promise(function (ok, erro) {
      var s = document.createElement("script");
      s.src = src; s.async = true; s.onload = ok; s.onerror = function () { erro(new Error("script")); };
      document.head.appendChild(s);
    });
  }

  // Fotos de celular são enormes: reduz e passa para tons de cinza, o que acelera e costuma melhorar a leitura.
  function prepararImagem(arquivo) {
    return new Promise(function (ok, erro) {
      var url = URL.createObjectURL(arquivo);
      var img = new Image();
      img.onload = function () {
        var escala = Math.min(1, 2000 / Math.max(img.width, img.height));
        var c = document.createElement("canvas");
        c.width = Math.round(img.width * escala); c.height = Math.round(img.height * escala);
        var ctx = c.getContext("2d");
        ctx.filter = "grayscale(1) contrast(1.3)";
        ctx.drawImage(img, 0, 0, c.width, c.height);
        URL.revokeObjectURL(url);
        ok(c);
      };
      img.onerror = function () { URL.revokeObjectURL(url); erro(new Error("imagem")); };
      img.src = url;
    });
  }

  function limpar(texto) {
    var t = String(texto || "").replace(/\r/g, "");
    var m = t.match(/(ingredient[se]s?|ingredientes|composi[cç][aã]o|inci)\s*[:\-]/i);
    if (m) t = t.slice(m.index + m[0].length);
    return t.replace(/-\n/g, "").replace(/\s*\n\s*/g, " ").replace(/\s{2,}/g, " ").replace(/\s*[,;]\s*/g, ", ").trim();
  }

  function ler(arquivo, status) {
    var worker;
    status.textContent = "Carregando o leitor…";
    return (window.Tesseract ? Promise.resolve() : carregarScript("https://cdn.jsdelivr.net/npm/tesseract.js@" + VERSAO + "/dist/tesseract.min.js"))
      .then(function () { return prepararImagem(arquivo); })
      .then(function (canvas) {
        return window.Tesseract.createWorker("eng", 1, {
          logger: function (m) {
            if (m.status === "recognizing text") status.textContent = "Lendo o rótulo… " + Math.round((m.progress || 0) * 100) + "%";
            else if (/loading|initializ/i.test(m.status || "")) status.textContent = "Preparando o leitor…";
          }
        }).then(function (w) { worker = w; return w.recognize(canvas); });
      })
      .then(function (res) {
        if (worker) worker.terminate();
        return limpar(res && res.data && res.data.text);
      }, function (e) {
        if (worker) worker.terminate();
        throw e;
      });
  }

  function ligar(input, status, aoLer) {
    if (!input || !status) return;
    input.addEventListener("change", function () {
      var arquivo = input.files && input.files[0];
      if (!arquivo) return;
      ler(arquivo, status).then(function (texto) {
        if (texto.length < 8) {
          status.textContent = "Não consegui ler o texto. Tente uma foto mais perto, reta e com mais luz, ou digite os ingredientes.";
          return;
        }
        status.textContent = "Pronto. Confira o texto lido (a leitura pode trocar letras) antes de continuar.";
        aoLer(texto);
      }).catch(function () {
        status.textContent = "Não deu para ler a foto agora. Verifique a conexão na primeira vez (o leitor precisa ser baixado) ou digite os ingredientes.";
      }).then(function () { input.value = ""; });
    });
  }

  window.PSOcr = { ligar: ligar, ler: ler, limpar: limpar };
})();
