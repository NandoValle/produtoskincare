/* Progressive enhancement: navigation stays available without JS.
   The Mais disclosure is a <details> element, so it works before this script runs. */
(() => {
  const header = document.querySelector('.ps-header');
  const button = header?.querySelector('.ps-menu');
  const navigation = document.getElementById('site-navigation');
  const mais = header?.querySelector('.ps-mais');
  const closeMais = () => { if (mais?.open) mais.open = false; };
  if (button && navigation) {
    const mobile = matchMedia('(max-width: 1040px)');
    const setOpen = (open) => {
      button.setAttribute('aria-expanded', String(open));
      navigation.hidden = mobile.matches && !open;
      if (!open) closeMais();
    };
    const sync = () => { button.hidden = !mobile.matches; setOpen(false); };
    button.addEventListener('click', () => setOpen(button.getAttribute('aria-expanded') !== 'true'));
    header.addEventListener('keydown', event => {
      if (event.key !== 'Escape') return;
      if (mais?.open) {
        closeMais();
        mais.querySelector('summary')?.focus();
        return;
      }
      if (mobile.matches && !navigation.hidden) {
        setOpen(false);
        button.focus();
      }
    });
    navigation.addEventListener('click', event => {
      if (event.target.closest('a') && mobile.matches) setOpen(false);
    });
    document.addEventListener('click', event => {
      if (mais && !mais.contains(event.target)) closeMais();
      if (!header.contains(event.target) && mobile.matches) setOpen(false);
    });
    mobile.addEventListener('change', sync);
    sync();
  } else if (mais) {
    document.addEventListener('click', event => {
      if (!mais.contains(event.target)) closeMais();
    });
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape' && mais.open) {
        closeMais();
        mais.querySelector('summary')?.focus();
      }
    });
  }
  // Modo leitura: botão nas páginas de texto (.ig). A escolha fica só neste aparelho.
  const topoTexto = document.querySelector('main.ig > .ig-top');
  if (topoTexto) {
    const CHAVE = 'ps-leitura';
    const raiz = document.documentElement;
    let ligado = false;
    try { ligado = localStorage.getItem(CHAVE) === '1'; } catch (e) {}
    const botao = document.createElement('button');
    botao.type = 'button';
    botao.className = 'ps-leitura-btn';
    botao.textContent = 'Modo leitura';
    const aplicar = () => {
      if (ligado) raiz.setAttribute('data-leitura', '1'); else raiz.removeAttribute('data-leitura');
      botao.setAttribute('aria-pressed', String(ligado));
      botao.title = ligado ? 'Voltar ao tamanho normal' : 'Letra maior, mais espaço entre as linhas e coluna estreita';
    };
    botao.addEventListener('click', () => {
      ligado = !ligado;
      try { localStorage.setItem(CHAVE, ligado ? '1' : '0'); } catch (e) {}
      aplicar();
    });
    aplicar();
    topoTexto.appendChild(botao);
  }
  // Ouvir este guia: leitura em voz alta nas páginas de texto (o código fica em /ouvir.js).
  if ('speechSynthesis' in window &&
      /^\/(blog|pele|condicoes|rotinas|ingredientes|ativos|ciencia|combina|comparativos)\/[^/]+\/|^\/(biodiversidade|comece-aqui|rotina-de-skincare|correcoes)\//.test(location.pathname)) {
    const s = document.createElement('script');
    s.src = '/ouvir.js';
    s.defer = true;
    document.head.appendChild(s);
  }
  // Site instalável e disponível offline em todas as páginas, não só no provador.
  if (!document.querySelector('link[rel="manifest"]')) {
    const m = document.createElement('link');
    m.rel = 'manifest';
    m.href = '/manifest.json';
    document.head.appendChild(m);
  }
  if ('serviceWorker' in navigator && location.protocol === 'https:') navigator.serviceWorker.register('/sw.js').catch(() => {});
  // Convite para instalar: só a partir da segunda visita, e só onde o navegador oferece a instalação
  // (o Safari do iPhone não oferece; lá o caminho é Compartilhar > Adicionar à Tela de Início).
  (() => {
    let visitas = 0, recusou = false;
    try {
      visitas = parseInt(localStorage.getItem('ps-visitas') || '0', 10) || 0;
      if (!sessionStorage.getItem('ps-visita')) {
        sessionStorage.setItem('ps-visita', '1');
        visitas += 1;
        localStorage.setItem('ps-visitas', String(visitas));
      }
      recusou = localStorage.getItem('ps-instalar') === 'nao';
    } catch (e) { return; }
    window.addEventListener('beforeinstallprompt', evento => {
      evento.preventDefault();
      if (visitas < 2 || recusou || document.querySelector('.ps-instalar')) return;
      const barra = document.createElement('aside');
      barra.className = 'ps-instalar';
      barra.setAttribute('aria-label', 'Instalar o site');
      const texto = document.createElement('p');
      texto.textContent = 'Instale o Produto Skincare neste aparelho: abre como um app, e as páginas que você já visitou continuam abrindo sem internet.';
      const sim = document.createElement('button');
      sim.type = 'button';
      sim.className = 'ps-instalar-sim';
      sim.textContent = 'Instalar';
      const nao = document.createElement('button');
      nao.type = 'button';
      nao.className = 'ps-instalar-nao';
      nao.textContent = 'Agora não';
      const fechar = lembrar => {
        barra.remove();
        if (lembrar) { try { localStorage.setItem('ps-instalar', 'nao'); } catch (e) {} }
      };
      sim.addEventListener('click', () => {
        evento.prompt();
        evento.userChoice.then(r => {
          if (window.PSAnalytics) window.PSAnalytics.evento('instalar/' + r.outcome, 'Instalação do site');
          fechar(true);
        }).catch(() => fechar(false));
      });
      nao.addEventListener('click', () => fechar(true));
      barra.append(texto, sim, nao);
      document.body.appendChild(barra);
    });
  })();
  const motion = matchMedia('(prefers-reduced-motion: reduce)');
  if (!motion.matches && 'IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('ps-revealed');
        observer.unobserve(entry.target);
      });
    }, {threshold: .08});
    document.querySelectorAll('.ps-section-head,.ps-skin,.ps-journey,.ps-tool,.ps-story').forEach(el => observer.observe(el));
    motion.addEventListener('change', () => {
      if (motion.matches) observer.disconnect();
    });
  }
})();
