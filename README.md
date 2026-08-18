# krisfricke.github.io

Landing page for my projects, served at <https://krisfricke.github.io/>.

Projects are plotted on two axes — usefulness across, fun up — as hexagonal
buttons. Hovering one reveals a description and a link to its source. Each
hexagon links to the project's own GitHub Pages site.

| Project | Repository |
|---|---|
| The Silk Road | [Silk-Road](https://github.com/krisfricke/Silk-Road) |
| Interstellar Trail | [Interstellar-Trail](https://github.com/krisfricke/Interstellar-Trail) |
| Recipe Calculator | [recipe-calculator](https://github.com/krisfricke/recipe-calculator) |
| Varroa Modelling | [varroa_interface](https://github.com/krisfricke/varroa_interface) |

## Notes

One self-contained `index.html` — no build step, no framework, no external
requests. The bee cursor image is embedded as base64.

The cursor replaces the system pointer with a bee that rotates to face its
direction of travel. It stands down for touch devices, for anyone with
reduced-motion enabled, and if the script fails to run at all — in each case
the normal cursor is left alone.

Node positions are inline `left` / `bottom` percentages on each `.node`,
so they are easy to adjust.
