#!/usr/bin/env python3
"""Make a Geelong Beekeepers Club reader's index.html from the Australian Bee Journal reader's.

The ABJ reader is the base: same page stack, rails, author/topic browsing, lanes and bee.
This script rewrites what is VAA-specific - name, masthead, palette, the western seam
(which leads to geelongbeekeepersclub.org.au), the pointer (the bee, always), the storage
keys and the baked data - and leaves everything else as it is, so fixes to the ABJ reader
can be carried across by running it again.

Two collections share the script:
    python fork_reader.py <ABJ reader dir> <newsletter reader dir> news
    python fork_reader.py <ABJ reader dir> <general reader dir>    gen

Each reader also bakes in the OTHER collections' catalogues (the sibling GBC reader and the
ABJ), so a topic or author lane can intersperse their articles, with three toggles at the top
of the lane: GBC website resources · GBC newsletter · Australian Bee Journal.

The article records come from _build/arts.json via gbc_articles.py, which also writes the
text versions; run that after this.
"""
import json, os, re, sys

SITE = 'https://geelongbeekeepersclub.org.au/'

COLLECTIONS = {
    'news': dict(
        key='news', name='GBC newsletter', title='Geelong Beekeepers Club Newsletter',
        reader_url='https://krisfricke.github.io/gbc/',
        issues=[('jul', 'July 2026', '2026-07 Newsletter', 28), ('aug', 'August 2026', '2026-08 Newsletter', 30),
                ('sep', 'September 2026', '2026-09 Newsletter', 32)],
        header='reader', west_what='newsletter',
        ext=[('gen', 'general/'), ('abj', '../abj/')]),
    'gen': dict(
        key='gen', name='GBC website resources', title='Geelong Beekeepers Club · General Beekeeping',
        reader_url='https://krisfricke.github.io/gbc/general/',
        issues=[('gen', 'General Beekeeping', 'Resources collection', None)],      # page count read from the build
        header='site', west_what='collection',
        ext=[('news', '../'), ('abj', '../../abj/')]),
}

def issue_records(cfg, root):
    out = []
    for iid, label, vol, n in cfg['issues']:
        if n is None:
            n = len([f for f in os.listdir(os.path.join(root, 'assets', iid)) if re.match(r'p-\d+\.jpg$', f)])
        rec = {'id': iid, 'label': label, 'vol': vol, 'dir': iid,
               'pages': ['p-%02d.jpg' % k for k in range(1, n + 1)], 'cover': 'assets/%s/p-01.jpg' % iid,
               'html': list(range(1, n + 1)), 'index': 2}
        # pages whose content stops part-way down are shown trimmed in the reader (print keeps the full sheet)
        tp = os.path.join(root, '_build', 'trim.json')
        if os.path.exists(tp): rec['trim'] = json.load(open(tp))
        lp = os.path.join(root, '_build', 'land.json')
        if os.path.exists(lp) and json.load(open(lp)): rec['land'] = json.load(open(lp))
        out.append(rec)
    out[-1]['current'] = True
    return out

def catalogue(key, abj_src, dst):
    """issues + arts of a collection, for baking into another reader as an external source"""
    if key == 'abj':
        s = open(os.path.join(abj_src, 'index.html'), encoding='utf-8').read()
        m = re.search(r'^const D=(\{.*\});$', s, flags=re.M)
        D = json.loads(m.group(1))
        return {'issues': D['issues'], 'arts': [a for a in D['arts'] if a.get('tags')]}
    cfg = COLLECTIONS[key]
    root = os.path.normpath(os.path.join(dst, dict(COLLECTIONS[[k for k in COLLECTIONS if k != key][0]]['ext'])[key]))
    arts_path = os.path.join(root, '_build', 'arts.json')
    arts = []
    if os.path.exists(arts_path):
        raw = json.load(open(arts_path, encoding='utf-8'))
        for iid, recs in raw.items():
            if iid.startswith('_'): continue
            for r in recs:
                arts.append({'issue': iid, 't': r['t'], 'p': r['p'], 'end': r['end'], 'tags': r['tags'], 'author': r.get('author', ''),
                             'slug': iid + '-' + re.sub(r'[^a-z0-9]+', '-', r['t'].lower()).strip('-')})
    return {'issues': issue_records(cfg, root) if os.path.isdir(os.path.join(root, 'assets')) else [], 'arts': arts}

