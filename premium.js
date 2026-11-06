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
