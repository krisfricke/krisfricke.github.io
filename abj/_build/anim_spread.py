#!/usr/bin/env python3
"""Pages that move: September's flowers sway in a breeze and its bees buzz when hovered.

Pages 4-5 (the spread), 8 (bee, top right), 29 (flowers, top right), 44 (back-cover bee, always buzzing).

Used by build_issue.py. For a page listed in ANIM:
  paintout(bp, spec)      before the background is rendered - the moving paths are painted
                          over in the sky blue so the raster carries no copy of them
  overlay(drs, spec, ...) the same paths as SVG, grouped as plants (stem, leaves, head)
                          and bees, with the CSS that moves them, inserted right after the
                          background image so the page's live text still sits on top.

The spread's body text is outlined in the PDF, so it lives in the raster; the one run that
prints across the orange petals is redrawn above the flower ('over'). Wings are still: a
strobe the eye cannot see is only CPU. The animation pauses while the page is off-screen
and stops entirely under prefers-reduced-motion. Motion numbers are in MOTION / DELAY.
"""
import re
import pymupdf

BLUE = (0x66 / 255, 0x9f / 255, 0xd5 / 255)
WING_FORE, WING_HIND, BODY = {'#ffe98f'}, {'#fec553', '#fac408'}, '#000000'

# ---- what moves, by drawing index on each page (checked against get_drawings() rects) ----
P4 = {
  'plants': [
    dict(name='pale', stem=[50], leaves=[(51, (78, 714)), (52, (78, 753))],
         head=list(range(53, 67)), nod=(78, 664), base=(76, 802)),
    dict(name='gold', stem=[69], leaves=[(70, (195, 691)), (78, (195, 742))],
         head=[67, 68, 71, 72, 73, 74, 75, 76, 77, 79, 80, 81, 82, 83], nod=(195, 630), base=(195, 802)),
  ],
  'bees': [dict(name='bee-small', ids=[116, 117, 118])],
  'drift': [dict(name='petals', ids=list(range(2, 11)))],
  'over': [], 'bg': 'paint', 'shard': True,
  'forage': [dict(cx=80, cy=653, rx=48, ry=48), dict(cx=190, cy=612, rx=58, ry=58)],   # dormant while the shard is on
}
P5 = {
  'plants': [
    dict(name='orange', stem=[9], leaves=[(10, (386, 600))],
         head=[2, 3, 5, 6, 7, 8, 11, 4], nod=(386, 428), base=(386, 802)),
  ],
  'bees': [dict(name='bee-left', ids=list(range(12, 18))), dict(name='bee-right', ids=[18, 19, 20]),
           dict(name='bee-top', ids=list(range(62, 68)))],
  'drift': [],
  'over': [42, 43, 44, 45],          # "Development of practical long-term floral..." prints over the petals
  'bg': 'paint', 'shard': True,
  'forage': [dict(cx=386, cy=380, rx=75, ry=75)],
}
P8 = {  # President's Report: the bee at the top right
  'plants': [], 'drift': [], 'over': [], 'bg': 'cut',
  'bees': [dict(name='bee-p8', ids=[2, 3, 4, 5, 6, 7])],
}
P29 = {  # Bee Bits: a pale flower on a stem and a gold burst cropped by the page's top edge
  'plants': [
    dict(name='pale29', stem=[22], leaves=[(23, (536, 100)), (24, (536, 125))],
         head=list(range(25, 39)), nod=(536.6, 64.6), base=(536.6, 158.7)),
    dict(name='burst29', stem=[], leaves=[], head=list(range(1, 15)), nod=(459, 0), base=(459, 0)),
  ],
  'bees': [], 'drift': [], 'over': [], 'bg': 'cut',
  'forage': [dict(cx=540, cy=55, rx=46, ry=44), dict(cx=459, cy=22, rx=72, ry=46)],
}
P44 = {  # back cover: the bee by the headline, wings going the whole time
  'plants': [], 'drift': [], 'over': [], 'bg': 'cut',
  'bees': [dict(name='bee-back', ids=[511, 512, 513, 514, 515, 516], always=True)],
}

