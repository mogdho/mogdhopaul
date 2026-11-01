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

// Blog topic buttons: show only the articles about one topic. Without JavaScript they stay hidden
// and every article is listed.
document.addEventListener('DOMContentLoaded', function () {
  var filter = document.querySelector('[data-topic-filter]');
  if (!filter) return;
  var buttons = filter.querySelectorAll('button');
  var posts = document.querySelectorAll('.post[data-topic]');
  filter.hidden = false;
  buttons.forEach(function (button) {
    button.addEventListener('click', function () {
      var topic = button.getAttribute('data-topic');
      buttons.forEach(function (b) { b.setAttribute('aria-pressed', String(b === button)); });
      posts.forEach(function (post) { post.hidden = topic !== '' && post.getAttribute('data-topic') !== topic; });
    });
  });
});
