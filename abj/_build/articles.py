#!/usr/bin/env python3
"""Article records and pages for one issue, the way August's were made.

Reads _build/<issue>_arts.json (title, p, end, skip, author, tags; an optional
"item" number for several Bee Bits sharing one page) and _build/<issue>_text.json
(from build_issue.py), then:
  - appends the records to `const D={...}` in index.html (slug = <issue>-<title>)
  - writes article/<slug>/index.html, the static text version of each article,
    using the CSS block of an existing article page verbatim
  - adds an issue section to article/index.html
  - adds the pages to sitemap.xml

    python articles.py <reader dir> <issue id> "<label>"
"""
import difflib
import datetime, html, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import issue_record

SITE = 'https://abj.org.au/reader/'
DESC_N = 157                      # August: 157 characters of text, then an ellipsis
FOLIO = re.compile(r'^\d+\s*\|\s*Published since 1918|^VAA AUSTRALIAN BEE JOURNAL\s*\||^INDUSTRY UPDATES FROM THE AHBIC NEWSLETTER$', re.I)
NOTE = re.compile(r'^\*\*Kris:|^Natalie:')          # layout notes left in the draft

def slugify(t):
    return re.sub(r'[^a-z0-9]+', '-', t.lower()).strip('-')

def esc(t):
    return html.escape(t, quote=True)

def topic_href(tag):
    return '../../index.html#/topic/' + esc(tag.replace(' ', '%20'))

def body_size(paras):
    c = {}
    for p in paras:
        c[p['size']] = c.get(p['size'], 0) + len(p['t'])
    return max(c, key=c.get) if c else 9.5

def norm(s):
    return re.sub(r'\W+', ' ', s).strip().lower()

def article_blocks(rec, text):
    """[(kind, text)] for the article: 'h2' for display-size lines, 'p' otherwise."""
    out = []
    pages = [p for p in range(rec['p'], rec['end'] + 1) if p not in (rec.get('skip') or [])]
    title = norm(rec['t'])
    for k, pno in enumerate(pages):
        paras = [p for p in text[str(pno)]['paras'] if not FOLIO.match(p['t']) and not NOTE.match(p['t'])]
        paras.sort(key=lambda p: (p['x'] > 300, p['y']))   # left column, then right
        bs = body_size(paras)
        if rec.get('item'):
            # One of several short items sharing a page. Its slice runs from its
            # own heading to the next one.
            #
            # Headings are found by size RELATIVE to the body text, not by a
            # fixed 11.5-15pt band: September set the Bee Bits headings at
            # 18-30pt, the band matched nothing, and all five items silently
            # received the whole page. A heading may also wrap over several
            # paragraphs, so consecutive big ones are grouped into one.
            big = [i for i, p in enumerate(paras)
                   if p['size'] >= max(11.5, 1.6 * bs) and len(p['t']) < 120]
            groups = []
            for i in big:
                if groups and i == groups[-1][-1] + 1:
                    groups[-1].append(i)
                else:
                    groups.append([i])
            # Match this record to ITS heading by title rather than by ordinal.
            # The ordinal assumes a column order that re-layout can change.
            want = norm(re.sub(r'^Bee Bit:\s*', '', rec['t'])).lower()
            best, score = None, 0.0
            for gi, g in enumerate(groups):
                cand = norm(' '.join(paras[j]['t'] for j in g)).lower()
                r1 = difflib.SequenceMatcher(None, want, cand).ratio()
                r2 = difflib.SequenceMatcher(None, want[:len(cand)], cand).ratio()
                sc = max(r1, r2)
                if sc > score:
                    best, score = gi, sc
            n = best if (best is not None and score >= 0.45) else rec['item'] - 1
            if n is not None and n < len(groups):
                stop = groups[n + 1][0] if n + 1 < len(groups) else len(paras)
                paras = paras[groups[n][-1] + 1:stop]
        for p in paras:
            t = p['t'].replace('\xa0', ' ').strip()
            if not t:
                continue
            if k == 0 and (norm(t) == title or p['size'] >= 24):
                continue                                    # the headline itself (display size)
            if k == 0 and rec.get('author') and re.match(r'(By|by)\s', t) and len(t) < 120:
                continue                                    # the byline
            kind = 'h2' if p['size'] >= 1.3 * bs and len(t) < 120 else 'p'
            out.append((kind, t))
    return out