# ---- the motion: one breeze from the left. Periods divide LOOP so a rendered clip loops cleanly.
LOOP = 14.8
P19 = {  # Almond pollination: nothing lifted; the bee cursor forages on the blossom's anthers
  'plants': [], 'bees': [], 'drift': [], 'over': [], 'bg': 'cut',
  'forage': [dict(cx=402, cy=612, rx=52, ry=50)],    # the anther cluster, page points
}
def _zones(*zs):   # a page with nothing lifted, only zones for the bee
    return {'plants': [], 'bees': [], 'drift': [], 'over': [], 'bg': 'cut', 'forage': list(zs)}
P10 = _zones(dict(cx=225, cy=625, rx=46, ry=40), dict(cx=185, cy=690, rx=72, ry=36))          # Bendigo ad: wattle
P21 = _zones(dict(cx=455, cy=185, rx=56, ry=52))                                                  # AgriFutures plan cover: wattle
P30 = _zones(dict(cx=388, cy=565, rx=46, ry=32), dict(cx=515, cy=552, rx=48, ry=48))              # Whirrakee ad: wattle
P18 = _zones(dict(cx=430, cy=150, rx=82, ry=112, mode='unload'))                                  # Swanpool ad: honeycomb
P36 = _zones(dict(cx=108, cy=500, rx=72, ry=72, mode='unload'), dict(cx=490, cy=720, rx=72, ry=52, mode='unload'))  # Steritech: the small hexagons
P38 = _zones(dict(cx=500, cy=730, rx=56, ry=72, mode='unload'))                                   # BeePlas: foundation
ANIM = {('sep', 4): P4, ('sep', 5): P5, ('sep', 8): P8, ('sep', 10): P10, ('sep', 18): P18, ('sep', 19): P19, ('sep', 21): P21,
        ('sep', 29): P29, ('sep', 30): P30, ('sep', 36): P36, ('sep', 38): P38, ('sep', 44): P44}

MOTION = {
  # class: (period s, from deg, to deg)   - rotation about the group's origin, ease-in-out, alternate
  'plant':  (LOOP / 2, -1.4, 1.6),
  'head':   (LOOP / 3, -2.2, 2.6),
  'leaf':   (LOOP / 5, -2.8, 3.2),
  'bee':    (LOOP / 6,  0.0, 0.0),      # bees bob rather than turn: see BOB
  'drift':  (LOOP / 4, -0.8, 0.8),
  'fore':   (0.10, -13.0, 7.0),        # two poses, held --wing each, no in-between
  'hind':   (0.10,  -7.0, 13.0),
}
STEP = {'fore', 'hind'}                 # jump between the two values rather than easing
WINGS_HOVER = True                      # beat only while the pointer is on the bee (bees with always=True ignore this)
HIT_PAD = 6                             # pt of slack around a bee's rectangle for the hover
BOB = (0.0, -1.6, 0.8, 1.4)             # bee translate: from (x,y) to (x,y) in pt
DELAY = {  # seconds, negative = already under way; staggered left-to-right across the spread
  'pale': 0.0, 'pale .head': -1.1, 'gold': -0.9, 'gold .head': -2.6, 'orange': -2.2, 'orange .head': -0.4,
  'pale .leaf:nth-of-type(2)': -1.3, 'gold .leaf:nth-of-type(2)': -0.7,
  'bee-small': -0.3, 'bee-left': -0.8, 'bee-right': -1.5, 'bee-top': -0.2, 'petals': -1.9,
  'bee-p8': -0.6, 'bee-back': -1.1, 'pale29': -1.4, 'pale29 .head': -0.7, 'burst29': -0.3, 'burst29 .head': -2.0,
  'pale29 .leaf:nth-of-type(2)': -1.0,
  'bee-left .fore': -0.05, 'bee-left .hind': -0.05, 'bee-right .fore': -0.12, 'bee-right .hind': -0.12,
  'bee-top .fore': -0.03, 'bee-top .hind': -0.03,
}

def hexc(c):
    return '#%02x%02x%02x' % tuple(int(round(v * 255)) for v in c)

