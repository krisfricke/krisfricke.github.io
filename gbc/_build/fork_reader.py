#!/usr/bin/env python3
"""Make the Geelong Beekeepers Club reader's index.html from the Australian Bee Journal reader's.

The ABJ reader is the base: same page stack, rails, author/topic browsing, lanes and bee.
This script rewrites what is VAA-specific - name, masthead, palette, the western seam
(which now leads to geelongbeekeepersclub.org.au), the pointer (the bee, always), the
storage keys and the baked data - and leaves everything else exactly as it is, so fixes
to the ABJ reader can be carried across by running it again.

    python fork_reader.py <ABJ reader dir> <GBC reader dir>

The article records come from _build/arts.json via gbc_articles.py, which also writes
the text versions; run that after this.
"""
import json, os, re, sys

SITE = 'https://geelongbeekeepersclub.org.au/'          # the club's own site: the western seam
READER_URL = 'https://krisfricke.github.io/gbc/'        # where the mock-up will be published (share links)
ISSUES = [('jul', 'July 2026', '2026-07 Newsletter', 28), ('aug', 'August 2026', '2026-08 Newsletter', 30),
          ('sep', 'September 2026', '2026-09 Newsletter', 32)]

def main(src, dst):
    s = open(os.path.join(src, 'index.html'), encoding='utf-8').read()
    lines = s.split('\n')

    # ---- baked data: issues and (for now) no records; gbc_articles.py fills D.arts ----
    issues = []
    for iid, label, vol, n in ISSUES:
        issues.append({'id': iid, 'label': label, 'vol': vol, 'dir': iid,
                       'pages': ['p-%02d.jpg' % k for k in range(1, n + 1)], 'cover': 'assets/%s/p-01.jpg' % iid,
                       'html': list(range(1, n + 1)), 'index': 2})
    issues[-1]['current'] = True
    D = {'issues': issues, 'arts': []}
    for i, ln in enumerate(lines):
        if ln.startswith('const D='): lines[i] = 'const D=' + json.dumps(D, ensure_ascii=False, separators=(',', ':')) + ';'
        if ln.startswith('const LINKS='): lines[i] = 'const LINKS={};   /* page links live inside the page documents themselves */'
    s = '\n'.join(lines)

    def sub(a, b, count=1, must=True):
        nonlocal s
        if must and a not in s: raise SystemExit('fork: pattern not found: %r' % a[:70])
        s = s.replace(a, b, count if count else -1)

    # ---- head ----
    sub('<title>Australian Bee Journal</title>', '<title>Geelong Beekeepers Club Newsletter</title>')
    sub('''<!-- MOCKUP GATE - delete this line and gate.js to ship the real thing.
     Dormant on file:// and localhost, so it only bites once published. -->
<script src="gate.js?v=3"></script>
<!-- bump ?v= whenever gate.js changes, or browsers keep serving the old one -->
''', '')
    # the pointer: the bee, always (no brand shard here)
    s = re.sub(r'<script>/\* THE POINTER\..*?\)\(\);</script>', "<script>window.ABJ_CURSOR='bee';</script>", s, count=1, flags=re.S)
    sub('<meta name="description" content="The Australian Bee Journal, published by the Victorian Apiarists\' Association since 1918. Read current and past issues, browse by topic and author.">',
        '<meta name="description" content="The Geelong Beekeepers Club newsletter: read current and past issues, browse by topic and author.">')
    s = re.sub(r'<link rel="icon"[^>]*>\n<link rel="icon"[^>]*>\n<link rel="apple-touch-icon"[^>]*>\n<link rel="shortcut icon"[^>]*>',
               '<link rel="icon" type="image/png" sizes="64x64" href="assets/favicon.png">', s, count=1)

    # ---- palette: honey and comb instead of sky ----
    sub(':root{--chromeH:58px;--gold:#f9c500;--paper:#faf8f2;--navy:#1f3a5f;--bg:#a9d2ec;\n  --ink:#14293b;--ink2:#3d6079;--sky1:#7db4dc;--sky2:#a9d2ec;--sky3:#d3e8f7}',
        ':root{--chromeH:58px;--gold:#f7c20b;--paper:#fffdf4;--navy:#3b2f12;--bg:#f8e67e;\n  --ink:#2a2412;--ink2:#6b5a2e;--sky1:#f3d14a;--sky2:#f8e67e;--sky3:#fdf4c6}')
    # one tile = one pointy-top hexagon plus the vertical edge below it; with the tile w x 3s (w = sqrt(3) s)
    # the half-row offset falls out of the tiling by itself, so the comb is continuous
    HEX = ('<svg xmlns=\'http://www.w3.org/2000/svg\' width=\'56\' height=\'97\' viewBox=\'0 0 56 97\'>'
           '<path d=\'M28 0 L56 16.17 L56 48.5 L28 64.66 L0 48.5 L0 16.17 Z M28 64.66 L28 97\' '
           'fill=\'none\' stroke=\'%23000\' stroke-opacity=\'.055\' stroke-width=\'1.4\'/></svg>')
    sub('body{margin:0;background:linear-gradient(180deg,var(--sky1) 0%,var(--sky2) 46%,var(--sky3) 100%) fixed;',
        'body{margin:0;background:url("data:image/svg+xml;utf8,' + HEX + '") fixed,linear-gradient(180deg,var(--sky1) 0%,var(--sky2) 46%,var(--sky3) 100%) fixed;')
    for a, b in [('#2f6d92', '#8a6a12'), ('#7ea9c6', '#d9b84a'), ('#6f9cbb', '#c9a93d'), ('#3d6079', '#6b5a2e'), ('#1f4b68', '#4a3a12'),
                 ('#17313f', '#2a2416'), ('#1c4258', '#3b2f1a'), ('#55748d', '#7a6a3a'), ('#12303f', '#221c10'), ('#1b4a6b', '#4a3a12'),
                 ('#2f5876', '#6b5a2e'), ('#f3f8fc', '#fffbe8'), ('#4aa3ff', '#f7c20b'),
                 ('rgba(80,170,255,.42)', 'rgba(247,194,11,.42)'), ('rgba(30,70,100,.35)', 'rgba(90,70,20,.35)'), ('rgba(30,70,100', 'rgba(90,70,20')]:
        s = s.replace(a, b)

    # ---- chrome ----
    sub('<a class="mast" href="#" onclick="gotoCover();return false" title="Australian Bee Journal"><img src="assets/vaa_masthead_approved.png" alt="Australian Bee Journal — Victorian Apiarists\' Association Inc"></a>',
        '<a class="mast" href="#" onclick="gotoCover();return false" title="Geelong Beekeepers Club Newsletter"><img src="assets/gbc_logo.png" alt="Geelong Beekeepers Club Inc."></a>')
    sub('.mast img{height:53px;display:block;margin:0}', '.mast img{height:44px;display:block;margin:7px 0 0 10px;border-radius:4px}')
    sub('<a class="t sub" href="https://vicbeekeepers.com.au/join-us" target="_blank" rel="noopener">Subscribe</a>',
        '<a class="t sub" href="https://geelongbeekeepersclub.org.au/" target="_blank" rel="noopener">Join the club</a>')
    sub('<h2 id="ititle">Australian Bee Journal</h2>', '<h2 id="ititle">Geelong Beekeepers Club Newsletter</h2>')
    sub('title="Go to the VAA main site"><span class="chev" aria-hidden="true"></span><span class="lbl">VAA Main Page</span>',
        'title="Go to the Geelong Beekeepers Club website"><span class="chev" aria-hidden="true"></span><span class="lbl">GBC Main Site</span>')
    # the western seam
    s = re.sub(r'<div class="lane" id="laneL"><div class="vaagate">.*?</div></div>\n  <div class="lane" id="lane0">', '''<div class="lane" id="laneL"><div class="vaagate">
    <div class="band"><img src="assets/gbc_logo.png" alt="" style="height:64px;border-radius:4px"><div><h2>Geelong Beekeepers Club Inc.</h2><div class="dom">GEELONGBEEKEEPERSCLUB.ORG.AU</div></div></div>
    <p>You&rsquo;ve reached the newsletter&rsquo;s western edge. From here the club&rsquo;s own website carries on &mdash; meetings, courses, the members&rsquo; area and the Varroa resources.</p>
    <div class="links"><span>Meetings</span><span>Courses</span><span>Membership</span><span>In the Hive</span><span>Edu Hub</span></div>
    <button class="back" onclick="setLane(0)">to the newsletter &rsaquo;</button>
    <p class="handoff">Taking you to geelongbeekeepersclub.org.au&hellip;</p>
  </div></div>
  <div class="lane" id="lane0">''', s, count=1, flags=re.S)
    sub("setTimeout(function(){ location.href='https://vicbeekeepers.com.au/'; },780);   /* slide, then hand over to the VAA's own site */",
        "setTimeout(function(){ location.href='%s'; },780);   /* slide, then hand over to the club's own site */" % SITE)
    sub('.vaagate .band img{height:56px}', '.vaagate .band img{height:64px}')
    # the band's label is the gold on the VAA; the logo is already yellow, so the band goes dark
    sub('.vaagate .band{display:flex;gap:16px;align-items:center;background:var(--gold);', '.vaagate .band{display:flex;gap:16px;align-items:center;background:#111;color:#fff;')
    sub('.vaagate h2{margin:0;font-size:24px;color:#111;text-align:left}', '.vaagate h2{margin:0;font-size:24px;color:#fff;text-align:left}')
    sub('.vaagate .dom{font-size:12.5px;color:#6a5600;text-align:left;letter-spacing:.06em}', '.vaagate .dom{font-size:12.5px;color:var(--gold);text-align:left;letter-spacing:.06em}')

    # ---- storage keys, share address, labels ----
    for a, b in [("'abj_editor'", "'gbc_editor'"), ("'abj_tags_v2'", "'gbc_tags_v1'"), ("'abj_zoom'", "'gbc_zoom'"), ("'abj_intro_v1'", "'gbc_intro_v1'"),
                 ("a.download='ABJ_tags.json'", "a.download='GBC_tags.json'"),
                 ("const dir=local ? 'https://abj.org.au/reader/'", "const dir=local ? '%s'" % READER_URL),
                 ("+'\\nIt will work once the reader is published at abj.org.au/reader/.'", "+'\\nIt will work once the reader is published at %s.'" % READER_URL.replace('https://', '')),
                 ("const NOTEXT=['Cover','Advertisements','VAA Advertisements','Classifieds','indexes'];", "const NOTEXT=['Cover','Advertisements','Classifieds','indexes'];"),
                 ("' issues — a special issue assembled from the archive'", "' issues — a special issue assembled from past newsletters'"),
                 ("<div class=\"hint\">▼ scroll down to read — topics appear beside each page</div>", "<div class=\"hint\">▼ scroll down to read — topics appear beside each page</div>")]:
        sub(a, b)
    s = s.replace('abj_nofwd', 'gbc_nofwd').replace("'abj_editor'", "'gbc_editor'").replace("'abj_zoom'", "'gbc_zoom'")
    s = s.replace(' · \'+it.vol+\'', ' · \'+it.vol+\'')   # (label · vol) kept: "July 2026 · 2026-07 Newsletter"


    # ---- closed issues sit on a short stack of pages (six, whatever the issue's real length) ----
    sub('.arc img{max-height:58vh;border:5px solid #fff;box-shadow:0 16px 44px rgba(0,0,0,.5);transition:transform .15s}',
        '.arc img{max-height:58vh;border:5px solid #fff;transition:transform .15s;margin:0 18px 18px 0;\n'
        ' box-shadow:2px 2px 0 0 #cfc7b2,3px 3px 0 0 #fff,5px 5px 0 0 #cfc7b2,6px 6px 0 0 #fff,8px 8px 0 0 #cfc7b2,9px 9px 0 0 #fff,\n'
        '  11px 11px 0 0 #cfc7b2,12px 12px 0 0 #fff,14px 14px 0 0 #cfc7b2,15px 15px 0 0 #fff,17px 17px 0 0 #bfb79f,18px 18px 0 0 #fff,22px 30px 44px rgba(0,0,0,.45)}')
    # ---- the interface credit, bottom left over the background ----
    sub('<div class="zoombar" role="group" aria-label="Page size">',
        '<a class="credit" href="https://krisfricke.github.io/" target="_blank" rel="noopener" title="About the reader">Hivejournal Interface &copy; Kris Fricke 2026</a>\n<div class="zoombar" role="group" aria-label="Page size">')
    s = s.replace('</style></head><body>', '.credit{position:fixed;left:14px;bottom:10px;z-index:70;font:11.5px/1 system-ui,sans-serif;color:rgba(40,30,0,.6);text-decoration:none;letter-spacing:.03em;padding:5px 8px;border-radius:6px}\n.credit:hover{color:#111;background:rgba(255,255,255,.55);text-decoration:underline}\n</style></head><body>', 1)
    # ---- a click on the bare background goes back to the issue's contents page ----
    sub("window.addEventListener('hashchange',route);",
        "/* a click on the bare background - not a page, card, rail or control - goes back to the contents page */\n"
        "document.getElementById('lane0').addEventListener('click',function(e){\n"
        "  if(e.target.closest('.page,.arc,.cov,.rail,.chrome,.edge,.zoombar,.credit,button,a,input,iframe,img')) return;\n"
        "  if(tagMode) return;\n"
        "  gotoIndex();\n"
        "});\n"
        "window.addEventListener('hashchange',route);")

    # ---- lightbox: a picture that fails to load from the website falls back to the copy in the reader ----
    sub("    img.src=m.src; img.alt=m.alt||''; cap.textContent=m.alt||'';",
        "    img.onerror=function(){ if(m.fallback&&img.getAttribute('src')!==m.fallback) img.src=m.fallback; };\n    img.src=m.src; img.alt=m.alt||''; cap.textContent=m.alt||'';")
    os.makedirs(dst, exist_ok=True)
    open(os.path.join(dst, 'index.html'), 'w', encoding='utf-8').write(s)
    print('wrote', os.path.join(dst, 'index.html'), len(s), 'bytes')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
