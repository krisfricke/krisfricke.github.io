# General Beekeeping — the club's resources as a reader

The subpages of geelongbeekeepersclub.org.au › Resources › General Beekeeping, rebuilt as one
A4 "issue" and read in the same page-turning reader as the club newsletter: cover, contents,
the articles and guides re-set in the club's style, every video playing inside its page, and a
card for each downloadable document (with its page count) that opens the PDF in a viewer over
the reader. The header is the website's own; the Newsletter button and the "Elsewhere" page at
the end tie it to the newsletter reader and the Varroa management page.

Topic and author lanes draw on three collections, with toggles at the top of the lane:
GBC website resources · GBC newsletter · Australian Bee Journal. The same toggles exist in the
newsletter reader, so a tag opened there shows the resources too.

## Layout

    index.html             the reader (made by ../_build/fork_reader.py <abj> . gen)
    print.html             print view (whole collection, or an item's pages)
    html/gen/N.html        one document per page: background JPEG + positioned live text (+ players)
    assets/gen/p-NN.jpg    the pages at strip size; assets/src/ the pictures captured from the website
    article/<slug>/        text version of each item
    _build/collection.json order, kinds, tags, documents (page counts, sizes, blurbs), video ids
    _build/raw/<slug>.json the harvested copy of each website page (text, headings, pictures, links)
    _build/gen_pages.py    composes and renders the A4 book (_build/general.pdf) and writes arts.json
    _build/gbc_build.py    the page builder shared with the newsletter
    _build/gen_post.py     puts the players and the document viewer hook into the pages
    _build/trim.json       pages whose content stops part-way down: the reader shows them cut off there (print keeps the full sheet)
    _build/build.sh        the whole sequence, in order

## Changing things

- Reorder, retitle or retag an item: `_build/collection.json`, then `sh _build/build.sh`.
- Fix a sentence: edit the item's `_build/raw/<slug>.json` (plain text; `LIST:`, `NUM:`, `STEP:n|text|pics`,
  `TABLE:a|b|c`, `REF:` and `PRES:` lines are the only markup), then rebuild.
- Add a page from the website: harvest its text and pictures into `raw/` and `assets/src/`
  (the pictures are named `<slug>__<FILENAME>.png`), add it to `collection.json`, rebuild.
- Document covers: a picture of the first page in `_build/covers/<file name>.png` is used as the cover;
  a PDF in `_build/docs/` is better still (first page rendered, exact page count). Put the PDFs (same file names as on the website) in
  `_build/docs/` and rebuild; `doc_cover()` renders each first page onto its stack of pages. Until then
  the cards carry a typeset stand-in cover.
- A document's page count: `pages` in `collection.json` (the Australian Beekeeping Guide's is still
  unknown; it will be read from the PDF once that is in `_build/docs/`).

The PDFs and videos stay on the club's server; only the pictures are copied here (captured at
screen resolution, which is all the website serves).
