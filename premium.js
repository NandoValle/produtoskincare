/* Progressive enhancement: navigation and content stay available without JS. */
(() => {
  const header = document.querySelector('.ps-header');
  const button = header?.querySelector('.ps-menu');
  const navigation = document.getElementById('site-navigation');
  if (button && navigation) {
    const mobile = matchMedia('(max-width: 1240px)');
    const setOpen = (open) => {
      button.setAttribute('aria-expanded', String(open));
      navigation.hidden = mobile.matches && !open;
    };
    const sync = () => { button.hidden = !mobile.matches; setOpen(false); };
    button.addEventListener('click', () => setOpen(button.getAttribute('aria-expanded') !== 'true'));
    header.addEventListener('keydown', event => {
      if (event.key === 'Escape' && mobile.matches && !navigation.hidden) {
        setOpen(false); button.focus();
      }
    });
    navigation.addEventListener('click', event => {
      if (event.target.closest('a') && mobile.matches) setOpen(false);
    });
    document.addEventListener('click', event => {
      if (!header.contains(event.target) && mobile.matches) setOpen(false);
    });
    mobile.addEventListener('change', sync);
    sync();
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
