#!/usr/bin/env python3
"""Article records and text pages for the Geelong Beekeepers Club reader.

Reads _build/arts.json (every issue's records) and _build/<issue>_text.json (from
gbc_build.py), then:
  - bakes the records into `const D={...}` in index.html (slug = <issue>-<title>)
  - writes article/<slug>/index.html, a plain-text version of each article for search
    engines, screen readers and "Read as text"
  - writes article/index.html, sitemap.xml and robots.txt

Where several items share a page, each item's text runs from its own heading to the
next item's heading (headings are the rust-coloured display lines of the newsletter).

    python gbc_articles.py <reader dir>
"""
import datetime, difflib, html, json, os, re, sys

SITE = 'https://krisfricke.github.io/gbc/general/'
NAME = 'Geelong Beekeepers Club · General Beekeeping'
CLUB = 'Geelong Beekeepers Club Inc.'
CLUB_URL = 'https://geelongbeekeepersclub.org.au/'
NOTEXT = {'Cover', 'Advertisements', 'Classifieds', 'indexes', 'Documents'}
DESC_N = 157
# running matter that is not article text
SKIP = re.compile(r'^\d{4}-\d{2} Newsletter$|^© Geelong Beekeepers Club|^Our Club Details: ABN|^https?://\S+$', re.I)

def slugify(t): return re.sub(r'[^a-z0-9]+', '-', t.lower()).strip('-')
def esc(t): return html.escape(t, quote=True)
def norm(s): return re.sub(r'\W+', ' ', s).strip().lower()

def heading_groups(paras):
    """indices of display-size lines, consecutive ones grouped (a heading can wrap)"""
    big = [i for i, p in enumerate(paras) if p['size'] >= 17 and len(p['t']) < 160]
    groups = []
    for i in big:
        if groups and i == groups[-1][-1] + 1: groups[-1].append(i)
        else: groups.append([i])
    return groups

def match_heading(title, paras, groups):
    """index into groups of the heading that is this title; a run-in heading set at body size
    (the zone updates) is matched among all paragraphs instead and returned as a one-line group"""
    want = norm(re.sub(r'[:,].*$', '', title))          # "Seasonal Report, July 2026" -> "seasonal report"
    want_full = norm(title)
    best, score = None, 0.0
    for gi, g in enumerate(groups):
        cand = norm(' '.join(paras[j]['t'] for j in g))
        sc = max(difflib.SequenceMatcher(None, w, cand).ratio() for w in (want, want_full))
        if cand.startswith(want) or want.startswith(cand): sc = max(sc, 0.9)
        if sc > score: best, score = gi, sc
    if score >= 0.6: return best
    for i, p in enumerate(paras):
        if norm(p['t']).startswith(want_full) or (len(want) > 8 and norm(p['t']).startswith(want)):
            groups.append([i]); return len(groups) - 1
    return None

def article_blocks(rec, others_on_page, text):
    out = []
    for k, pno in enumerate(range(rec['p'], rec['end'] + 1)):
        paras = [p for p in text.get(str(pno), {'paras': []})['paras'] if not SKIP.match(p['t'].strip())]
        groups = heading_groups(paras)
        start, stop = 0, len(paras)
        if k == 0:
            g = match_heading(rec['t'], paras, groups)
            if g is not None: start = groups[g][-1] + 1
        # on the last page, stop at the heading of the next item that starts there (after our own start)
        if pno == rec['end']:
            nxt = [match_heading(o['t'], paras, groups) for o in others_on_page.get(pno, []) if o is not rec]
            nxt = [groups[g][0] for g in nxt if g is not None and groups[g][0] >= start]
            if nxt: stop = min(nxt)
        bs_counts = {}
        for p in paras[start:stop]: bs_counts[p['size']] = bs_counts.get(p['size'], 0) + len(p['t'])
        bs = max(bs_counts, key=bs_counts.get) if bs_counts else 11.4
        for p in paras[start:stop]:
            t = p['t'].replace('\xa0', ' ').strip()
            if not t: continue
            if k == 0 and rec.get('author') and re.match(r'\(?(By|by)\s', t) and len(t) < 80: continue
            if k == 0 and not out and (norm(t) in (norm(rec.get('author', '')), 'the conversation')): continue   # a bare byline or the source's name
            kind = 'h2' if (p['size'] >= 1.3 * bs and len(t) < 160) else 'p'
            out.append((kind, t))
    return out

