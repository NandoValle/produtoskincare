/* Home "Lumière": entrada dos blocos ao rolar.
   Sem JavaScript nada fica escondido: a classe lm-js só entra aqui.
   Se o observador não responder (aba em segundo plano, navegador antigo), mostra tudo. */
(function () {
  var raiz = document.getElementById('conteudo');
  if (!raiz || !raiz.classList.contains('lm')) return;
  var itens = raiz.querySelectorAll('.lm-revela');
  if (!itens.length) return;
  function mostrarTudo() {
    itens.forEach(function (el) { el.classList.add('lm-dentro'); });
  }
  raiz.classList.add('lm-js');
  if (!('IntersectionObserver' in window) || matchMedia('(prefers-reduced-motion: reduce)').matches) {
    mostrarTudo();
    return;
  }
  var vivo = false;
  var olheiro = new IntersectionObserver(function (entradas) {
    vivo = true;
    entradas.forEach(function (e) {
      if (!e.isIntersecting) return;
      e.target.classList.add('lm-dentro');
      olheiro.unobserve(e.target);
    });
  }, { threshold: 0.08, rootMargin: '0px 0px -5% 0px' });
  itens.forEach(function (el) { olheiro.observe(el); });
  setTimeout(function () {
    if (vivo) return;
    olheiro.disconnect();
    mostrarTudo();
  }, 1500);
})();
