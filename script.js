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