def write_print_page(dst, cfg, issues):
    iss = {i['id']: {'label': i['label'], 'n': len(i['pages']), 'land': i.get('land', [])} for i in issues}
    whole = 'the whole collection' if cfg['key'] == 'gen' else 'the whole issue'
    page = """<!doctype html><html lang="en-AU"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Print \u2014 %(title)s</title>
<link rel="icon" type="image/png" sizes="64x64" href="assets/favicon.png">
<style>
@page{size:A4;margin:0}
html,body{margin:0;background:#6d6a60;font:14px/1.4 system-ui,sans-serif;color:#222}
.bar{position:fixed;top:0;left:0;right:0;z-index:5;background:#111;color:#fff;padding:0 16px;height:48px;display:flex;gap:16px;align-items:center}
.bar .what{font-weight:700;color:#f7c20b}.bar .n{color:#bbb;font-size:12.5px}.bar .sp{flex:1}
.bar button{background:#f7c20b;color:#111;border:none;border-radius:18px;padding:7px 18px;cursor:pointer;font:inherit;font-weight:700}
.bar button:hover{background:#ffd733}.bar a{color:#ddd;text-decoration:none;font-size:13px}.bar a:hover{color:#fff;text-decoration:underline}
.stack{padding:66px 0 40px;display:flex;flex-direction:column;align-items:center;gap:14px}
.sheet{width:210mm;height:297mm;background:#fff;box-shadow:0 8px 28px rgba(0,0,0,.45);overflow:hidden;position:relative}
.sheet iframe{width:210mm;height:297mm;border:0;display:block}
.sheet.land{width:297mm;height:210mm;page:land}.sheet.land iframe{width:297mm;height:210mm}
@page land{size:A4 landscape;margin:0}
.none{color:#fff;padding:100px 20px;text-align:center}
@media print{.bar{display:none}html,body{background:#fff}.stack{padding:0;gap:0;display:block}
 .sheet{box-shadow:none;page-break-after:always;break-after:page;margin:0}.sheet:last-child{page-break-after:auto;break-after:auto}}
</style></head><body>
<div class="bar"><span class="what" id="what">%(title)s</span><span class="n" id="n"></span><span class="sp"></span>
<button onclick="window.print()">Print</button><a id="back" href="index.html">\u2039 back to the reader</a></div>
<div class="stack" id="stack"></div>
<script>
const ISS=%(iss)s;
(function(){
  const m=/^#\\/([a-z0-9]+)(?:\\/(\\d+)(?:-(\\d+))?)?/.exec(location.hash||'');
  const stack=document.getElementById('stack');
  if(!m||!ISS[m[1]]){ stack.innerHTML='<div class="none">Nothing to print: open this page from a "Print" link in the reader.</div>'; return; }
  const iss=m[1], info=ISS[iss];
  let a=m[2]?parseInt(m[2],10):1, b=m[3]?parseInt(m[3],10):(m[2]?a:info.n);
  a=Math.max(1,Math.min(info.n,a)); b=Math.max(a,Math.min(info.n,b));
  const what=info.label+(m[2]?(a===b?' \u00b7 page '+a:' \u00b7 pages '+a+'\u2013'+b):' \u00b7 %(whole)s');
  document.getElementById('what').textContent=what;
  document.getElementById('n').textContent=(b-a+1)+' sheet'+(b-a?'s':'')+' of A4';
  document.getElementById('back').href='index.html#/page/'+iss+'/'+a;
  document.title='%(short)s '+info.label+(m[2]?' pp'+a+'-'+b:'');
  let left=b-a+1, done=false;
  function ready(){ if(--left>0||done) return; done=true; setTimeout(function(){ try{ window.print(); }catch(e){} },900); }
  for(let p=a;p<=b;p++){
    const d=document.createElement('div'); d.className='sheet'+((info.land||[]).indexOf(p)>=0?' land':'');
    const f=document.createElement('iframe'); f.title=info.label+' page '+p; f.src='html/'+iss+'/'+p+'.html';
    f.addEventListener('load',ready); f.addEventListener('error',ready);
    d.appendChild(f); stack.appendChild(d);
  }
  window.addEventListener('message',function(e){ const q=e.data; if(q&&q.abj==='hello'&&e.source){ try{ e.source.postMessage({abj:'zoom',k:1},'*'); }catch(err){} } });
})();
</script></body></html>
""" % dict(title=cfg['title'], iss=json.dumps(iss, ensure_ascii=False), whole=whole, short='GBC Newsletter' if cfg['key'] == 'news' else 'GBC')
    open(os.path.join(dst, 'print.html'), 'w', encoding='utf-8').write(page)

SITE_HEADER = '''<div class="chrome site">
  <div class="band">
    <a class="mast" href="#" onclick="gotoCover();return false" title="%(title)s"><img src="assets/gbc_logo.png" alt="Geelong Beekeepers Club Inc."></a>
    <div class="tag">For hobbyist and<br>professional beekeepers</div>
    <div class="rt">
      <span class="iss" id="issLabel"></span>
      <a class="t edonly" id="tabTag" onclick="toggleTag()">Tag mode</a>
      <a class="t edonly" onclick="exportTags()">Export tags</a>
      <a class="sbtn" href="%(site)sMain.asp?_=Members%%20area" target="_blank" rel="noopener">Members/Login</a>
      <a class="sbtn" href="%(site)sMain.asp?_=CONTACT" target="_blank" rel="noopener">Contact us</a>
    </div>
  </div>
  <div class="nav">
    <a href="%(site)s" target="_blank" rel="noopener">Home</a><i></i><a href="%(site)sMain.asp?_=ABOUT%%20US" target="_blank" rel="noopener">About us</a><i></i><a href="%(site)sMain.asp?_=MEETINGS" target="_blank" rel="noopener">Meetings</a><i></i><a href="%(site)sMain.asp?_=COURSES" target="_blank" rel="noopener">Courses</a><i></i><a href="%(site)sMain.asp?_=RESOURCES" target="_blank" rel="noopener" class="here">Resources</a><i></i><a href="%(site)sMain.asp?_=MEMBERSHIP" target="_blank" rel="noopener">Membership</a><i></i><a href="%(site)sMain.asp?_=IN%%20THE%%20HIVE" target="_blank" rel="noopener">In the hive</a><i></i><a href="%(site)sMain.asp?_=Edu%%20Hub" target="_blank" rel="noopener">Edu hub</a>
    <span class="sp"></span>
    <nav class="ctr">
      <a class="t" id="toIndex" onclick="gotoIndex()" title="The contents page"><span class="lg">Contents</span><span class="sm">Contents</span></a>
      <a class="t" onclick="openBrowse('author')"><span class="lg">Search by author</span><span class="sm">Authors</span></a>
      <a class="t" onclick="openBrowse('topic')"><span class="lg">Search by topic</span><span class="sm">Topics</span></a>
      <a class="t sub" href="../index.html" title="The club newsletter reader">Newsletter</a>
    </nav>
  </div>
</div>'''

