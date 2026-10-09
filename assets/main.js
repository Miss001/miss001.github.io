(function () {
  var root = document.documentElement;

  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var EASE = 'cubic-bezier(.22,1,.36,1)';

  // 深色模式：支持 View Transitions 时从按钮处圆形展开，否则平滑渐变
  var themeBtn = document.getElementById('theme-btn');
  function setTheme(t) {
    root.dataset.theme = t;
    try { localStorage.setItem('theme', t); } catch (e) {}
  }
  themeBtn && themeBtn.addEventListener('click', function () {
    var t = root.dataset.theme === 'dark' ? 'light' : 'dark';
    if (reduce) { setTheme(t); return; }
    if (!document.startViewTransition) {
      root.classList.add('theme-fade'); setTheme(t);
      setTimeout(function () { root.classList.remove('theme-fade'); }, 700);
      return;
    }
    var r = themeBtn.getBoundingClientRect(), x = r.left + r.width / 2, y = r.top + r.height / 2;
    var R = Math.hypot(Math.max(x, innerWidth - x), Math.max(y, innerHeight - y));
    root.classList.add('vt-theme');
    var vt = document.startViewTransition(function () { setTheme(t); });
    vt.ready.then(function () {
      root.animate({ clipPath: ['circle(0px at ' + x + 'px ' + y + 'px)', 'circle(' + R + 'px at ' + x + 'px ' + y + 'px)'] },
        { duration: 900, easing: EASE, pseudoElement: '::view-transition-new(root)' });
    }).catch(function () {});
    vt.finished.finally(function () { root.classList.remove('vt-theme'); });
  });

  // 入场与滚动显现：同一批进入视口的元素依次错开
  var RV = '.hero-inner > *, .tile, .post-row, .tag-group, .sec-head, .page-head, .page-head + .chips, .cat-hero, .post-header, .prose, .post-nav a, .about-hero, .empty, .pager, .more-row, .toc-inner';
  var rvEls = Array.prototype.slice.call(document.querySelectorAll(RV));
  var hero = document.getElementById('hero');
  function show(el, delay) {
    el.style.setProperty('--d', delay + 'ms');
    el.classList.add('in');
    setTimeout(function () { el.style.removeProperty('--d'); }, delay + 1100);
    if (el.classList.contains('intro-stats')) countUp(el);
  }
  if (hero) hero.classList.add('in');
  if (reduce || !('IntersectionObserver' in window)) {
    rvEls.forEach(function (el) { el.classList.add('in'); });
  } else {
    rvEls.forEach(function (el) { el.classList.add('rv'); });
    var batch = 0, batchTimer = null;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        io.unobserve(en.target);
        show(en.target, Math.min(batch++, 8) * 80 + (hero && hero.contains(en.target) ? 120 : 0));
      });
      clearTimeout(batchTimer); batchTimer = setTimeout(function () { batch = 0; }, 120);
    }, { rootMargin: '0px 0px -6% 0px', threshold: 0 });
    requestAnimationFrame(function () { rvEls.forEach(function (el) { io.observe(el); }); });
  }

  // 首页数字：从 0 缓动到目标值
  function countUp(box) {
    box.querySelectorAll('[data-count]').forEach(function (b, i) {
      var n = +b.dataset.count, t0 = null, dur = 1400 + i * 150;
      if (reduce || !n) return;
      b.textContent = '0';
      function step(ts) {
        if (!t0) t0 = ts;
        var k = Math.min(1, (ts - t0) / dur), v = 1 - Math.pow(1 - k, 4);
        b.textContent = Math.round(n * v);
        if (k < 1) requestAnimationFrame(step);
      }
      requestAnimationFrame(step);
    });
  }

  // 首页 Hero：细线流场（canvas），离屏或页面隐藏时暂停
  var cv = document.getElementById('hero-canvas');
  if (cv && cv.getContext) (function () {
    var ctx = cv.getContext('2d'), w = 0, h = 0, dpr = Math.min(window.devicePixelRatio || 1, 1.5);
    var running = false, visible = true, raf = 0, t = 0, last = 0;
    function size() {
      var r = cv.getBoundingClientRect(); w = r.width; h = r.height;
      cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr); ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    function color(name) { return getComputedStyle(root).getPropertyValue(name).trim(); }
    function draw() {
      ctx.clearRect(0, 0, w, h);
      var lr = color('--line-rgb'), la = color('--line-accent'), lines = 26, step = w > 900 ? 14 : 10;
      for (var i = 0; i < lines; i++) {
        var p = i / (lines - 1), base = h * (.12 + p * .8), amp = 22 + 34 * Math.sin(p * Math.PI);
        var accent = i === 9 || i === 17;
        ctx.beginPath();
        for (var x = -10; x <= w + 10; x += step) {
          var u = x / w;
          var y = base
            + Math.sin(u * 3.2 + t * .00022 + p * 2.4) * amp
            + Math.sin(u * 7.1 - t * .00016 + p * 5.0) * amp * .28
            - Math.pow(u, 1.6) * h * .18 * (1 - p);
          x === -10 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
        }
        var fade = .05 + .13 * Math.sin(p * Math.PI);
        ctx.strokeStyle = accent ? 'rgba(' + la + ',' + (fade + .22) + ')' : 'rgba(' + lr + ',' + fade + ')';
        ctx.lineWidth = accent ? 1.1 : .7;
        ctx.stroke();
      }
    }
    function loop(ts) {
      raf = 0;
      if (!running) return;
      t += Math.min(ts - (last || ts), 50); last = ts;
      draw();
      raf = requestAnimationFrame(loop);
    }
    function update() {
      var go = visible && !document.hidden && !reduce;
      if (go && !running) { running = true; last = 0; raf = requestAnimationFrame(loop); }
      if (!go) { running = false; if (raf) cancelAnimationFrame(raf); raf = 0; }
    }
    size(); t = 4000; draw();
    window.addEventListener('resize', function () { size(); draw(); });
    new MutationObserver(function () { draw(); }).observe(root, { attributes: true, attributeFilter: ['data-theme'] });
    document.addEventListener('visibilitychange', update);
    if ('IntersectionObserver' in window) new IntersectionObserver(function (es) { visible = es[0].isIntersecting; update(); }).observe(cv);
    update();
  })();

  // 滚动：Hero 视差 + 文章阅读进度
  var heroBg = hero && hero.querySelector('.hero-bg'), heroIn = hero && hero.querySelector('.hero-inner');
  var bar = document.getElementById('progress'), article = document.querySelector('.post .prose');
  var ticking = false;
  function onScroll() {
    ticking = false;
    var y = window.scrollY;
    if (heroBg && !reduce && y < 1200) {
      heroBg.style.transform = 'translate3d(0,' + (y * .22).toFixed(1) + 'px,0)';
      heroIn.style.transform = 'translate3d(0,' + (y * .08).toFixed(1) + 'px,0)';
      heroIn.style.opacity = Math.max(.15, 1 - y / 700).toFixed(3);
    }
    if (bar && article) {
      var r = article.getBoundingClientRect(), total = r.height - innerHeight * .6;
      var k = Math.max(0, Math.min(1, (-r.top + 120) / Math.max(total, 1)));
      bar.style.transform = 'scaleX(' + k.toFixed(4) + ')';
    }
  }
  if (bar && article) bar.classList.add('on');
  window.addEventListener('scroll', function () { if (!ticking) { ticking = true; requestAnimationFrame(onScroll); } }, { passive: true });
  onScroll();

  // 代码复制按钮
  document.querySelectorAll('.prose .highlight').forEach(function (block) {
    var btn = document.createElement('button');
    btn.className = 'copy-btn'; btn.type = 'button'; btn.textContent = '复制';
    btn.addEventListener('click', function () {
      var code = block.querySelector('pre').innerText;
      var done = function () { btn.textContent = '已复制'; btn.classList.add('done'); setTimeout(function () { btn.textContent = '复制'; btn.classList.remove('done'); }, 1500); };
      var legacy = function () { var ta = document.createElement('textarea'); ta.value = code; ta.style.position = 'fixed'; ta.style.opacity = '0'; document.body.appendChild(ta); ta.select(); try { document.execCommand('copy'); } catch (e) {} ta.remove(); done(); };
      if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(code).then(done, legacy);
      else legacy();
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
  var isOpen = false, closeTimer = null;
  function open() {
    clearTimeout(closeTimer); isOpen = true;
    modal.hidden = false;
    requestAnimationFrame(function () { requestAnimationFrame(function () { if (isOpen) modal.classList.add('open'); }); });
    input.focus(); input.select();
    load().then(function () { render(input.value); });
  }
  function close() {
    if (!isOpen) return;
    isOpen = false; modal.classList.remove('open');
    closeTimer = setTimeout(function () { modal.hidden = true; }, reduce ? 0 : 420);
  }
  document.getElementById('search-btn').addEventListener('click', open);
  document.querySelectorAll('[data-open-search]').forEach(function (b) { b.addEventListener('click', open); });
  modal.querySelectorAll('[data-close]').forEach(function (b) { b.addEventListener('click', close); });
  input.addEventListener('input', function () { if (index) render(input.value); });
  document.addEventListener('keydown', function (e) {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); isOpen ? close() : open(); return; }
    if (e.key === '/' && !isOpen && !/input|textarea/i.test(document.activeElement.tagName)) { e.preventDefault(); open(); return; }
    if (!isOpen) return;
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
