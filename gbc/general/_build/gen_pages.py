#!/usr/bin/env python3
"""Lay up the General Beekeeping collection as an A4 "issue" and build its reader pages.

Sources: _build/raw/<slug>.json (text, headings, images, links harvested from the club website),
assets/src/*.png (the pictures), _build/collection.json (order, kinds, tags, documents, videos).

Steps:
  1. compose each item as HTML in the club's style and render it with WeasyPrint (A4)
  2. concatenate into general.pdf, stamp running feet, and write _build/arts.json
  3. run gbc_build.py on general.pdf -> html/gen/N.html + assets/gen/p-NN.jpg (live text, links kept)
  4. post-process the pages: video players and the document viewer are injected where the
     PDF carries their placeholders, contents entries jump within the reader

    python gen_pages.py <general reader dir>
"""
import base64, html, json, os, re, subprocess, sys, urllib.parse
import fitz
from PIL import Image
from weasyprint import HTML

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, 'raw')
SITE = 'https://geelongbeekeepersclub.org.au/'
PLACE = '#fef3c6'
NEWS_FROM_PAGE = 'https://krisfricke.github.io/gbc/index.html'      # the newsletter reader (published address, so the link works wherever the page is opened)        # the player / viewer placeholder fill: found again in the PDF after rendering
MM = 72 / 25.4

def esc(t): return html.escape(t, quote=False)
def img_uri(p):
    return 'data:image/png;base64,' + base64.b64encode(open(p, 'rb').read()).decode()
def page_url(name): return SITE + 'Main.asp?_=' + urllib.parse.quote(name)