def path_d(items):
    d, cur = [], None
    def mv(p):
        nonlocal cur
        if cur is None or abs(cur.x - p.x) > 1e-3 or abs(cur.y - p.y) > 1e-3:
            d.append('M%.2f %.2f' % (p.x, p.y))
        cur = p
    for it in items:
        op = it[0]
        if op == 'l':
            mv(it[1]); d.append('L%.2f %.2f' % (it[2].x, it[2].y)); cur = it[2]
        elif op == 'c':
            mv(it[1]); d.append('C%.2f %.2f %.2f %.2f %.2f %.2f' % (it[2].x, it[2].y, it[3].x, it[3].y, it[4].x, it[4].y)); cur = it[4]
        elif op == 're':
            r = it[1]; d.append('M%.2f %.2fH%.2fV%.2fH%.2fZ' % (r.x0, r.y0, r.x1, r.y1, r.x0)); cur = None
        elif op == 'qu':
            q = it[1]; d.append('M%.2f %.2fL%.2f %.2fL%.2f %.2fL%.2f %.2fZ' % (q.ul.x, q.ul.y, q.ur.x, q.ur.y, q.lr.x, q.lr.y, q.ll.x, q.ll.y)); cur = None
    return ''.join(d)

def svg_path(dr):
    a = ['d="%s"' % path_d(dr['items'])]
    if dr.get('closePath'): a[0] = a[0][:-1] + 'Z"'
    f = dr.get('fill'); s = dr.get('color')
    a.append('fill="%s"' % (hexc(f) if f else 'none'))
    if dr.get('even_odd'): a.append('fill-rule="evenodd"')
    if s and dr.get('width'):
        a.append('stroke="%s" stroke-width="%.2f"' % (hexc(s), dr['width']))
        cap = dr.get('lineCap'); join = dr.get('lineJoin')
        if cap is not None:
            c = int(cap[0]) if isinstance(cap, (list, tuple)) else int(cap)
            a.append('stroke-linecap="%s"' % ('butt', 'round', 'square')[max(0, min(2, c))])
        if join is not None: a.append('stroke-linejoin="%s"' % ('miter', 'round', 'bevel')[max(0, min(2, int(join)))])
    fo = dr.get('fill_opacity'); so = dr.get('stroke_opacity')
    if fo is not None and fo < 1: a.append('fill-opacity="%.3f"' % fo)
    if so is not None and so < 1: a.append('stroke-opacity="%.3f"' % so)
    return '<path %s/>' % ' '.join(a)

def points_of(dr):
    pts = []
    for it in dr['items']:
        if it[0] == 'l': pts += [it[1], it[2]]
        elif it[0] == 'c': pts += [it[1], it[4]]
        elif it[0] == 're': r = it[1]; pts += [r.tl, r.tr, r.br, r.bl]
        elif it[0] == 'qu': q = it[1]; pts += [q.ul, q.ur, q.lr, q.ll]
    return pts

def G(cls, ox, oy, inner, key=None):
    """an animated group. The origin is written as CSS (for the page) and as data (for the frame
    renderer), with the motion class and the delay the CSS gives this selector."""
    anim = 'bee' if cls.startswith('bee') else cls.split()[0]
    delay = DELAY.get(key or cls.split()[-1], 0.0)
    return ('<g class="%s" data-anim="%s" data-delay="%.2f" data-ox="%.1f" data-oy="%.1f" style="transform-origin:%.1fpx %.1fpx">%s</g>'
            % (cls, anim, delay, ox, oy, ox, oy, inner))

def bee_svg(drs, b):
    """body and head parts still; each wing in its own group rooted at its corner nearest the body;
    an invisible rectangle over the whole bee (plus HIT_PAD) is what the hover responds to"""
    body = [i for i in b['ids'] if drs[i].get('fill') and hexc(drs[i]['fill']) == BODY]
    br = pymupdf.Rect()
    for i in body: br |= drs[i]['rect']
    bc = pymupdf.Point((br.x0 + br.x1) / 2, (br.y0 + br.y1) / 2)
    parts, wings = [], []
    for i in b['ids']:
        col = hexc(drs[i]['fill']) if drs[i].get('fill') else ''
        if col in WING_FORE or col in WING_HIND:
            root = min(points_of(drs[i]), key=lambda p: (p.x - bc.x) ** 2 + (p.y - bc.y) ** 2)
            wings.append(('hind' if col in WING_HIND else 'fore', root, i))
        else:
            parts.append(svg_path(drs[i]))
    whole = pymupdf.Rect()
    for i in b['ids']: whole |= drs[i]['rect']
    inner = '<rect class="hit" x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="none" pointer-events="all"/>' % (
        whole.x0 - HIT_PAD, whole.y0 - HIT_PAD, whole.width + 2 * HIT_PAD, whole.height + 2 * HIT_PAD)
    inner += ''.join(parts)
    for w, root, i in sorted(wings, key=lambda w: 0 if w[0] == 'hind' else 1):   # hind under fore, as drawn
        inner += G(w, root.x, root.y, svg_path(drs[i]), key='%s .%s' % (b['name'], w))
    cls = 'bee ' + b['name'] + (' always' if b.get('always') else '')
    return G(cls, (whole.x0 + whole.x1) / 2, (whole.y0 + whole.y1) / 2, inner, key=b['name'])