def page_html(rec, label, iid, blocks, css):
    slug = rec['slug']
    text = ' '.join(t for k, t in blocks if k == 'p')
    desc = text if len(text) <= DESC_N else text[:DESC_N] + '…'
    ld = {'@context': 'https://schema.org', '@type': 'Article', 'headline': rec['t'],
          'isPartOf': {'@type': 'PublicationIssue', 'issueNumber': label, 'name': 'Australian Bee Journal'},
          'publisher': {'@type': 'Organization', 'name': "Victorian Apiarists' Association", 'url': 'https://vicbeekeepers.com.au/'},
          'url': SITE + 'article/%s/' % slug, 'keywords': ', '.join(rec['tags']), 'pagination': str(rec['p'])}
    if rec.get('author'):
        ld['author'] = {'@type': 'Person', 'name': rec['author']}
    meta = ''
    if rec.get('author'):
        meta = '<a href="../../index.html#/author/%s">%s</a> &middot; ' % (esc(rec['author'].replace(' ', '%20')), esc(rec['author']))
    meta += 'Page %d &middot; %s' % (rec['p'], esc(label))
    body = '\n'.join('<%s>%s</%s>' % (k, esc(t), k) for k, t in blocks)
    tags = '<div class="tags">' + ' '.join('<a class="tag" href="%s">%s</a>' % (topic_href(t), esc(t)) for t in rec['tags']) + '</div>\n'
    return ('<!doctype html><html lang="en-AU"><head>\n'
            '<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">\n'
            '<title>%(title)s — %(label)s | Australian Bee Journal</title>\n'
            '<meta name="description" content="%(desc)s">\n'
            '<link rel="canonical" href="%(url)s">\n'
            '<meta property="og:type" content="article"><meta property="og:title" content="%(title)s">\n'
            '<meta property="og:description" content="%(desc)s"><meta property="og:url" content="%(url)s">\n'
            '<meta property="og:site_name" content="Australian Bee Journal">\n'
            '<script type="application/ld+json">%(ld)s</script>\n'
            '%(css)s</head><body><div class="w">\n'
            '<div class="bc"><a href="../../index.html">Australian Bee Journal</a> &nbsp;&rsaquo;&nbsp; <a href="../../index.html#/issue/%(iid)s">%(label)s</a></div>\n'
            '<h1>%(title)s</h1>\n'
            '<div class="meta">%(meta)s</div>\n'
            '%(body)s\n'
            '%(tags)s'
            '<a class="cta" href="../../index.html#/article/%(slug)s">Read this in the journal &rsaquo;</a>\n'
            '<div class="note">Published by the Victorian Apiarists\' Association. This page is a text version; the journal reader shows the article as laid out.</div>\n'
            '</div>\n'
            '<script>\n'
            '/* Send a human visitor into the reader. Crawlers and no-JS visitors keep the text above. */\n'
            '(function(){try{\n'
            '  if(location.hash) return;\n'
            "  if(sessionStorage.getItem('abj_nofwd')) return;\n"
            "  location.replace('../../index.html#/article/%(slug)s');\n"
            '}catch(e){}})();\n'
            '</script>\n'
            '</body></html>') % dict(title=esc(rec['t']), label=esc(label), desc=esc(desc), url=SITE + 'article/%s/' % slug,
                                    ld=json.dumps(ld, ensure_ascii=False), css=css, iid=iid, meta=meta, body=body, tags=tags, slug=slug)

