// Comparador visual de texturas (wipe). Liga o controle deslizante ao corte
// da ilustração de cima. Sem JavaScript, o corte estático de 50% já mostra a
// comparação; o controle não move (aviso <noscript> no próprio bloco).
(function () {
  "use strict";
  function ligar(bloco) {
    var range = bloco.querySelector("input[type=range]");
    var cima = bloco.querySelector(".ps-textura-cima");
    var alca = bloco.querySelector(".ps-textura-alca");
    var moldura = bloco.querySelector(".ps-textura-moldura");
    if (!range || !cima || !moldura) return;
    function aplicar(v) {
      v = Math.max(0, Math.min(100, v));
      cima.style.clipPath = "inset(0 " + (100 - v) + "% 0 0)";
      if (alca) alca.style.left = v + "%";
      range.value = String(Math.round(v));
    }
    range.addEventListener("input", function () { aplicar(parseFloat(range.value)); });
    var arrastando = false;
    function doPonteiro(e) {
      var r = moldura.getBoundingClientRect();
      if (r.width > 0) aplicar(((e.clientX - r.left) / r.width) * 100);
    }
    moldura.addEventListener("pointerdown", function (e) {
      arrastando = true;
      try { moldura.setPointerCapture(e.pointerId); } catch (x) {}
      doPonteiro(e);
      e.preventDefault();
    });
    moldura.addEventListener("pointermove", function (e) { if (arrastando) doPonteiro(e); });
    function soltar() { arrastando = false; }
    moldura.addEventListener("pointerup", soltar);
    moldura.addEventListener("pointercancel", soltar);
    aplicar(50);
  }
  document.querySelectorAll(".ps-textura").forEach(ligar);
})();