def moving_ids(spec):
    ids = set()
    for pl in spec['plants']:
        ids.update(pl['stem']); ids.update(i for i, _ in pl['leaves']); ids.update(pl['head'])
    for b in spec['bees'] + spec['drift']: ids.update(b['ids'])
    return ids

def _blocks(c):
    """every q...Q span (byte offsets) of a content stream, at any depth"""
    out=[]; stack=[]
    for m in re.finditer(rb'(?<![\w.\-])(q|Q)(?![\w.])', c):
        if m.group(1) == b'q': stack.append(m.start())
        elif stack: out.append((stack.pop(), m.end()))
    return out

_CM = re.compile(rb'^q\s+1 0 0 1 (-?[\d.]+) (-?[\d.]+) cm\b')

def cut_drawings(bp, ids):
    """Remove the given get_drawings() entries from the page's own content stream. Each exported
    shape is its own `q 1 0 0 1 X Y cm <path> f Q`, X,Y being its first point in PDF space; the
    innermost block starting with that translation is cut. Returns the ids it could not match."""
    bp.clean_contents()
    xref = bp.get_contents()[0]; c = bp.read_contents()
    H = bp.rect.height; drs = bp.get_drawings()
    blocks = []
    for (s0, e0) in _blocks(c):
        m = _CM.match(c[s0:e0])
        if m: blocks.append((s0, e0, float(m.group(1)), float(m.group(2))))
    cut, missing = [], []
    for i in ids:
        it = drs[i]['items'][0]; pt = it[1] if it[0] != 're' else it[1].tl
        wx, wy = pt.x, H - pt.y
        cands = [b for b in blocks if abs(b[2] - wx) < 0.06 and abs(b[3] - wy) < 0.06 and b[:2] not in [k[:2] for k in cut]]
        if not cands: missing.append(i); continue
        cut.append(min(cands, key=lambda b: b[1] - b[0]))
    for s0, e0, _, _ in sorted(cut, key=lambda b: -b[0]):
        c = c[:s0] + c[e0:]
    bp.parent.update_stream(xref, c)
    return missing

def paintout(bp, spec):
    """Take the moving paths out of the background copy of the page, before its raster is made.
    Returns the untouched page's drawings (the overlay is built from these, by index)."""
    drs = bp.get_drawings()
    ids = sorted(moving_ids(spec))
    if spec.get('bg') == 'cut':
        missing = cut_drawings(bp, ids)
        if missing: raise RuntimeError('anim: could not cut drawings %s from the page stream' % missing)
        return drs
    # 'paint': cover each path in the sky blue, a touch fat to swallow its anti-aliased edge,
    # then put the white margin back where a stem or petal met the panel's edge
    W = bp.rect.width
    sh = bp.new_shape()
    for i in ids:
        dr = drs[i]
        for it in dr['items']:
            if it[0] == 'l': sh.draw_line(it[1], it[2])
            elif it[0] == 'c': sh.draw_bezier(it[1], it[2], it[3], it[4])
            elif it[0] == 're': sh.draw_rect(it[1])
            elif it[0] == 'qu': sh.draw_quad(it[1])
        sh.finish(fill=BLUE if dr.get('fill') is not None else None, color=BLUE, width=(dr.get('width') or 0) + 1.4,
                  closePath=bool(dr.get('closePath')), even_odd=bool(dr.get('even_odd')), lineJoin=1, lineCap=1)
    sh.commit()
    panel = next(d['rect'] for d in drs if d.get('fill') and hexc(d['fill']) == '#669fd5' and d['rect'].width > 400)
    wh = bp.new_shape()
    wh.draw_rect(pymupdf.Rect(0, panel.y1 + 0.3, W, 815.4))
    if panel.x0 > 10: wh.draw_rect(pymupdf.Rect(0, 560, panel.x0 - 0.3, panel.y1 + 0.3))
    if panel.x1 < W - 10: wh.draw_rect(pymupdf.Rect(panel.x1 + 0.3, 400, W, panel.y1 + 0.3))
    wh.finish(fill=(1, 1, 1), color=None); wh.commit()
    return drs

