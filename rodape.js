/* Rodapé no celular: cada coluna (Tipos de pele, Ferramentas, Conteúdo...) vira um acordeão fechado.
   Sem JavaScript, ou em telas maiores, o rodapé continua todo aberto. */
(() => {
  const grade = document.querySelector('.ps-rodape-grid');
  if (!grade || grade.dataset.acordeao) return;
  grade.dataset.acordeao = '1';
  const celular = matchMedia('(max-width: 560px)');
  const grupos = [];
  grade.querySelectorAll(':scope > nav').forEach((nav, i) => {
    const titulo = nav.querySelector('.ps-rodape-titulo');
    const lista = nav.querySelector('ul');
    if (!titulo || !lista) return;
    lista.id = lista.id || `ps-rodape-lista-${i + 1}`;
    const botao = document.createElement('button');
    botao.type = 'button';
    botao.className = 'ps-rodape-toggle';
    botao.textContent = titulo.textContent;
    botao.setAttribute('aria-controls', lista.id);
    botao.setAttribute('aria-expanded', 'false');
    titulo.before(botao);
    const grupo = { nav, titulo, lista, botao };
    botao.addEventListener('click', () => abrir(grupo, botao.getAttribute('aria-expanded') !== 'true'));
    grupos.push(grupo);
  });
  function abrir(g, aberto) {
    g.botao.setAttribute('aria-expanded', String(aberto));
    g.lista.hidden = celular.matches && !aberto;
  }
  function sincronizar() {
    grupos.forEach(g => {
      g.botao.hidden = !celular.matches;
      g.titulo.hidden = celular.matches;
      abrir(g, false);
    });
  }
  celular.addEventListener('change', sincronizar);
  sincronizar();
})();
