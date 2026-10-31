// mogdhopaul.com: marks that JS is running, then lets photos and their stamps land once as they scroll in.
// Loaded in <head> (not deferred) so the js class is set before first paint.
document.documentElement.classList.add('js');

document.addEventListener('DOMContentLoaded', function () {
  var items = document.querySelectorAll('.fade');
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (reduce || !('IntersectionObserver' in window)) {
    items.forEach(function (el) { el.classList.add('is-visible'); });
    return;
  }

  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        observer.unobserve(entry.target);
      }
    });
  }, { rootMargin: '0px 0px -8% 0px', threshold: 0.15 });

  items.forEach(function (el) { observer.observe(el); });
});

// The "More" menu opens on its own (it's a <details>); this closes it on an outside click or Escape.
document.addEventListener('DOMContentLoaded', function () {
  var menu = document.querySelector('.site-nav__more details');
  if (!menu) return;
  document.addEventListener('click', function (e) {
    if (menu.open && !menu.contains(e.target)) menu.open = false;
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && menu.open) {
      menu.open = false;
      menu.querySelector('summary').focus();
    }
  });
});
