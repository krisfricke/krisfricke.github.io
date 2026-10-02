#!/usr/bin/env python3
"""Turn the contents-page tiles into page jumps.

In the PDF every tile on page 2 links to the newsletter's web page (eNews.asp?id=N#ArticleM).
Inside the reader those should go to the page the item is on. The tile's words say which item it
is, so: match each #ArticleM link's text to a record in arts.json, learn M -> page, and rewrite
every anchor carrying that M (the picture hotspots too) as an in-reader jump.

    python gbc_toc_links.py <reader dir>
"""
import difflib, json, os, re, sys

def norm(s): return re.sub(r'\W+', ' ', s).strip().lower()

def main(reader):
    arts = json.load(open(os.path.join(reader, '_build', 'arts.json'), encoding='utf-8'))
    for iid, recs in arts.items():
        if iid.startswith('_'): continue
        hdir = os.path.join(reader, 'html', iid)
        titles = [(norm(re.sub(r'[:,].*$', '', r['t'])), norm(r['t']), r['p'], r.get('tags', [])) for r in recs]
        for fn in sorted(os.listdir(hdir)):
            if not fn.endswith('.html'): continue
            path = os.path.join(hdir, fn); s = open(path, encoding='utf-8').read()
            if '#Article' not in s: continue
            # 1. learn M -> page: the tile's words arrive as one anchor per span, so gather them per M first
            frags = {}
            for m in re.finditer(r'<a href="[^"]*#Article(\d+)"[^>]*>(.*?)</a>', s):
                frags.setdefault(m.group(1), []).append(re.sub(r'<[^>]+>', '', m.group(2)))
            jump = {}
            for M, parts in frags.items():
                words = norm(' '.join(parts))
                if len(words) < 3: continue
                best, score = None, 0.0
                for short, full, p, tags in titles:
                    sc = max(difflib.SequenceMatcher(None, words, full).ratio(), difflib.SequenceMatcher(None, words, short).ratio())
                    if len(words) >= 8 and (full.startswith(words) or short.startswith(words) or words.startswith(short)): sc = max(sc, 0.85)
                    if words in [norm(t) for t in tags]: sc = max(sc, 0.8)          # "The Conversation" names the source, tagged on the record
                    if sc > score: best, score = p, sc
                if score >= 0.55: jump[M] = best
            # 2. rewrite every anchor with a learned M
            def rep(m):
                M = m.group(2)
                if M not in jump: return m.group(0)
                p = jump[M]
                attrs = m.group(3)
                attrs = re.sub(r'\s+target="[^"]*"|\s+rel="[^"]*"|\s+title="[^"]*"|\s+aria-label="[^"]*"', '', attrs)
                cls = ' hot' if 'class="hot"' in m.group(0) else ''
                attrs = re.sub(r'\s+class="[^"]*"', '', attrs)
                return '<a class="ixlink%s" href="../../#/page/%s/%d" target="_top" title="Go to page %d"%s>' % (cls, iid, p, p, attrs)
            n0 = s.count('#Article')
            s = re.sub(r'<a (class="[^"]*" )?href="[^"]*#Article(\d+)"([^>]*)>', rep, s)
            open(path, 'w', encoding='utf-8').write(s)
            print('%s/%s: %d tile links -> %d page jumps (%d items)' % (iid, fn, n0, n0 - s.count('#Article'), len(jump)))

if __name__ == '__main__':
    main(sys.argv[1])
