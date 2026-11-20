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

/* Carta aberta da home: a linha "hoje" (dia da semana) e a contagem de cliques nas respostas.
   Sem JavaScript a linha mostra "Hoje ainda dá tempo." e os links funcionam igual. */
(function () {
  var hoje = document.querySelector('[data-carta-hoje]');
  if (hoje) {
    var agora = new Date();
    var dia = ['domingo', 'segunda-feira', 'terça-feira', 'quarta-feira', 'quinta-feira', 'sexta-feira', 'sábado'][agora.getDay()];
    hoje.textContent = agora.getHours() < 15
      ? 'Hoje é ' + dia + '. Ainda dá tempo de proteger a pele de hoje.'
      : 'Hoje é ' + dia + '. A rotina desta noite ainda está de pé: limpar e hidratar.';
  }
  document.addEventListener('click', function (ev) {
    var a = ev.target.closest && ev.target.closest('a[data-carta]');
    if (!a || !window.PSAnalytics) return;
    window.PSAnalytics.evento('carta/' + a.getAttribute('data-carta'), 'Carta da home: ' + a.getAttribute('data-carta'));
  });
})();
