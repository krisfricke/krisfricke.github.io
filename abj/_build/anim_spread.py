#!/usr/bin/env python3
"""Pages that move: the September pp. 4-5 spread, whose flowers sway in a breeze.

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
import pymupdf

BLUE = (0x66 / 255, 0x9f / 255, 0xd5 / 255)
WING_FORE, WING_HIND, BODY = '#ffe98f', '#fec553', '#000000'

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
  'over': [],
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
}

# ---- the motion: one breeze from the left. Periods divide LOOP so a rendered clip loops cleanly.
LOOP = 14.8
MOTION = {
  # class: (period s, from deg, to deg)   - rotation about the group's origin, ease-in-out, alternate
  'plant':  (LOOP / 2, -1.4, 1.6),
  'head':   (LOOP / 3, -2.2, 2.6),
  'leaf':   (LOOP / 5, -2.8, 3.2),
  'bee':    (LOOP / 6,  0.0, 0.0),      # bees bob rather than turn: see BOB
  'drift':  (LOOP / 4, -0.8, 0.8),
}
BOB = (0.0, -1.6, 0.8, 1.4)             # bee translate: from (x,y) to (x,y) in pt
DELAY = {  # seconds, negative = already under way; staggered left-to-right across the spread
  'pale': 0.0, 'pale .head': -1.1, 'gold': -0.9, 'gold .head': -2.6, 'orange': -2.2, 'orange .head': -0.4,
  'pale .leaf:nth-of-type(2)': -1.3, 'gold .leaf:nth-of-type(2)': -0.7,
  'bee-small': -0.3, 'bee-left': -0.8, 'bee-right': -1.5, 'bee-top': -0.2, 'petals': -1.9,
  'bee-small .hind': 0.0, 'bee-small .fore': 0.0, 'bee-left .hind': -0.02, 'bee-left .fore': -0.02,
  'bee-right .hind': -0.01, 'bee-right .fore': -0.01, 'bee-top .hind': -0.03, 'bee-top .fore': -0.03,
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
    """body and head parts still; each wing in its own group, rooted at its corner nearest the body"""
    body = [i for i in b['ids'] if drs[i].get('fill') and hexc(drs[i]['fill']) == BODY]
    br = pymupdf.Rect()
    for i in body: br |= drs[i]['rect']
    bc = pymupdf.Point((br.x0 + br.x1) / 2, (br.y0 + br.y1) / 2)
    parts, wings = [], []
    for i in b['ids']:
        col = hexc(drs[i]['fill']) if drs[i].get('fill') else ''
        if col in (WING_FORE, WING_HIND):
            root = min(points_of(drs[i]), key=lambda p: (p.x - bc.x) ** 2 + (p.y - bc.y) ** 2)
            wings.append((col, root, i))
        else:
            parts.append(svg_path(drs[i]))
    inner = ''.join(parts)
    # hind wing drawn under the fore wing, as in the source order (gold first, pale second)
    for col, root, i in sorted(wings, key=lambda w: 0 if w[0] == WING_HIND else 1):
        inner += svg_path(drs[i])              # wings still
    whole = pymupdf.Rect()
    for i in b['ids']: whole |= drs[i]['rect']
    return G('bee ' + b['name'], (whole.x0 + whole.x1) / 2, (whole.y0 + whole.y1) / 2, inner, key=b['name'])


ANIM = {('sep', 4): P4, ('sep', 5): P5}

def moving_ids(spec):
    ids = set()
    for pl in spec['plants']:
        ids.update(pl['stem']); ids.update(i for i, _ in pl['leaves']); ids.update(pl['head'])
    for b in spec['bees'] + spec['drift']: ids.update(b['ids'])
    return ids

def paintout(bp, spec):
    """paint the moving paths over in the sky blue on the background copy of the page, a touch
    fat to swallow their anti-aliased edges, then restore the white margin where a stem or petal
    meets the panel's edge"""
    drs = bp.get_drawings()
    W = bp.rect.width
    sh = bp.new_shape()
    for i in sorted(moving_ids(spec)):
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
        else:
            out.append('@keyframes k-%s{from{transform:rotate(%.1fdeg)}to{transform:rotate(%.1fdeg)}}' % (cls, a, b))
            out.append('.anim .%s{animation:k-%s %.3fs ease-in-out infinite alternate}' % (cls, cls, T))
    for sel, d in DELAY.items():
        if '.fore' in sel or '.hind' in sel: continue
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
             '.anim g{transform-box:view-box}\n%s\n'
             '.anim.still g{animation-play-state:paused}\n'
             '@media (prefers-reduced-motion:reduce){.anim g{animation:none}}\n</style>\n') % (pw, ph, css_motion())
    svg = '<svg class="anim" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %.2f %.2f" aria-hidden="true">%s</svg>\n' % (W, H, ''.join(g))
    script = ('<script>/* no work while the spread is off-screen */(function(){var s=document.querySelector("svg.anim");'
              'if(!s||!("IntersectionObserver" in window))return;new IntersectionObserver(function(e){'
              's.classList.toggle("still",!e[0].isIntersecting)},{threshold:0}).observe(s);})();</script>\n')
    return style + svg + script + (shard_cursor() if SHARD_CURSOR else '')

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
