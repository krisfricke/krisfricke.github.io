#!/usr/bin/env python3
"""Add or update an issue record in the reader's `const D={...}` line.

Checks first that serialising D reproduces the existing line exactly, so the
other records come out untouched. Keeps a copy of index.html in _build/.

    python issue_record.py <reader dir> <id> "<label>" "<vol>" <dir> <pages> <index page> [current]
"""
import json, os, re, shutil, sys

def load(reader):
    path = os.path.join(reader, 'index.html')
    s = open(path, encoding='utf-8').read()
    m = re.search(r'const D=(\{.*?\});\n', s, re.S)
    D = json.loads(m.group(1))
    if dumps(D) != m.group(1):
        raise SystemExit('round trip of D does not reproduce the file - stopping before touching it')
    return path, s, m, D

def dumps(D):
    return json.dumps(D, separators=(',', ':'), ensure_ascii=False)

def save(path, s, m, D):
    bak = os.path.join(os.path.dirname(path), '_build', 'index.html.bak')
    if not os.path.exists(bak):
        shutil.copyfile(path, bak)
    s2 = s[:m.start(1)] + dumps(D) + s[m.end(1):]
    open(path, 'w', encoding='utf-8').write(s2)

if __name__ == '__main__':
    reader, iid, label, vol, adir, npages, index = sys.argv[1:8]
    current = len(sys.argv) > 8 and sys.argv[8] == 'current'
    path, s, m, D = load(reader)
    rec = {'id': iid, 'label': label, 'vol': vol, 'dir': adir}
    if current:
        rec['current'] = True
    n = int(npages)
    rec['pages'] = ['p-%02d.jpg' % k for k in range(1, n + 1)]
    rec['cover'] = 'assets/%s/p-01.jpg' % adir
    rec['html'] = list(range(1, n + 1))
    rec['index'] = int(index)
    D['issues'] = [i for i in D['issues'] if i['id'] != iid]
    if current:
        for i in D['issues']:
            i.pop('current', None)
    D['issues'].append(rec)
    save(path, s, m, D)
    print('issues now:', [(i['id'], i.get('current', False)) for i in D['issues']])
