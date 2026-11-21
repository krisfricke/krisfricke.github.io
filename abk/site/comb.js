/* The Australasian Beekeeper website - the comb.
   Every page except the reader is a cell of one honeycomb (see CELLS), all cells the same size. The
   cell you are on is in the middle of the window, on paper; the cells around it show at the edges of
   the window in a paler yellow, each with its name as near the middle of it as the window allows, and
   are the ways on. Moving slides the whole comb until the cell you chose is in the middle (a cell two
   away is one movement, with the cell between going past) and changes the address (each cell has a
   real page of its own, so links, Back and a reload all work).
   On a phone the cells are shown one at a time and the map of the comb is a menu under the cell.
   Needs site/config.js and site/abk.js first. Data: data/clubs.js, stores.js, products.js,
   postcodes.js (plain data in a one-line wrapper, so the site also works opened straight from a
   folder, with no web server). */
(function () {
  'use strict';
  var ABK = window.ABK, cfg = ABK.cfg || {}, ROOT = ABK.root;

  /* The honeycomb. q across, r down (each row down is shifted half a cell to the right).
                              Varroa     Native bees
                        Clubs     INFORMATION
        About    SUBSCRIBE   WEBSITE HUB   THE MAGAZINE
            Honey sales   Supplies   Pollination   Advertise
     (Kris's plan, 21 Nov 2026.) The hub is directly left of the magazine and Subscribe directly left of the hub,
     so west of the magazine is always the same cell: a subscriber stops there, a visitor is carried across it
     to Subscribe. The hub says which way everything lies.
     THE COMB GOES ROUND. Left of About is the magazine again, and down-left of About is Advertise; up from
     Native bees are Pollination (up-left) and Advertise (up-right); and so on. It is four cells round from side
     to side, and four rows round from top to bottom (LAT). The two short rows leave four places empty: that way
     there is only sky. */
  var CELLS = [
    { id: 'reader',      q: 0,  r: 0,  path: 'index.html',             title: 'The magazine',        peek: 'The magazine' },
    { id: 'hub',         q: -1, r: 0,  path: 'hub/index.html',         title: 'Website hub',         peek: 'Website hub' },
    { id: 'subscribe',   q: -2, r: 0,  path: 'subscribe/index.html',   title: 'Subscribe',           peek: 'Subscribe' },
    { id: 'clubs',       q: -1, r: -1, path: 'clubs/index.html',       title: 'Beekeeping clubs',    peek: 'Clubs' },
    { id: 'info',        q: 0,  r: -1, path: 'information/index.html', title: 'Information resources', peek: 'Information' },
    { id: 'about',       q: -3, r: 0,  path: 'about/index.html',       title: 'About',               peek: 'About' },
    { id: 'honey',       q: -3, r: 1,  path: 'honey/index.html',       title: 'Honey sales',         peek: 'Honey sales' },
    { id: 'varroa',      q: 0,  r: -2, path: 'varroa/index.html',      title: 'Varroa',              peek: 'Varroa' },
    { id: 'native',      q: 1,  r: -2, path: 'native-bees/index.html', title: 'Native bees',         peek: 'Native bees' },
    { id: 'supplies',    q: -2, r: 1,  path: 'supplies/index.html',    title: 'Beekeeping supplies', peek: 'Supplies' },
    { id: 'pollination', q: -1, r: 1,  path: 'pollination/index.html', title: 'Pollination',         peek: 'Pollination' },
    { id: 'advertise',   q: 0,  r: 1,  path: 'advertise/index.html',   title: 'Advertising',         peek: 'Advertise' }
  ];
  var DIRS = { '1,0': 'e', '-1,0': 'w', '1,-1': 'ne', '0,-1': 'nw', '0,1': 'se', '-1,1': 'sw' };
  var ARROW = { e: '→', w: '←', ne: '↗', nw: '↖', se: '↘', sw: '↙' };
  var SIDE = 168, BAND = 70;          /* room kept beside, and above and below, the middle cell for its neighbours' names */
  var G = { w: 0, h: 0, dx: 0, dy: 0, gap: 16, planeW: 0, planeH: 0, compact: false, at: null, mv: 0.62 }, cur = null, browse = { clubs: null, stores: null };

  function $(s, r) { return (r || document).querySelector(s); }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function cell(id) { for (var i = 0; i < CELLS.length; i++) if (CELLS[i].id === id) return CELLS[i]; return null; }
  function node(id) { return document.getElementById('cell-' + id); }
  function peekName(c) { return c.id === 'subscribe' ? (ABK.isSub() ? 'My details' : 'Subscribe') : c.peek; }
  function titleOf(c) { return c.id === 'subscribe' ? (ABK.isSub() ? 'Your details' : 'Subscribe') : c.title; }
  /* Round the comb: a place and the same place 4 cells across, or 4 rows down and 2 back, are one place. */
  CELLS.forEach(function (k) { k.wq = k.q; k.wr = k.r; });       /* where each cell is drawn just now (wq, wr) */
  function dist(dq, dr) { return (Math.abs(dq) + Math.abs(dr) + Math.abs(dq + dr)) / 2; }
  function at(q, r) {                                     /* the cell at a place, the long way round included; null = sky */
    for (var i = 0; i < CELLS.length; i++) {
      var k = CELLS[i], j = (r - k.r) / 4;
      if (j === Math.round(j) && (q - k.q + 2 * j) % 4 === 0) return k;
    }
    return null;
  }
  function image(k, C) {                                  /* where cell k is drawn when the middle of the window is the place C: the nearest way round */
    var best = null, bd = 1e9;
    for (var j = -2; j <= 2; j++) for (var i = -2; i <= 2; i++) {
      var q = k.q + 4 * i - 2 * j, r = k.r + 4 * j;
      var d = dist(q - C.q, r - C.r) - (k.wq === q && k.wr === r ? 0.01 : 0);       /* as near either way: it stays where it is */
      if (d < bd) { bd = d; best = { q: q, r: r }; }
    }
    return best;
  }
  function neighbour(dir) {
    var c = cell(cur);
    for (var k in DIRS) if (DIRS[k] === dir) { var p = k.split(','), n = at(c.q + (+p[0]), c.r + (+p[1])); return n ? n.id : null; }
    return null;
  }

  /* ---------------------------------------------------------------- layout and movement */
  function layout() {
    var W = innerWidth, H = innerHeight, B = 58, g = G.gap, root = document.documentElement;
    G.compact = W < 900;
    root.classList.toggle('compact', G.compact);
    if (G.compact) {
      root.style.setProperty('--cap', Math.round(0.2887 * Math.min(W - 16, 540)) + 'px');
      CELLS.forEach(function (c) { var e = node(c.id); if (e) e.style.transform = ''; });
      paintFlower(); return;
    }
    /* every cell is four-fifths of the window's height (never too small to hold a form), and never so wide
       that there is no room either side of the middle one for its neighbours' names */
    var h = Math.max(690, Math.min((H - B) * 0.8, 800)), w = Math.round(h * 0.8660254);
    var maxW = W - 2 * (SIDE + g);
    if (w > maxW) { w = Math.round(Math.max(maxW, 560)); h = Math.round(w / 0.8660254); }
    G.w = w; G.h = h;
    G.dx = w + g; G.dy = 0.75 * h + 0.8660254 * g;            /* one cell across; one row down */
    G.planeH = Math.max(H - B, h + 2 * BAND);
    root.style.setProperty('--w', w + 'px'); root.style.setProperty('--h', h + 'px');
    root.style.setProperty('--planeH', Math.round(G.planeH) + 'px');
    /* what can be seen of the plane: its width (less a scrollbar, when the window is too short for a cell and
       the sky scrolls), and the height of the window below the bar */
    var pl = $('#plane');
    G.planeW = (pl && pl.clientWidth) || W; G.seenH = Math.min(G.planeH, H - B);
    place(false); labels(); paintFlower();
  }
  function put(k, C) {
    var e = node(k.id); if (!e) return;
    e.style.transform = 'translate(' + ((k.wq - C.q + (k.wr - C.r) / 2) * G.dx).toFixed(1) + 'px,' + ((k.wr - C.r) * G.dy).toFixed(1) + 'px)';
  }
  /* the comb, with the given cell (or the one you are on) in the middle of the window */
  function place(animate, centre) {
    if (G.compact) return;
    var c = cell(centre || cur), root = document.documentElement, was = G.c;
    var to = was ? image(c, was) : { q: c.q, r: c.r };          /* the cell's nearest self: perhaps round the edge of the comb */
    /* a longer way takes a little longer and is still one movement: the cells between go past */
    G.mv = animate ? 0.62 + 0.4 * Math.max(0, (was ? dist(to.q - was.q, to.r - was.r) : 1) - 1) : 0;
    root.style.setProperty('--mv', (G.mv || 0.62).toFixed(2) + 's');
    /* every cell takes the place nearest the new middle. One that has to come round from the other side does
       so first, in one jump, out beyond the edge of the window; then the whole comb slides. */
    var jump = [];
    CELLS.forEach(function (k) { var p = image(k, to); if (p.q !== k.wq || p.r !== k.wr) { k.wq = p.q; k.wr = p.r; jump.push(k); } });
    if (animate && was && jump.length) {
      root.classList.add('still'); jump.forEach(function (k) { put(k, was); }); void document.body.offsetWidth;
    }
    root.classList.toggle('still', !animate);
    CELLS.forEach(function (k) { put(k, to); });
    /* count from the comb's own numbering again: the same picture, with the middle cell at its own place */
    var sq = to.q - c.q, sr = to.r - c.r;
    CELLS.forEach(function (k) { k.wq -= sq; k.wr -= sr; });
    G.c = { q: c.q, r: c.r }; G.at = c.id;
  }
  /* A cell's name goes in the middle of its hexagon when the middle is in the window, and otherwise as near
     the middle as the window lets it be: the nearest spot to the centre where the whole name is inside both
     the hexagon and the window. It is tried smaller before it is given up; a cell with no room for its name
     shows none (it can still be clicked, and says what it is when pointed at). */
  function labels() {
    if (G.compact) return;
    /* "the window" is the part of the plane in view when the sky is centred on the middle cell (it only
       scrolls when the window is too short for a cell) */
    var c = G.c || cell(cur), PW = G.planeW, PH = G.planeH, M = 14, pad = 12, hw = G.w / 2, hh = G.h / 2, s = hh / G.w;
    var top = (PH - G.seenH) / 2, bot = (PH + G.seenH) / 2;
    CELLS.forEach(function (k) {
      var e = node(k.id), lab = e && $('.peek .lab', e); if (!lab || k.id === cur) return;
      var cx = PW / 2 + (k.wq - c.q + (k.wr - c.r) / 2) * G.dx, cy = PH / 2 + (k.wr - c.r) * G.dy, spot = null, small;
      for (small = 0; small < 2 && !spot; small++) {
        lab.classList.toggle('sm', !!small);
        var lw = lab.offsetWidth, lh = lab.offsetHeight;
        var ax = hw - lw / 2 - pad, ay = hh - lh / 2 - (lw / 2) * s - pad;       /* the hexagon, drawn in by the name's own size */
        var x0 = Math.max(-ax, M + lw / 2 - cx), x1 = Math.min(ax, PW - M - lw / 2 - cx);
        var y0 = Math.max(-ay, top + M + lh / 2 - cy), y1 = Math.min(ay, bot - M - lh / 2 - cy);
        if (ax <= 0 || ay <= 0 || x0 > x1 || y0 > y1) continue;
        var nx = Math.min(x1, Math.max(x0, 0)), ny = Math.min(y1, Math.max(y0, 0));
        if (Math.abs(ny) + Math.abs(nx) * s <= ay) { spot = [nx, ny]; continue; }   /* the nearest spot in the window is inside the hexagon */
        var bd = 1e18, sx = Math.max(3, (x1 - x0) / 80), sy = Math.max(3, (y1 - y0) / 80), x, y, d;
        for (x = x0; x <= x1 + 0.01; x += sx) for (y = y0; y <= y1 + 0.01; y += sy) {
          if (Math.abs(y) + Math.abs(x) * s > ay) continue;
          d = x * x + y * y; if (d < bd) { bd = d; spot = [x, y]; }
        }
      }
      lab.classList.toggle('off', !spot);
      if (spot) { lab.style.setProperty('--lx', spot[0].toFixed(1) + 'px'); lab.style.setProperty('--ly', spot[1].toFixed(1) + 'px'); }
    });
  }
  function centreSky() { var sky = $('#sky'); if (sky && !G.compact) sky.scrollTop = Math.max(0, (G.planeH - sky.clientHeight) / 2); }
  function arrowTo(c, k) {                                /* which way cell k lies (as it is drawn) from the middle c */
    var dq = k.wq - c.q, dr = k.wr - c.r, d = DIRS[dq + ',' + dr];
    if (d) return ARROW[d];
    var a = Math.atan2(dr * 0.8660254, dq + dr / 2) * 180 / Math.PI;
    return ['→', '↘', '↓', '↙', '←', '↖', '↑', '↗'][((Math.round(a / 45) % 8) + 8) % 8];
  }
  function mark() {
    var c = G.c || cell(cur);
    CELLS.forEach(function (k) {
      var e = node(k.id); if (!e) return;
      var d = k.id === cur ? '' : (DIRS[(k.wq - c.q) + ',' + (k.wr - c.r)] || 'far');
      e.classList.toggle('current', k.id === cur);
      e.setAttribute('data-dir', d);
      e.toggleAttribute('data-below', k.wr > c.r);         /* a cell below has its arrow under its name */
      var a = $('.peek .ar', e), p = $('.peek .pl', e), pk = $('.peek', e);
      if (a) a.textContent = k.id === cur ? '' : arrowTo(c, k);
      if (p) p.textContent = peekName(k);
      if (pk && k.id !== 'reader') pk.title = titleOf(k);
      if (pk) pk.tabIndex = k.id === cur ? -1 : 0;
    });
    document.title = titleOf(cell(cur)) + ' | The Australasian Beekeeper';
    paintFlower();
  }
  function go(id, o) {
    o = o || {};
    var c = cell(id); if (!c) return;
    if (id === 'reader') return toReader();
    if (id === cur && o.push !== false) return;                /* already here */
    var prev = cell(cur);
    cur = id;
    var e = node(id);
    if (prev && e) {                                  /* phones: the new cell comes in from the side it lies on */
      e.style.setProperty('--inx', (c.q + c.r / 2 > prev.q + prev.r / 2 ? 46 : c.q + c.r / 2 < prev.q + prev.r / 2 ? -46 : 0) + 'px');
      e.style.setProperty('--iny', (c.r > prev.r ? 34 : c.r < prev.r ? -34 : 0) + 'px');
    }
    place(o.animate !== false); mark(); labels(); centreSky();
    if (G.compact) window.scrollTo(0, 0);
    if (o.push !== false) { try { history.pushState({ cell: id }, '', ABK.url(ROOT + c.path)); } catch (err) {} }
    render(id);
    if (o.focus !== false) { var h = $('h1', e); if (h) { h.tabIndex = -1; try { h.focus({ preventScroll: true }); } catch (err) {} } }
  }
  function toReader() {                                   /* the magazine's cell comes to the middle, then the reader opens */
    try { sessionStorage.setItem('abk_arrive', 'from-comb'); } catch (e) {}
    var wait = 60;
    if (!G.compact) { document.documentElement.classList.add('to-reader'); place(true, 'reader'); wait = Math.round(G.mv * 740); }
    setTimeout(function () { location.href = ABK.url(ROOT + 'index.html'); }, wait);
  }
  function fromPath() {
    var p = location.pathname.replace(/index\.html$/, ''), best = 'subscribe';
    CELLS.forEach(function (c) { var d = c.path.replace(/index\.html$/, ''); if (d && p.slice(-d.length - 1) === '/' + d) best = c.id; });
    return best;
  }
  function paintFlower() {
    ['flower', 'flowerBig'].forEach(function (id) {
      var n = document.getElementById(id); if (!n) return;
      var big = id === 'flowerBig', g = big ? 5 : 2, lo = 1e9, hi = -1e9;
      CELLS.forEach(function (c) { lo = Math.min(lo, c.q + c.r / 2); hi = Math.max(hi, c.q + c.r / 2); });
      var across = hi - lo + 1;                               /* how many cells wide the comb is (3.5) */
      var s = big ? Math.min(104, Math.floor((Math.min(innerWidth, 540) - 32 - (across - 1) * g) / across)) : 13, hh = s * 1.1547;
      if (big) n.style.fontSize = Math.max(9.5, Math.min(12, s * 0.113)).toFixed(1) + 'px';
      var minX = 1e9, minY = 1e9, maxX = -1e9, maxY = -1e9, html = '';
      CELLS.forEach(function (c) { c.fx = (s + g) * (c.q + c.r / 2); c.fy = (0.75 * hh + g * 0.866) * c.r;
        minX = Math.min(minX, c.fx); minY = Math.min(minY, c.fy); maxX = Math.max(maxX, c.fx); maxY = Math.max(maxY, c.fy); });
      CELLS.forEach(function (c) {
        html += '<a class="fh' + (c.id === cur ? ' on' : '') + (c.id === 'reader' ? ' rd' : '') + '" href="' + ROOT + c.path + '" data-go="' + c.id + '" title="' + esc(peekName(c)) + '"' +
          (c.id === cur ? ' aria-current="page"' : '') + ' style="left:' + (c.fx - minX) + 'px;top:' + (c.fy - minY) + 'px;width:' + s + 'px;height:' + hh + 'px">' +
          (big ? esc(peekName(c)) : '<span class="vh">' + esc(peekName(c)) + '</span>') + '</a>';
      });
      n.style.width = (maxX - minX + s) + 'px'; n.style.height = (maxY - minY + hh) + 'px'; n.innerHTML = html;
    });
  }

  /* ---------------------------------------------------------------- place and distance */
  function postcodes() {
    if (!cfg.postcodeTable) return Promise.resolve(false);
    return load('postcodes').catch(function () { return false; });
  }
  /* A subscriber's address -> a point. With a street address (and config.js geocoder: "address", Kris
     15 Nov 2026: "pin point their location to the street address rather than the middle of the zip
     code") the street, postcode and state are looked up once on OpenStreetMap's Nominatim; the answer is
     used only if it lies in or near that postcode (within MAX_KM of the postcode's middle), so a street of
     the same name elsewhere is not taken. Otherwise, or with no street given, the postcode's middle from
     data/postcodes.js, which never leaves the browser. Returns {lat, lon, place: "address"|"postcode"}. */
  var MAX_KM = 40;
  function locate(d) {
    var pc = String(d.postcode || '').trim(), street = String(d.street || '').trim();
    if (!/^\d{4}$/.test(pc)) return Promise.reject(new Error('no postcode'));
    var base = 'https://nominatim.openstreetmap.org/search?format=jsonv2&countrycodes=au&limit=1&';
    function ask(q) { return fetch(base + q, { headers: { 'Accept': 'application/json' } }).then(function (r) { return r.json(); }); }
    return postcodes().then(function (tab) {
      var t = tab && tab[pc], mid = t ? { lat: t[0], lon: t[1], place: 'postcode' } : null;
      var byStreet = (cfg.geocoder === 'address' && street)
        ? ask('street=' + encodeURIComponent(street) + '&postalcode=' + pc + (d.state ? '&state=' + encodeURIComponent(d.state) : '')).then(function (a) {
            if (!a || !a[0]) return null;
            var p = { lat: +a[0].lat, lon: +a[0].lon, place: 'address' };
            return (!mid || km(p, mid) <= MAX_KM) ? p : null;
          }).catch(function () { return null; })
        : Promise.resolve(null);
      return byStreet.then(function (p) {
        if (p) return p;
        if (mid) return mid;
        if (cfg.geocoder === 'none') throw new Error('postcode not in the table');
        return ask('postalcode=' + pc).then(function (a) {
          if (a && a[0]) return { lat: +a[0].lat, lon: +a[0].lon, place: 'postcode' };
          throw new Error('postcode not found');
        });
      });
    });
  }
  function km(a, b) {
    var p = Math.PI / 180, x = Math.sin((b.lat - a.lat) * p / 2), y = Math.sin((b.lon - a.lon) * p / 2);
    return 2 * 6371 * Math.asin(Math.sqrt(x * x + Math.cos(a.lat * p) * Math.cos(b.lat * p) * y * y));
  }
  function kmText(k) { return (k < 10 ? Math.round(k * 10) / 10 : Math.round(k)) + ' km'; }
  function hasGeo(c) { return typeof c.lat === 'number' && typeof c.lon === 'number'; }
  function byName(a, b) { return a.name < b.name ? -1 : a.name > b.name ? 1 : 0; }

  /* ---------------------------------------------------------------- when a club next meets */
  var DOW = { sun: 0, mon: 1, tue: 2, wed: 3, thu: 4, fri: 5, sat: 6 };
  var DAY3 = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'], DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  var MON3 = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  var MONS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  function day(s) { var m = /^(\d{4})-(\d\d)-(\d\d)/.exec(s || ''); return m ? new Date(+m[1], +m[2] - 1, +m[3]) : null; }
  function nthOf(y, m, dow, n) {                          /* the n-th <weekday> of a month; n = -1 for the last */
    var d;
    if (n === -1) { d = new Date(y, m + 1, 0); d.setDate(d.getDate() - ((d.getDay() - dow + 7) % 7)); return d; }
    d = new Date(y, m, 1); d.setDate(1 + ((dow - d.getDay() + 7) % 7) + (n - 1) * 7);
    return d.getMonth() === m ? d : null;
  }
  function nextByRule(r, from) {
    var dow = DOW[r.dow], best = null, i, d;
    if (dow === undefined) return null;
    function ok(x) {
      var mo = x.getMonth() + 1;
      if (r.months && r.months.length && r.months.indexOf(mo) < 0) return false;
      if (r.except_months && r.except_months.indexOf(mo) >= 0) return false;
      return x >= from;
    }
    if (r.freq === 'monthly') {
      var nth = (r.nth && r.nth.length) ? r.nth : [1];
      for (i = 0; i < 15 && !best; i++) {
        var mm = from.getMonth() + i, y = from.getFullYear() + Math.floor(mm / 12), m = mm % 12;
        nth.map(function (n) { return nthOf(y, m, dow, n); }).filter(function (x) { return x && ok(x); })
          .sort(function (a, b) { return a - b; }).slice(0, 1).forEach(function (x) { best = x; });
      }
    } else if (r.freq === 'weekly' || r.freq === 'fortnightly') {
      var anchor = r.freq === 'fortnightly' ? day(r.anchor) : null;
      if (r.freq === 'fortnightly' && !anchor) return null;
      for (i = 0; i < 420 && !best; i++) {
        d = new Date(from.getFullYear(), from.getMonth(), from.getDate() + i);
        if (d.getDay() !== dow || !ok(d)) continue;
        if (anchor && Math.abs(Math.round((d - anchor) / 864e5)) % 14 !== 0) continue;
        best = d;
      }
    }
    return best;
  }
  function nextMeeting(c) {
    var today = new Date(); today.setHours(0, 0, 0, 0);
    var best = null;
    (c.meetings || []).forEach(function (r) {
      if (r.kind === 'committee') return;
      var d = nextByRule(r, today);
      if (d && (!best || d < best.date)) best = { date: d, time: r.time || null, rule: r };
    });
    (c.next_dates || []).forEach(function (s) {            /* dates the club itself has published win over the pattern */
      var d = day(s); if (!d || d < today) return;
      if (!best || d <= best.date) best = { date: d, time: best && +best.date === +d ? best.time : ((c.meetings || [])[0] || {}).time || null, rule: best && +best.date === +d ? best.rule : null, listed: true };
    });
    return best;
  }
  function clock(t) { var m = /^(\d\d?):(\d\d)/.exec(t || ''); if (!m) return ''; var h = +m[1]; return ((h + 11) % 12 + 1) + (m[2] === '00' ? '' : ':' + m[2]) + (h < 12 ? ' am' : ' pm'); }
  function longDate(d) { return DAYS[d.getDay()] + ' ' + d.getDate() + ' ' + MONS[d.getMonth()]; }

  /* ---------------------------------------------------------------- data */
  /* data/<name>.js is a script that hands its contents to ABK_DATA(): no fetch, so it also works from a folder */
  var DATA = {};
  function load(name) {
    if (!DATA[name]) DATA[name] = new Promise(function (ok, fail) {
      if (ABK.data[name]) return ok(ABK.data[name]);
      var s = document.createElement('script');
      s.src = ROOT + 'data/' + name + '.js';
      s.onload = function () { if (ABK.data[name]) ok(ABK.data[name]); else fail(new Error(name)); };
      s.onerror = function () { fail(new Error(name)); };
      document.head.appendChild(s);
    });
    return DATA[name];
  }
  function invite(what) {
    var sub = ABK.isSub(), s = ABK.get() || {};
    var lost = sub && s.lost ? '<p><b>We could not find postcode ' + esc(s.lost) + ' on the map.</b> Please check it in your details.</p>' : '';
    return '<div class="invite">' + lost + '<p>' + (sub
      ? 'Add your address to your subscription and this page will show your nearest ' + what + '.'
      : 'Subscribe (it’s free) with your address, and this page will show your nearest ' + what + '.') + '</p><p>' +
      '<a class="btn gold" href="' + ROOT + 'subscribe/index.html" data-go="subscribe">' + (sub ? (s.lost ? 'Check my details' : 'Add my address') : 'Subscribe') + '</a>' +
      (sub && navigator.geolocation ? ' &nbsp;<button type="button" class="lnk" data-geo="1">or use this device’s location</button>' : '') + '</p></div>';
  }
  function chips(items, sel, kind) {
    var out = '';
    ['VIC', 'NSW', 'QLD', 'SA', 'WA', 'TAS', 'ACT', 'NT'].forEach(function (st) {
      var n = items.filter(function (c) { return c.state === st; }).length;
      if (n) out += '<button type="button" data-kind="' + kind + '" data-state="' + st + '"' + (st === sel ? ' class="on"' : '') + '>' + st + ' · ' + n + '</button>';
    });
    return '<div class="chips">' + out + '</div>';
  }
  function whereText(s) { return esc(s.place === 'device' ? 'where you are' : s.place === 'address' && s.street ? s.street : ([s.postcode].filter(Boolean).join(' ') || 'you')); }
  function links(c) {
    var a = [];
    if (c.website) a.push('<a href="' + esc(c.website) + '" target="_blank" rel="noopener">Website</a>');
    if (c.facebook) a.push('<a href="' + esc(c.facebook) + '" target="_blank" rel="noopener">Facebook</a>');
    if (c.email) a.push('<a href="mailto:' + esc(c.email) + '">' + esc(c.email) + '</a>');
    if (c.phone) a.push(esc(c.phone));
    return a.length ? '<p class="links">' + a.join(' · ') + '</p>' : '';
  }

  /* An address as a link to Google Maps (Kris, 15 Nov 2026): a pin on the place, or, when the reader has given a
     street address (or let the site use this device's location), directions from there. Opens in a new tab. The
     reader's address goes to Google only when they click. */
  function mapLink(text, place, rec) {
    if (!text) return '';
    var dest = [rec.name, place].filter(Boolean).join(', ') + ', Australia', s = ABK.get() || {}, url;
    var from = s.place === 'device' && typeof s.lat === 'number' ? s.lat + ',' + s.lon
      : (s.street && s.postcode) ? [s.street, s.state, s.postcode, 'Australia'].filter(Boolean).join(' ') : '';
    url = from ? 'https://www.google.com/maps/dir/?api=1&origin=' + encodeURIComponent(from) + '&destination=' + encodeURIComponent(dest)
               : 'https://www.google.com/maps/search/?api=1&query=' + encodeURIComponent(dest);
    return '<a class="maplink" href="' + esc(url) + '" target="_blank" rel="noopener" title="' + (from ? 'Directions in Google Maps' : 'Show on Google Maps') + '">' + esc(text) + '</a>';
  }

  /* ---------------------------------------------------------------- clubs */
  function clubRow(c, dist, first) {
    var n = nextMeeting(c), badge, when;
    if (n) {
      badge = '<div class="hexdate"><i>' + DAY3[n.date.getDay()] + '</i><b>' + n.date.getDate() + '</b><span>' + MON3[n.date.getMonth()] + '</span></div>';
      var at = n.rule && n.rule.venue ? ' at ' + esc(n.rule.venue) : '', note = n.rule && n.rule.note ? ' <span class="fine">(' + esc(n.rule.note) + ')</span>' : '';
      when = '<p class="when">Next meeting: ' + longDate(n.date) + (n.time ? ', ' + clock(n.time) : '') + at + note + '</p>';
    } else {
      badge = '<div class="hexdate none"><b>?</b></div>';
      when = '<p class="when q">' + (c.meets_text ? esc(c.meets_text) : 'Meeting times are not published: ask the club.') + '</p>';
    }
    var where = [c.venue, c.address || [c.town, c.state].filter(Boolean).join(' ')].filter(Boolean).join(', ');
    var whereHtml = c.address ? mapLink(where, c.address, { name: c.venue || '' }) : esc(where);       /* a street address to go to: linked */
    return '<article class="row' + (first ? ' first' : '') + '">' + badge + '<div><h3>' + esc(c.name) + '</h3><p class="meta">' +
      (dist != null ? '<b>' + kmText(dist) + '</b> · ' : '') + whereHtml + '</p>' + when + links(c) + '</div></article>';
  }
  function renderClubs() {
    var box = $('#clubs-body');
    load('clubs').then(function (d) {
      var all = d.clubs || [], s = ABK.get() || {}, R = cfg.radiusKm || 50, html = '', placed = typeof s.lat === 'number';
      if (placed) {
        var near = all.filter(hasGeo).map(function (c) { return { c: c, km: km(s, c) }; }).sort(function (a, b) { return a.km - b.km; });
        var within = near.filter(function (x) { return x.km <= R; });
        if (within.length > 1) html += '<p class="lede"><b>' + within.length + ' clubs</b> within ' + R + ' km of ' + whereText(s) + ', nearest first.</p>';
        else if (within.length === 1) html += '<p class="lede">Your nearest club is ' + kmText(within[0].km) + ' from ' + whereText(s) + '.</p>';
        else if (near.length) html += '<p class="lede">No club on our list is within ' + R + ' km of ' + whereText(s) + '. The nearest:</p>';
        html += (within.length ? within : near.slice(0, 1)).map(function (x, i) { return clubRow(x.c, x.km, i === 0); }).join('');
        html += '<p class="fine">Dates are worked out from each club’s usual pattern. Check with the club before you travel.</p>';
      } else html += invite('club and when it next meets');
      html += '<h2>All clubs, by state</h2>' + chips(all, browse.clubs, 'clubs');
      if (browse.clubs) html += all.filter(function (c) { return c.state === browse.clubs; }).sort(byName)
        .map(function (c) { return clubRow(c, placed && hasGeo(c) ? km(s, c) : null, false); }).join('');
      html += '<p class="fine">' + all.length + ' clubs listed' + (d.updated ? ', checked ' + esc(d.updated) : '') + '. Missing or out of date? <a href="mailto:' +
        esc(cfg.emails.editor) + '?subject=Club%20listing">Tell the editor</a>.</p>';
      box.innerHTML = html;
    }).catch(function () { box.innerHTML = '<p class="warn">The club list could not be loaded.</p>'; });
  }

  /* ---------------------------------------------------------------- supplies */
  var KIND = { shop: 'Shop', pickup: 'Pick-up by arrangement', online: 'Online', manufacturer: 'Maker, sells direct' };
  function storeRow(st, dist) {
    var badge = dist != null ? '<div class="hexdate km"><b>' + (dist < 10 ? Math.round(dist * 10) / 10 : Math.round(dist)) + '</b><span>km</span></div>'
      : '<div class="hexdate none"><span>' + esc(st.state || '') + '</span></div>';
    var tags = (st.sells || []).map(function (t) { return '<span>' + esc(t) + '</span>'; }).join('');
    return '<article class="row">' + badge + '<div><h3>' + esc(st.name) + '</h3><p class="meta">' + esc(KIND[st.kind] || 'Supplier') +
      (st.address ? ' · ' + mapLink(st.address, st.address, st) : '') + (st.hours_text ? '<br>' + esc(st.hours_text) : '') + '</p>' +
      (tags ? '<div class="tags">' + tags + '</div>' : '') + links(st) + '</div></article>';
  }
  /* Price search, ready for when data/products.js has items:
     { "updated": "2026-12-01", "items": [ { "store": "<store id>", "name": "8-frame full-depth super, assembled",
       "category": "hives", "price": 49.5, "unit": "each", "url": "https://...", "seen": "2026-12-01" } ] }
     Every word typed must occur in the item's name or category; results are given cheapest first
     and, if the reader's place is known, nearest first. */
  function searchProducts(items, stores, q, s) {
    var words = q.toLowerCase().split(/\s+/).filter(Boolean), byId = {}, placed = typeof s.lat === 'number';
    stores.forEach(function (st) { byId[st.id] = st; });
    var hits = items.filter(function (it) { var t = (it.name + ' ' + (it.category || '')).toLowerCase(); return words.every(function (w) { return t.indexOf(w) >= 0; }); })
      .map(function (it) { var st = byId[it.store] || {}; return { it: it, st: st, km: placed && hasGeo(st) ? km(s, st) : null }; })
      .filter(function (h) { return h.st.id; });
    return { cheapest: hits.slice().sort(function (a, b) { return a.it.price - b.it.price; }).slice(0, 5),
             nearest: hits.filter(function (h) { return h.km != null; }).sort(function (a, b) { return a.km - b.km || a.it.price - b.it.price; }).slice(0, 5) };
  }
  function productRows(list) {
    return list.map(function (h) {
      return '<article class="row"><div class="hexdate km"><i>$</i><b>' + (Math.round(h.it.price) === h.it.price ? h.it.price : h.it.price.toFixed(2)) + '</b><span>' + esc(h.it.unit || '') + '</span></div><div><h3>' +
        esc(h.it.name) + '</h3><p class="meta">' + esc(h.st.name) + (h.km != null ? ' · ' + kmText(h.km) : '') + (h.it.seen ? ' · price seen ' + esc(h.it.seen) : '') + '</p>' +
        (h.it.url ? '<p class="links"><a href="' + esc(h.it.url) + '" target="_blank" rel="noopener">See it at the store</a></p>' : '') + '</div></article>';
    }).join('');
  }
  function renderSupplies() {
    var box = $('#supplies-body');
    Promise.all([load('stores'), load('products').catch(function () { return { items: [] }; })]).then(function (r) {
      var all = r[0].stores || [], items = r[1].items || [], s = ABK.get() || {}, placed = typeof s.lat === 'number', html = '';
      if (items.length) html += '<div class="search"><input id="psearch" type="search" placeholder="Find an item: smoker, 8-frame super, foundation…" aria-label="Find an item"></div><div id="presults"></div>';
      if (placed) {
        var near = all.filter(function (st) { return hasGeo(st) && st.kind !== 'online'; }).map(function (st) { return { st: st, km: km(s, st) }; })
          .sort(function (a, b) { return a.km - b.km; }).slice(0, cfg.storeCount || 5);
        html += '<p class="lede">The nearest suppliers to ' + whereText(s) + '.</p>' + near.map(function (x) { return storeRow(x.st, x.km); }).join('');
        var online = all.filter(function (st) { return st.kind === 'online' || st.ships === true; });
        if (online.length) html += '<h2>Order from anywhere</h2><p>' + online.sort(byName).map(function (st) {
          return st.website ? '<a href="' + esc(st.website) + '" target="_blank" rel="noopener">' + esc(st.name) + '</a>' : esc(st.name); }).join(' · ') + '</p>';
      } else html += invite('supplier');
      html += '<h2>All suppliers, by state</h2>' + chips(all, browse.stores, 'stores');
      if (browse.stores) html += all.filter(function (st) { return st.state === browse.stores; }).sort(byName)
        .map(function (st) { return storeRow(st, placed && hasGeo(st) ? km(s, st) : null); }).join('');
      html += '<p class="fine">' + all.length + ' suppliers listed' + (r[0].updated ? ', checked ' + esc(r[0].updated) : '') + '. Missing or out of date? <a href="mailto:' +
        esc(cfg.emails.editor) + '?subject=Supplier%20listing">Tell the editor</a>.</p>';
      box.innerHTML = html;
      var inp = $('#psearch');
      if (inp) inp.addEventListener('input', function () {
        var q = inp.value.trim(), out = $('#presults');
        if (q.length < 2) { out.innerHTML = ''; return; }
        var res = searchProducts(items, all, q, s);
        out.innerHTML = res.cheapest.length ? '<h2>Cheapest</h2>' + productRows(res.cheapest) + (res.nearest.length ? '<h2>Nearest</h2>' + productRows(res.nearest) : '')
          : '<p class="fine">Nothing on our price list matches that yet.</p>';
      });
    }).catch(function () { box.innerHTML = '<p class="warn">The supplier list could not be loaded.</p>'; });
  }

  /* ---------------------------------------------------------------- advertising */
  function money(p) { return p == null ? 'on request' : '$' + (Math.round(p) === p ? p : p.toFixed(2)); }
  function renderAds() {
    var a = cfg.advertising || {}, box = $('#ads-body');
    function table(title, rows) {
      return '<table class="rates"><thead><tr><th>' + title + '</th><th>Size (wide × high)</th><th>Price</th></tr></thead><tbody>' +
        (rows || []).map(function (r) { return '<tr><td>' + esc(r.name) + '</td><td>' + esc(r.size || '–') + '</td><td>' + money(r.price) + '</td></tr>'; }).join('') + '</tbody></table>';
    }
    box.innerHTML = '<p class="lede">To book, or to ask about anything not listed here, email <a href="mailto:' + esc(cfg.emails.advertising) + '">' + esc(cfg.emails.advertising) + '</a>.</p>' +
      table('Display', a.display) + table('Marketplace', a.classifieds) +
      '<p class="fine">' + (a.page || []).map(function (p) { return esc(p[0]) + ' ' + esc(p[1]); }).join(' · ') + '. ' + esc(a.artwork || '') + '</p>';
    var m = $('#ads-mail'); if (m) m.href = 'mailto:' + cfg.emails.advertising + '?subject=Advertising%20in%20The%20Australasian%20Beekeeper';
  }

  /* ---------------------------------------------------------------- Subscribe, and the Website hub */
  function field(n) { return $('#subform [name=' + n + ']'); }
  function status(t, bad) { var e = $('#hub-status'); e.textContent = t || ''; e.classList.toggle('err', !!bad); }
  /* the Subscribe cell: the form. For a subscriber it is "Your details", filled in, and saves changes. */
  function renderSubscribe() {
    var s = ABK.get() || {}, sub = !!s.on, form = $('#subform');
    $('#hub-kick').textContent = sub ? 'Your subscription' : 'Free · monthly';
    $('#hub-h1').textContent = titleOf(cell('subscribe'));
    $('#hub-go span').textContent = sub ? 'Save' : 'Subscribe';
    $('#hub-lede').textContent = sub ? 'Change anything here and press Save. Your address is what finds your nearest club and supplier.'
      : 'Free to read, always. Subscribe and we’ll email you once a month, when the new issue is out.';
    $('#hub-already').hidden = sub; $('#hub-forget').hidden = !sub;
    if (sub && !form.getAttribute('data-filled')) {
      ['name', 'email', 'street', 'state', 'postcode'].forEach(function (n) { if (s[n]) field(n).value = s[n]; });
      field('print').checked = !!s.print; form.setAttribute('data-filled', '1');
    }
    if (!sub) form.removeAttribute('data-filled');
  }
  /* the Website hub: open to everyone. West is Subscribe for a visitor and "My details" for a subscriber. */
  function renderHub() {
    var s = ABK.get() || {}, sub = !!s.on;
    $('#wh-kick').textContent = sub ? (s.name ? 'Welcome, ' + s.name.split(' ')[0] : 'You’re subscribed') : 'The Australasian Beekeeper';
    $('#wh-sub').textContent = sub ? 'My details' : 'Subscribe';
    $('#wh-subnote').textContent = sub ? 'Change your details' : 'Free: one email a month';
    $('#wh-preview').hidden = !sub || !!(cfg.subscribe && cfg.subscribe.endpoint) || !s.preview;
  }
  /* Sending. With no endpoint set (site/config.js) nothing is sent: preview mode. */
  function send(d, update) {
    var sc = cfg.subscribe || {}, F = sc.fields || {}, pairs = [], k;
    if (!sc.endpoint) return Promise.resolve({ preview: true });
    function add(key, v) { if (F[key]) pairs.push([F[key], v]); }
    add('name', d.name); add('email', d.email); add('street', d.street); add('state', d.state);
    add('postcode', d.postcode); add('print', d.print ? 'yes' : 'no'); if (update) add('update', 'yes');
    for (k in (sc.extra || {})) pairs.push([k, sc.extra[k]]);
    if (sc.method === 'fetch') {
      var fd = new FormData(); pairs.forEach(function (p) { fd.append(p[0], p[1]); });
      return fetch(sc.endpoint, { method: 'POST', body: fd, headers: { 'Accept': 'application/json' } }).then(function (r) {
        if (!r.ok) throw new Error('The subscription service did not accept that (' + r.status + '). Please try again.');
        return {};
      });
    }
    return new Promise(function (ok, fail) {
      var fr = document.createElement('iframe'); fr.name = 'abk_post_' + Date.now(); fr.style.display = 'none'; fr.setAttribute('aria-hidden', 'true');
      document.body.appendChild(fr);
      var f = document.createElement('form'); f.method = 'POST'; f.action = sc.endpoint; f.target = fr.name; f.style.display = 'none';
      pairs.forEach(function (p) { var i = document.createElement('input'); i.type = 'hidden'; i.name = p[0]; i.value = p[1]; f.appendChild(i); });
      document.body.appendChild(f);
      var done = false, t = setTimeout(function () { if (!done) { done = true; fail(new Error('No answer from the subscription service. Please try again.')); } }, 15000);
      fr.addEventListener('load', function () {
        var blank = false; try { blank = fr.contentWindow.location.href === 'about:blank'; } catch (e) {}
        if (blank || done) return;
        done = true; clearTimeout(t); ok({}); setTimeout(function () { fr.remove(); f.remove(); }, 600);
      });
      f.submit();
    });
  }
  function bindHub() {
    var form = $('#subform'), btn = $('#hub-go');
    btn.addEventListener('click', function () {
      if (form.requestSubmit) form.requestSubmit(); else form.dispatchEvent(new Event('submit', { cancelable: true }));
    });
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var d = { name: field('name').value.trim(), email: field('email').value.trim(), street: field('street').value.trim(),
                state: field('state').value, postcode: field('postcode').value.trim(), print: field('print').checked }, bad = [];
      if (d.name.length < 2) bad.push('name');
      if (!/^[^@\s]+@[^@\s]+\.[^@\s]{2,}$/.test(d.email)) bad.push('email');
      if (d.postcode && !/^\d{4}$/.test(d.postcode)) bad.push('postcode');
      ['name', 'email', 'postcode'].forEach(function (n) { field(n).classList.toggle('bad', bad.indexOf(n) >= 0); });
      if (bad.length) { status(bad[0] === 'postcode' ? 'A postcode is four digits.' : 'Please give your ' + bad.filter(function (b) { return b !== 'postcode'; }).join(' and ') + '.', true); field(bad[0]).focus(); return; }
      if (field('website').value) { status(''); return; }                 /* a robot filled the hidden field */
      var was = ABK.isSub(); status('Sending…'); btn.disabled = true;
      send(d, was).then(function (r) {
        var s = ABK.get() || {}, moved = s.postcode !== d.postcode || (s.street || '') !== d.street;
        s.on = true; s.ts = Date.now(); delete s.suburb;                   /* (asked for by the first version of the form) */
        ['name', 'email', 'street', 'state', 'postcode', 'print'].forEach(function (n) { s[n] = d[n]; });
        if (r && r.preview) s.preview = true; else delete s.preview;
        delete s.lost;
        if (moved && (d.postcode || s.place !== 'device')) { delete s.lat; delete s.lon; delete s.place; }
        status(''); ABK.set(s);
        if (d.postcode && typeof s.lat !== 'number') locate(d).then(function (p) {
          var t = ABK.get() || s; t.lat = p.lat; t.lon = p.lon; t.place = p.place || 'postcode'; delete t.lost; ABK.set(t);
        }).catch(function () { var t = ABK.get() || s; t.lost = d.postcode; ABK.set(t); });      /* not a postcode we know */
        if (cur === 'subscribe') go('hub');                           /* subscribed: on to what it opens */
      }).catch(function (err) { status((err && err.message) || 'That did not go through. Please try again.', true); })
        .then(function () { btn.disabled = false; });
    });
    $('#hub-already').addEventListener('click', function () {
      var s = ABK.get() || {}; s.on = true; s.via = 'self'; s.ts = Date.now(); ABK.set(s); go('hub');
    });
    $('#hub-forget').addEventListener('click', function () { form.reset(); form.removeAttribute('data-filled'); status(''); ABK.set(null); });
  }

  /* ---------------------------------------------------------------- Honey sales (Kris, 21 Nov 2026) */
  /* Places where beekeepers sell their own honey, within cfg.honey.radiusKm (50) of the visitor. The visitor need not
     be a subscriber: where they are comes from their subscription's address if they have one, else from this
     device (the browser asks them) or a postcode they type, kept for this visit only. "List your honey" opens a
     form for a beekeeper: it subscribes them if they are not yet, and sends the listing to the editor (to
     cfg.honey.endpoint if one is set, otherwise as an e-mail their own program sends). Listings are added by
     hand to data/honey.js. */
  var HERE = null; try { HERE = JSON.parse(sessionStorage.getItem('abk_here') || 'null'); } catch (e) {}
  function honeyRow(h, d) {
    var bits = [];
    if (h.hours) bits.push(esc(h.hours));
    if (h.phone) bits.push('<a href="tel:' + esc(String(h.phone).replace(/[^0-9+]/g, '')) + '">' + esc(h.phone) + '</a>');
    return '<article class="row"><div class="hexdate km"><b>' + (d < 10 ? Math.round(d * 10) / 10 : Math.round(d)) + '</b><span>km</span></div><div>' +
      '<h3>' + esc(h.name) + '</h3>' +
      (h.address ? '<p class="meta">' + mapLink(h.address, h.address, { name: h.name }) + '</p>' : '') +
      (bits.length ? '<p class="when q">' + bits.join(' · ') + '</p>' : '') +
      ((h.honey || []).length ? '<div class="tags">' + h.honey.map(function (x) { return '<span>' + esc(x) + '</span>'; }).join('') + '</div>' : '') +
      '</div></article>';
  }
  function renderHoney() {
    var el = $('#honey-body'); if (!el) return;
    load('honey').catch(function () { return { sellers: [] }; }).then(function (H) {
      var s = ABK.get() || {}, here = typeof s.lat === 'number' ? s : HERE, R = (cfg.honey && cfg.honey.radiusKm) || 50;
      var html = '<p class="lede">Honey straight from the beekeeper: farm gates, stalls and shops where beekeepers sell their own honey.</p>';
      if (!here) {
        html += '<p class="find"><button type="button" class="btn gold" data-honey="geo">Use my location</button><span>or</span>' +
          '<input id="honey-pc" inputmode="numeric" maxlength="4" placeholder="Postcode" aria-label="Your postcode">' +
          '<button type="button" class="btn" data-honey="pc">Find</button></p><p class="status" id="honey-status" role="status"></p>' +
          '<p class="fine">Your location is used only to work out what is within ' + R + '&nbsp;km of you. It stays in this browser.</p>';
      } else {
        var near = ((H && H.sellers) || []).filter(function (h) { return typeof h.lat === 'number'; })
          .map(function (h) { return { h: h, d: km(here, h) }; }).filter(function (x) { return x.d <= R; }).sort(function (a, b) { return a.d - b.d; });
        html += '<h2>Within ' + R + ' km of ' + (here === HERE ? esc(HERE.label || 'you') : whereText(s)) + '</h2>';
        html += near.length ? near.map(function (x) { return honeyRow(x.h, x.d); }).join('')
          : '<p>No honey sellers are listed within ' + R + '&nbsp;km yet.</p>';
        if (here === HERE) html += '<p class="fine"><button type="button" class="lnk" data-honey="reset">Somewhere else</button></p>';
      }
      html += '<p class="fine">Do you sell your own honey? Press <b>List your honey</b> below to add your farm gate.</p>';
      el.innerHTML = html;
    });
  }
  function honeyHere(p, label) { HERE = { lat: p.lat, lon: p.lon, label: label }; try { sessionStorage.setItem('abk_here', JSON.stringify(HERE)); } catch (e) {} renderHoney(); }
  function bindHoney() {
    var dlg = $('#honey-dlg'), form = $('#honeyform'); if (!dlg || !form) return;
    function note(t, bad) { var e = $('#honey-note'); e.textContent = t || ''; e.classList.toggle('err', !!bad); }
    document.addEventListener('click', function (e) {
      var t = e.target.closest && e.target.closest('[data-honey]'); if (!t) return;
      var what = t.getAttribute('data-honey'), st = $('#honey-status');
      if (what === 'geo') {
        if (!navigator.geolocation) { st.textContent = 'This browser cannot give its location. Try your postcode.'; return; }
        st.textContent = 'Finding you…';
        navigator.geolocation.getCurrentPosition(function (p) { honeyHere({ lat: p.coords.latitude, lon: p.coords.longitude }, 'where you are'); },
          function () { st.textContent = 'This device would not give its location. Try your postcode.'; }, { maximumAge: 6e5, timeout: 12000 });
      } else if (what === 'pc') {
        var pc = ($('#honey-pc').value || '').trim();
        if (!/^\d{4}$/.test(pc)) { st.textContent = 'A postcode has four figures.'; return; }
        st.textContent = 'Finding ' + pc + '…';
        locate({ postcode: pc }).then(function (p) { honeyHere(p, pc); }).catch(function () { st.textContent = 'That postcode was not found.'; });
      } else if (what === 'reset') { HERE = null; try { sessionStorage.removeItem('abk_here'); } catch (e2) {} renderHoney(); }
      else if (what === 'open') {
        var sub = ABK.isSub();
        $('#honey-sub').hidden = sub; $('#honey-sub').querySelectorAll('input').forEach(function (i) { i.required = !sub; });
        note(''); if (dlg.showModal) dlg.showModal(); else dlg.setAttribute('open', '');
      } else if (what === 'close') { if (dlg.close) dlg.close(); else dlg.removeAttribute('open'); }
    });
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var f = function (n) { return (form.elements[n] && form.elements[n].value || '').trim(); }, sub = ABK.isSub(), s = ABK.get() || {};
      if (form.elements.website && form.elements.website.value) return;                       /* a robot filled the hidden field */
      if (!sub && (!f('name') || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(f('email')))) { note('Please give your name and a working email address.', true); return; }
      if (!f('place') || !f('address') || !/^\d{4}$/.test(f('postcode'))) { note('Please give the name of the place, its address and its postcode.', true); return; }
      var who = { name: sub ? (s.name || '') : f('name'), email: sub ? (s.email || '') : f('email') };
      var L = { place: f('place'), address: f('address'), state: f('state'), postcode: f('postcode'), phone: f('phone'), hours: f('hours'), honey: f('honey') };
      var btn = $('#honey-send'); btn.disabled = true; note('Sending…');
      /* (A) subscribe, if they have not already */
      var step = sub ? Promise.resolve() : send({ name: who.name, email: who.email, street: '', state: L.state, postcode: L.postcode, print: false }, false).then(function (r) {
        var t = ABK.get() || {}; t.on = true; t.ts = Date.now(); t.name = who.name; t.email = who.email; t.state = L.state; t.postcode = L.postcode;
        if (r && r.preview) t.preview = true; ABK.set(t);
      });
      /* (B) the listing, to the editor */
      step.then(function () {
        var hc = cfg.honey || {};
        if (hc.endpoint) {
          var pairs = []; Object.keys(L).forEach(function (k) { pairs.push(encodeURIComponent('honey_' + k) + '=' + encodeURIComponent(L[k])); });
          pairs.push('name=' + encodeURIComponent(who.name), 'email=' + encodeURIComponent(who.email));
          return fetch(hc.endpoint, { method: 'POST', mode: 'no-cors', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: pairs.join('&') })
            .then(function () { return 'Thank you. Your listing has gone to the editor and will appear here once it has been added.'; });
        }
        var body = ['Honey sales listing for The Australasian Beekeeper website', '', 'Place: ' + L.place, 'Address: ' + L.address + ', ' + [L.state, L.postcode].filter(Boolean).join(' '),
          'Phone: ' + L.phone, 'Hours: ' + L.hours, 'Honey sold: ' + L.honey, '', 'From: ' + who.name + ' <' + who.email + '>'].join('\n');
        location.href = 'mailto:' + ((cfg.emails && cfg.emails.editor) || '') + '?subject=' + encodeURIComponent('Honey sales listing: ' + L.place) + '&body=' + encodeURIComponent(body);
        return 'Your email program should now be open with the listing ready to send to the editor. It will appear here once it has been added.';
      }).then(function (msg) { note(msg); form.reset(); })
        .catch(function (err) { note((err && err.message) || 'That did not go through. Please try again.', true); })
        .then(function () { btn.disabled = false; });
    });
  }
  /* Native bees: an event that has passed is taken off the list */
  function renderNative() {
    var today = new Date(); today.setHours(0, 0, 0, 0); var left = 0;
    document.querySelectorAll('#native-events li[data-date]').forEach(function (li) {
      var gone = new Date(li.getAttribute('data-date') + 'T23:59:59') < today; li.hidden = gone; if (!gone) left++;
    });
    var none = $('#native-none'); if (none) none.hidden = left > 0;
  }

  function render(id) {
    if (id === 'subscribe') renderSubscribe();
    else if (id === 'hub') renderHub();
    else if (id === 'clubs') renderClubs();
    else if (id === 'supplies') renderSupplies();
    else if (id === 'advertise') renderAds();
    else if (id === 'honey') renderHoney();
    else if (id === 'native') renderNative();
  }

  /* ---------------------------------------------------------------- getting about */
  var dragged = false;
  document.addEventListener('click', function (e) {
    if (dragged) { dragged = false; e.preventDefault(); e.stopPropagation(); return; }     /* the end of a pull is not a click */
    var t = e.target, a = t.closest && t.closest('[data-go]');
    if (a) {
      if (e.metaKey || e.ctrlKey || e.shiftKey || e.button) return;
      e.preventDefault(); go(a.getAttribute('data-go')); return;
    }
    var c = t.closest && t.closest('.chips button');
    if (c) { var k = c.getAttribute('data-kind'), st = c.getAttribute('data-state'); browse[k] = browse[k] === st ? null : st; render(cur); return; }
    if (t.getAttribute && t.getAttribute('data-geo')) {
      t.textContent = 'Finding you…';
      navigator.geolocation.getCurrentPosition(function (p) {
        var s = ABK.get() || {}; s.lat = p.coords.latitude; s.lon = p.coords.longitude; s.place = 'device'; delete s.lost; ABK.set(s);
      }, function () { t.textContent = 'This device would not give its location'; }, { maximumAge: 6e5, timeout: 12000 });
    }
  }, true);
  window.addEventListener('keydown', function (e) {
    if (/INPUT|TEXTAREA|SELECT/.test((e.target && e.target.tagName) || '') || e.altKey || e.metaKey || e.ctrlKey) return;
    var to = null;
    if (e.key === 'ArrowRight') to = neighbour('e') || neighbour('ne') || neighbour('se');
    else if (e.key === 'ArrowLeft') to = neighbour('w') || neighbour('sw') || neighbour('nw');
    else if (e.key === 'ArrowUp') to = e.shiftKey ? (neighbour('ne') || neighbour('nw')) : (neighbour('nw') || neighbour('ne'));
    else if (e.key === 'ArrowDown') to = e.shiftKey ? (neighbour('se') || neighbour('sw')) : (neighbour('sw') || neighbour('se'));
    if (to) { e.preventDefault(); go(to); }
  });
  /* which cell the point (in the window) is on, by the hexagons themselves; null in the sky between them */
  function under(x, y) {
    var pl = $('#plane'); if (!pl || G.compact) return null;
    var r = pl.getBoundingClientRect(), c = G.c || cell(cur), ox = r.left + r.width / 2, oy = r.top + G.planeH / 2, s = G.h / (2 * G.w), hit = null;
    CELLS.forEach(function (k) {
      var dx = Math.abs(x - ox - (k.wq - c.q + (k.wr - c.r) / 2) * G.dx), dy = Math.abs(y - oy - (k.wr - c.r) * G.dy);
      if (dx <= G.w / 2 && dy + dx * s <= G.h / 2) hit = k;
    });
    return hit;
  }
  /* The wheel. Sideways (or a swipe) pans east or west. Up or down goes to a cell in the row above or below:
     the one the pointer is on if it lies that way (Advertise, in the corner), otherwise the nearer of the two
     that touch this cell - the left one with the pointer left of the middle, the right one with it right.
     Anything under the pointer that can itself scroll that way (a long list, the sky in a short window) scrolls
     first, and the turn of the wheel that scrolled it never also moves the page: the move waits for a fresh
     turn, begun after the wheel has been still for a moment (busy: when something last scrolled). */
  (function () {
    var acc = 0, at = 0, lock = 0, accY = 0, atY = 0, busy = 0;
    document.addEventListener('scroll', function () { busy = Date.now(); }, true);
    function scrollsOn(el, dir) {
      for (; el && el.nodeType === 1 && el !== document.documentElement; el = el.parentElement) {
        if (el.scrollHeight <= el.clientHeight + 1) continue;
        var oy = getComputedStyle(el).overflowY;
        if ((oy === 'auto' || oy === 'scroll') && (dir < 0 ? el.scrollTop > 0 : el.scrollTop < el.scrollHeight - el.clientHeight - 1)) return true;
      }
      return false;
    }
    window.addEventListener('wheel', function (e) {
      if (G.compact || e.ctrlKey) return;
      var now = Date.now();
      if (Math.abs(e.deltaX) > Math.abs(e.deltaY) * 1.5) {
        if (now < lock) return; if (now - at > 320) acc = 0; at = now; acc += e.deltaX;
        if (Math.abs(acc) > 150) { var ew = acc > 0 ? (neighbour('e') || neighbour('ne') || neighbour('se')) : (neighbour('w') || neighbour('sw') || neighbour('nw')); acc = 0; lock = now + 800; if (ew) go(ew); }
        return;
      }
      if (Math.abs(e.deltaY) <= Math.abs(e.deltaX) * 1.5 || now < lock) return;
      var dir = e.deltaY < 0 ? -1 : 1;
      if (scrollsOn(e.target, dir) || now - busy < 700) { busy = now; accY = 0; return; }
      if (now - atY > 320 || (accY < 0) !== (dir < 0)) accY = 0;
      atY = now; accY += e.deltaY * (e.deltaMode === 1 ? 33 : e.deltaMode === 2 ? 400 : 1);     /* lines or pages, as pixels */
      if (Math.abs(accY) < 60) return;                        /* one notch of a wheel is enough; a touchpad gathers to it */
      accY = 0;
      var c = cell(cur), on = under(e.clientX, e.clientY), to = null;
      if (on && on.id !== cur && (on.wr - c.r) * dir > 0) to = on.id;
      else {
        var pl = $('#plane').getBoundingClientRect(), west = e.clientX < pl.left + pl.width / 2;
        to = dir < 0 ? (neighbour(west ? 'nw' : 'ne') || neighbour(west ? 'ne' : 'nw')) : (neighbour(west ? 'sw' : 'se') || neighbour(west ? 'se' : 'sw'));
      }
      if (to) { go(to); lock = Date.now() + Math.round(G.mv * 1000) + 350; }      /* not again until this move is over */
    }, { passive: true });
    var sx = null, sy = 0, st = 0;
    window.addEventListener('touchstart', function (e) { if (e.touches.length !== 1) { sx = null; return; } sx = e.touches[0].clientX; sy = e.touches[0].clientY; st = Date.now(); }, { passive: true });
    window.addEventListener('touchend', function (e) {
      if (sx === null) return;
      var t = e.changedTouches[0], dx = t.clientX - sx, dy = t.clientY - sy; sx = null;
      if (Math.abs(dx) < 90 || Math.abs(dy) > 60 || Date.now() - st > 650) return;
      var to = dx > 0 ? (neighbour('w') || neighbour('sw') || neighbour('nw')) : (neighbour('e') || neighbour('ne') || neighbour('se')); if (to) go(to);
    }, { passive: true });
  })();
  (function () {                 /* pull the comb with the mouse: let go and it settles on the cell you pulled into view */
    var on = false, moved = false, sx = 0, sy = 0;
    var SIX = [['e', 0], ['se', 60], ['sw', 120], ['w', 180], ['w', -180], ['nw', -120], ['ne', -60]];
    window.addEventListener('mousedown', function (e) {
      if (e.button !== 0 || G.compact) return;
      var t = e.target; if (t.closest && t.closest('input,select,textarea,button,label,.body,.bar,.hexbtn')) return;
      on = true; moved = false; sx = e.clientX; sy = e.clientY;
    });
    window.addEventListener('mousemove', function (e) {
      if (!on) return;
      var dx = e.clientX - sx, dy = e.clientY - sy;
      if (!moved && dx * dx + dy * dy < 64) return;
      moved = true; document.documentElement.classList.add('dragging');
      $('#comb').style.transform = 'translate(' + (dx * 0.55).toFixed(1) + 'px,' + (dy * 0.55).toFixed(1) + 'px)';
      e.preventDefault();
    });
    window.addEventListener('mouseup', function (e) {
      if (!on) return; on = false;
      if (!moved) return;
      var dx = e.clientX - sx, dy = e.clientY - sy;
      document.documentElement.classList.remove('dragging'); $('#comb').style.transform = '';
      dragged = true; setTimeout(function () { dragged = false; }, 0);
      if (dx * dx + dy * dy < 8100) return;
      var ang = Math.atan2(-dy, -dx) * 180 / Math.PI, best = null, bd = 999;        /* the way is opposite the pull */
      SIX.forEach(function (d) { var x = Math.abs(ang - d[1]); if (x < bd) { bd = x; best = d[0]; } });
      var to = neighbour(best); if (to) go(to);
    });
  })();
  window.addEventListener('popstate', function (e) { go((e.state && e.state.cell) || fromPath(), { push: false, focus: false }); });
  window.addEventListener('pageshow', function (e) { if (e.persisted) { document.documentElement.classList.remove('to-reader'); place(false); mark(); labels(); } });
  window.addEventListener('abk:state', function () { if (cur) { mark(); labels(); render(cur); } });
  var rz; window.addEventListener('resize', function () { clearTimeout(rz); rz = setTimeout(function () { layout(); centreSky(); }, 80); });

  /* ---------------------------------------------------------------- start */
  function start() {
    cur = document.body.getAttribute('data-start') || fromPath();
    if (!cell(cur) || cur === 'reader') cur = 'subscribe';
    var arrive = null; try { arrive = sessionStorage.getItem('abk_arrive'); sessionStorage.removeItem('abk_arrive'); } catch (e) {}
    bindHub(); bindHoney(); layout(); mark(); labels(); render(cur); centreSky();
    try { history.replaceState({ cell: cur }, ''); } catch (e) {}
    /* Come in from the magazine: the comb starts with the magazine's cell in the middle and slides east to
       west until this cell is. The hub is one cell over; Subscribe is two, so the hub goes past on the way. */
    if (arrive === 'from-reader' && !G.compact) {
      place(false, 'reader');
      void document.body.offsetWidth;                         /* the starting position is taken in before the move begins */
      var begun = false, begin = function () { if (!begun) { begun = true; place(true); } };
      requestAnimationFrame(function () { requestAnimationFrame(begin); });
      setTimeout(begin, 160);                                 /* in case no frame comes (a tab opened in the background) */
    }
    document.documentElement.classList.add('ready');
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
