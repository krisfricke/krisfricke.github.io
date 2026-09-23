#!/usr/bin/env python3
"""Give every text-version page a way out and a way on.

The static article pages (article/<slug>/index.html) were built to be crawled and to be
a plain-text fallback; arriving at one from the reader's "Text version" link left you with
no exit but the browser's Back button. This adds, to each of them:

  * a top bar and a click target on the sky: back to the journal, centred on this article
  * previous / next within the same issue, in page order, reached by over-pulling past the
    ends of the scroll (the same idiom the reader uses to turn pages) or by the arrows
  * a right-hand rail carrying the author and the subject tags, as the reader has
  * a print stylesheet: text reflows to the paper, chrome drops away

Re-runnable: it strips its own previous output first.
    python3 _build/textnav.py <reader dir>
"""
import io, json, os, re, sys, html

MARK_A = '<!--TEXTNAV-->'
MARK_B = '<!--/TEXTNAV-->'

CSS = """
<style>/*TEXTNAV*/
body{padding-top:56px}
.tnbar{position:fixed;left:0;right:0;top:0;height:44px;z-index:30;display:flex;align-items:center;gap:14px;
  padding:0 16px;background:rgba(255,253,248,.94);backdrop-filter:blur(6px);border-bottom:1px solid #d8d0bd;
  font:13px/1 system-ui,sans-serif;color:#3d6079}
.tnbar a{color:#0f4b70;text-decoration:none;white-space:nowrap}
.tnbar a:hover{text-decoration:underline}
.tnbar .sp{flex:1 1 auto}
.tnbar .bk{font-weight:600}
.tnwrap{display:flex;gap:26px;align-items:flex-start;justify-content:center;max-width:1010px;margin:0 auto}
.tnwrap .w{margin:0;flex:0 1 680px}
.tnrail{flex:0 0 190px;position:sticky;top:64px;font:13px/1.5 system-ui,sans-serif;color:#274b63}
.tnrail h3{margin:0 0 8px;font:600 11px/1 system-ui,sans-serif;letter-spacing:.14em;text-transform:uppercase;color:#5c7d95}
.tnrail a{display:block;color:#0f4b70;text-decoration:none;padding:5px 9px;margin-bottom:5px;border-radius:9px;
  background:rgba(255,253,248,.8);border:1px solid rgba(56,40,26,.14)}
.tnrail a:hover{background:#fff}
.tnrail .sep{height:1px;background:rgba(56,40,26,.16);margin:16px 0}
.tnstep{display:flex;justify-content:space-between;gap:12px;margin:26px auto 0;max-width:680px;
  font:13px/1.4 system-ui,sans-serif}
.tnstep a{color:#0f4b70;text-decoration:none;background:rgba(255,253,248,.9);border:1px solid rgba(56,40,26,.18);
  border-radius:10px;padding:9px 13px;max-width:47%}
.tnstep a:hover{background:#fff}
.tnstep b{display:block;font:600 11px/1 system-ui,sans-serif;letter-spacing:.1em;text-transform:uppercase;color:#5c7d95;margin-bottom:4px}
.tncue{position:fixed;left:50%;transform:translateX(-50%);z-index:40;pointer-events:none;opacity:0;transition:opacity .15s;
  background:rgba(20,50,70,.86);color:#fff;font:12px/1 system-ui,sans-serif;padding:8px 14px;border-radius:14px;white-space:nowrap}
.tncue.on{opacity:1}
.tncue.top{top:58px}.tncue.bot{bottom:16px}
.tncue i{display:inline-block;width:52px;height:3px;background:rgba(255,255,255,.3);border-radius:2px;margin-left:9px;vertical-align:middle}
.tncue i>span{display:block;height:100%;width:0;background:#f9c500;border-radius:2px}
@media(max-width:900px){.tnrail{display:none}.tnwrap{display:block}.tnwrap .w{max-width:680px;margin:0 auto}}
@media print{
  .tnbar,.tnrail,.tnstep,.tncue,.cta,.note,.tags{display:none!important}
  body{background:#fff!important;padding:0!important;font:11.5pt/1.5 Georgia,'Times New Roman',serif;color:#000}
  .tnwrap{display:block;max-width:none}
  .w{max-width:none!important;margin:0!important;padding:0!important;background:#fff!important;
     border-radius:0!important;box-shadow:none!important}
  h1{font-size:20pt}h2{font-size:13pt;color:#000}
  .bc{color:#444}.meta{color:#444}
  a{color:#000;text-decoration:none}
  p{orphans:3;widows:3}
  h1,h2{break-after:avoid-page}
  @page{size:A4;margin:18mm 16mm}
}
</style>"""