SITE_HEADER_CSS = '''
/* ---------- the website's own header, carried into the reader ---------- */
:root{--chromeH:122px}
.chrome.site{display:block;padding:0;background:#fff;height:var(--chromeH);box-shadow:0 2px 8px rgba(0,0,0,.18);backdrop-filter:none;color:#222}
.chrome.site .band{height:84px;display:flex;align-items:center;gap:22px;padding:0 24px;background:#fbf255 url("data:image/svg+xml;utf8,HEXSMALL") repeat}
.chrome.site .mast{background:none;padding:0;height:auto}
.chrome.site .mast img{height:58px;margin:0;border:1px solid #c9b600;border-radius:2px;box-shadow:0 1px 3px rgba(0,0,0,.25)}
.chrome.site .tag{font:italic 17px/1.15 Lato,'Proxima Nova','Segoe UI',Arial,sans-serif;color:#222}
.chrome.site .rt{margin-left:auto;display:flex;align-items:center;gap:10px;padding:0}
.chrome.site .rt .iss{color:#5a4500;font-size:12px;letter-spacing:.06em;text-transform:uppercase;margin-right:6px}
.chrome.site .sbtn{background:#f7c20b;color:#111;text-decoration:none;font-size:15px;padding:9px 16px;border-radius:2px;white-space:nowrap}
.chrome.site .sbtn:hover{background:#ffd733}
.chrome.site .nav{height:38px;display:flex;align-items:center;padding:0 18px 0 24px;gap:4px;border-bottom:1px solid #e3e3e3;font:12.5px/1 Lato,'Proxima Nova','Segoe UI',Arial,sans-serif;letter-spacing:.06em;text-transform:uppercase}
.chrome.site .nav>a{color:#555;text-decoration:none;padding:4px 6px;white-space:nowrap}
.chrome.site .nav>a:hover,.chrome.site .nav>a.here{color:#111}
.chrome.site .nav>a.here{font-weight:700}
.chrome.site .nav i{display:inline-block;width:16px;height:17px;margin:0 6px;background:url("assets/bee_sep.png") center/contain no-repeat}
.chrome.site .nav .sp{flex:1}
.chrome.site nav.ctr{margin:0;gap:2px;flex-wrap:nowrap}
.chrome.site nav.ctr a.t{color:#444;font-size:12.5px;padding:5px 9px;text-transform:none;letter-spacing:0}
.chrome.site nav.ctr a.t:hover{background:#f3eecd;color:#111}
.chrome.site nav.ctr a.t.sub{background:#111;color:#fff;margin-left:6px}
.chrome.site nav.ctr a.t.sub:hover{background:#333;color:#fff}
.chrome.site .edonly{display:none}body.editor .chrome.site .edonly{display:inline-block;color:#5a4500}
@media(max-width:980px){.chrome.site .nav>a,.chrome.site .nav i{display:none}.chrome.site .tag{display:none}}
@media(max-width:620px){:root{--chromeH:98px}.chrome.site .band{height:60px}.chrome.site .mast img{height:40px}.chrome.site .sbtn{font-size:12px;padding:6px 10px}}
'''

CROSS_JS = r'''
/* ---------- the other collections: the sibling GBC reader and the Australian Bee Journal ----------
   A topic or author lane can intersperse their articles; three toggles at the top of the lane say which. */
const EXT=__EXT__;
const HOME=__HOME__;
const SRCKEY='gbc_srcs_v1';
let SRCS=(function(){ try{ const v=JSON.parse(localStorage.getItem(SRCKEY)); if(v&&typeof v==='object') return v; }catch(e){} return {gen:true,news:true,abj:true}; })();
function srcOn(k){ return k===HOME || SRCS[k]!==false; }
function toggleSrc(k){ SRCS[k]=!srcOn(k); try{ localStorage.setItem(SRCKEY,JSON.stringify(SRCS)); }catch(e){}
  const h=location.hash; if(h.startsWith('#/topic/')) openTopic(decodeURIComponent(h.slice(8))); else if(h.startsWith('#/author/')) openAuthor(decodeURIComponent(h.slice(9))); }
function extIssue(src,id){ const c=EXT.find(x=>x.key===src); return c && c.issues.find(i=>i.id===id); }
/* every record from every collection that is switched on, each knowing where it lives */
function allArtsX(){
  let out=allArts().map(a=>Object.assign({src:HOME,base:''},a));
  EXT.forEach(function(c){ if(!srcOn(c.key)) return; c.arts.forEach(a=>out.push(Object.assign({src:c.key,base:c.base},a))); });
  return out;
}
function onPageX(a,p){
  if(a.src===HOME) return onPage(a.issue,p);
  const c=EXT.find(x=>x.key===a.src); if(!c) return [];
  return c.arts.filter(x=>x.issue===a.issue&&x.p<=p&&(x.end||x.p)>=p).map(x=>Object.assign({},x,{cont:x.p<p,base:c.base,src:a.src}));
}
function srcBar(){
  const names={gen:'GBC website resources',news:'GBC newsletter',abj:'Australian Bee Journal'};
  const order=['gen','news','abj'];
  return '<div class="srcs"><span class="srcl">Show articles from</span>'+order.map(function(k){
    const home=(k===HOME); const on=srcOn(k);
    return '<button class="srcb'+(on?' on':'')+(home?' home':'')+'" role="switch" aria-checked="'+(on?'true':'false')+'" '+(home?'disabled title="This collection is always shown"':'onclick="toggleSrc(\''+k+'\')" title="'+(on?'Hide':'Show')+' articles from the '+names[k]+'"')+'>'+
      '<span class="sw"><span class="knob"></span></span><span class="lab">'+names[k]+(home?' <em>(here)</em>':'')+'</span></button>';
  }).join('')+'</div>';
}
'''

