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

// Newsletter: remembers on this device that the popup was shown or the reader subscribed.
var NEWSLETTER_KEY = 'mp-newsletter-popup';
function newsletterSeen() {
  try { return localStorage.getItem(NEWSLETTER_KEY); } catch (e) { return 'storage-blocked'; }
}
function rememberNewsletter(value) {
  try { localStorage.setItem(NEWSLETTER_KEY, value); } catch (e) { /* private mode: nothing to keep */ }
}

// Newsletter forms (footer and popup): send the email to MailerLite in the background and show the
// result in place. Without JavaScript the forms still post straight to MailerLite.
document.addEventListener('DOMContentLoaded', function () {
  if (!window.fetch) return;
  document.querySelectorAll('[data-newsletter]').forEach(function (form) {
    var status = form.querySelector('[data-newsletter-status]');
    var button = form.querySelector('button');
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      button.disabled = true;
      status.textContent = 'Sending…';
      fetch(form.action, { method: 'POST', body: new FormData(form) })
        .then(function (res) { return res.json(); })
        .then(function (data) {
          if (!data.success) throw new Error('rejected');
          form.reset();
          rememberNewsletter('subscribed');
          status.textContent = 'Almost done: check your inbox and confirm your email.';
        })
        .catch(function () {
          status.textContent = 'That did not go through. Check the address and try again.';
        })
        .then(function () { button.disabled = false; });
    });
  });
});

// Newsletter popup on articles and project pages: opens once per device, when the reader is halfway
// down the page. A centred dialog on wide screens; a small bar at the bottom on phones, so it never
// covers the article (Google penalises full-screen popups on mobile).
document.addEventListener('DOMContentLoaded', function () {
  var popup = document.querySelector('[data-newsletter-popup]');
  if (!popup || typeof popup.showModal !== 'function' || newsletterSeen()) return;
  // phones, upright or sideways (keep in step with the matching @media rule in style.css)
  var phone = window.matchMedia('(max-width: 40rem), (max-height: 30rem)');

  function open() {
    if (phone.matches) {
      // the bar must not take focus: that would draw a focus ring and could pop up the keyboard
      popup.show();
      if (popup.contains(document.activeElement)) document.activeElement.blur();
    } else {
      popup.showModal();
      popup.querySelector('input[type="email"]').focus();
    }
  }

  function onScroll() {
    var room = document.documentElement.scrollHeight - window.innerHeight;
    if (room <= 0 || window.scrollY / room < 0.5) return;
    window.removeEventListener('scroll', onScroll);
    if (newsletterSeen()) return;  // subscribed in the footer meanwhile
    rememberNewsletter('shown');
    open();
  }
  window.addEventListener('scroll', onScroll, { passive: true });

  // rotating the device (or resizing the window) while it's open: reopen it in the right form
  phone.addEventListener('change', function () {
    if (!popup.open) return;
    popup.close();
    open();
  });

  popup.querySelector('[data-popup-close]').addEventListener('click', function () { popup.close(); });
  // a click on the dimmed area outside the card closes it too
  popup.addEventListener('click', function (e) { if (e.target === popup) popup.close(); });
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

// "Ask your AI" on tool pages: two tabs (chat or agent) and a Copy button for each prompt.
// Without JavaScript both prompts are shown, one under the other, and can be selected by hand.
document.addEventListener('DOMContentLoaded', function () {
  var box = document.querySelector('[data-ask-ai]');
  if (!box) return;
  var tablist = box.querySelector('[role="tablist"]');
  var tabs = Array.prototype.slice.call(box.querySelectorAll('[role="tab"]'));
  var panels = tabs.map(function (t) { return document.getElementById(t.getAttribute('aria-controls')); });

  function select(i, focus) {
    tabs.forEach(function (t, n) {
      var on = n === i;
      t.setAttribute('aria-selected', on ? 'true' : 'false');
      t.tabIndex = on ? 0 : -1;
      panels[n].hidden = !on;
    });
    if (focus) tabs[i].focus();
  }
  if (tablist) {  // browser tools have one prompt and no tabs
    tablist.hidden = false;
    select(0, false);
  }
  tabs.forEach(function (t, i) {
    t.addEventListener('click', function () { select(i, false); });
    t.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
        e.preventDefault();
        select((i + (e.key === 'ArrowRight' ? 1 : tabs.length - 1)) % tabs.length, true);
      }
    });
  });

  box.querySelectorAll('[data-copy-prompt]').forEach(function (button) {
    var panel = button.closest('[role="tabpanel"]');
    var prompt = panel.querySelector('.ask-ai__prompt');
    var status = panel.querySelector('.ask-ai__status');
    function done(ok) {
      status.textContent = ok ? 'Copied. Now paste it into your AI chat.' : 'Select the text above and copy it with Ctrl + C.';
    }
    button.addEventListener('click', function () {
      var text = prompt.textContent;
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function () { done(true); }, function () { done(fallback()); });
      } else {
        done(fallback());
      }
      function fallback() {
        panel.querySelector('details').open = true;  // the text must be visible to be selected
        var range = document.createRange();
        range.selectNodeContents(prompt);
        var sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(range);
        try { return document.execCommand('copy'); } catch (err) { return false; }
      }
    });
  });
});