JS = """
<script>/*TEXTNAV*/
(function(){
  var BACK=%(back)s, PREV=%(prev)s, NEXT=%(next)s, NEED=150;
  function go(u){ if(u) location.href=u; }
  /* the sky around the sheet, and the left margin, are a way back to the journal */
  document.addEventListener('click',function(e){
    if(e.target.closest('a,button,input,select,textarea')) return;
    if(e.target.closest('.w')) return;
    if(e.clientX>window.innerWidth*0.78 && e.target.closest('.tnrail')) return;
    go(BACK);
  });
  /* over-pull past either end to step through the issue - the reader's own idiom */
  var cueT=document.querySelector('.tncue.top'), cueB=document.querySelector('.tncue.bot');
  var acc=0, dir=0, lock=0;
  function cue(c,f){ if(!c) return; c.classList.toggle('on',f>0.02); var i=c.querySelector('i>span'); if(i) i.style.width=(Math.min(1,f)*100).toFixed(0)+'%%'; }
  function atTop(){ return (window.scrollY||document.documentElement.scrollTop)<=1; }
  function atBot(){ var d=document.documentElement; return (window.scrollY||d.scrollTop)+window.innerHeight>=d.scrollHeight-2; }
  function reset(){ acc=0; dir=0; cue(cueT,0); cue(cueB,0); }
  addEventListener('wheel',function(e){
    var now=Date.now(); if(now<lock) return;
    if(e.deltaY<0 && atTop() && PREV){ if(dir!==-1){acc=0;dir=-1;} acc+=-e.deltaY; cue(cueT,acc/NEED);
      if(acc>NEED){ lock=now+900; reset(); go(PREV); } return; }
    if(e.deltaY>0 && atBot() && NEXT){ if(dir!==1){acc=0;dir=1;} acc+=e.deltaY; cue(cueB,acc/NEED);
      if(acc>NEED){ lock=now+900; reset(); go(NEXT); } return; }
    reset();
  },{passive:true});
  var sx=0,sy=0,st=0;
  addEventListener('touchstart',function(e){var t=e.touches[0];sx=t.clientX;sy=t.clientY;st=Date.now();},{passive:true});
  addEventListener('touchmove',function(e){
    var t=e.touches[0], dy=t.clientY-sy;
    if(dy<0 && atBot() && NEXT) cue(cueB,-dy/NEED);
    else if(dy>0 && atTop() && PREV) cue(cueT,dy/NEED);
    else reset();
  },{passive:true});
  addEventListener('touchend',function(e){
    var t=e.changedTouches[0], dx=t.clientX-sx, dy=t.clientY-sy, quick=Date.now()-st<900;
    reset();
    if(quick && dx>70 && Math.abs(dx)>Math.abs(dy)*1.6){ go(BACK); return; }   /* swipe right-ward: back */
    if(dy<-NEED && atBot() && NEXT){ go(NEXT); return; }
    if(dy>NEED && atTop() && PREV){ go(PREV); return; }
  },{passive:true});
  addEventListener('keydown',function(e){
    if(/INPUT|TEXTAREA|SELECT/.test((e.target&&e.target.tagName)||'')) return;
    if(e.key==='Escape'){ go(BACK); }
    if(e.key==='ArrowLeft'){ go(BACK); }
    if(e.key==='PageDown'&&atBot()&&NEXT){ e.preventDefault(); go(NEXT); }
    if(e.key==='PageUp'&&atTop()&&PREV){ e.preventDefault(); go(PREV); }
  });
})();
</script>"""


def esc(t):
    return html.escape(t or '', quote=True)


def strip_old(s):
    """Undo a previous run completely, so this script is safe to re-run."""
    s = re.sub(re.escape(MARK_A) + '.*?' + re.escape(MARK_B), '', s, flags=re.S)
    s = re.sub(r'<style>/\*TEXTNAV\*/.*?</style>', '', s, flags=re.S)
    s = re.sub(r'<script>/\*TEXTNAV\*/.*?</script>', '', s, flags=re.S)
    s = s.replace('<!--/tnwrap--></div>', '').replace('<!--/tnwrap-->', '')
    s = s.replace('<div class="tnwrap">', '')
    s = re.sub(r'\n{3,}', '\n\n', s)
    return s