CSS = '''<style>
:root{color-scheme:light}
body{margin:0;min-height:100vh;background:linear-gradient(180deg,#f3d14a 0%,#f8e67e 46%,#fdf4c6 100%) fixed;
 color:#1d1b16;font:16px/1.62 Lato,'Proxima Nova','Segoe UI',Arial,sans-serif;padding:34px 18px 70px}
.w{max-width:680px;margin:0 auto;background:#fffdf6;border-radius:12px;padding:34px 40px 36px;box-shadow:0 18px 50px rgba(90,70,10,.22)}
.bc{font:12px/1.5 system-ui,sans-serif;color:#6b5a2e;letter-spacing:.06em;text-transform:uppercase;margin-bottom:14px}
.bc a{color:#4a3a12;text-decoration:none}.bc a:hover{text-decoration:underline}
h1{font-size:30px;line-height:1.18;margin:0 0 8px;color:#993300;font-style:italic;font-weight:400}
h2{font:600 17px/1.35 system-ui,sans-serif;color:#7a5a1a;margin:1.7em 0 .5em}
.meta{font:13px/1.6 system-ui,sans-serif;color:#6b5a2e;margin:0 0 22px;border-bottom:1px solid #e9dfb8;padding-bottom:16px}
.meta a{color:#4a3a12;text-decoration:none}.meta a:hover{text-decoration:underline}
p{margin:0 0 .95em}
.tags{margin:26px 0 0;padding-top:16px;border-top:1px solid #e9dfb8}
.tag{display:inline-block;font:12px/1 system-ui,sans-serif;background:#fff8dc;border:1px solid #d9b84a;color:#2a2416;border-radius:14px;padding:5px 11px;margin:0 5px 6px 0;text-decoration:none}
.tag:hover{background:#f7c20b;border-color:#f7c20b;color:#111}
.cta{display:inline-block;margin-top:26px;background:#f7c20b;color:#111;font:700 14px/1 system-ui,sans-serif;padding:12px 20px;border-radius:7px;text-decoration:none}
.cta:hover{background:#ffd733}
.note{font:12px/1.6 system-ui,sans-serif;color:#8a7a4a;margin-top:30px}
ol{padding-left:22px}li{margin:0 0 6px}li span{color:#6b5a2e;font-size:13px;margin-left:8px}
section h2{color:#993300;font-style:italic;font-weight:400;font-size:22px;font-family:inherit}
@media(max-width:560px){.w{padding:24px 20px 28px}h1{font-size:25px}}
</style>'''

def page_html(rec, label, iid, blocks):
    slug = rec['slug']
    text = ' '.join(t for k, t in blocks if k == 'p')
    desc = text if len(text) <= DESC_N else text[:DESC_N] + '…'
    ld = {'@context': 'https://schema.org', '@type': 'Article', 'headline': rec['t'],
          'isPartOf': {'@type': 'PublicationIssue', 'issueNumber': label, 'name': NAME},
          'publisher': {'@type': 'Organization', 'name': CLUB, 'url': CLUB_URL},
          'url': SITE + 'article/%s/' % slug, 'keywords': ', '.join(rec['tags']), 'pagination': str(rec['p'])}
    if rec.get('author'): ld['author'] = [{'@type': 'Person', 'name': a.strip()} for a in rec['author'].split(',')]
    meta = ''
    if rec.get('author'):
        meta = ', '.join('<a href="../../index.html#/author/%s">%s</a>' % (esc(a.strip().replace(' ', '%20')), esc(a.strip())) for a in rec['author'].split(',')) + ' &middot; '
    meta += ('Pages %d–%d' % (rec['p'], rec['end']) if rec['end'] > rec['p'] else 'Page %d' % rec['p']) + ' &middot; ' + esc(label)
    body = '\n'.join('<%s>%s</%s>' % (k, esc(t), k) for k, t in blocks) or '<p><i>This item is a picture page; open it in the reader.</i></p>'
    tags = '<div class="tags">' + ' '.join('<a class="tag" href="../../index.html#/topic/%s">%s</a>' % (esc(t.replace(' ', '%20')), esc(t)) for t in rec['tags']) + '</div>\n'
    return ('<!doctype html><html lang="en-AU"><head>\n<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n'
            '<title>%(title)s — %(label)s | %(name)s</title>\n<meta name="description" content="%(desc)s">\n'
            '<link rel="canonical" href="%(url)s">\n<meta property="og:type" content="article"><meta property="og:title" content="%(title)s">\n'
            '<meta property="og:description" content="%(desc)s"><meta property="og:url" content="%(url)s">\n<meta property="og:site_name" content="%(name)s">\n'
            '<script type="application/ld+json">%(ld)s</script>\n%(css)s</head><body><div class="w">\n'
            '<div class="bc"><a href="../../index.html">%(name)s</a> &nbsp;&rsaquo;&nbsp; <a href="../../index.html#/issue/%(iid)s">%(label)s</a></div>\n'
            '<h1>%(title)s</h1>\n<div class="meta">%(meta)s</div>\n%(body)s\n%(tags)s'
            '<a class="cta" href="../../index.html#/article/%(slug)s">Read this in the newsletter &rsaquo;</a>\n'
            '<div class="note">Published by the %(club)s. This page is a text version; the reader shows the item as laid out.</div>\n</div>\n'
            '<script>\n/* Send a human visitor into the reader. Crawlers and no-JS visitors keep the text above. */\n'
            "(function(){try{\n  if(location.hash) return;\n  if(sessionStorage.getItem('gbc_nofwd')) return;\n  location.replace('../../index.html#/article/%(slug)s');\n}catch(e){}})();\n</script>\n</body></html>"
            ) % dict(title=esc(rec['t']), label=esc(label), desc=esc(desc), url=SITE + 'article/%s/' % slug, ld=json.dumps(ld, ensure_ascii=False),
                     css=CSS, iid=iid, meta=meta, body=body, tags=tags, slug=slug, name=NAME, club=CLUB)

