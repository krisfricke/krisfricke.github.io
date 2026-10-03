#!/bin/sh
# Rebuild the General Beekeeping collection from the harvested copy. Run from the beekeeping/ folder.
#   1. pages as an A4 book (WeasyPrint) + catalogue        2. live-text pages + page images
#   3. players and the document viewer                      4. the reader itself, then text versions
set -e
ABJ=${ABJ:-/sessions/wizardly-festive-rubin/mnt/reader}     # the Australian Bee Journal reader (the base template)
python3 _build/gen_pages.py .
python3 _build/gbc_build.py . gen gen "General Beekeeping" _build/general.pdf pages
python3 _build/gen_post.py .
python3 _build/gen_trim.py .
python3 ../_build/fork_reader.py "$ABJ" . gen
python3 _build/gbc_articles.py .
# the newsletter reader bakes in this collection's catalogue too, so refresh it as well
( cd .. && python3 _build/fork_reader.py "$ABJ" . news && python3 _build/gbc_articles.py . )
