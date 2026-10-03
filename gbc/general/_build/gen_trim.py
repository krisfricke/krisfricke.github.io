#!/usr/bin/env python3
"""Measure where each page's content starts and stops. Pages with a lot of blank sheet above or
below their content are listed in _build/trim.json as [top, bottom] fractions of the page height;
the reader shows those pages cut to that band, so a half-page article does not drag half a page
of white with it. Print is unaffected (it uses the full sheets)."""
import json, os, sys, fitz
reader = os.path.abspath(sys.argv[1])
d = fitz.open(os.path.join(reader, '_build', 'general.pdf')); MM = 72 / 25.4
trim = {}
for i, pg in enumerate(d):
    n = i + 1
    if n <= 2: continue                                   # cover and contents stay whole
    H = pg.rect.height                                    # per page: a landscape page is shorter
    tops, bots = [], []
    for b in pg.get_text('blocks'):
        if not b[4].strip(): continue                     # whitespace-only blocks are not content
        if b[3] < H - 16 * MM: bots.append(b[3])
        if b[1] < H - 16 * MM: tops.append(b[1])
    for dr in pg.get_drawings():
        r = dr['rect']
        if r.y1 < H - 16 * MM: bots.append(r.y1)
        if r.y0 < H - 16 * MM and r.width > 20: tops.append(r.y0)
    for im in pg.get_image_info():
        if im['bbox'][3] < H - 16 * MM: bots.append(im['bbox'][3])
        if im['bbox'][1] < H - 16 * MM: tops.append(im['bbox'][1])
    y1 = max(bots) if bots else H; y0 = min(tops) if tops else 0
    bot = min(1.0, (y1 + 12 * MM) / H); top = max(0.0, (y0 - 12 * MM) / H)
    if top < 0.12: top = 0.0                               # the normal head margin is not a blank
    if bot < 0.78 or top > 0:
        trim[n] = [round(top, 3), round(bot, 3)] if top > 0 else round(bot, 3)
json.dump(trim, open(os.path.join(reader, '_build', 'trim.json'), 'w'), indent=0)
print('%d trimmed pages' % len(trim), {k: v for k, v in trim.items() if isinstance(v, list)})