def main(reader):
    arts = json.load(open(os.path.join(reader, '_build', 'arts.json'), encoding='utf-8'))
    ip = os.path.join(reader, 'index.html'); s = open(ip, encoding='utf-8').read()
    m = re.search(r'^const D=(\{.*\});$', s, flags=re.M)
    D = json.loads(m.group(1))
    labels = {i['id']: i['label'] for i in D['issues']}
    D['arts'] = []
    today = datetime.date.today().isoformat()
    sections, urls = [], []
    for iid in [i['id'] for i in D['issues']]:
        recs = arts.get(iid, [])
        text = json.load(open(os.path.join(reader, '_build', '%s_text.json' % iid), encoding='utf-8'))
        seen = {}
        for r in recs:
            r['slug'] = iid + '-' + slugify(r['t'])
            if r['slug'] in seen: r['slug'] += '-p%d' % r['p']
            seen[r['slug']] = 1
            D['arts'].append({'issue': iid, 't': r['t'], 'p': r['p'], 'end': r['end'], 'tags': r['tags'], 'author': r.get('author', ''), 'slug': r['slug']})
        on = {}
        for r in recs:
            for p in range(r['p'], r['end'] + 1): on.setdefault(p, []).append(r)
        items = ''
        for r in recs:
            d = os.path.join(reader, 'article', r['slug']); os.makedirs(d, exist_ok=True)
            blocks = [] if set(r['tags']) & NOTEXT else article_blocks(r, on, text)
            open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(page_html(r, labels[iid], iid, blocks))
            print('  %-60s %2d blocks  %s' % (r['slug'][:60], len(blocks), (blocks[0][1][:50] if blocks else '(no text)')))
            items += '<li><a href="%s/index.html">%s</a><span>%s p%d</span></li>' % (r['slug'], esc(r['t']), esc(r.get('author', '')), r['p'])
            urls.append('  <url><loc>%sarticle/%s/</loc><lastmod>%s</lastmod><priority>0.8</priority></url>\n' % (SITE, r['slug'], today))
        sections.append('<section><h2>%s</h2><ol>%s</ol></section>\n' % (esc(labels[iid]), items))
    s = s[:m.start()] + 'const D=' + json.dumps(D, ensure_ascii=False, separators=(',', ':')) + ';' + s[m.end():]
    open(ip, 'w', encoding='utf-8').write(s)
    print('D: %d records' % len(D['arts']))
    idx = ('<!doctype html><html lang="en-AU"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n'
           '<title>All articles | %s</title><link rel="canonical" href="%sarticle/">%s</head><body><div class="w">\n'
           '<div class="bc"><a href="../index.html">%s</a> &nbsp;&rsaquo;&nbsp; All articles</div><h1>Every item, by issue</h1>\n%s'
           '<a class="cta back" href="../index.html">Open the reader &rsaquo;</a></div></body></html>') % (NAME, SITE, CSS, NAME, ''.join(reversed(sections)))
    open(os.path.join(reader, 'article', 'index.html'), 'w', encoding='utf-8').write(idx)
    sm = ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          '  <url><loc>%s</loc><lastmod>%s</lastmod><priority>1.0</priority></url>\n  <url><loc>%sarticle/</loc><lastmod>%s</lastmod><priority>0.6</priority></url>\n'
          % (SITE, today, SITE, today) + ''.join(urls) + '</urlset>\n')
    open(os.path.join(reader, 'sitemap.xml'), 'w', encoding='utf-8').write(sm)
    open(os.path.join(reader, 'robots.txt'), 'w', encoding='utf-8').write('User-agent: *\nAllow: /\nSitemap: %ssitemap.xml\n' % SITE)
    print('article/index.html, sitemap.xml, robots.txt written')

if __name__ == '__main__':
    main(sys.argv[1])