# ------------------------------------------------------------------ style
CSS = '''
@page{size:A4;margin:18mm 16mm 20mm 16mm}
@font-face{font-family:Lato;src:url(FONTS/Lato-Regular.ttf)}
@font-face{font-family:Lato;src:url(FONTS/Lato-Bold.ttf);font-weight:700}
@font-face{font-family:Lato;src:url(FONTS/Lato-Italic.ttf);font-style:italic}
@font-face{font-family:Lato;src:url(FONTS/Lato-BoldItalic.ttf);font-weight:700;font-style:italic}
html,body{margin:0;padding:0}
body{font-family:Lato,sans-serif;font-size:10.6pt;line-height:1.5;color:#333}
.run{position:running(run)}
.kicker{font-size:8pt;letter-spacing:.14em;text-transform:uppercase;color:#8a6a12;margin:0 0 2mm}
h1{font-size:24pt;line-height:1.15;font-style:italic;font-weight:400;color:#993300;margin:0 0 2mm}
.by{font-size:10pt;font-style:italic;color:#777;margin:0 0 6mm}
h2{font-size:14pt;line-height:1.2;font-weight:400;color:#d2691e;margin:7mm 0 2mm;page-break-after:avoid}
h3{font-size:11.5pt;font-weight:700;color:#444;margin:5mm 0 1.5mm;page-break-after:avoid}
p{margin:0 0 3mm;orphans:3;widows:3;text-align:justify;hyphens:auto}
li{text-align:justify;hyphens:auto}
.step .txt{text-align:justify;hyphens:auto}
.vmeta,.by,.src,.card .meta,figcaption,.toc .row,.cover .sub,.cover .foot{text-align:left;hyphens:manual}
a{color:#b35400;text-decoration:none;border-bottom:.4pt solid #e3b98a}
ul,ol{margin:0 0 3mm;padding-left:6mm}li{margin:0 0 1.2mm}
ol ol{margin-top:1mm}
.sub{list-style:none;padding-left:0}
.note{background:#fff8dc;border-left:3pt solid #f7c20b;padding:2.5mm 4mm;margin:0 0 4mm;font-size:10pt}
.warn{background:#fdecea;border-left:3pt solid #d9534f;padding:2.5mm 4mm;margin:0 0 4mm;font-weight:700}
.src{font-size:8.6pt;color:#777;margin-top:6mm;border-top:.5pt solid #e5dcc0;padding-top:2mm}
table{border-collapse:collapse;margin:1mm 0 5mm;font-size:9.6pt;width:100%}
th{text-align:left;background:#fbf255;padding:1.6mm 2.4mm;border-bottom:1pt solid #e0cf3a;font-weight:700}
td{padding:1.4mm 2.4mm;border-bottom:.4pt solid #e9e3c8;vertical-align:top}
tr:nth-child(even) td{background:#fffdf0}
figure{margin:0 0 3mm 5mm;float:right;width:44%;page-break-inside:avoid}
figure.left{float:left;margin:0 5mm 3mm 0}
figure.wide{float:none;width:100%;margin:2mm 0 4mm}
figure img{width:100%;display:block;border-radius:2pt}
figcaption{font-size:8.4pt;color:#777;margin-top:1mm;font-style:italic}
.clear{clear:both}
.steps{clear:both}
.step{display:flex;gap:5mm;align-items:flex-start;margin:0 0 4mm;page-break-inside:avoid;border-top:.5pt solid #efe7c8;padding-top:3mm}
.step .n{flex:0 0 11mm;font-size:22pt;line-height:1;color:#f7c20b;font-weight:700;font-style:italic}
.step .txt{flex:1 1 auto}
.step .pics{flex:0 0 auto;display:flex;gap:2mm}
.step .pics img{height:30mm;width:auto;display:block;border-radius:2pt}
.step .pics img.w{height:22mm}
.step .pics.col{flex-direction:column;width:46mm;gap:2.5mm}.step .pics.col img,.step .pics.col img.w{width:46mm;height:auto}
.poster{text-align:center}
.poster img{max-width:100%;max-height:228mm;display:block;margin:0 auto}
.poster.land img{max-height:158mm}
@page land{size:A4 landscape;margin:12mm 14mm 16mm 14mm}
.poster.land{page:land}
.poster h1{font-size:18pt;margin-bottom:1mm}
.poster .credit{font-size:8.6pt;color:#777;margin-top:3mm}
.player{background:PLACE;border:.6pt solid #e6cf7a;border-radius:3pt;height:101mm;position:relative;margin:4mm 0 3mm}
.player .pl{position:absolute;left:50%;top:50%;width:18mm;height:18mm;margin:-9mm 0 0 -9mm;border-radius:50%;background:#111}
.player .pl::after{content:"";position:absolute;left:7.2mm;top:4.6mm;border-left:6.5mm solid #f7c20b;border-top:4.4mm solid transparent;border-bottom:4.4mm solid transparent}
.player .lab{position:absolute;left:0;right:0;bottom:4mm;text-align:center;font-size:9pt;color:#8a6a12}
.vmeta{font-size:9.6pt;color:#666}
.card{border:.6pt solid #e0cf3a;border-radius:4pt;padding:9mm 10mm;background:#fffef6;page-break-inside:avoid}
table.doc{border-collapse:collapse;margin:0;width:100%}table.doc td{border:none;padding:0;vertical-align:top;background:none}table.doc td.l{width:48mm;padding-right:8mm}
.card img.cov{width:48mm;display:block}
.vmeta{overflow-wrap:anywhere}
.card .ico{width:36mm;height:48mm;background:PLACE;border:.6pt solid #e6cf7a;border-radius:2pt;position:relative}
.card .ico::before{content:"PDF";position:absolute;left:0;right:0;top:19mm;text-align:center;font-weight:700;font-size:13pt;color:#b35400;letter-spacing:.08em}
.card .ico::after{content:attr(data-pages);position:absolute;left:0;right:0;bottom:4mm;text-align:center;font-size:9pt;color:#8a6a12}
.card h1{font-size:20pt}
.card .meta{font-size:9.6pt;color:#666;margin:0 0 4mm}
.card .btn{display:inline-block;background:#f7c20b;color:#111;font-weight:700;border:none;border-radius:4pt;padding:3mm 6mm;margin-top:3mm;font-size:10.5pt}
.cover{position:relative;height:257mm}
.cover .band{background:#fbf255 url(HEX) repeat;height:52mm;margin:-18mm -16mm 0;padding:10mm 16mm 0;display:flex;align-items:center;gap:8mm}
.cover .band img{height:30mm;border-radius:2pt}
.cover .band .tag{font-size:14pt;font-style:italic;color:#222;line-height:1.2}
.cover h1{font-size:44pt;line-height:1.05;margin:16mm 0 4mm;color:#993300}
.cover .sub{font-size:15pt;color:#444;max-width:120mm;line-height:1.35}
.cover .hero{position:absolute;left:0;right:0;bottom:22mm;height:118mm;overflow:hidden;border-radius:4pt}
.cover .hero img{width:100%;height:100%;object-fit:cover;display:block}
.cover .foot{position:absolute;left:0;right:0;bottom:6mm;font-size:9pt;color:#777;display:flex;justify-content:space-between}
.toc h1{margin-bottom:5mm}
.toc .sec{font-size:9pt;letter-spacing:.14em;text-transform:uppercase;color:#8a6a12;margin:5mm 0 1.5mm;border-bottom:1pt solid #f7c20b;padding-bottom:1mm}
.toc .row{display:flex;justify-content:space-between;gap:3mm;font-size:9.4pt;line-height:1.3;padding:.8mm 0;border-bottom:.3pt dotted #d8d0a8}
.toc .row a{border:none;color:#333;flex:1 1 auto}
.toc .row .n{color:#8a6a12;flex:0 0 auto;font-weight:700}
.toc .row .au{color:#888;font-size:9pt;font-style:italic;flex:0 0 auto;margin-left:3mm}
.toc .cols{columns:2;column-gap:10mm}
.toc .cols .sec{break-inside:avoid}
.toc .row{break-inside:avoid}
.links .big{display:block;border:.6pt solid #e0cf3a;border-radius:4pt;padding:7mm 9mm;margin:0 0 6mm;background:#fffef6;color:#333}
.links .big b{display:block;font-size:16pt;color:#993300;font-style:italic;font-weight:400;margin-bottom:1.5mm}
.links .big span{font-size:10pt;color:#666}
'''

