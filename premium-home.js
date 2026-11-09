/* The mobile menu opens natively, even before JavaScript is available.
   Only add dismissal and focus behavior; never change the initial layout. */
(() => {
  const menu = document.querySelector('.ps-mobile-menu');
  if (!menu) return;
  const toggle = menu.querySelector(':scope > summary');
  const more = menu.querySelector('.ps-mais');
  const close = () => {
    menu.open = false;
    if (more) more.open = false;
  };
  menu.addEventListener('keydown', event => {
    if (event.key !== 'Escape') return;
    if (more?.open) {
      more.open = false;
      more.querySelector('summary')?.focus();
    } else if (menu.open) {
      close();
      toggle.focus();
    }
  });
  menu.addEventListener('click', event => {
    if (event.target.closest('a')) close();
  });
  menu.addEventListener('toggle', () => {
    if (!menu.open && more) more.open = false;
  });
  document.addEventListener('click', event => {
    if (!menu.contains(event.target)) close();
  });
  matchMedia('(max-width: 1040px)').addEventListener('change', close);
})();