CROSS_CSS = '''
.srcs{display:flex;flex-wrap:wrap;align-items:center;gap:8px 14px;margin:12px 0 4px}
.srcl{font-size:11.5px;letter-spacing:.06em;text-transform:uppercase;color:#6b5a2e}
.srcb{display:inline-flex;align-items:center;gap:8px;background:none;border:none;padding:4px 2px;font-size:12.5px;color:#6b5a2e;cursor:pointer;font-family:inherit}
.srcb .sw{position:relative;width:36px;height:20px;border-radius:10px;background:#cfc7b2;box-shadow:inset 0 1px 2px rgba(0,0,0,.25);transition:background .18s;flex:0 0 auto}
.srcb .knob{position:absolute;top:2px;left:2px;width:16px;height:16px;border-radius:50%;background:#fff;box-shadow:0 1px 3px rgba(0,0,0,.35);transition:left .18s}
.srcb.on .sw{background:#f7c20b}.srcb.on .knob{left:18px}
.srcb.on{color:#2a2416}
.srcb .lab em{font-style:normal;color:#9a8a5a;font-size:11px}
.srcb.home{cursor:default}.srcb.home .sw{background:#e2c75a}
.srcb:not(.home):hover .sw{box-shadow:inset 0 1px 2px rgba(0,0,0,.25),0 0 0 3px rgba(247,194,11,.28)}
.tstoryhead .from{display:inline-block;margin-left:8px;font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:#8a6a12;background:rgba(255,255,255,.6);border-radius:10px;padding:2px 8px}
/* the document viewer over the reader */
#pdfv{position:fixed;inset:0;z-index:95;background:rgba(20,16,4,.78);display:none;flex-direction:column}
#pdfv.on{display:flex}
#pdfv .bar{height:46px;display:flex;align-items:center;gap:14px;padding:0 16px;background:#111;color:#fff;font-size:13.5px}
#pdfv .bar b{color:#f7c20b;font-weight:700;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#pdfv .bar a,#pdfv .bar button{color:#fff;background:none;border:1px solid #666;border-radius:14px;padding:5px 12px;font:inherit;cursor:pointer;text-decoration:none}
#pdfv .bar a:hover,#pdfv .bar button:hover{border-color:#f7c20b;color:#f7c20b}
#pdfv iframe{flex:1;border:0;background:#525659}
'''

PDFV_HTML = '''<div id="pdfv" role="dialog" aria-modal="true" aria-label="Document">
  <div class="bar"><b id="pdfvt">Document</b><a id="pdfvo" href="#" target="_blank" rel="noopener">Open in a new tab</a><button onclick="closePdf()">Close</button></div>
  <iframe id="pdfvf" title="Document"></iframe>
</div>
'''

PDFV_JS = '''
/* ---------- document viewer: a page asks for a PDF to be shown over the reader ---------- */
function openPdf(src,title){ const v=document.getElementById('pdfv'); document.getElementById('pdfvt').textContent=title||src.split('/').pop();
  document.getElementById('pdfvo').href=src; document.getElementById('pdfvf').src=src; v.classList.add('on'); }
function closePdf(){ const v=document.getElementById('pdfv'); v.classList.remove('on'); document.getElementById('pdfvf').src='about:blank'; }
window.addEventListener('message',function(e){ const m=e&&e.data; if(!m||m.abj!=='pdf'||!m.src) return;
  let t=(m.title||'').replace(/\\s*[—-]\\s*page\\s*\\d+$/,'').replace(/^.*?,\\s*/,'');
  openPdf(m.src, decodeURIComponent(m.src.split('/').pop().split('?')[0]).replace(/\\.pdf$/i,'')); });
window.addEventListener('keydown',function(e){ if(e.key==='Escape'&&document.getElementById('pdfv').classList.contains('on')) closePdf(); });
'''