def css(reader):
    hexsvg = ("<svg xmlns='http://www.w3.org/2000/svg' width='14' height='24.25' viewBox='0 0 14 24.25'>"
              "<path d='M7 0 L14 4.04 L14 12.12 L7 16.17 L0 12.12 L0 4.04 Z M7 16.17 L7 24.25' fill='none' stroke='%23000' stroke-opacity='.13' stroke-width='.7'/></svg>")
    return (CSS.replace('FONTS/', 'file://' + os.path.join(reader, 'fonts') + '/')
               .replace('PLACE', PLACE).replace('HEX', '"data:image/svg+xml;utf8,' + hexsvg + '"'))

# ------------------------------------------------------------------ copy -> html
def load_raw(slug):
    p = os.path.join(RAW, slug + '.json')
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else None

def pic(reader, slug, src):
    """the captured copy of a website picture"""
    name = os.path.basename(urllib.parse.unquote(src)).rsplit('.', 1)[0].replace(' ', '_')
    p = os.path.join(reader, 'assets', 'src', '%s__%s.png' % (slug, name))
    return p if os.path.exists(p) else None

def linkify(text, links, internal):
    """wrap the first occurrence of each link's words in an anchor; bare URLs become links too"""
    out = esc(text)
    for lt, target in links:
        if not lt or len(lt) < 3: continue
        href = None
        if target.startswith('PAGE:'):
            name = target[5:]
            href = internal.get(name.lower()) or page_url(name)
        elif target.startswith('http') or target.startswith('mailto:') or target.startswith('tel:'):
            href = target
        if not href: continue
        k = out.find(esc(lt))
        if k >= 0:
            out = out[:k] + '<a href="%s">%s</a>' % (html.escape(href, quote=True), esc(lt)) + out[k + len(esc(lt)):]
    out = re.sub(r'(?<!href=")(?<!">)(https?://[^\s<)]+)', lambda m: '<a href="%s">%s</a>' % (m.group(1), m.group(1)), out)
    return out

