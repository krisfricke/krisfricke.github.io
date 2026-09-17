#!/usr/bin/env python3
"""Give every enlargeable picture its real caption.

The lightbox caption should be what the page itself says under the picture,
and where the page says nothing, the alt text we wrote for the issue - not a
placeholder. So both come out of the PDF rather than being typed here:

  * the caption is the small (7-8.5pt) Calibri-Light line sitting right under
    the picture, or tucked inside its bottom edge, which is how this layout
    sets them. Body text is 9.5-10.5pt, so the size is a reliable tell.
  * the alt text is the /Alt on the tagged Figure element. Those carry no
    /BBox in this file, so a picture is matched to its alt by a keyword, listed
    below, rather than by position - explicit and checkable.
  * a caption that is only a credit ("Photo credit DPIRD", "Courtesy ...")
    describes nothing, so it is appended to the alt text instead of replacing it.

    python sep_captions.py <reader dir> <issue id> <pdf>
"""
import json, os, re, sys
import fitz

# picture (page, file) -> a distinctive phrase from its /Alt entry
KEYWORD = {
    (9,  "p09_49.jpg"):  "Lindsay Callaway",
    (13, "p13_71.jpg"):  "queen bee and some workers",
    (14, "p14_75.jpg"):  "candlebark",
    (15, "p15_115.jpg"): "two queens visible",
    (16, "p16_118.jpg"): "lone bee truck",
    (17, "p17_121.jpg"): "forklift",
    (19, "p19_133.jpg"): "almond blossom",
    (19, "p19_135.jpg"): "Jana Hamilton",
    (22, "p22_155.jpg"): "Winter colony losses",
    (24, "p24_163.jpg"): "spotty, irregular pattern",
    (24, "p24_171.jpg"): "pupal",
    (24, "p24_165.jpg"): "greasy sheen",
    (24, "p24_167.jpg"): "matchstick",
    (24, "p24_169.jpg"): "Unhealthy-looking",
    (26, "p26_186.jpg"): "coolabah",
    (26, "p26_188.jpg"): "beard-heath",
    (27, "p27_193.jpg"): "brimble box",
    (32, "p32_250.jpg"): "cornbread",
    (37, "p37_270.jpg"): "Volker Herzig",
    (44, "p44_385.jpg"): "event space",
}

CAPTION_MAX = 8.6          # pt: captions are 7.5-8, body starts at 9.5
CREDIT = re.compile(r"^(photo credit|courtesy|image credit|adapted|source)\b", re.I)


def pdf_alts(doc):
    """[(page, alt)] for every tagged element that carries one."""
    out = []
    pageof = {doc[i].xref: i + 1 for i in range(len(doc))}
    for x in range(1, doc.xref_length()):
        try:
            a = doc.xref_get_key(x, "Alt")
        except Exception:
            continue
        if a[0] == "null":
            continue
        v = a[1]
        if v.startswith("<") and v.endswith(">"):
            b = bytes.fromhex(v[1:-1])
            v = b[2:].decode("utf-16-be", "replace") if b[:2] == b"\xfe\xff" else b.decode("latin-1", "replace")
        elif v.startswith("(") and v.endswith(")"):
            v = v[1:-1]
        pg = doc.xref_get_key(x, "Pg")
        pno = pageof.get(int(pg[1].split()[0])) if pg[0] == "xref" else None
        out.append((pno, v.strip()))
    return out


def caption_for(page, rect):
    """The layout's own caption line(s): small type directly under the picture,
    or inside its bottom edge (used where a caption is overlaid on the photo)."""
    r = fitz.Rect(rect)
    lines = []
    for b in page.get_text("dict")["blocks"]:
        if b["type"] != 0:
            continue
        for l in b["lines"]:
            lb = fitz.Rect(l["bbox"])
            size = max(s["size"] for s in l["spans"])
            t = "".join(s["text"] for s in l["spans"]).strip()
            if not t or size > CAPTION_MAX:
                continue
            if "Barlow" in l["spans"][0]["font"]:        # the running folio
                continue
            if lb.x1 < r.x0 - 5 or lb.x0 > r.x1 + 5:
                continue
            dy = lb.y0 - r.y1
            if -24 <= dy <= 16:                          # just below, or just inside the foot
                lines.append((lb.y0, lb.x0, t))
    lines.sort()
    # keep only the run that starts at the topmost caption line (a caption may wrap)
    out, last = [], None
    for y, _x, t in lines:
        if last is not None and y - last > 14:
            break
        out.append(t)
        last = y
    return " ".join(out).strip()


def main(reader, iid, pdf):
    doc = fitz.open(pdf)
    alts = pdf_alts(doc)
    path = os.path.join(reader, "_build", "%s_imgs.json" % iid)
    imgs = json.load(open(path, encoding="utf-8"))
    for pg, lst in sorted(imgs.items(), key=lambda t: int(t[0])):
        page = doc[int(pg) - 1]
        for e in lst:
            fn = e["src"].split("/")[-1]
            key = KEYWORD.get((int(pg), fn))
            alt = ""
            if key:
                hits = [a for p, a in alts if p == int(pg) and key.lower() in a.lower()]
                if len(hits) != 1:
                    raise SystemExit("p%s %s: %d alt entries match %r" % (pg, fn, len(hits), key))
                alt = hits[0]
            cap = caption_for(page, e["rect"])
            if cap and CREDIT.match(cap):
                text = "%s (%s)" % (alt or fn, cap.rstrip("."))
            elif cap:
                text = cap
            else:
                text = alt
            if not text:
                raise SystemExit("p%s %s: no caption and no alt text" % (pg, fn))
            e["alt"] = re.sub(r"\s+", " ", text)
            print("p%-3s %-12s %s" % (pg, fn, e["alt"]))
    json.dump(imgs, open("/tmp/%s_imgs.json" % iid, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    open(path, "wb").write(open("/tmp/%s_imgs.json" % iid, "rb").read())
    print("\n%d captions written to %s" % (sum(len(v) for v in imgs.values()), path))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