def css_motion():
    out = []
    for cls, (T, a, b) in MOTION.items():
        if cls == 'bee':
            out.append('@keyframes bob{from{transform:translate(%.1fpx,%.1fpx)}to{transform:translate(%.1fpx,%.1fpx)}}' % BOB)
            out.append('.anim .bee{animation:bob %.3fs ease-in-out infinite alternate}' % T)
        elif cls in STEP:
            # two poses, hard cut, NOT alternate (with steps(1,end) an alternating animation shows
            # only its start value). At rest the animation is absent, so the wing is the artwork.
            out.append('@keyframes k-%s{0%%,49.99%%{transform:rotate(%.1fdeg)}50%%,100%%{transform:rotate(%.1fdeg)}}' % (cls, a, b))
            sel = '.anim .bee.always .%s,.anim .bee:hover .%s,.anim .bee.buzz .%s' % (cls, cls, cls) if WINGS_HOVER else '.anim .%s' % cls
            out.append('%s{animation:k-%s %.3fs steps(1,end) infinite}' % (sel, cls, 2 * T))
        else:
            out.append('@keyframes k-%s{from{transform:rotate(%.1fdeg)}to{transform:rotate(%.1fdeg)}}' % (cls, a, b))
            out.append('.anim .%s{animation:k-%s %.3fs ease-in-out infinite alternate}' % (cls, cls, T))
    for sel, d in DELAY.items():
        out.append('.anim .%s{animation-delay:%.2fs}' % (sel, d))
    return '\n'.join(out)