def compose_article(reader, item, internal):
    raw = load_raw(item['slug'])
    text, meta = raw['text'], raw['meta']
    heads = {}
    for h in meta.get('h', []):
        lvl, t = h.split(':', 1); heads[t.strip().lower()] = int(lvl)
    links = meta.get('l', [])
    imgs = meta.get('i', [])
    lines = [l.rstrip() for l in text.split('\n')]
    body = []
    first = True
    byline = ''
    i = 0
    pending_imgs = list(imgs)
    def place_images_after(block_text):
        """pictures whose 'prev' text begins this block go right after it"""
        out = ''
        for im in list(pending_imgs):
            prev = (im[5] or '').strip().lower()
            if prev and block_text.lower().startswith(prev[:24]):
                p = pic(reader, item['slug'], im[0])
                if p:
                    cls = 'left' if 'left' in (im[4] or '') else ''
                    wide = (im[1] or 0) > 900 and (im[2] or 0) < 0.7 * (im[1] or 1)
                    out += '<figure class="%s"><img src="%s"></figure>' % ('wide' if wide else cls, img_uri(p))
                pending_imgs.remove(im)
        return out
    while i < len(lines):
        l = lines[i]
        if not l.strip(): i += 1; continue
        if first:
            first = False; i += 1; continue                       # the title: set by the template
        if re.match(r'^\(?[Bb]y\s+\S', l) and len(l) < 120 and not byline:
            byline = l.strip('()'); i += 1; continue
        tag = l.split(':', 1)[0] if ':' in l else ''
        if tag in ('LIST', 'NUM', 'SUB', 'STEP', 'TABLE', 'REF', 'PRES'):
            j = i; grp = []
            while j < len(lines) and lines[j].split(':', 1)[0] in ('LIST', 'NUM', 'SUB', 'STEP', 'TABLE', 'REF', 'PRES') and (lines[j].split(':', 1)[0] == tag or (tag in ('NUM', 'SUB') and lines[j].split(':', 1)[0] in ('NUM', 'SUB'))):
                grp.append(lines[j]); j += 1
            if tag == 'LIST':
                body.append('<ul>' + ''.join('<li>%s</li>' % linkify(g.split(':', 1)[1], links, internal) for g in grp) + '</ul>')
            elif tag in ('NUM', 'SUB'):
                h = '<ol>'
                for g in grp:
                    k, t = g.split(':', 1)
                    if k == 'NUM': h += '<li>%s' % linkify(t, links, internal)
                    else: h += '<ul class="sub"><li>%s</li></ul>' % linkify(t, links, internal)
                body.append(h + '</ol>')
            elif tag == 'STEP':
                h = '<div class="steps">'
                for g in grp:
                    parts = g.split('|'); n = parts[0].split(':', 1)[1]; t = parts[1]; pics = parts[2].split(',') if len(parts) > 2 else []
                    ph = ''; wide = 0
                    for pn in pics:
                        p = pic(reader, item['slug'], pn.strip())
                        if p:
                            im = Image.open(p); ph += '<img class="%s" src="%s">' % ('w' if im.width > im.height else '', img_uri(p)); wide += im.width > im.height
                            for q in list(pending_imgs):          # a step's picture is placed here, not as a lead figure
                                if os.path.basename(urllib.parse.unquote(q[0])).lower() == pn.strip().lower(): pending_imgs.remove(q)
                    col = ' col' if wide else ''                 # a step with a diagram among its pictures stacks them beside the text
                    h += '<div class="step"><div class="n">%s</div><div class="txt">%s</div>%s</div>' % (n, linkify(t, links, internal), ('<div class="pics%s">%s</div>' % (col, ph)) if ph else '')
                body.append(h + '</div>')
            elif tag == 'TABLE':
                rows = [g.split(':', 1)[1].split('|') for g in grp]
                h = '<table><tr>' + ''.join('<th>%s</th>' % esc(c) for c in rows[0]) + '</tr>'
                for r in rows[1:]: h += '<tr>' + ''.join('<td>%s</td>' % esc(c) for c in r) + '</tr>'
                body.append(h + '</table>')
            elif tag == 'REF':
                body.append('<div class="src">' + '<br>'.join(esc(g.split(':', 1)[1]) for g in grp) + '</div>')
            elif tag == 'PRES':
                body.append('<ul>' + ''.join('<li><a href="%s">%s</a></li>' % (page_url('Biosecurity - ' + g.split(':', 1)[1]), esc(g.split(':', 1)[1])) for g in grp) + '</ul>')
            i = j; continue
        key = l.strip().lower().rstrip('.')
        lvl = heads.get(key) or heads.get(l.strip().lower())
        if lvl and lvl >= 2 and len(l) < 110:
            body.append(('<h2>%s</h2>' if lvl == 2 else '<h3>%s</h3>') % esc(l.strip()))
            body.append(place_images_after(l)); i += 1; continue
        if lvl == 1 and len(l) < 80:
            body.append('<h2>%s</h2>' % esc(l.strip())); body.append(place_images_after(l)); i += 1; continue
        # a short line ending without punctuation followed by a list-ish block reads as a sub-heading
        if len(l) < 60 and not re.search(r'[.!?:;,)]$', l) and i + 1 < len(lines) and lines[i + 1].strip() and l.strip().lower() not in ('[online request form - on the club website]',) and l[0].isupper() and sum(w[0].isupper() for w in l.split()) >= 1 and not l.startswith('Go to'):
            body.append('<h3>%s</h3>' % esc(l.strip())); body.append(place_images_after(l)); i += 1; continue
        cls = ''
        if re.search(r'NOT permitted|PLAN AHEAD', l): cls = ' class="warn"'
        elif l.startswith('Please note') or l.startswith('Disclaimer') or l.startswith('Note:'): cls = ' class="note"'
        body.append('<p%s>%s</p>' % (cls, linkify(l.strip(), links, internal)))
        body.append(place_images_after(l))
        i += 1
    # pictures that found no anchor go at the top, after the byline
    lead = ''
    for im in pending_imgs:
        p = pic(reader, item['slug'], im[0])
        if p: lead += '<figure><img src="%s"></figure>' % img_uri(p)
    vid = ''
    if item.get('video'):
        v = item['video']
        vid = '<div class="clear"></div><h2>%s</h2><div class="player" data-video="1"><div class="pl"></div><div class="lab">The video plays here in the reader. On paper: %s</div></div>' % (
            esc(v.get('caption', 'Video')), esc('youtube.com/watch?v=' + v['id'] if v['kind'] == 'yt' else v['src'].replace(SITE, 'geelongbeekeepersclub.org.au/')))
    src = '<div class="src">Source: the Geelong Beekeepers Club website, <a href="%s">%s</a></div>' % (page_url(raw['page']), esc('geelongbeekeepersclub.org.au › Resources › General Beekeeping › ' + raw['page']))
    return ('<div class="kicker">General Beekeeping</div><h1 id="%s">%s</h1>%s%s%s%s<div class="clear"></div>%s'
            % (item['slug'], esc(item['t']), ('<div class="by">%s</div>' % esc(byline)) if byline else '', lead, ''.join(body), vid, src))

