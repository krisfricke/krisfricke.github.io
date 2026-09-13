#!/usr/bin/env python3
"""Build one issue of the ABJ reader from a single-page PDF, the way August was built.

For each page n:
  assets/<dir>/p-NN.jpg   full page, 761x1076, JPEG q76        (issue strip, fallbacks)
  html/<id>/pgNNN.jpg     page with its text removed, 953x1348, JPEG q84  (overlay background)
  html/<id>/N.html        the text, absolutely positioned over that background
and _build/<id>_text.json with each page's paragraphs, for the article pages.

Coordinates: PDF points x 1.6 = page pixels. Markup follows html/aug exactly:
  <p style="position:absolute;left:Xpx;top:Ypx;font-size:Spx;white-space:nowrap" data-w="W"[ data-j="1"]>
  <span style="[font-weight:700;][font-style:italic;][color:#rrggbb;]font-family:...">text</span>
  links: <a href=".." target="_blank" rel="noopener">..spans..</a>
  ads:   <a class="adlink" href="../../out/<slug>/index.html" ... style="left:%;top:%;width:%;height:%">
Footnote markers are left as plain spans: abj_notes.py sets them superscript afterwards.

    python build_issue.py <reader dir> <issue id> <asset dir> "<label>" <pdf>  [pages|ads|all]
"""
import html, json, os, re, sys
import warnings; warnings.filterwarnings("ignore")
import fitz
from PIL import Image

SCALE = 1.6
PT_MM = 25.4 / 72.0
ASSET_W, ASSET_H, ASSET_Q = 761, 1076, 76
PAGE_Q = 84

SERIF_HINTS = ('times', 'palatino', 'georgia', 'garamond', 'minion', 'book antiqua', 'cambria', 'caslon', 'bodoni')

def fam(fontname):
    f = fontname.lower()
    if any(h in f for h in SERIF_HINTS):
        return "'Times New Roman',Times,serif"
    if 'calibri' in f:
        return "Carlito,Calibri,'Segoe UI',Arial,sans-serif"
    return "Arial,Helvetica,sans-serif"

def esc(t):
    return html.escape(t, quote=False).replace('\xa0', '&#160;')

def span_style(s):
    st = []
    fl, fn = s['flags'], s['font'].lower()
    if (fl & 16) or 'bold' in fn or 'black' in fn or 'semibold' in fn or 'heavy' in fn:
        st.append('font-weight:700')
    if (fl & 2) or 'italic' in fn or 'oblique' in fn:
        st.append('font-style:italic')
    if s['color'] != 0:
        st.append('color:#%06x' % s['color'])
    st.append('font-family:' + fam(s['font']))
    return ';'.join(st)

def inter(a, b):
    x0, y0 = max(a[0], b[0]), max(a[1], b[1]); x1, y1 = min(a[2], b[2]), min(a[3], b[3])
    return max(0, x1 - x0) * max(0, y1 - y0)

HEAD = '''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%(title)s &mdash; page %(n)d</title>
<style>
html,body{margin:0;padding:0;background:#fff}
.sheet{width:calc(%(wmm).0fmm * var(--k,1));height:calc(%(hmm).0fmm * var(--k,1));overflow:hidden;position:relative}
.scaler{transform:scale(calc(%(scaler).5f * var(--k,1)));transform-origin:top left}
.page{position:relative;width:%(pw)dpx;height:%(ph)dpx}
.page img.bg{position:absolute;left:0;top:0;width:%(pw)dpx;height:%(ph)dpx}
p{margin:0;position:absolute}
a{color:inherit}
a:hover{text-decoration:underline}
a.adlink{position:absolute;display:block;z-index:5;text-decoration:none;border-radius:3px;transition:box-shadow .12s,background .12s}
a.adlink:hover{background:rgba(249,197,0,.13);box-shadow:0 0 0 2px rgba(249,197,0,.75) inset}
@font-face{font-family:'Carlito';src:url('../../fonts/Carlito-Regular.ttf');font-weight:400;font-style:normal}
@font-face{font-family:'Carlito';src:url('../../fonts/Carlito-Bold.ttf');font-weight:700;font-style:normal}
@font-face{font-family:'Carlito';src:url('../../fonts/Carlito-Italic.ttf');font-weight:400;font-style:italic}
</style></head><body><div class="sheet"><div class="scaler"><div class="page">
'''