def overlay(drs, spec, W, H, pw, ph):
    """the moving art as SVG, sized to the page's pixel box, plus its CSS and the pause-when-hidden script"""
    g = []
    for pl in spec['plants']:
        inner = ''.join(svg_path(drs[i]) for i in pl['stem'])
        for k, (i, at) in enumerate(pl['leaves']):
            inner += G('leaf', at[0], at[1], svg_path(drs[i]), key='%s .leaf:nth-of-type(%d)' % (pl['name'], k + 1))
        inner += G('head', pl['nod'][0], pl['nod'][1], ''.join(svg_path(drs[i]) for i in pl['head']), key='%s .head' % pl['name'])
        g.append(G('plant ' + pl['name'], pl['base'][0], pl['base'][1], inner, key=pl['name']))
    for b in spec['drift']:
        r = pymupdf.Rect()
        for i in b['ids']: r |= drs[i]['rect']
        g.append(G('drift ' + b['name'], (r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2, ''.join(svg_path(drs[i]) for i in b['ids']), key=b['name']))
    for b in spec['bees']: g.append(bee_svg(drs, b))
    if spec['over']: g.append('<g class="over">' + ''.join(svg_path(drs[i]) for i in spec['over']) + '</g>')
    style = ('<style>\n.anim{position:absolute;left:0;top:0;width:%dpx;height:%dpx;pointer-events:none}\n'
             '.anim g{transform-box:view-box}\n'
             '.anim .bee{pointer-events:visiblePainted;cursor:inherit}.anim .bee .hit{pointer-events:all}\n%s\n'
             '.anim.still g{animation-play-state:paused}\n'
             '@media (prefers-reduced-motion:reduce){.anim g{animation:none}}\n</style>\n') % (pw, ph, css_motion())
    svg = '<svg class="anim" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %.2f %.2f" aria-hidden="true">%s</svg>\n' % (W, H, ''.join(g))
    script = ('<script>/* no work while the spread is off-screen */(function(){var s=document.querySelector("svg.anim");'
              'if(!s||!("IntersectionObserver" in window))return;new IntersectionObserver(function(e){'
              's.classList.toggle("still",!e[0].isIntersecting)},{threshold:0}).observe(s);'
              '/* no hover on touch: a tap buzzes the bee for a moment */'
              's.querySelectorAll(".bee").forEach(function(b){b.addEventListener("pointerdown",function(e){if(e.pointerType==="mouse")return;'
              'b.classList.add("buzz");clearTimeout(b._t);b._t=setTimeout(function(){b.classList.remove("buzz");},1800);});});})();</script>\n')
    out = (style + svg + script) if g else ''
    if spec.get('forage'): out += forage_zone(spec['forage'], W, pw)
    return out + (shard_cursor() if SHARD_CURSOR and spec.get('shard') else '')

def forage_zone(zones, W, pw):
    """Invisible ellipses over flowers (the bee gathers pollen) or comb (mode 'unload': she empties
    her baskets), in page pixels so they follow the zoom. The page tests the pointer against them and
    tells the reader ({abj:'forage', on, mode}). pointer-events stay off, so anything beneath - a
    photo's enlarge hotspot, an advertiser's link - still works."""
    k = pw / W
    divs = ''.join('<div class="anthers" data-mode="%s" aria-hidden="true" style="position:absolute;left:%.1fpx;top:%.1fpx;width:%.1fpx;height:%.1fpx;border-radius:50%%;pointer-events:none"></div>\n'
                   % (z.get('mode', 'gather'), (z['cx'] - z['rx']) * k, (z['cy'] - z['ry']) * k, 2 * z['rx'] * k, 2 * z['ry'] * k) for z in zones)
    return divs + ('<script>/* pollen: tell the reader when the pointer is on a flower or on comb */(function(){'
            'var zs=[].slice.call(document.querySelectorAll(".anthers"));if(!zs.length||window.parent===window)return;var cur=null;'
            'function say(m){cur=m;try{parent.postMessage({abj:"forage",on:!!m,mode:m||undefined},"*");}catch(e){}}'
            'document.addEventListener("mousemove",function(e){var hit=null;for(var i=0;i<zs.length&&!hit;i++){var r=zs[i].getBoundingClientRect(),'
            'dx=(e.clientX-r.left-r.width/2)/(r.width/2),dy=(e.clientY-r.top-r.height/2)/(r.height/2);if(dx*dx+dy*dy<=1)hit=zs[i].getAttribute("data-mode");}'
            'if(hit!==cur)say(hit);},{passive:true});'
            'document.addEventListener("mouseleave",function(){if(cur)say(null);});})();</script>\n')

# ---- Barry's suggestion, on this spread only: the brand shard as the pointer instead of the bee.
# Delete SHARD_CURSOR (or set it False) to go back to the bee here. assets/shard.png and
# shard@2x.png are the shard from p.10 of the brand guidelines (its own vector: 34.8/105/40.2
# degrees, level top edge) in PMS 7549 #f9c500, no outline; the hotspot is the sting. The page hides the reader's bee while the
# pointer is over it, and stops reporting the pointer so the bee is not pulled back.
SHARD_CURSOR = True
SHARD_HOT = (34, 24)

def shard_cursor():
    x, y = SHARD_HOT
    return ('<style>/* shard pointer, this spread only */\n'
            'html.shard,html.shard *,html.bee-on.shard,html.bee-on.shard *{cursor:url("../../assets/shard.png") %d %d,auto !important;'
            'cursor:image-set(url("../../assets/shard.png") 1x,url("../../assets/shard@2x.png") 2x) %d %d,auto !important}\n'
            'html.shard a[href],html.shard a[href] *,html.bee-on.shard a[href],html.bee-on.shard a[href] *{cursor:url("../../assets/shard.png") %d %d,pointer !important;'
            'cursor:image-set(url("../../assets/shard.png") 1x,url("../../assets/shard@2x.png") 2x) %d %d,pointer !important}\n'
            '</style>\n'
            '<script>(function(){if(!matchMedia("(hover:hover) and (pointer:fine)").matches)return;'
            'var h=document.documentElement;h.classList.add("shard");'
            '/* the page owns the pointer here: the reader\'s bee is parked and not fed positions */'
            'window.addEventListener("mousemove",function(e){e.stopImmediatePropagation();},{capture:true,passive:true});'
            'document.addEventListener("mouseenter",function(){try{parent.postMessage({abj:"pointerleave"},"*");}catch(e){}});'
            '})();</script>\n') % (x, y, x, y, x, y, x, y)
