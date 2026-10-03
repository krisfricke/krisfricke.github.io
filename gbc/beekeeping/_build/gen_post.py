#!/usr/bin/env python3
"""After gbc_build: put the live things into the General Beekeeping pages.

  - video pages: the player (YouTube embed or the club's own mp4) is laid over the placeholder
    the PDF carries, at exactly its rectangle
  - document pages: "Open the document" asks the reader to show the PDF in a viewer over the
    reader rather than leaving for a new tab (it still opens the file when the page is on its own)

    python gen_post.py <general reader dir>
"""
import json, os, re, sys, html

SCALE = 1.6

def main(reader):
    marks = json.load(open(os.path.join(reader, '_build', 'gen_marks.json')))
    arts = json.load(open(os.path.join(reader, '_build', 'arts.json')))['gen']
    spans = {a['t']: (a['p'], a['end']) for a in arts}
    hdir = os.path.join(reader, 'html', 'gen')
    for it in marks['seq']:
        if not it.get('video'): continue
        # the player placeholder is the first mark inside this item's pages
        a = it['p']; b = max([x['end'] for x in arts if x['p'] == a] or [a])
        hit = None
        for pno in range(a, b + 1):
            for r in marks['marks'].get(str(pno), []):
                if r[2] - r[0] > 200: hit = (pno, r); break
            if hit: break
        if not hit:
            print('!! no player placeholder for', it['slug']); continue
        pno, (x0, y0, x1, y1) = hit
        v = it['video']
        if v['kind'] == 'yt':
            el = ('<iframe src="https://www.youtube-nocookie.com/embed/%s?rel=0" title="%s" frameborder="0" '
                  'allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; fullscreen" allowfullscreen '
                  'style="position:absolute;left:%.1fpx;top:%.1fpx;width:%.1fpx;height:%.1fpx;border:0;border-radius:4px;background:#000;z-index:7"></iframe>'
                  % (v['id'], html.escape(it['slug']), x0 * SCALE, y0 * SCALE, (x1 - x0) * SCALE, (y1 - y0) * SCALE))
        else:
            el = ('<video controls preload="metadata" src="%s" style="position:absolute;left:%.1fpx;top:%.1fpx;width:%.1fpx;height:%.1fpx;border-radius:4px;background:#000;z-index:7"></video>'
                  % (html.escape(v['src'], quote=True), x0 * SCALE, y0 * SCALE, (x1 - x0) * SCALE, (y1 - y0) * SCALE))
        path = os.path.join(hdir, '%d.html' % pno); s = open(path, encoding='utf-8').read()
        s = re.sub(r'<(iframe|video)[^>]*data-gen-player[^>]*>.*?</\1>', '', s, flags=re.S)
        el = el.replace('style="', 'data-gen-player="1" style="', 1)
        s = s.replace('</div></div></div>\n<script>', el + '\n</div></div></div>\n<script>', 1)
        open(path, 'w', encoding='utf-8').write(s)
        print('player on p%d: %s' % (pno, it['slug']))
    # document buttons: open in the reader's viewer
    hook = '''
<script>
/* "Open the document": the parent reader shows the PDF in a viewer over the page; on its own the link just opens */
document.addEventListener('click',function(e){
  var a=e.target && e.target.closest ? e.target.closest('a[href$=".pdf"],a[href*=".pdf?"],a.hot[href*=".pdf"]') : null;
  if(!a) return;
  if(window.parent && window.parent!==window){
    e.preventDefault();
    try{ window.parent.postMessage({abj:'pdf',src:a.getAttribute('href'),title:document.title},'*'); }
    catch(err){ window.open(a.getAttribute('href'),'_blank'); }
  }
},true);
</script>
'''
    # links into the newsletter reader (a topic lane) open in this window, not a new tab
    for fn in os.listdir(hdir):
        if not fn.endswith('.html'): continue
        path = os.path.join(hdir, fn); s = open(path, encoding='utf-8').read()
        s2 = re.sub(r'(<a [^>]*href="[^"]*#/topic/[^"]*"[^>]*) target="_blank"', r'\1 target="_top"', s)
        if s2 != s: open(path, 'w', encoding='utf-8').write(s2)
    n = 0
    for fn in os.listdir(hdir):
        if not fn.endswith('.html'): continue
        path = os.path.join(hdir, fn); s = open(path, encoding='utf-8').read()
        if '.pdf' not in s or 'abj:\'pdf\'' in s: continue
        s = s.replace('</body></html>', hook + '</body></html>')
        open(path, 'w', encoding='utf-8').write(s); n += 1
    print('document hook on %d pages' % n)

if __name__ == '__main__':
    main(os.path.abspath(sys.argv[1]))