TAIL = '''</div></div></div>
<script>
/* Fit each line to the width it occupied in the PDF: stretch the spaces on
   justified lines, and tighten any line the substitute font renders too wide
   (which would otherwise run into the next column). Compression is kept
   gentle on purpose, and backs off completely rather than mashing words
   together when a line (typically bold/display-sized ad text in a
   substitute font) is too far off to fix with reasonable spacing. */
(function(){
  function fit(){
    var ps=document.querySelectorAll('p[data-w]');
    for(var i=0;i<ps.length;i++){
      var p=ps[i];
      p.style.wordSpacing=''; p.style.letterSpacing='';
      var target=parseFloat(p.getAttribute('data-w')), nat=p.offsetWidth;
      if(!target||!nat) continue;
      var d=target-nat, stretch=p.hasAttribute('data-j');
      if(Math.abs(d)<0.5) continue;
      if(d>0&&!stretch) continue;
      if(Math.abs(d)>target*0.18){ continue; } /* too far off to fix by squeezing -- leave it alone rather than crush the spacing */
      var txt=p.textContent||'', sp=(txt.match(/ /g)||[]).length;
      var fs=parseFloat(getComputedStyle(p).fontSize)||12;
      if(sp>0){
        var ws=d/sp, cap=fs*0.6, floor=-fs*0.06;
        if(ws>cap)ws=cap; if(ws<floor)ws=floor;
        p.style.wordSpacing=ws.toFixed(3)+'px';
        d=target-p.offsetWidth;
      }
      if(d<-0.5){
        var n=Math.max(1,txt.length-1), ls=d/n, lf=-fs*0.02;
        if(ls<lf)ls=lf;
        p.style.letterSpacing=ls.toFixed(3)+'px';
      }
    }
  }
  fit();
  if(document.fonts&&document.fonts.ready) document.fonts.ready.then(fit);
  window.addEventListener('resize',fit);
})();
</script>

<script>
/* The reader tells this page how big to draw itself, so text is re-rendered at the new size
   instead of being stretched as a bitmap (which is what happens when an iframe is transform-scaled). */
(function(){
  function setK(k){ document.documentElement.style.setProperty('--k', String(k)); }
  window.addEventListener('message',function(e){ var m=e.data; if(m&&m.abj==='zoom'&&isFinite(m.k)&&m.k>0) setK(m.k); });
})();
</script>
<style>html.bee-on,html.bee-on *{cursor:none !important}</style>
<script>
/* Report the pointer to the parent reader so its bee can follow across the page,
   and hide this document's own cursor only once the parent confirms the bee is on. */
(function(){
  if(window.parent===window) return;
  if(!matchMedia('(hover:hover)').matches) return;
  if(matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  window.addEventListener('message',function(e){
    var m=e.data; if(m&&m.abj==='bee') document.documentElement.classList.toggle('bee-on',!!m.on);
  });
  try{ parent.postMessage({abj:'hello'},'*'); }catch(e){}
  var raf=0,px=0,py=0,pl=false;
  document.addEventListener('mousemove',function(e){
    px=e.clientX; py=e.clientY;
    /* the page hit-tests itself and tells the parent, because a parent cannot
       look inside a same-origin iframe when both are local files */
    pl=!!(e.target&&e.target.closest&&e.target.closest('a[href],area[href]'));
    if(!raf) raf=requestAnimationFrame(function(){ raf=0;
      try{ parent.postMessage({abj:'pointer',x:px,y:py,link:pl},'*'); }catch(err){} });
  },{passive:true});
  document.addEventListener('mouseleave',function(){
    try{ parent.postMessage({abj:'pointerleave'},'*'); }catch(err){} });
})();
</script>
</body></html>'''


def page_lines(page):
    """[(head, [(text, style, href)], textline)] and paragraphs, in block order."""
    flags = fitz.TEXT_PRESERVE_WHITESPACE | fitz.TEXT_MEDIABOX_CLIP
    d = page.get_text('dict', flags=flags)
    uris = [(l['from'], l['uri']) for l in page.get_links() if l.get('kind') == fitz.LINK_URI and l.get('uri')]
    lines, redact, paras = [], [], []
    for b in d['blocks']:
        if b['type'] != 0:
            continue
        blines = [l for l in b['lines'] if any(s['text'].strip() for s in l['spans'])]
        if not blines:
            continue
        ptxt = ''
        for l in blines:
            t = ''.join(s['text'] for s in l['spans']).strip()
            if not t:
                continue
            if ptxt.endswith('-') and t[:1].islower():
                ptxt = ptxt[:-1] + t
            else:
                ptxt = (ptxt + ' ' + t).strip()
        if ptxt:
            sz = max(s['size'] for l in blines for s in l['spans'])
            paras.append({'t': ptxt, 'size': round(sz, 1), 'y': round(b['bbox'][1], 1), 'x': round(b['bbox'][0], 1)})
        widths = [l['bbox'][2] - l['bbox'][0] for l in blines]
        maxw = max(widths)
        for li, l in enumerate(blines):
            if abs(l['dir'][0]) < 0.9:                 # rotated text stays in the picture
                continue
            x0, y0, x1, y1 = l['bbox']
            spans = [s for s in l['spans'] if s['text']]
            if not spans:
                continue
            size = max(s['size'] for s in spans)
            segs = []
            for s in spans:
                t = s['text']
                if not t:
                    continue
                href = None
                sb = s['bbox']; sa = max(1e-6, (sb[2] - sb[0]) * (sb[3] - sb[1]))
                for r, u in uris:
                    if inter(sb, (r.x0, r.y0, r.x1, r.y1)) > 0.5 * sa:
                        href = u
                        break
                segs.append((t, span_style(s), href))
            if not segs:
                continue
            just = len(blines) >= 2 and li < len(blines) - 1 and widths[li] >= 0.985 * maxw
            attrs = ' data-w="%.1f"' % ((x1 - x0) * SCALE) + (' data-j="1"' if just else '')
            head = '<p style="position:absolute;left:%.1fpx;top:%.1fpx;font-size:%.1fpx;white-space:nowrap"%s>' % (
                x0 * SCALE, y0 * SCALE, size * SCALE, attrs)
            lines.append((head, segs, ''.join(t for t, _s, _h in segs)))
            redact.append(fitz.Rect(x0 - 0.5, y0 - 0.5, x1 + 0.5, y1 + 0.5))
    return lines, redact, paras


