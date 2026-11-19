/* The Australasian Beekeeper website - what every page shares.
   1. Who is reading: whether this browser belongs to a subscriber, and where they are (kept in
      this browser only, under one key; see ABK.get()).
   2. Data files (data/*.js) hand themselves in through ABK_DATA(), so the site works from a web
      server and also opened straight from a folder.
   3. In the reader: the way west. Left of the pages lies the Resources cell and, beyond it, the
      Subscribe cell: a band down the left edge with three arrows on it, a hexagon for each cell,
      and "pulling" the page that way (dragging it with the mouse, the left arrow, a sideways
      scroll, a swipe). West means Subscribe for a visitor - the comb glides across Resources to
      reach it - and Resources for a subscriber.
   Loaded after site/config.js. No dependencies. Every link is to an index.html by name, never to
   a bare folder, so nothing depends on a server choosing the index page. */
(function () {
  'use strict';
  var KEY = 'abk_sub_v1', cfg = window.ABK_CONFIG || {};
  var me = document.currentScript, ROOT = (me && me.src ? me.src : '').replace(/site\/abk\.js.*$/, '');

  /* #notsub (or #nosub) on a page's address (Kris, 15 Nov 2026): the page shows the site as someone who has not
     subscribed. The address is the only switch - nothing is stored, nothing to turn off: load a page without it and
     you are yourself again. While it is on, the record is a blank stand-in held in memory (so you can try the
     subscribe form), the site's own links carry the #notsub on with them, and your real record is never read or
     touched. */
  var PREV = /(^#|[#&\/])not?sub\b/.test(location.hash), mem = null;
  window.addEventListener('hashchange', function () { if (/(^#|[#&\/])not?sub\b/.test(location.hash) !== PREV) location.reload(); });
  function read() {
    if (PREV) return mem ? JSON.parse(JSON.stringify(mem)) : null;
    try { return JSON.parse(localStorage.getItem(KEY) || 'null') || null; } catch (e) { return null; }
  }
  function write(o) {
    if (PREV) mem = o ? JSON.parse(JSON.stringify(o)) : null;
    else { try { if (o) localStorage.setItem(KEY, JSON.stringify(o)); else localStorage.removeItem(KEY); } catch (e) {} }
    paint();
  }
  function flagged(u) { return PREV && ROOT && u && u.indexOf(ROOT) === 0 && u.indexOf('#') < 0 ? u + '#notsub' : u; }
  if (PREV) document.addEventListener('click', function (e) {     /* a link to another of the site's pages keeps the flag */
    var a = e.target && e.target.closest && e.target.closest('a[href]');
    if (a && !a.target) { var u = flagged(a.href); if (u !== a.href) a.href = u; }
  }, true);
  function paint() {
    var s = read(), h = document.documentElement;
    h.classList.toggle('abk-sub', !!(s && s.on));
    h.classList.toggle('abk-placed', !!(s && typeof s.lat === 'number'));
    try { window.dispatchEvent(new CustomEvent('abk:state')); } catch (e) {}
  }
  /* The record: { on: true, name, email, street, state, postcode, print: bool,
                   lat, lon, place: "postcode"|"device", ts }  - every field optional but "on". */
  var ABK = window.ABK = {
    root: ROOT, cfg: cfg, data: {}, get: read, set: write, paint: paint, preview: PREV, url: flagged,
    isSub: function () { var s = read(); return !!(s && s.on); },
    hasPlace: function () { var s = read(); return !!(s && typeof s.lat === 'number'); }
  };
  window.ABK_DATA = function (name, value) { ABK.data[name] = value; };

  /* a link from the monthly email carries ?sub=1: this browser is a subscriber's */
  (function () {
    var p = cfg.subscriberParam || 'sub', re = new RegExp('([?&])' + p + '=[^&#]*(&|$)');
    if (!re.test(location.search)) return;
    var s = read() || {};
    if (!s.on) { s.on = true; s.via = 'link'; s.ts = Date.now(); write(s); }
    try {
      var q = location.search.replace(re, function (m, a, b) { return b ? a : ''; });
      history.replaceState(history.state, '', location.pathname + q + location.hash);
    } catch (e) {}
  })();
  paint();
  window.addEventListener('storage', function (e) { if (e.key === KEY && !PREV) paint(); });

  /* ------------------------------------------------------------------ the reader */
  function readerHook() {
    var track = document.getElementById('track');
    if (!track) return;
    var HEX = '<svg viewBox="0 0 100 115.47" preserveAspectRatio="none" aria-hidden="true"><polygon points="50,1 99,29.4 99,86.1 50,114.5 1,86.1 1,29.4"/></svg>';
    var SUB = ROOT + 'subscribe/index.html', RES = ROOT + 'resources/index.html';
    var strip = document.createElement('div');
    strip.id = 'abkWest'; strip.className = 'abk-west';
    strip.innerHTML =
      '<span class="abk-band" aria-hidden="true"></span>' +
      '<span class="abk-hexes">' +
        '<a class="abk-hexb abk-h-sub" href="' + SUB + '" title="Subscribe – it’s free">' + HEX +
          '<span class="abk-hexl"><em>←</em><b>Subscribe!</b><small>Free · a monthly email when the new issue is out</small></span></a>' +
        '<a class="abk-hexb abk-h-res" href="' + RES + '" title="Resources: clubs, supplies, pollination">' + HEX +
          '<span class="abk-hexl"><em>←</em><b>Resources</b><small>Clubs · supplies · pollination</small></span></a>' +
      '</span>';
    document.body.appendChild(strip);
    function target() { return ABK.isSub() ? RES : SUB; }           /* what lies west: Subscribe, or Resources once subscribed */
    function label() { strip.title = ABK.isSub() ? 'Resources: clubs, supplies, pollination' : 'Subscribe – it’s free'; }

    /* the strip is the sky to the left of the pages; with no room there, the band and one hexagon in the corner */
    function first() {                                              /* what the sky is to the left of: a page, or a cover in Past issues */
      return document.querySelector('#lane0 .page .pframe') || document.querySelector('#lane0 .covpic') || document.querySelector('#lane0 .arc img');
    }
    function place() {
      var el = first();
      var left = el ? el.getBoundingClientRect().left : 0;
      var w = Math.floor(left) - 12, slim = w < 132 || innerWidth < 760;
      strip.classList.toggle('slim', slim);
      strip.style.width = slim ? '' : w + 'px';
      /* the hexagons shrink to fit a narrow strip, or a short window (two of them, one above the other) */
      var two = ABK.isSub() ? 182 : 374, tall = (strip.clientHeight - 28) / two;
      strip.style.setProperty('--hs', slim ? 1 : Math.max(0.5, Math.min(1, (w - 46) / 158, tall)).toFixed(3));
    }
    label(); place();
    window.addEventListener('abk:state', function () { label(); place(); });
    window.addEventListener('resize', place);
    window.addEventListener('load', place);
    /* where the pages sit changes with the issue (trim sizes differ), the zoom and the window, and the reader
       sizes its page frames a moment after it builds them: so watch the first frame itself, and pick up the
       new first frame whenever the reader builds another issue */
    try {
      var ro = new ResizeObserver(place), watched = null;
      var watch = function () {
        var el = first();
        if (el !== watched) { if (watched) ro.unobserve(watched); if (el) ro.observe(el); watched = el; }
        place();
      };
      ro.observe(document.getElementById('lane0'));
      new MutationObserver(function () { requestAnimationFrame(watch); }).observe(document.getElementById('sheet'), { childList: true });
      watch();
    } catch (e) { setInterval(place, 1200); }

    var leaving = false;
    function west(url) {
      if (leaving) return; leaving = true;
      try { sessionStorage.setItem('abk_arrive', 'from-reader'); } catch (e) {}
      track.style.removeProperty('--pull');
      document.documentElement.classList.remove('abk-pull');
      document.documentElement.classList.add('abk-leave-west');
      setTimeout(function () { location.href = flagged(url || target()); }, 250);
    }
    ABK.west = west;
    var pulled = false;                                              /* the end of a pull is not a click */
    strip.addEventListener('click', function (e) {
      if (pulled) { pulled = false; e.preventDefault(); return; }
      var a = e.target.closest && e.target.closest('a');
      if (a && (e.metaKey || e.ctrlKey || e.shiftKey || e.button)) return;
      e.preventDefault(); west(a ? a.href : target());
    });
    window.addEventListener('pageshow', function () {
      leaving = false; document.documentElement.classList.remove('abk-leave-west'); label(); place();
    });

    /* going west only from the issue itself, with nothing open over it and nothing more to scroll that way */
    function ready() {
      if (track.classList.contains('right') || document.body.classList.contains('inlane')) return false;
      if (document.querySelector('#lb.on,.iscrim.on,.bscrim.on')) return false;
      var lane = document.getElementById('lane0');
      return !lane || lane.scrollLeft <= 0;
    }
    var acc = 0, accT = 0;
    function onWheel(e) {
      if (Math.abs(e.deltaX) <= Math.abs(e.deltaY) * 1.5 || e.deltaX >= 0 || !ready()) return;
      var now = Date.now(); if (now - accT > 320) acc = 0; accT = now;
      acc += e.deltaX; if (acc < -150) { acc = 0; west(); }
    }
    /* pulling the page: press on anything that is not text or a control, drag to the right, and the issue comes
       with the mouse; let go far enough over and you are through to the west. Text keeps its ordinary selection. */
    var drag = null;
    function down(e) {
      if (e.button !== 0 || !ready()) return;
      var t = e.target;
      if (t.closest && t.closest('a,button,input,select,textarea,p,.rail,.chrome,.zoombar,.edge')) { if (!(t.closest('.abk-west'))) return; }
      drag = { x: e.screenX, y: e.screenY, on: false };
    }
    function move(e) {
      if (!drag) return;
      var dx = e.screenX - drag.x, dy = e.screenY - drag.y;
      if (!drag.on) {
        if (Math.abs(dy) > 16 || dx < -12) { drag = null; return; }
        if (dx < 12) return;
        drag.on = true; document.documentElement.classList.add('abk-pull');
      }
      track.style.setProperty('--pull', Math.max(0, dx * 0.6).toFixed(1) + 'px');
      e.preventDefault();
    }
    function up(e) {
      if (!drag) return;
      var d = drag; drag = null;
      if (!d.on) return;
      pulled = true; setTimeout(function () { pulled = false; }, 0);
      if (e.screenX - d.x > 130) west();
      else { document.documentElement.classList.remove('abk-pull'); track.style.removeProperty('--pull'); }
    }
    function swallow(e) { if (pulled) { e.preventDefault(); e.stopPropagation(); } }
    function hook(w) {
      try {
        w.addEventListener('wheel', onWheel, { passive: true });
        w.addEventListener('mousedown', down);
        w.addEventListener('mousemove', move);
        w.addEventListener('mouseup', up);
        w.addEventListener('click', swallow, true);
        var sx = null, sy = 0, st = 0;
        w.addEventListener('touchstart', function (e) {
          if (e.touches.length !== 1) { sx = null; return; }
          sx = e.touches[0].clientX; sy = e.touches[0].clientY; st = Date.now();
        }, { passive: true });
        w.addEventListener('touchend', function (e) {
          if (sx === null) return;
          var t = e.changedTouches[0], dx = t.clientX - sx, dy = t.clientY - sy; sx = null;
          if (dx > 96 && Math.abs(dy) < 56 && Date.now() - st < 650 && ready()) west();
        }, { passive: true });
      } catch (err) {}
    }
    hook(window);
    /* the pages are documents of their own (iframes): what starts on a page lands there */
    document.addEventListener('load', function (e) {
      var t = e.target; if (t && t.tagName === 'IFRAME') { try { hook(t.contentWindow); } catch (err) {} }
    }, true);
    Array.prototype.forEach.call(document.querySelectorAll('iframe'), function (f) {
      try { if (f.contentDocument && f.contentDocument.readyState === 'complete') hook(f.contentWindow); } catch (err) {}
    });

    /* arriving back from the comb: the issue slides in from that side */
    try {
      if (sessionStorage.getItem('abk_arrive') === 'from-comb') {
        sessionStorage.removeItem('abk_arrive');
        document.documentElement.classList.add('abk-enter');
        setTimeout(function () { document.documentElement.classList.remove('abk-enter'); }, 700);
      }
    } catch (e) {}
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', readerHook); else readerHook();
})();