def main(src, dst, key):
    cfg = COLLECTIONS[key]
    s = open(os.path.join(src, 'index.html'), encoding='utf-8').read()
    lines = s.split('\n')
    issues = issue_records(cfg, dst)
    D = {'issues': issues, 'arts': []}
    ext = []
    for k, base in cfg['ext']:
        cat = catalogue(k, src, dst)
        ext.append({'key': k, 'base': base, 'issues': cat['issues'], 'arts': cat['arts']})
        print('  external %-4s %3d issues %4d records (base %s)' % (k, len(cat['issues']), len(cat['arts']), base))
    for i, ln in enumerate(lines):
        if ln.startswith('const D='): lines[i] = 'const D=' + json.dumps(D, ensure_ascii=False, separators=(',', ':')) + ';'
        if ln.startswith('const LINKS='): lines[i] = 'const LINKS={};   /* page links live inside the page documents themselves */'
    s = '\n'.join(lines)

    def sub(a, b, count=1, must=True):
        nonlocal s
        if must and a not in s: raise SystemExit('fork: pattern not found: %r' % a[:70])
        s = s.replace(a, b, count if count else -1)

    # ---- head ----
    sub('<title>Australian Bee Journal</title>', '<title>%s</title>' % cfg['title'])
    sub('''<!-- MOCKUP GATE - delete this line and gate.js to ship the real thing.
     Dormant on file:// and localhost, so it only bites once published. -->
<script src="gate.js?v=3"></script>
<!-- bump ?v= whenever gate.js changes, or browsers keep serving the old one -->
''', '')
    s = re.sub(r'<script>/\* THE POINTER\..*?\)\(\);</script>', "<script>window.ABJ_CURSOR='bee';</script>", s, count=1, flags=re.S)
    sub('<meta name="description" content="The Australian Bee Journal, published by the Victorian Apiarists\' Association since 1918. Read current and past issues, browse by topic and author.">',
        '<meta name="description" content="%s">' % ('The Geelong Beekeepers Club newsletter: read current and past issues, browse by topic and author.' if key == 'news'
                                                     else 'The Geelong Beekeepers Club\'s General Beekeeping resources - articles, videos and documents - as one readable collection.'))
    s = re.sub(r'<link rel="icon"[^>]*>\n<link rel="icon"[^>]*>\n<link rel="apple-touch-icon"[^>]*>\n<link rel="shortcut icon"[^>]*>',
               '<link rel="icon" type="image/png" sizes="64x64" href="assets/favicon.png">', s, count=1)

    # ---- palette ----
    sub(':root{--chromeH:58px;--gold:#f9c500;--paper:#faf8f2;--navy:#1f3a5f;--bg:#a9d2ec;\n  --ink:#14293b;--ink2:#3d6079;--sky1:#7db4dc;--sky2:#a9d2ec;--sky3:#d3e8f7}',
        ':root{--chromeH:58px;--gold:#f7c20b;--paper:#fffdf4;--navy:#3b2f12;--bg:#f8e67e;\n  --ink:#2a2412;--ink2:#6b5a2e;--sky1:#f3d14a;--sky2:#f8e67e;--sky3:#fdf4c6}')
    HEX = ('<svg xmlns=\'http://www.w3.org/2000/svg\' width=\'56\' height=\'97\' viewBox=\'0 0 56 97\'>'
           '<path d=\'M28 0 L56 16.17 L56 48.5 L28 64.66 L0 48.5 L0 16.17 Z M28 64.66 L28 97\' '
           'fill=\'none\' stroke=\'%23000\' stroke-opacity=\'.055\' stroke-width=\'1.4\'/></svg>')
    HEXSMALL = ('<svg xmlns=\'http://www.w3.org/2000/svg\' width=\'14\' height=\'24.25\' viewBox=\'0 0 14 24.25\'>'
                '<path d=\'M7 0 L14 4.04 L14 12.12 L7 16.17 L0 12.12 L0 4.04 Z M7 16.17 L7 24.25\' fill=\'none\' stroke=\'%23000\' stroke-opacity=\'.13\' stroke-width=\'.7\'/></svg>')
    sub('body{margin:0;background:linear-gradient(180deg,var(--sky1) 0%,var(--sky2) 46%,var(--sky3) 100%) fixed;',
        'body{margin:0;background:url("data:image/svg+xml;utf8,' + HEX + '") fixed,linear-gradient(180deg,var(--sky1) 0%,var(--sky2) 46%,var(--sky3) 100%) fixed;')
    for a, b in [('#2f6d92', '#8a6a12'), ('#7ea9c6', '#d9b84a'), ('#6f9cbb', '#c9a93d'), ('#3d6079', '#6b5a2e'), ('#1f4b68', '#4a3a12'),
                 ('#17313f', '#2a2416'), ('#1c4258', '#3b2f1a'), ('#55748d', '#7a6a3a'), ('#12303f', '#221c10'), ('#1b4a6b', '#4a3a12'),
                 ('#2f5876', '#6b5a2e'), ('#f3f8fc', '#fffbe8'), ('#4aa3ff', '#f7c20b'),
                 ('rgba(80,170,255,.42)', 'rgba(247,194,11,.42)'), ('rgba(30,70,100,.35)', 'rgba(90,70,20,.35)'), ('rgba(30,70,100', 'rgba(90,70,20')]:
        s = s.replace(a, b)

    # ---- chrome ----
    if cfg['header'] == 'reader':
        sub('<a class="mast" href="#" onclick="gotoCover();return false" title="Australian Bee Journal"><img src="assets/vaa_masthead_approved.png" alt="Australian Bee Journal — Victorian Apiarists\' Association Inc"></a>',
            '<a class="mast" href="#" onclick="gotoCover();return false" title="Geelong Beekeepers Club Newsletter"><img src="assets/gbc_logo.png" alt="Geelong Beekeepers Club Inc."></a>')
        sub('.mast img{height:53px;display:block;margin:0}', '.mast img{height:44px;display:block;margin:7px 0 0 10px;border-radius:4px}')
        sub('<a class="t sub" href="https://vicbeekeepers.com.au/join-us" target="_blank" rel="noopener">Subscribe</a>',
            '<a class="t" href="general/index.html" title="Articles, videos and documents from the club website">Resources</a>\n'
            '    <a class="t sub" href="https://geelongbeekeepersclub.org.au/" target="_blank" rel="noopener">Join the club</a>')
    else:
        s = re.sub(r'<div class="chrome">.*?</div>\n</div>\n', SITE_HEADER % dict(title=cfg['title'], site=SITE) + '\n', s, count=1, flags=re.S)
        s = s.replace('</style></head><body>', SITE_HEADER_CSS.replace('HEXSMALL', HEXSMALL) + '</style></head><body>', 1)
    sub('<h2 id="ititle">Australian Bee Journal</h2>', '<h2 id="ititle">%s</h2>' % cfg['title'])
    if key == 'gen':
        sub('<p><span class="ar">&#9650;</span> Scroll up to select a previous issue</p>', '<p>Topics and authors sit beside every page</p>')
    sub('title="Go to the VAA main site"><span class="chev" aria-hidden="true"></span><span class="lbl">VAA Main Page</span>',
        'title="Go to the Geelong Beekeepers Club website"><span class="chev" aria-hidden="true"></span><span class="lbl">GBC Main Site</span>')
    s = re.sub(r'<div class="lane" id="laneL"><div class="vaagate">.*?</div></div>\n  <div class="lane" id="lane0">', '''<div class="lane" id="laneL"><div class="vaagate">
    <div class="band"><img src="assets/gbc_logo.png" alt="" style="height:64px;border-radius:4px"><div><h2>Geelong Beekeepers Club Inc.</h2><div class="dom">GEELONGBEEKEEPERSCLUB.ORG.AU</div></div></div>
    <p>You&rsquo;ve reached the %s&rsquo;s western edge. From here the club&rsquo;s own website carries on &mdash; meetings, courses, the members&rsquo; area and the Varroa resources.</p>
    <div class="links"><span>Meetings</span><span>Courses</span><span>Membership</span><span>In the Hive</span><span>Edu Hub</span></div>
    <button class="back" onclick="setLane(0)">to the %s &rsaquo;</button>
    <p class="handoff">Taking you to geelongbeekeepersclub.org.au&hellip;</p>
  </div></div>
  <div class="lane" id="lane0">''' % (cfg['west_what'], cfg['west_what']), s, count=1, flags=re.S)
    sub("setTimeout(function(){ location.href='https://vicbeekeepers.com.au/'; },780);   /* slide, then hand over to the VAA's own site */",
        "setTimeout(function(){ location.href='%s'; },780);   /* slide, then hand over to the club's own site */" % SITE)
    sub('.vaagate .band img{height:56px}', '.vaagate .band img{height:64px}')
    sub('.vaagate .band{display:flex;gap:16px;align-items:center;background:var(--gold);', '.vaagate .band{display:flex;gap:16px;align-items:center;background:#111;color:#fff;')
    sub('.vaagate h2{margin:0;font-size:24px;color:#111;text-align:left}', '.vaagate h2{margin:0;font-size:24px;color:#fff;text-align:left}')
    sub('.vaagate .dom{font-size:12.5px;color:#6a5600;text-align:left;letter-spacing:.06em}', '.vaagate .dom{font-size:12.5px;color:var(--gold);text-align:left;letter-spacing:.06em}')

    # ---- storage keys, share address, labels ----
    pre = 'gbc' if key == 'news' else 'gbcgen'
    for a, b in [("'abj_tags_v2'", "'%s_tags_v1'" % pre), ("'abj_intro_v1'", "'%s_intro_v1'" % pre),
                 ("a.download='ABJ_tags.json'", "a.download='GBC_tags.json'"),
                 ("const dir=local ? 'https://abj.org.au/reader/'", "const dir=local ? '%s'" % cfg['reader_url']),
                 ("+'\\nIt will work once the reader is published at abj.org.au/reader/.'", "+'\\nIt will work once the reader is published at %s.'" % cfg['reader_url'].replace('https://', '')),
                 ("const NOTEXT=['Cover','Advertisements','VAA Advertisements','Classifieds','indexes'];", "const NOTEXT=['Cover','Advertisements','Classifieds','indexes'];"),
                 ("' issues — a special issue assembled from the archive'", "' issues — a special issue assembled from past newsletters'" if key == 'news' else "' sources — a special issue assembled from the collection'")]:
        sub(a, b)
    s = s.replace('abj_nofwd', 'gbc_nofwd').replace("'abj_editor'", "'gbc_editor'").replace("'abj_zoom'", "'gbc_zoom'")
    if key == 'gen':
        sub("<div class=\"hint\">▲ scroll up for past issues</div>", "<div class=\"hint\"></div>")

    # ---- closed issues sit on a short stack of pages ----
    sub('.arc img{max-height:58vh;border:5px solid #fff;box-shadow:0 16px 44px rgba(0,0,0,.5);transition:transform .15s}',
        '.arc img{max-height:58vh;border:5px solid #fff;transition:transform .15s;margin:0 18px 18px 0;\n'
        ' box-shadow:2px 2px 0 0 #cfc7b2,3px 3px 0 0 #fff,5px 5px 0 0 #cfc7b2,6px 6px 0 0 #fff,8px 8px 0 0 #cfc7b2,9px 9px 0 0 #fff,\n'
        '  11px 11px 0 0 #cfc7b2,12px 12px 0 0 #fff,14px 14px 0 0 #cfc7b2,15px 15px 0 0 #fff,17px 17px 0 0 #bfb79f,18px 18px 0 0 #fff,22px 30px 44px rgba(0,0,0,.45)}')
    # ---- the interface credit ----
    sub('<div class="zoombar" role="group" aria-label="Page size">',
        '<a class="credit" href="https://krisfricke.github.io/" target="_blank" rel="noopener" title="About the reader">Hivejournal Interface &copy; Kris Fricke 2026</a>\n' + PDFV_HTML + '<div class="zoombar" role="group" aria-label="Page size">')
    s = s.replace('</style></head><body>', '.credit{position:fixed;left:14px;bottom:10px;z-index:70;font:11.5px/1 system-ui,sans-serif;color:rgba(40,30,0,.6);text-decoration:none;letter-spacing:.03em;padding:5px 8px;border-radius:6px}\n.credit:hover{color:#111;background:rgba(255,255,255,.55);text-decoration:underline}\n' + CROSS_CSS + '</style></head><body>', 1)
    # ---- background click -> contents ----
    sub("window.addEventListener('hashchange',route);",
        "document.getElementById('lane0').addEventListener('click',function(e){\n"
        "  if(e.target.closest('.page,.arc,.cov,.rail,.chrome,.edge,.zoombar,.credit,button,a,input,iframe,img')) return;\n"
        "  if(tagMode) return;\n  gotoIndex();\n});\n"
        + PDFV_JS +
        "window.addEventListener('hashchange',route);")

    # ---- printing ----
    sub("    if(!a.cont) rail+='<button class=\"share\" onclick=\"copyArt(\\''+sg+'\\')\" title=\"Copy a link straight to this article\">Share this article</button>';",
        "    if(!a.cont) rail+='<button class=\"share\" onclick=\"copyArt(\\''+sg+'\\')\" title=\"Copy a link straight to this article\">Share this article</button>';\n"
        "    if(!a.cont) rail+='<a class=\"txt prt\" href=\"'+(a.base||'')+'print.html#/'+a.issue+'/'+a.p+'-'+a.end+'\" target=\"_blank\" rel=\"noopener\" title=\"Open the pages of this article ready to print\">Print this article</a>';")
    hint = 'scroll down to read — topics appear beside each page' if key == 'news' else 'scroll down to read the collection — topics appear beside each page'
    sub("'<div class=\"cap\">'+act.label+' · '+act.vol+'</div><div class=\"hint\">▼ scroll down to read — topics appear beside each page</div>';",
        "'<div class=\"cap\">'+act.label+' · '+act.vol+'</div>'+\n"
        "    '<a class=\"prt-issue\" href=\"print.html#/'+act.id+'\" target=\"_blank\" rel=\"noopener\" title=\"Open the whole %s ready to print\">&#x1F5A8;&#xFE0E; Print this %s</a>'+\n"
        "    '<div class=\"hint\">▼ %s</div>';" % (('issue', 'issue', hint) if key == 'news' else ('collection', 'collection', hint)))
    sub('.rail .txt::before{content:"\\1F4C4  "}',
        '.rail .txt::before{content:"\\1F4C4  "}\n.rail .txt.prt::before{content:"\\1F5A8\\FE0E  "}\n'
        '.cov .prt-issue{display:inline-block;margin-top:12px;background:rgba(255,255,255,.7);border:1px solid #d9b84a;color:#3b2f1a;border-radius:18px;padding:7px 16px;font-size:12.5px;text-decoration:none}\n'
        '.cov .prt-issue:hover{background:var(--gold);border-color:var(--gold);color:#111}')
    write_print_page(dst, cfg, issues)

    # ---- short pages: the frame stops where the content does (the page document keeps its full height) ----
    sub("      const base=Math.min(1, availWidth(fr)/(A4W*across*(1-gut)));", "      const L=landFor(ifr.getAttribute('src')), PW=L?A4H:A4W, PH=L?A4W:A4H;\n      const base=Math.min(1, availWidth(fr)/(PW*across*(1-gut)));")
    sub("      fr.style.width=(A4W*k*(1-gut))+'px';", "      fr.style.width=(PW*k*(1-gut))+'px';")
    sub("      fr.style.height=(A4H*k)+'px';", "      fr.style.height=(PH*k*trimFor(ifr.getAttribute('src')))+'px';")
    sub("      ifr.style.width=(A4W*k)+'px'; ifr.style.height=(A4H*k)+'px';", "      ifr.style.width=(PW*k)+'px'; ifr.style.height=(PH*k)+'px';")
    sub("      ifr.style.left=fr.classList.contains('gutL')?(-(A4W*k*gut))+'px':'0px';", "      ifr.style.left=fr.classList.contains('gutL')?(-(PW*k*gut))+'px':'0px';\n      ifr.style.top=(-(PH*k*topFor(ifr.getAttribute('src'))))+'px';")
    sub("function fitFrames(){", """function trimFor(src){
  const m=/html\\/([a-z0-9]+)\\/(\\d+)\\.html/.exec(src||''); if(!m) return 1;
  let iss=byId(m[1]);
  if(!(iss&&iss.trim)&&typeof EXT!=='undefined') EXT.some(c=>{ const i=c.issues.find(x=>x.id===m[1]&&x.trim); if(i){ iss=i; return true; } return false; });
  const t=iss&&iss.trim&&iss.trim[m[2]]; if(!t) return 1;
  return Array.isArray(t) ? t[1]-t[0] : t;
}
/* the blank band above a page's content, as a fraction of the page height (the frame starts below it) */
function topFor(src){
  const m=/html\\/([a-z0-9]+)\\/(\\d+)\\.html/.exec(src||''); if(!m) return 0;
  let iss=byId(m[1]);
  if(!(iss&&iss.trim)&&typeof EXT!=='undefined') EXT.some(c=>{ const i=c.issues.find(x=>x.id===m[1]&&x.trim); if(i){ iss=i; return true; } return false; });
  const t=iss&&iss.trim&&iss.trim[m[2]]; return Array.isArray(t)?t[0]:0;
}
function landFor(src){
  const m=/html\\/([a-z0-9]+)\\/(\\d+)\\.html/.exec(src||''); if(!m) return false;
  let iss=byId(m[1]);
  if(!(iss&&iss.land)&&typeof EXT!=='undefined') EXT.some(c=>{ const i=c.issues.find(x=>x.id===m[1]&&x.land); if(i){ iss=i; return true; } return false; });
  return !!(iss&&iss.land&&iss.land.indexOf(parseInt(m[2],10))>=0);
}
function fitFrames(){""")
    # ---- lightbox fallback ----
    sub("    img.src=m.src; img.alt=m.alt||''; cap.textContent=m.alt||'';",
        "    img.onerror=function(){ if(m.fallback&&img.getAttribute('src')!==m.fallback) img.src=m.fallback; };\n    img.src=m.src; img.alt=m.alt||''; cap.textContent=m.alt||'';")

    # ---- cross-collection lanes ----
    sub("/* ---------------- sideways lanes ---------------- */",
        CROSS_JS.replace('__EXT__', json.dumps(ext, ensure_ascii=False, separators=(',', ':'))).replace('__HOME__', json.dumps(key)) +
        "/* ---------------- sideways lanes ---------------- */")
    # lane(): pages and rails come from the record's own collection; the head says where it is from
    sub("""  ts.innerHTML='<div class="tophead"><h2>'+esc(title)+'</h2><div class="sub">'+sub+'</div>'+
    '<button class="back" onclick="closeTopic()">‹ back to the issue</button></div>';""",
        """  ts.innerHTML='<div class="tophead"><h2>'+esc(title)+'</h2><div class="sub">'+sub+'</div>'+srcBar()+
    '<button class="back" onclick="closeTopic()">‹ back</button></div>';""")
    sub("""  hits.forEach(function(a){
    const iss=byId(a.issue);
    const pages=(a.end>a.p)?('pages '+a.p+'–'+a.end):('page '+a.p);
    const head=document.createElement('div'); head.className='tstoryhead';
    head.innerHTML='<b>'+esc(a.t)+'</b>'+(a.author?' · '+esc(a.author):'')+' — '+iss.label+', '+pages+
      '<a onclick="jumpTo(\\''+a.issue+'\\','+a.p+')">open in issue ›</a>';""",
        """  const NAMES={gen:'GBC website',news:'GBC newsletter',abj:'Australian Bee Journal'};
  hits.forEach(function(a){
    const ext=(a.src&&a.src!==HOME);
    const iss=ext?extIssue(a.src,a.issue):byId(a.issue); if(!iss) return;
    const base=ext?a.base:'';
    const pages=(a.end>a.p)?('pages '+a.p+'–'+a.end):('page '+a.p);
    const head=document.createElement('div'); head.className='tstoryhead';
    head.innerHTML='<b>'+esc(a.t)+'</b>'+(a.author?' · '+esc(a.author):'')+' — '+iss.label+', '+pages+
      (ext?'<span class="from">'+NAMES[a.src]+'</span><a href="'+base+'index.html#/page/'+a.issue+'/'+a.p+'">open there ›</a>'
          :'<a onclick="jumpTo(\\''+a.issue+'\\','+a.p+')">open in issue ›</a>');""")
    sub("""        d.innerHTML='<div class="pframe htmlpage"><iframe loading="lazy" scrolling="no" title="'+esc(a.t)+' — page '+p+'" src="html/'+iss.id+'/'+p+'.html"></iframe></div>'+
          '<div class="rail">'+readRail(iss,p,onPage(iss.id,p))+'</div>';""",
        """        d.innerHTML='<div class="pframe htmlpage"><iframe loading="lazy" scrolling="no" title="'+esc(a.t)+' — page '+p+'" src="'+base+'html/'+iss.id+'/'+p+'.html"></iframe></div>'+
          '<div class="rail">'+readRail(iss,p,onPageX(a,p))+'</div>';""")
    sub("""      d.innerHTML='<img src="assets/'+iss.dir+'/'+f+'" loading="lazy" alt="'+esc(a.t)+' — page '+p+'">';
      d.querySelector('img').onclick=(function(pp){return ()=>jumpTo(a.issue,pp);})(p);""",
        """      d.innerHTML='<img src="'+base+'assets/'+iss.dir+'/'+f+'" loading="lazy" alt="'+esc(a.t)+' — page '+p+'">';
      d.querySelector('img').onclick=(function(pp){return ()=>{ if(ext) location.href=base+'index.html#/page/'+a.issue+'/'+pp; else jumpTo(a.issue,pp); };})(p);""")
    # the lanes draw on every collection that is switched on
    sub("  const hits=allArts().filter(a=>expandTags(a.tags).some(t=>t.toLowerCase()===tag.toLowerCase()));",
        "  const hits=allArtsX().filter(a=>expandTags(a.tags).some(t=>t.toLowerCase()===tag.toLowerCase()));")
    sub("  const hits=allArts().filter(a=>hasAuthor(a,name));", "  const hits=allArtsX().filter(a=>hasAuthor(a,name));")
    sub("' issues — a special issue assembled from past newsletters',hits);" if key == 'news' else "' sources — a special issue assembled from the collection',hits);",
        "' sources — a special issue assembled across the collections',hits);")
    # the browse lists: this collection and the sibling GBC reader (the ABJ's hundred-odd topics only join an opened lane)
    sub("function knownTags(){ const s=new Set(); allArts().forEach(a=>a.tags.forEach(t=>s.add(t)));",
        "function browseArts(){ return allArtsX().filter(a=>a.src!=='abj'); }\nfunction knownTags(){ const s=new Set(); allArts().forEach(a=>a.tags.forEach(t=>s.add(t)));")
    sub("""function authorIndex(){
  var m={};
  allArts().forEach(function(a){""", """function authorIndex(){
  var m={};
  browseArts().forEach(function(a){""")
    sub("""function topicIndex(){
  var m={};
  allArts().forEach(function(a){ expandTags(a.tags||[]).forEach(function(t){""", """function topicIndex(){
  var m={};
  browseArts().forEach(function(a){ expandTags(a.tags||[]).forEach(function(t){""")
    # the rail's "Read as text" must point into the record's own collection
    sub("""    if(!a.cont && hasText(a)) rail+='<a class="txt" href="article/'+sg+'/index.html#text" onclick="openText(\\''+sg+'\\');return false" title="Read this article as reflowable text">Read as text</a>';""",
        """    if(!a.cont && hasText(a) && a.src!=='abj') rail+='<a class="txt" href="'+(a.base||'')+'article/'+sg+'/index.html#text" title="Read this article as reflowable text">Read as text</a>';""")

    os.makedirs(dst, exist_ok=True)
    open(os.path.join(dst, 'index.html'), 'w', encoding='utf-8').write(s)
    print('wrote', os.path.join(dst, 'index.html'), len(s), 'bytes')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else 'news')
