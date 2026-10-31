// mogdhopaul.com/currency-converter: leu or euro to Bangladeshi taka, with the 2.5% government incentive.
(function () {
  'use strict';

  var INCENTIVE = 0.025;
  var RATE_URL = 'https://api.exchangerate-api.com/v4/latest/';
  var QUICK_TK = [10000, 20000, 50000, 100000];
  var OFFER = {
    RON: 'Sign up with my link and get <strong>50 RON off</strong> your first transfer of 500 RON or more.',
    EUR: 'Sign up with my link and get a <strong>discount on your first transfer</strong>. Remitly shows the exact offer when you sign up.'
  };

  var root = document.querySelector('[data-converter]');
  if (!root) return;
  var form = root.querySelector('form');
  var amount = form.elements.amount;
  var rate = form.elements.rate;
  var note = root.querySelector('[data-rate-note]');
  var error = root.querySelector('[data-error]');
  var rates = {};        // live rates by currency
  var typedRate = {};    // rates the visitor typed, by currency
  var loading = true;

  function store(key, value) {
    try {
      if (value === undefined) return window.localStorage.getItem(key);
      window.localStorage.setItem(key, value);
    } catch (e) { return null; }
  }

  // "1.234,56", "1,234.56", "1234,5" and "1 234" all read the way a person means them.
  function parse(text) {
    var s = String(text || '').replace(/[\s ']/g, '');
    if (!s) return NaN;
    var comma = s.lastIndexOf(','), dot = s.lastIndexOf('.');
    if (comma > -1 && dot > -1) {
      s = comma > dot ? s.replace(/\./g, '').replace(',', '.') : s.replace(/,/g, '');
    } else if (comma > -1) {
      var parts = s.split(',');
      s = parts.length === 2 && parts[1].length !== 3 ? parts.join('.') : parts.join('');
    }
    return /^(\d+\.?\d*|\.\d+)$/.test(s) ? parseFloat(s) : NaN;
  }

  function money(n, unit) {
    return n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' ' + unit;
  }

  function currency() { return form.elements.currency.value; }
  function mode() { return form.elements.mode.value; }

  // send = amount in RON/EUR; base = converted taka; total = taka after the incentive.
  function work(value, r, from) {
    if (from === 'send') {
      var base = value * r;
      return { send: value, base: base, incentive: base * INCENTIVE, total: base * (1 + INCENTIVE) };
    }
    var b = value / (1 + INCENTIVE);
    return { send: b / r, base: b, incentive: value - b, total: value };
  }

  function set(name, text) {
    root.querySelector('[data-out="' + name + '"]').textContent = text;
  }

  function render() {
    var cur = currency();
    var value = parse(amount.value), r = parse(rate.value);
    var ok = value > 0 && r > 0;
    error.hidden = ok || (loading && !rate.value);
    if (!ok) {
      ['send', 'base', 'incentive', 'total'].forEach(function (k) { set(k, '–'); });
    } else {
      var res = work(value, r, mode());
      set('send', money(res.send, cur));
      set('base', money(res.base, 'TK'));
      set('incentive', '+ ' + money(res.incentive, 'TK'));
      set('total', money(res.total, 'TK'));
    }
    renderQuick(r > 0 ? r : 0, cur);
  }

  function renderQuick(r, cur) {
    var list = document.querySelector('[data-quick]');
    list.innerHTML = '';
    QUICK_TK.forEach(function (tk) {
      var li = document.createElement('li');
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'quick__item';
      var send = r ? money(work(tk, r, 'receive').send, cur) : '…';
      btn.innerHTML = '<span class="quick__tk"></span><span class="quick__send"></span>';
      btn.querySelector('.quick__tk').textContent = tk.toLocaleString('en-US') + ' TK arrives';
      btn.querySelector('.quick__send').textContent = 'send ' + send;
      btn.addEventListener('click', function () {
        form.elements.mode.value = 'receive';
        amount.value = String(tk);
        labels();
        render();
        root.scrollIntoView({ behavior: 'smooth', block: 'start' });
        amount.focus({ preventScroll: true });
      });
      li.appendChild(btn);
      list.appendChild(li);
    });
  }

  function labels() {
    var cur = currency(), send = mode() === 'send';
    root.querySelector('[data-amount-label]').textContent = send ? 'Amount you send' : 'Amount that should arrive';
    root.querySelector('[data-amount-unit]').textContent = send ? cur : 'TK';
    root.querySelector('[data-rate-unit]').textContent = '1 ' + cur + ' =';
    document.querySelector('[data-offer-text]').innerHTML = OFFER[cur];
  }

  function showRate() {
    var cur = currency();
    if (typedRate[cur]) {
      rate.value = typedRate[cur];
      note.textContent = 'Using the rate you typed. Clear the box to go back to today’s rate.';
    } else if (rates[cur]) {
      rate.value = rates[cur].value.toFixed(2);
      note.textContent = rates[cur].saved
        ? 'Saved rate from ' + rates[cur].date + '. You can type your own.'
        : 'Today’s rate, filled in for you. You can type your own.';
    } else {
      rate.value = '';
      note.textContent = 'Couldn’t get today’s rate. Type the rate from your bank or app.';
    }
  }

  // The last rate this browser saw, used until today's arrives (or if it can't be fetched).
  function loadSaved(cur) {
    try {
      var saved = JSON.parse(store('rate-' + cur));
      if (saved && saved.value > 0) rates[cur] = { value: saved.value, date: saved.date, saved: true };
    } catch (e) { /* nothing saved */ }
  }

  function fetchRate(cur) {
    return fetch(RATE_URL + cur)
      .then(function (res) { if (!res.ok) throw new Error(res.status); return res.json(); })
      .then(function (data) {
        var v = data && data.rates && data.rates.BDT;
        if (!(v > 0)) throw new Error('no BDT');
        rates[cur] = { value: v, date: data.date };
        store('rate-' + cur, JSON.stringify({ value: v, date: data.date }));
      })
      .catch(function () { /* keep the saved rate, if any */ });
  }

  form.addEventListener('submit', function (e) { e.preventDefault(); });
  form.addEventListener('change', function (e) {
    if (e.target.name === 'currency') { store('currency', currency()); showRate(); }
    labels();
    render();
  });
  amount.addEventListener('input', render);
  rate.addEventListener('input', function () {
    var cur = currency();
    if (rate.value.trim()) {
      typedRate[cur] = rate.value;
      note.textContent = 'Using the rate you typed. Clear the box to go back to today’s rate.';
      render();
    } else {
      delete typedRate[cur];
      showRate();
      render();
    }
  });

  root.querySelector('[data-copy="send"]').addEventListener('click', function () {
    var res = work(parse(amount.value), parse(rate.value), mode());
    if (!(res.send > 0) || !navigator.clipboard) return;
    var btn = this;
    navigator.clipboard.writeText(res.send.toFixed(2)).then(function () {
      btn.textContent = 'Copied';
      setTimeout(function () { btn.textContent = 'Copy'; }, 1500);
    });
  });

  var remembered = store('currency');
  if (remembered === 'EUR' || remembered === 'RON') form.elements.currency.value = remembered;
  ['RON', 'EUR'].forEach(loadSaved);
  labels();
  if (rates[currency()]) showRate();
  render();
  Promise.all([fetchRate('RON'), fetchRate('EUR')]).then(function () {
    loading = false;
    if (!typedRate[currency()]) showRate();
    render();
  });
})();