def compose_poster(reader, item):
    p = os.path.join(reader, 'assets', 'src', item['img'])
    return '<div class="poster %s"><div class="kicker">General Beekeeping</div><h1 id="%s">%s</h1><img src="%s"><div class="credit">%s · from the club website</div></div>' % (
        'land' if item.get('landscape') else '', item['slug'], esc(item['t']), img_uri(p), esc(item.get('credit', '')))

def compose_video(item, section='', n=None, total=None):
    v = item['video']
    where = ('youtube.com/watch?v=' + v['id']) if v['kind'] == 'yt' else v['src'].replace(SITE, 'geelongbeekeepersclub.org.au/')
    kick = section or 'General Beekeeping · Video'
    if n: kick += ' · %d of %d' % (n, total)
    by = ('<div class="by">%s</div>' % esc(item['author'])) if item.get('author') else ''
    return ('<div class="kicker">%s</div><h1 id="%s">%s</h1>%s<p class="vmeta">%s</p>'
            '<div class="player" data-video="1"><div class="pl"></div><div class="lab">The video plays here in the reader. On paper: %s</div></div>'
            '<p class="vmeta">%s</p>') % (esc(kick), item['slug'], esc(item['t']), by, esc(item.get('blurb', '')), esc(where),
                                         'Source: ' + esc(item.get('source', 'Geelong Beekeepers Club website')))

def doc_cover(reader, d, k):
    """assets/docs/doc-k.png: the document's first page on a stack of pages. A small document shows its
    pages one behind another; a long one shows the block of a book's edge, thicker the longer it is."""
    from PIL import Image, ImageDraw, ImageFont
    out_dir = os.path.join(reader, 'assets', 'docs'); os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, 'doc-%d.png' % k)
    W = 420                                           # cover width in px; A4 proportions
    pdf = os.path.join(HERE, 'docs', d['file'])
    cover = None; pages = d.get('pages')
    if os.path.exists(pdf):
        try:
            doc = fitz.open(pdf); pages = len(doc); pg = doc[0]
            z = W / pg.rect.width
            pix = pg.get_pixmap(matrix=fitz.Matrix(z, z), alpha=False)
            cover = Image.frombytes('RGB', (pix.width, pix.height), pix.samples); doc.close()
        except Exception as e:
            print('   cover failed for', d['file'], e)
    if cover is None:
        pic_ = os.path.join(HERE, 'covers', os.path.splitext(d['file'])[0] + '.png')
        if os.path.exists(pic_):
            im = Image.open(pic_).convert('RGB'); cover = im.resize((W, int(W * im.height / im.width)), Image.LANCZOS)
    if cover is None:
        H = int(W * 1.414); cover = Image.new('RGB', (W, H), '#fffdf4'); dr = ImageDraw.Draw(cover)
        try:
            f1 = ImageFont.truetype(os.path.join(reader, 'fonts', 'Lato-Bold.ttf'), 30); f2 = ImageFont.truetype(os.path.join(reader, 'fonts', 'Lato-Italic.ttf'), 20)
        except Exception:
            f1 = f2 = ImageFont.load_default()
        dr.rectangle([0, 0, W - 1, 46], fill='#f7c20b')
        words = d['t'].split(); lines = []; cur = ''
        for w_ in words:
            t = (cur + ' ' + w_).strip()
            if dr.textlength(t, font=f1) > W - 60 and cur: lines.append(cur); cur = w_
            else: cur = t
        if cur: lines.append(cur)
        y = 90
        for ln in lines[:7]: dr.text((30, y), ln, font=f1, fill='#993300'); y += 38
        if d.get('author'): dr.text((30, y + 14), d['author'], font=f2, fill='#555')
        dr.text((30, H - 60), 'PDF', font=f2, fill='#8a6a12')
    cw, ch = cover.size
    n = pages or 1
    if n <= 12:
        off = 4; layers = max(0, n - 1)
        canvas = Image.new('RGBA', (cw + off * layers + 2, ch + off * layers + 2), (0, 0, 0, 0)); dr = ImageDraw.Draw(canvas)
        for i in range(layers, 0, -1):
            x = i * off; y = i * off
            dr.rectangle([x, y, x + cw, y + ch], fill='#fbfaf3', outline='#c9c1a8')
        canvas.paste(cover, (0, 0)); dr.rectangle([0, 0, cw - 1, ch - 1], outline='#b9b094')
    else:
        import math
        t = int(10 + 11 * math.log10(n / 10.0))       # 20 pages -> 13 px, 88 -> 20, 364 -> 27
        canvas = Image.new('RGBA', (cw + t + 2, ch + t + 2), (0, 0, 0, 0)); dr = ImageDraw.Draw(canvas)
        # the block of leaves: right edge and bottom edge, with fine lines for the pages
        for i in range(t, 0, -1):
            shade = 236 - int(28 * i / t)
            dr.rectangle([i, i, i + cw, i + ch], fill=(shade + 10, shade + 6, shade - 12), outline=(190, 182, 160) if i % 2 == 0 else (215, 208, 186))
        canvas.paste(cover, (0, 0)); dr.rectangle([0, 0, cw - 1, ch - 1], outline='#b9b094')
    canvas.save(out)
    return out, pages