def render_line(head, segs):
    out = []
    for t, st, href in segs:
        inner = '<span style="%s">%s</span>' % (st, esc(t))
        out.append('<a href="%s" target="_blank" rel="noopener">%s</a>' % (html.escape(href, quote=True), inner) if href else inner)
    return head + ''.join(out) + '</p>'


def adlinks_html(ads):
    out = []
    for a in ads:
        out.append('<a class="adlink" href="../../out/%s/index.html" target="_blank" rel="noopener sponsored" '
                   'style="left:%.2f%%;top:%.2f%%;width:%.2f%%;height:%.2f%%" title="Visit %s" aria-label="Advertisement: %s"></a>'
                   % (a['slug'], a['l'], a['t'], a['w'], a['h'], html.escape(a['name'], quote=True), html.escape(a['name'], quote=True)))
    return out


def build(reader, issue, adir, label, pdf, what='all', ads=None):
    ads = ads or {}
    doc = fitz.open(pdf)
    hdir = os.path.join(reader, 'html', issue)
    adir_full = os.path.join(reader, 'assets', adir)
    os.makedirs(hdir, exist_ok=True); os.makedirs(adir_full, exist_ok=True)
    title = 'Australian Bee Journal, ' + label
    text = {}
    for pno in range(len(doc)):
        n = pno + 1
        page = doc[pno]
        W, H = page.rect.width, page.rect.height
        lines, redact, paras = page_lines(page)
        text[n] = {'paras': paras, 'lines': [tl for _h, _s, tl in lines]}
        if what in ('pages', 'all'):
            # the issue-strip image: the whole page, text and all
            pix = page.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=False)
            im = Image.frombytes('RGB', (pix.width, pix.height), pix.samples).resize((ASSET_W, ASSET_H), Image.LANCZOS)
            im.save(os.path.join(adir_full, 'p-%02d.jpg' % n), quality=ASSET_Q)
            # the overlay background: text lifted, pictures and rules kept
            bg = fitz.open(); bg.insert_pdf(doc, from_page=pno, to_page=pno)
            bp = bg[0]
            for r in redact:
                bp.add_redact_annot(r)
            bp.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, graphics=fitz.PDF_REDACT_LINE_ART_NONE,
                                text=fitz.PDF_REDACT_TEXT_REMOVE)
            bp.get_pixmap(matrix=fitz.Matrix(SCALE, SCALE), alpha=False).save(os.path.join(hdir, 'pg%03d.jpg' % n), jpg_quality=PAGE_Q)
            bg.close()
        pw, ph = round(W * SCALE), round(H * SCALE)
        wmm, hmm = W * PT_MM, H * PT_MM
        scaler = (wmm * 96 / 25.4) / pw
        body = [render_line(h, s) for h, s, _t in lines] + adlinks_html(ads.get(n, []))
        doc_html = (HEAD % dict(title=html.escape(title), n=n, wmm=wmm, hmm=hmm, scaler=scaler, pw=pw, ph=ph)
                    + '<img class="bg" src="pg%03d.jpg" alt="">\n' % n + '\n'.join(body) + '\n' + TAIL)
        open(os.path.join(hdir, '%d.html' % n), 'w', encoding='utf-8').write(doc_html)
        print('p%-3d %3d lines %3d paras  %s' % (n, len(lines), len(paras), (paras[0]['t'][:60] if paras else '')))
    json.dump(text, open(os.path.join(reader, '_build', '%s_text.json' % issue), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('%d pages -> %s, %s' % (len(doc), hdir, adir_full))
    doc.close()


if __name__ == '__main__':
    reader, issue, adir, label, pdf = sys.argv[1:6]
    what = sys.argv[6] if len(sys.argv) > 6 else 'all'
    adsfile = os.path.join(reader, '_build', '%s_ads.json' % issue)
    ads = {int(k): v for k, v in json.load(open(adsfile, encoding='utf-8')).items()} if os.path.exists(adsfile) else {}
    build(reader, issue, adir, label, pdf, what, ads)
