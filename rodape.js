/* Redes sociais no rodapé. Cole o link de cada perfil aqui; o que ficar vazio não aparece.
   Depois de preencher, acrescente os mesmos links em "sameAs" da organização em _scripts/schema_site.py. */
(() => {
  const REDES = {
    Instagram: '',
    TikTok: '',
    Pinterest: '',
    YouTube: '',
    WhatsApp: '',
  };
  const base = document.querySelector('.ps-rodape-links');
  if (!base || base.dataset.redes) return;
  base.dataset.redes = '1';
  Object.entries(REDES).forEach(([nome, url]) => {
    if (!/^https:\/\//.test(url)) return;
    const a = document.createElement('a');
    a.href = url;
    a.rel = 'me noopener';
    a.target = '_blank';
    a.textContent = nome;
    base.prepend(a);
  });
})();

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


/* Camada de sonho — lente do cursor e particulas de luz.
   So com ponteiro fino e movimento permitido; nada disso roda em toque
   ou com prefers-reduced-motion. */
(() => {
  if (document.querySelector('.sonho-motes')) return;
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  if (!matchMedia('(pointer: fine)').matches) return;

  const motes = document.createElement('div');
  motes.className = 'sonho-motes';
  motes.setAttribute('aria-hidden', 'true');
  for (let i = 0; i < 5; i++) {
    const m = document.createElement('i');
    m.style.left = (8 + Math.random() * 84) + '%';
    m.style.animationDuration = (38 + Math.random() * 42) + 's';
    m.style.animationDelay = (-Math.random() * 60) + 's';
    const s = 4 + Math.random() * 5;
    m.style.width = m.style.height = s + 'px';
    motes.appendChild(m);
  }
  document.body.appendChild(motes);

  const lente = document.createElement('div');
  lente.className = 'sonho-lente';
  lente.setAttribute('aria-hidden', 'true');
  // Palco fixo com overflow:hidden (estilo inline porque a home nao carrega premium.css):
  // a lente, ao seguir o mouse ate a borda, nao cria rolagem lateral.
  const palco = document.createElement('div');
  palco.style.cssText = 'position:fixed;inset:0;z-index:62;pointer-events:none;overflow:hidden';
  palco.setAttribute('aria-hidden', 'true');
  palco.appendChild(lente);
  document.body.appendChild(palco);
  let alvoX = -500, alvoY = -500, x = -500, y = -500, vivo = false;
  addEventListener('pointermove', (e) => {
    if (e.pointerType && e.pointerType !== 'mouse') return;
    alvoX = e.clientX; alvoY = e.clientY;
    if (!vivo) { vivo = true; x = alvoX; y = alvoY; lente.classList.add('vida'); }
  }, { passive: true });
  (function seguir() {
    x += (alvoX - x) * 0.12;
    y += (alvoY - y) * 0.12;
    lente.style.transform = 'translate(' + x + 'px, ' + y + 'px)';
    requestAnimationFrame(seguir);
  })();
})();

/* Som do sonho — carrega o motor de áudio (sons.js) em todas as páginas
   que já têm este rodapé. O script se protege contra dupla inclusão. */
(() => {
  if (document.querySelector('script[src="/sons.js"]')) return;
  const s = document.createElement('script');
  s.src = '/sons.js';
  s.defer = true;
  document.body.appendChild(s);
})();