def compose_doc(d, base, slug):
    pages = ('%d page%s' % (d['pages'], '' if d['pages'] == 1 else 's')) if d.get('pages') else 'PDF'
    size = ('%.1f MB' % (d['kb'] / 1024)) if d['kb'] >= 1000 else '%d KB' % d['kb']
    url = base + urllib.parse.quote(d['file'])
    meta = ' · '.join(x for x in [('by ' + d['author']) if d.get('author') else '', pages, size] if x)
    cov = d.get('_cover')
    ico = ('<img class="cov" src="%s">' % img_uri(cov)) if cov else '<div class="ico" data-pages="%s"></div>' % esc(pages)
    return ('<div class="kicker">General Beekeeping · Longer document</div><div class="card"><table class="doc"><tr><td class="l">%s</td><td>'
            '<h1 id="%s">%s</h1><div class="meta">%s</div><p>%s</p>'
            '<a class="btn" href="%s" data-pdf="1">Open the document &rsaquo;</a>'
            '<p class="vmeta" style="margin-top:4mm">Opens in a viewer over the reader; on paper, the file is at<br>%s</p></td></tr></table></div>'
            % (ico, slug, esc(d['t']), esc(meta), esc(d['blurb']), html.escape(url, quote=True), esc(urllib.parse.unquote(url).replace('https://', ''))))

def compose_links(news_base):
    return ('<div class="kicker">General Beekeeping</div><h1 id="elsewhere">Elsewhere on the website</h1>'
            '<p>The club keeps its varroa material together on the website: treatments and the current advice for the Geelong region, monitoring methods, the GBC Varroa Watch, and the latest from Agriculture Victoria.</p><div class="links">'
            '<a class="big" href="%sMain.asp?_=Varroa%%20management"><b>Varroa Management Hub &rsaquo;</b><span>geelongbeekeepersclub.org.au &rsaquo; Resources &rsaquo; Varroa management</span></a>'
            '<a class="big" href="%s#/topic/Bee%%20biology"><b>Bee biology in the newsletter &rsaquo;</b><span>Bruce Ward\'s "This month\'s bit of bee biology" series and everything else tagged Bee biology in the club newsletter reader.</span></a>'
            '</div><div class="src">These pages were compiled from <a href="%sMain.asp?_=General%%20Beekeeping">the General Beekeeping page</a> on geelongbeekeepersclub.org.au, where the downloadable documents live.</div>') % (SITE, news_base, SITE)

def compose_cover(reader, col):
    logo = img_uri(os.path.join(reader, 'assets', 'gbc_logo.png'))
    hero = img_uri(os.path.join(reader, 'assets', 'src', 'spring-hive-development__05_WELL_DEVELOPED_BROOD_-_CASHMANBEES.png'))
    return ('<div class="cover"><div class="band"><img src="%s"><div class="tag">For hobbyist and<br>professional beekeepers</div></div>'
            '<h1>General<br>Beekeeping</h1><div class="sub">Articles, guides, videos and documents from the Geelong Beekeepers Club, gathered as one issue.</div>'
            '<div class="hero"><img src="%s"></div>'
            '<div class="foot"><span>geelongbeekeepersclub.org.au · Resources · General Beekeeping</span><span>Compiled October 2026</span></div></div>') % (logo, hero)

def compose_contents(col, spans, docs_first, vids):
    rows = lambda items: ''.join('<div class="row"><a href="gen://%s">%s</a>%s<span class="n">%d</span></div>' % (
        s, esc(t), ('<span class="au">%s</span>' % esc(a)) if a else '', p) for s, t, a, p in items)
    arts = [(it['slug'], it['t'], it.get('author', ''), spans[it['slug']][0]) for it in col['items'] if it['kind'] in ('article', 'poster', 'pdf')]
    videos = [(it['slug'], it['t'], it.get('author', ''), spans[it['slug']][0]) for it in col['items'] if it['kind'] == 'video'] + \
             [('vb-%d' % (k + 1), v[0], '', spans['vb-%d' % (k + 1)][0]) for k, v in enumerate(vids)]
    docs = [('doc-%d' % (k + 1), d['t'], d.get('author', ''), spans['doc-%d' % (k + 1)][0]) for k, d in enumerate(col['documents'])]

    return ('<div class="toc"><div class="kicker">General Beekeeping</div><h1 id="contents">In this collection</h1><div class="cols">'
            '<div class="sec">Articles and guides</div>%s<div class="sec">Videos</div>%s<div class="sec">Longer documents</div>%s<div class="sec">Also</div>'
            '<div class="row"><a href="%sMain.asp?_=Varroa%%20management">Varroa Management Hub &mdash; on the club website</a><span class="n">&rsaquo;</span></div>'
            '<div class="row"><a href="%s#/topic/Bee%%20biology">Bee biology &mdash; in the club newsletter</a><span class="n">&rsaquo;</span></div>'
            '</div></div>') % (rows(arts), rows(videos), rows(docs), SITE, NEWS_FROM_PAGE)

