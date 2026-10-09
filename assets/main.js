(function () {
  var root = document.documentElement;

  // 深色模式
  var themeBtn = document.getElementById('theme-btn');
  themeBtn && themeBtn.addEventListener('click', function () {
    var t = root.dataset.theme === 'dark' ? 'light' : 'dark';
    root.dataset.theme = t;
    try { localStorage.setItem('theme', t); } catch (e) {}
  });

  // 代码复制按钮
  document.querySelectorAll('.prose .highlight').forEach(function (block) {
    var btn = document.createElement('button');
    btn.className = 'copy-btn'; btn.type = 'button'; btn.textContent = '复制';
    btn.addEventListener('click', function () {
      var code = block.querySelector('pre').innerText;
      var done = function () { btn.textContent = '已复制'; btn.classList.add('done'); setTimeout(function () { btn.textContent = '复制'; btn.classList.remove('done'); }, 1500); };
      if (navigator.clipboard) navigator.clipboard.writeText(code).then(done);
      else { var ta = document.createElement('textarea'); ta.value = code; document.body.appendChild(ta); ta.select(); document.execCommand('copy'); ta.remove(); done(); }
    });
    block.appendChild(btn);
  });

  // 目录高亮
  var tocLinks = document.querySelectorAll('.toc a');
  if (tocLinks.length && 'IntersectionObserver' in window) {
    var map = {};
    tocLinks.forEach(function (a) { map[decodeURIComponent(a.getAttribute('href').slice(1))] = a; });
    var obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting && map[e.target.id]) {
          tocLinks.forEach(function (a) { a.classList.remove('active'); });
          map[e.target.id].classList.add('active');
        }
      });
    }, { rootMargin: '-70px 0px -70% 0px' });
    document.querySelectorAll('.prose h2[id], .prose h3[id]').forEach(function (h) { obs.observe(h); });
  }

  // 搜索
  var modal = document.getElementById('search-modal');
  var input = document.getElementById('search-input');
  var list = document.getElementById('search-results');
  var index = null, sel = -1;

  function esc(s) { return s.replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function hl(text, terms) {
    var out = esc(text);
    terms.forEach(function (t) {
      if (!t) return;
      var re = new RegExp(esc(t).replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');
      out = out.replace(re, function (m) { return '<mark>' + m + '</mark>'; });
    });
    return out;
  }
  function load() {
    if (index) return Promise.resolve(index);
    return fetch('/search.json').then(function (r) { return r.json(); }).then(function (d) { index = d; return d; });
  }
  function render(q) {
    var terms = q.toLowerCase().split(/\s+/).filter(Boolean);
    if (!terms.length) {
      list.innerHTML = index.slice(0, 20).map(function (p) {
        return '<li><a href="' + p.url + '"><div class="r-title">' + esc(p.title) + '</div><div class="r-snippet">' + esc(p.summary) + '</div></a></li>';
      }).join('');
      sel = -1; return;
    }
    var res = [];
    index.forEach(function (p) {
      var title = p.title.toLowerCase(), tags = p.tags.join(' ').toLowerCase(), body = (p.summary + ' ' + p.text).toLowerCase();
      var score = 0, ok = terms.every(function (t) {
        var s = 0;
        if (title.indexOf(t) > -1) s += 10;
        if (tags.indexOf(t) > -1) s += 5;
        if (body.indexOf(t) > -1) s += 1;
        score += s; return s > 0;
      });
      if (ok) {
        var full = p.summary + ' ' + p.text, pos = full.toLowerCase().indexOf(terms[0]);
        var start = Math.max(0, pos - 30), snip = (start > 0 ? '…' : '') + full.slice(start, start + 110) + '…';
        res.push({ p: p, score: score, snip: snip });
      }
    });
    res.sort(function (a, b) { return b.score - a.score; });
    res = res.slice(0, 50);
    list.innerHTML = res.length ? res.map(function (r) {
      return '<li><a href="' + r.p.url + '"><div class="r-title">' + hl(r.p.title, terms) + '</div><div class="r-snippet">' + hl(r.snip, terms) + '</div></a></li>';
    }).join('') : '<li class="s-empty">没有找到相关文章</li>';
    sel = -1;
  }
  function open() {
    modal.hidden = false; input.focus(); input.select();
    load().then(function () { render(input.value); });
  }
  function close() { modal.hidden = true; }
  document.getElementById('search-btn').addEventListener('click', open);
  document.querySelectorAll('[data-open-search]').forEach(function (b) { b.addEventListener('click', open); });
  modal.querySelectorAll('[data-close]').forEach(function (b) { b.addEventListener('click', close); });
  input.addEventListener('input', function () { if (index) render(input.value); });
  document.addEventListener('keydown', function (e) {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); modal.hidden ? open() : close(); return; }
    if (e.key === '/' && modal.hidden && !/input|textarea/i.test(document.activeElement.tagName)) { e.preventDefault(); open(); return; }
    if (modal.hidden) return;
    var items = list.querySelectorAll('li a');
    if (e.key === 'Escape') close();
    else if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault();
      if (!items.length) return;
      sel = (sel + (e.key === 'ArrowDown' ? 1 : -1) + items.length) % items.length;
      list.querySelectorAll('li').forEach(function (li, i) { li.classList.toggle('sel', i === sel); });
      items[sel].scrollIntoView({ block: 'nearest' });
    } else if (e.key === 'Enter' && items.length) {
      e.preventDefault(); location.href = items[Math.max(sel, 0)].getAttribute('href');
    }
  });
  // 支持 ?q= 直接打开搜索
  var q = new URLSearchParams(location.search).get('q');
  if (q) { input.value = q; open(); }
})();