def main(root):
    idx = io.open(os.path.join(root, 'index.html'), encoding='utf-8').read()
    D = json.loads(re.search(r'const D=(\{.*?\});', idx, re.S).group(1))
    arts = D['arts']
    labels = {i['id']: i['label'] for i in D['issues']}
    by_issue = {}
    for a in arts:
        by_issue.setdefault(a['issue'], []).append(a)
    for k in by_issue:
        by_issue[k].sort(key=lambda a: (a['p'], a['t']))

    done = 0
    for a in arts:
        path = os.path.join(root, 'article', a['slug'], 'index.html')
        if not os.path.exists(path):
            continue
        seq = by_issue[a['issue']]
        i = next(n for n, x in enumerate(seq) if x['slug'] == a['slug'])
        prev = seq[i - 1] if i > 0 else None
        nxt = seq[i + 1] if i + 1 < len(seq) else None
        back = '../../index.html#/article/' + a['slug']
        s = strip_old(io.open(path, encoding='utf-8').read())

        rail = ['<div class="tnrail">']
        if a.get('author'):
            rail.append('<h3>Author</h3><a href="../../index.html#/author/%s">%s</a>'
                        % (esc(a['author'].replace(' ', '%20')), esc(a['author'])))
            rail.append('<div class="sep"></div>')
        if a.get('tags'):
            rail.append('<h3>Topics</h3>')
            for t in a['tags']:
                rail.append('<a href="../../index.html#/topic/%s">%s</a>' % (esc(t.replace(' ', '%20')), esc(t)))
            rail.append('<div class="sep"></div>')
        rail.append('<h3>Issue</h3><a href="../../index.html#/issue/%s">%s</a>' % (a['issue'], esc(labels.get(a['issue'], a['issue']))))
        rail.append('</div>')

        bar = ('<div class="tnbar"><a class="bk" href="%s">&lsaquo; Back to the journal</a>'
               '<span class="sp"></span>'
               '%s%s'
               '<a href="#" onclick="window.print();return false;">Print</a></div>'
               % (esc(back),
                  ('<a href="../%s/#text">&uarr; %s</a>' % (esc(prev['slug']), esc(prev['t'])) if prev else ''),
                  ('<a href="../%s/#text">&darr; %s</a>' % (esc(nxt['slug']), esc(nxt['t'])) if nxt else '')))
        cues = ('<div class="tncue top">&uarr; keep pulling for the previous article<i><span></span></i></div>'
                '<div class="tncue bot">&darr; keep pulling for the next article<i><span></span></i></div>')
        step = ['<div class="tnstep">']
        step.append('<a href="../%s/#text"><b>Previous</b>%s</a>' % (esc(prev['slug']), esc(prev['t'])) if prev else '<span></span>')
        step.append('<a href="../%s/#text"><b>Next</b>%s</a>' % (esc(nxt['slug']), esc(nxt['t'])) if nxt else '<span></span>')
        step.append('</div>')

        js = JS % dict(back=json.dumps(back), prev=json.dumps('../%s/#text' % prev['slug'] if prev else ''),
                       next=json.dumps('../%s/#text' % nxt['slug'] if nxt else ''))

        anchor = '<script>\n/* Send a human visitor'
        for tag, txt in (('</head>', '</head>'), ('<body>', '<body>'), ('the anchor', anchor)):
            if txt not in s:
                raise SystemExit('%s: expected %r in the page - aborting rather than half-writing it' % (a['slug'], txt))
        s = s.replace('</head>', CSS + '\n</head>', 1)
        s = s.replace('<body>', '<body>\n' + MARK_A + bar + cues + MARK_B + '\n<div class="tnwrap">', 1)
        s = s.replace(anchor, MARK_A + ''.join(rail) + MARK_B + '<!--/tnwrap--></div>\n'
                      + MARK_A + ''.join(step) + MARK_B + '\n' + js + '\n' + anchor, 1)
        io.open(path, 'w', encoding='utf-8').write(s)
        done += 1
    print('text-version navigation added to %d article pages' % done)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '.')
