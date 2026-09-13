#!/usr/bin/env python3
"""Bring the pointer-reporting block of every built page up to the form in
html/sep/43.html: the page hit-tests links itself and tells the parent
(link:pl), with 'a[href],area[href]' as the selector.

Handles the two older forms - the plain block (no link flag) and the April
"plink" block - and is idempotent: a page already in the target form is left
untouched. Every rewritten block is compared with the reference block before
the file is written.

    python fix_pointer.py <reader dir> [--check]
"""
import glob, os, re, sys

REF = os.path.join('html', 'sep', '43.html')
START = "  var raf=0,px=0,py=0"
END = "  },{passive:true});"

def block(s):
    """The slice from the var line to the end of the mousemove listener."""
    i = s.find(START)
    if i < 0:
        return None
    j = s.find(END, i)
    return s[i:j + len(END)] if j > 0 else None

def convert(s):
    # 1. the var line, absorbing April's separate 'var plink=false;'
    s = s.replace("  var raf=0,px=0,py=0;\n  var plink=false;\n", "  var raf=0,px=0,py=0,pl=false;\n")
    s = s.replace("  var raf=0,px=0,py=0;\n", "  var raf=0,px=0,py=0,pl=false;\n")
    # 2. the hit-test line after the coordinates (replacing April's plink line if present)
    hit = ("    /* the page hit-tests itself and tells the parent, because a parent cannot\n"
           "       look inside a same-origin iframe when both are local files */\n"
           "    pl=!!(e.target&&e.target.closest&&e.target.closest('a[href],area[href]'));\n")
    s = re.sub(r"(    px=e\.clientX; py=e\.clientY;\n)    plink=!!\([^\n]*\n", r"\1" + hit.replace("\\", "\\\\"), s)
    s = re.sub(r"(    px=e\.clientX; py=e\.clientY;\n)(?!    /\* the page hit-tests)", r"\1" + hit.replace("\\", "\\\\"), s)
    # 3. the message
    s = s.replace("{abj:'pointer',x:px,y:py,link:plink}", "{abj:'pointer',x:px,y:py,link:pl}")
    s = s.replace("{abj:'pointer',x:px,y:py}", "{abj:'pointer',x:px,y:py,link:pl}")
    return s

def main(reader, check=False):
    ref = block(open(os.path.join(reader, REF), encoding='utf-8').read())
    if not ref or "link:pl}" not in ref:
        raise SystemExit("reference block not found in " + REF)
    changed = same = failed = 0
    for path in sorted(glob.glob(os.path.join(reader, 'html', '*', '*.html'))):
        s = open(path, encoding='utf-8').read()
        if block(s) == ref:
            same += 1
            continue
        s2 = convert(s)
        if block(s2) != ref:
            failed += 1
            print('   could not convert:', os.path.relpath(path, reader))
            continue
        if not check:
            open(path, 'w', encoding='utf-8').write(s2)
        changed += 1
    print('%s: %d files changed, %d already in the target form, %d could not be converted'
          % ('would be' if check else 'done', changed, same, failed))
    return failed

if __name__ == '__main__':
    sys.exit(1 if main(sys.argv[1], '--check' in sys.argv) else 0)