def main(reader, iid, label):
    recs = json.load(open(os.path.join(reader, '_build', '%s_arts.json' % iid), encoding='utf-8'))
    text = json.load(open(os.path.join(reader, '_build', '%s_text.json' % iid), encoding='utf-8'))
    for r in recs:
        r['slug'] = iid + '-' + slugify(r['t'])
        if r['t'].lower() in ('advertisement', 'advertisements'):
            r['slug'] += '-p%d' % r['p']                   # August: aug-advertisement-p15
    seen = {}
    for r in recs:
        if r['slug'] in seen:                               # same title twice: page tells them apart
            r['slug'] += '-p%d' % r['p']
        seen[r['slug']] = 1
    # folders from an earlier run of this issue whose slug has since changed
    keep = {r['slug'] for r in recs}
    adir = os.path.join(reader, 'article')
    for d in os.listdir(adir):
        if d.startswith(iid + '-') and d not in keep and os.path.isdir(os.path.join(adir, d)):
            try:
                os.remove(os.path.join(adir, d, 'index.html'))
                os.rmdir(os.path.join(adir, d))
                print('   removed stale article folder', d)
            except OSError:
                # the folder cannot be deleted from here (Windows-backed mount):
                # leave a redirect to the issue's article list so an old link
                # still lands somewhere sensible, and say so
                open(os.path.join(adir, d, 'index.html'), 'w', encoding='utf-8').write(
                    '<!DOCTYPE html><meta charset="utf-8"><meta name="robots" content="noindex">'
                    '<meta http-equiv="refresh" content="0;url=../index.html"><title>Moved</title>'
                    '<a href="../index.html">This article has moved</a>')
                print('   STALE article folder %s could not be deleted - left a redirect; delete it by hand' % d)

    # 1. records in D, August's key order
    path, s, m, D = issue_record.load(reader)
    D['arts'] = [a for a in D['arts'] if a['issue'] != iid]
    for r in recs:
        a = {'issue': iid, 't': r['t'], 'p': r['p'], 'end': r['end'], 'tags': r['tags'], 'author': r.get('author', ''), 'slug': r['slug']}
        if r.get('skip'):
            a['skip'] = r['skip']
        D['arts'].append(a)
    issue_record.save(path, s, m, D)
    print('D: %d records for %s (%d in all)' % (len(recs), iid, len(D['arts'])))

    # 2. pages
    ref = open(os.path.join(reader, 'article', 'aug-president-s-report', 'index.html'), encoding='utf-8').read()
    css = ref[ref.index('<style>'):ref.index('</style>') + len('</style>')]
    for r in recs:
        blocks = article_blocks(r, text)
        d = os.path.join(reader, 'article', r['slug'])
        os.makedirs(d, exist_ok=True)
        open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(page_html(r, label, iid, blocks, css))
        print('   %-52s %2d blocks  %s' % (r['slug'][:52], len(blocks), (blocks[0][1][:50] if blocks else '(no text)')))

    # 3. article index
    ip = os.path.join(reader, 'article', 'index.html')
    idx = open(ip, encoding='utf-8').read()
    idx = re.sub(r'<section><h2>%s</h2>.*?</section>\n' % re.escape(label), '', idx, flags=re.S)
    items = ''.join('<li><a href="%s/index.html">%s</a><span>%s p%d</span></li>' % (r['slug'], esc(r['t']), esc(r.get('author', '')), r['p']) for r in recs)
    sec = '<section><h2>%s</h2><ol>%s</ol></section>\n' % (esc(label), items)
    idx = idx.replace('<a class="back"', sec + '<a class="back"', 1)
    open(ip, 'w', encoding='utf-8').write(idx)

    # 4. sitemap
    sp = os.path.join(reader, 'sitemap.xml')
    sm = open(sp, encoding='utf-8').read()
    today = datetime.date.today().isoformat()
    sm = re.sub(r'  <url><loc>%sarticle/%s-[^<]*</loc>.*?</url>\n' % (re.escape(SITE), iid), '', sm)
    new = ''.join('  <url><loc>%sarticle/%s/</loc><lastmod>%s</lastmod><priority>0.8</priority></url>\n' % (SITE, r['slug'], today) for r in recs)
    sm = sm.replace('</urlset>', new + '</urlset>')
    sm = re.sub(r'(<loc>%s(?:article/)?</loc><lastmod>)[^<]+' % re.escape(SITE), r'\g<1>' + today, sm)
    open(sp, 'w', encoding='utf-8').write(sm)
    print('article/index.html and sitemap.xml updated (%s)' % today)

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