# ------------------------------------------------------------------ build
def render(reader, inner, out, landscape=False):
    extra = '@page{size:A4 landscape;margin:12mm 14mm 16mm 14mm}' if landscape else ''
    HTML(string='<!doctype html><html lang="en-AU"><head><meta charset="utf-8"><style>%s%s</style></head><body>%s</body></html>' % (css(reader), extra, inner),
         base_url=reader).write_pdf(out)
    d = fitz.open(out); n = len(d); d.close(); return n

def main(reader):
    col = json.load(open(os.path.join(HERE, 'collection.json'), encoding='utf-8'))
    tmp = os.path.join(HERE, 'tmp'); os.makedirs(tmp, exist_ok=True)
    news_base = NEWS_FROM_PAGE
    # the items that will actually be pages, in order (the biosecurity videos and documents expand)
    seq = []
    for it in col['items']:
        if it['kind'] == 'videos':
            for k, v in enumerate(col['videos_biosecurity']):
                seq.append({'slug': 'vb-%d' % (k + 1), 'kind': 'video', 't': v[0], 'author': '', 'source': v[1], 'tags': it['tags'],
                            'video': {'kind': v[2], 'id': v[3]} if v[2] == 'yt' else {'kind': 'mp4', 'src': v[3]}, 'blurb': v[1], 'section': 'Biosecurity videos', 'n': k + 1, 'total': len(col['videos_biosecurity'])})
        elif it['kind'] == 'docs':
            for k, d in enumerate(col['documents']):
                seq.append({'slug': 'doc-%d' % (k + 1), 'kind': 'doc', 't': d['t'], 'author': d.get('author', ''), 'tags': d['tags'] + ['Documents'], 'doc': d})
        else:
            seq.append(it)
    internal = {}                    # website page name -> in-document anchor
    names = {it['slug']: it['t'] for it in seq}
    for it in seq:
        raw = load_raw(it['slug'])
        if raw: internal[raw['page'].lower()] = 'gen://' + it['slug']       # in-book links keep a URI form that survives rendering alone
    # 1. render every item to its own PDF; the contents page needs page numbers, so it is rendered last
    pdfs, spans, p = [], {}, 1
    for it in seq:
        out = os.path.join(tmp, it['slug'] + '.pdf')
        k = it['kind']
        if k == 'cover': n = render(reader, compose_cover(reader, col), out)
        elif k == 'contents':
            # measure with placeholder numbers so the right number of pages is reserved
            fake = {x['slug']: (999, 999) for x in seq}
            for kk in range(len(col['videos_biosecurity'])): fake['vb-%d' % (kk + 1)] = (999, 999)
            for kk in range(len(col['documents'])): fake['doc-%d' % (kk + 1)] = (999, 999)
            n = render(reader, compose_contents(col, fake, None, col['videos_biosecurity']), os.path.join(tmp, 'contents.pdf'))
            pdfs.append(None); spans[it['slug']] = (p, p + n - 1); p += n; print('contents reserved %d page(s)' % n); continue
        elif k == 'article': n = render(reader, compose_article(reader, it, internal), out)
        elif k == 'poster': n = render(reader, compose_poster(reader, it), out, landscape=it.get('landscape', False))
        elif k == 'video': n = render(reader, compose_video(it, it.get('section', ''), it.get('n'), it.get('total')), out)
        elif k == 'doc':
            cov, pages = doc_cover(reader, it['doc'], int(it['slug'].split('-')[1]))
            it['doc']['_cover'] = cov
            if pages: it['doc']['pages'] = pages
            n = render(reader, compose_doc(it['doc'], col['doc_base'], it['slug']), out)
        elif k == 'links': n = render(reader, compose_links(news_base), out)
        elif k == 'pdf':
            src = os.path.join(HERE, 'docs', it['file']); out = src
            dd = fitz.open(src); n = len(dd); dd.close()
        pdfs.append(out); spans[it['slug']] = (p, p + n - 1); p += n
        print('%-40s %2d page%s  from %d' % (it['slug'], n, '' if n == 1 else 's', spans[it['slug']][0]))
    cpath = os.path.join(tmp, 'contents.pdf')
    n = render(reader, compose_contents(col, spans, None, col['videos_biosecurity']), cpath)
    if (spans['contents'][1] - spans['contents'][0] + 1) != n: raise SystemExit('contents changed length between passes (%d)' % n)
    pdfs[[it['slug'] for it in seq].index('contents')] = cpath
    # 2. concatenate; internal links (#slug) become page jumps by resolving the anchors across the whole book
    book = fitz.open()
    for f in pdfs: book.insert_pdf(fitz.open(f))
    # anchors: find each heading id by searching the text of its first page
    anchor_page = {s: spans[s][0] for s in spans}
    for pg in book:
        for l in pg.get_links():
            if l.get('kind') == fitz.LINK_URI and l.get('uri', '').startswith('gen://'):
                name = l['uri'][6:]
                if name in anchor_page:
                    pg.delete_link(l); l2 = {'kind': fitz.LINK_GOTO, 'from': l['from'], 'page': anchor_page[name] - 1, 'to': fitz.Point(0, 0)}
                    pg.insert_link(l2)
    # running feet
    book_pdf = os.path.join(reader, '_build', 'general.pdf')
    inserted = set()
    for it in seq:
        if it['kind'] == 'pdf': inserted.update(range(spans[it['slug']][0], spans[it['slug']][1] + 1))
    for i, pg in enumerate(book):
        n = i + 1
        if n == 1: continue
        W, H = pg.rect.width, pg.rect.height
        pg.insert_font(fontname='lato', fontfile=os.path.join(reader, 'fonts', 'Lato-Regular.ttf'))
        if n not in inserted:
            pg.insert_text((16 * MM, H - 10 * MM), 'Geelong Beekeepers Club  ·  General Beekeeping', fontname='lato', fontsize=7.5, color=(0.45, 0.4, 0.25))
        s = str(n); w = fitz.get_text_length(s, fontname='helv', fontsize=8.5)
        pg.insert_text((W - 16 * MM - w, H - 10 * MM), s, fontname='lato', fontsize=8.5, color=(0.2, 0.17, 0.08))
    book.save(book_pdf, garbage=3, deflate=True)
    print('book: %d pages -> %s' % (len(book), book_pdf))
    # 3. arts.json for the reader (the catalogue the reader bakes in)
    arts = []
    for it in seq:
        a, b = spans[it['slug']]
        arts.append({'t': it['t'], 'p': a, 'end': b, 'author': it.get('author', ''), 'tags': it['tags'], 'kind': it['kind']})
    json.dump({'gen': arts}, open(os.path.join(reader, '_build', 'arts.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    # 4. placeholder rectangles (players, document buttons) per page, for the post-processor
    marks = {}
    for i, pg in enumerate(book):
        for dr in pg.get_drawings():
            f = dr.get('fill')
            if f and abs(f[0] - 0xfe / 255) < .01 and abs(f[1] - 0xf3 / 255) < .01 and abs(f[2] - 0xc6 / 255) < .01 and dr['rect'].width > 60:
                marks.setdefault(i + 1, []).append([round(v, 1) for v in dr['rect']])
    # pictures: every raster on a page whose captured copy is larger than it is printed opens in the lightbox
    srcdir = os.path.join(reader, 'assets', 'src'); dims = {}
    for fn in os.listdir(srcdir):
        if fn.endswith('.png'):
            with Image.open(os.path.join(srcdir, fn)) as im: dims.setdefault(im.size, fn)
    zooms = {}
    titles = {}
    for it in seq:
        for pno in range(spans[it['slug']][0], spans[it['slug']][1] + 1): titles[pno] = it['t']
    for i, pg in enumerate(book):
        for info in pg.get_image_info(xrefs=True):
            try: pix = fitz.Pixmap(book, info['xref'])
            except Exception: continue
            fn = dims.get((pix.width, pix.height))
            x0, y0, x1, y1 = info['bbox']
            if not fn or (x1 - x0) < 30: continue
            if pix.width <= (x1 - x0) * 1.6 * 1.15: continue          # no bigger than it is shown: nothing to enlarge
            zooms.setdefault(str(i + 1), []).append({'rect': [round(x0, 1), round(y0, 1), round(x1, 1), round(y1, 1)], 'src': 'assets/src/' + fn,
                                                     'alt': titles.get(i + 1, ''), 'w': pix.width, 'h': pix.height})
    json.dump(zooms, open(os.path.join(reader, '_build', 'gen_imgs.json'), 'w'), indent=0)
    print('zoomable pictures on %d pages' % len(zooms))
    land = [i + 1 for i, pg in enumerate(book) if pg.rect.width > pg.rect.height]
    json.dump(land, open(os.path.join(reader, '_build', 'land.json'), 'w'))
    json.dump({'marks': marks, 'seq': [{'slug': it['slug'], 'kind': it['kind'], 'p': spans[it['slug']][0], 'video': it.get('video'), 'doc': it.get('doc', {}).get('file') if it.get('doc') else None} for it in seq]},
              open(os.path.join(reader, '_build', 'gen_marks.json'), 'w'), indent=0)
    book.close()

if __name__ == '__main__':
    main(os.path.abspath(sys.argv[1]))
