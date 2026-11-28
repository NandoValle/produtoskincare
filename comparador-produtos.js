/* Comparador visual de texturas — slider antes/depois (pilar "experiência sensorial").
   Uso: <div class="ct" data-ct>…ver documento…</div> + este script com defer.
   Sem JavaScript as duas imagens continuam empilhadas e legíveis (fallback). */
(function () {
  function init(root) {
    var range = root.querySelector(".ct-range");
    var top = root.querySelector(".ct-top");
    var handle = root.querySelector(".ct-handle");
    if (!range || !top) return;
    function update() {
      var p = range.value;
      top.style.clipPath = "inset(0 " + (100 - p) + "% 0 0)";
      if (handle) handle.style.left = p + "%";
    }
    range.addEventListener("input", update);
    update();
  }
  function boot() {
    var nodes = document.querySelectorAll("[data-ct]");
    for (var i = 0; i < nodes.length; i++) init(nodes[i]);
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
