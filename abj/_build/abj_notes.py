"""Footnotes as hover text for the journal reader's already-built pages (html/<issue>/<n>.html).

The journal pages were built before the superscript flag was honoured, so a footnote marker sits in the text
as a separate span of plain digits glued to the word before it ("Queensland.1,2"). This finds those spans,
sets them as superscripts, and - where the article's notes can be found - wraps them for the hover card.
Notes are harvested with the same rules as the other readers (notes.harvest_lines), from the page lines.
Usage: python3 abj_notes.py <reader dir> <issue id>
"""
import re, sys, os, json, html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import notes

SCALE = 1.6
QUOTE_FIX = [('―', '“'), ('‖', '”'), ('ﬁ', 'fi'), ('ﬂ', 'fl')]
P_RE = re.compile(r'<p style="position:absolute;left:([\d.]+)px;top:([\d.]+)px;font-size:([\d.]+)px;white-space:nowrap"( data-w="([\d.]+)")?( data-j="1")?>(.*?)</p>', re.S)
SPAN_RE = re.compile(r'<span style="([^"]*)">(.*?)</span>', re.S)
MARK_SPAN = re.compile(r'^(\d{1,2}(?:,\d{1,2})*)(\s*)$')

def fix(t):
    for a, b in QUOTE_FIX: t = t.replace(a, b)
    return t

def page_lines(path, n):
    """Sewn lines (in pt) from one built page, for the note harvester."""
    s = open(path, encoding='utf-8').read()
    frags = []
    for m in P_RE.finditer(s):
        x, y, fs = float(m.group(1)), float(m.group(2)), float(m.group(3))
        w = float(m.group(5)) if m.group(5) else None
        spans = [(st, html.unescape(re.sub('<[^>]+>', '', t))) for st, t in SPAN_RE.findall(m.group(7))]
        text = fix(''.join(t for _, t in spans))
        if not text.strip(): continue
        sup = ''
        if spans and 'vertical-align:super' in spans[0][0]:
            mm = re.fullmatch(r'\s*(\d{1,2}|\*{1,3}|†|‡)\s*', spans[0][1])
            if mm: sup = mm.group(1)
        frags.append({'x': x, 'y': y, 'fs': fs, 'w': w, 'text': text, 'sup': sup})
    frags.sort(key=lambda f: (round(f['y']), f['x']))
    lines = []
    for f in frags:
        L = lines[-1] if lines else None
        if L and abs(L['ytop'] - f['y']) <= 1.5 and -2 <= f['x'] - L['xend'] < 25 and abs(L['fs'] - f['fs']) < 0.5 and (f['x'] < 470) == (L['x0'] < 470):
            L['text'] = (L['text'].rstrip() + ' ' + f['text'].lstrip()) if not L['text'].endswith(' ') and not f['text'].startswith(' ') else L['text'] + f['text']
            L['xend'] = f['x'] + (f['w'] or 0)
        else:
            lines.append({'n': n, 'x': f['x'] / SCALE, 'x0': f['x'], 'y': f['y'] / SCALE, 'ytop': f['y'], 'xend': f['x'] + (f['w'] or 0),
                          'fs': f['fs'], 'size': round(f['fs'] / SCALE * 2) / 2, 'text': f['text'], 'sup': f['sup']})
    return lines

def mark_page(path, NOTES, STARTS, n):
    s = open(path, encoding='utf-8').read()
    changed = 0; wrapped = 0
    def fix_line(m):
        nonlocal changed, wrapped
        body = m.group(7); spans = SPAN_RE.findall(body)
        if len(spans) < 2: return m.group(0)
        out = []; prev_txt = ''
        for i, (st, t) in enumerate(spans):
            raw = html.unescape(re.sub('<[^>]+>', '', t))
            mm = MARK_SPAN.match(raw)
            if mm and i > 0 and re.search(r'[A-Za-z.,;:!?)”‖\]]$', prev_txt.rstrip()) and 'vertical-align:super' not in st and (n, round(float(m.group(2)) / SCALE)) not in STARTS:
                marks = mm.group(1); tail = mm.group(2)
                inner = '<span style="%s;vertical-align:super;font-size:.7em">%s</span>' % (st, marks)
                note = notes.note_for(marks.split(','), NOTES)
                if note:
                    inner = '<span class="fn" tabindex="0" data-n="%s" data-note="%s" aria-label="Note %s: %s">%s</span>' % (
                        html.escape(marks, quote=True), html.escape(note, quote=True), html.escape(marks, quote=True), html.escape(note, quote=True), inner)
                    wrapped += 1
                out.append(inner + ('<span style="%s">%s</span>' % (st, tail) if tail else ''))
                changed += 1
            else:
                out.append('<span style="%s">%s</span>' % (st, t))
            prev_txt = raw
        return m.group(0)[:m.start(7) - m.start(0)] + ''.join(out) + '</p>'
    s2 = P_RE.sub(fix_line, s)
    if changed:
        if '.fnpop{' not in s2:
            s2 = s2.replace('</style>', notes.CSS + '</style>', 1)
            s2 = s2.replace('</body>', '<script>' + notes.JS + '</script>\n</body>', 1) if '</body>' in s2 else s2 + '<script>' + notes.JS + '</script>'
        open(path, 'w', encoding='utf-8').write(s2)
    return changed, wrapped

def main(reader, issue):
    idx = open(os.path.join(reader, 'index.html'), encoding='utf-8').read()
    D = json.loads(re.search(r'const D=(\{.*?\});\n', idx, re.S).group(1))
    iss = next(i for i in D['issues'] if i['id'] == issue)
    arts = [a for a in D['arts'] if a['issue'] == issue]
    hdir = os.path.join(reader, 'html', issue)
    tot_notes = tot_marks = tot_wrapped = 0
    for a in arts:
        pages = [p for p in range(a['p'], (a.get('end') or a['p']) + 1) if p in iss['html'] and p not in (a.get('skip') or [])]
        if not pages: continue
        lines = []
        for k, p in enumerate(pages, start=1): lines += page_lines(os.path.join(hdir, '%d.html' % p), k)
        NOTES, STARTS = notes.harvest_lines(lines)
        NOTES = {k: fix(v) for k, v in NOTES.items()}
        marks = wrapped = 0
        for k, p in enumerate(pages, start=1):
            c, w = mark_page(os.path.join(hdir, '%d.html' % p), NOTES, STARTS, k); marks += c; wrapped += w
        if marks or NOTES:
            print('%-52s pages %s: %d markers set superscript, %d with hover; notes %s' % (a['t'][:52], pages, marks, wrapped, ', '.join(sorted(NOTES, key=lambda k: (len(k), k))) or '-'))
        tot_notes += len(NOTES); tot_marks += marks; tot_wrapped += wrapped
    print('total: %d notes, %d markers, %d hoverable' % (tot_notes, tot_marks, tot_wrapped))

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
