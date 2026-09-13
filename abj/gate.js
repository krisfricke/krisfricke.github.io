/* ===========================================================================
   MOCKUP GATE  -  Australian Bee Journal reader
   ---------------------------------------------------------------------------
   TO REMOVE THIS ENTIRELY when the real version ships:
       1. delete the single <script src="gate.js"></script> line from index.html
       2. delete this file
       3. delete the "Disallow: /abj/" line from robots.txt
   Nothing else in the reader is touched or aware of it. That is the whole
   point of doing it this way rather than editing the reader itself.

   WHAT IT IS: a doormat, not a lock. The check runs in the browser, so the
   password can be read out of this file by anyone who opens it. It is here to
   make plain that the issue is not meant to be public, and to keep casual
   visitors and search engines out - nothing more.
   =========================================================================== */

(function () {
  "use strict";

  var KEY  = "abj-gate-ok";                 // remembered for this browser tab
  var WORD = atob("aG9sZ2F0ZQ==");          // not plaintext, not a secret either
  var MSG  = "This is a non-public mockup Australian Bee Journal reader, " +
             "please enter the password";

  /* ?gate on the URL: forget any earlier unlock and ask again. Useful for
     testing, and for showing someone the gate without opening a fresh tab. */
  var forced = location.search.indexOf("gate") >= 0;
  if (forced) sessionStorage.removeItem(KEY);

  if (sessionStorage.getItem(KEY) === "1") return;

  /* Dormant when you are working locally, so the gate can live permanently in
     the working copy and you never have to remember to add it at deploy time.
     ?gate overrides that too, so the gate itself can be tested from a folder. */
  var localish = location.protocol === "file:" ||
                 location.hostname === "localhost" ||
                 location.hostname === "127.0.0.1";
  if (localish && !forced) return;

  /* Hide the page immediately, before anything renders, so the issue never
     flashes up behind the gate on a slow connection. */
  var early = document.createElement("style");
  early.textContent = "html.gated body{visibility:hidden}";
  (document.head || document.documentElement).appendChild(early);
  document.documentElement.className += " gated";

  /* Ask search engines not to index it. robots.txt is the one that actually
     gets obeyed; this is belt and braces for crawlers that render script. */
  var meta = document.createElement("meta");
  meta.name = "robots";
  meta.content = "noindex,nofollow,noarchive";
  (document.head || document.documentElement).appendChild(meta);

  var CSS = [
    /* visibility:visible is doing real work here. The early style hides <body>
       so the issue never flashes up, and this overlay lives inside <body>, so
       without this line it inherits the hiding and you get a blank page. A
       child may override an ancestor's visibility:hidden; that is the one
       property where that works. */
    "#abjgate{visibility:visible;position:fixed;inset:0;z-index:99999;display:flex;align-items:center;",
    "  justify-content:center;padding:24px;background:#16130e;",
    "  background-image:radial-gradient(ellipse at 50% 30%,#241f16 0%,#16130e 70%);",
    "  font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif}",
    /* The reader hides the system cursor (cursor:none !important on everything)
       because the bee replaces it - but the bee is hidden behind this gate, so
       without these you get no pointer at all. An id selector outranks the
       reader's class selector, so these !importants win. */
    "#abjgate,#abjgate *{cursor:default !important}",
    "#abjgate input{cursor:text !important}",
    "#abjgate button{cursor:pointer !important}",
    "#abjgate .card{max-width:430px;width:100%;text-align:center;color:#e9e3d2}",
    "#abjgate .mark{font:700 13px/1 system-ui,sans-serif;letter-spacing:.19em;",
    "  text-transform:uppercase;color:#f9c500;margin-bottom:22px}",
    "#abjgate p{font:17px/1.55 Georgia,'Times New Roman',serif;color:#d8d2c2;margin:0 0 24px}",
    "#abjgate form{display:flex;gap:9px;justify-content:center;flex-wrap:wrap}",
    "#abjgate input{flex:1 1 200px;min-width:0;background:rgba(255,255,255,.06);",
    "  border:1px solid #4b422e;border-radius:9px;padding:12px 14px;color:#fff;",
    "  font:16px/1 system-ui,sans-serif;outline:none}",
    "#abjgate input:focus{border-color:#f9c500;background:rgba(255,255,255,.1)}",
    "#abjgate button{background:#f9c500;color:#16130e;border:none;border-radius:9px;",
    "  padding:12px 24px;font:700 15px/1 system-ui,sans-serif;cursor:pointer}",
    "#abjgate button:hover{background:#ffd733}",
    "#abjgate .no{min-height:20px;margin-top:14px;font:13.5px/1.4 system-ui,sans-serif;",
    "  color:#e08a7a;opacity:0;transition:opacity .18s}",
    "#abjgate .no.on{opacity:1}",
    "#abjgate .card.shake{animation:abjshake .38s}",
    "@keyframes abjshake{10%,90%{transform:translateX(-2px)}30%,70%{transform:translateX(5px)}",
    "  50%{transform:translateX(-7px)}100%{transform:none}}"
  ].join("");

  function build() {
    var s = document.createElement("style");
    s.textContent = CSS;
    document.head.appendChild(s);

    var g = document.createElement("div");
    g.id = "abjgate";
    g.innerHTML =
      '<div class="card">' +
        '<div class="mark">Australian Bee Journal</div>' +
        '<p>' + MSG + '</p>' +
        '<form><input type="password" aria-label="Password" autocomplete="off" ' +
          'autocapitalize="off" spellcheck="false"><button type="submit">Enter</button></form>' +
        '<div class="no" role="status">That is not the password.</div>' +
      '</div>';
    document.body.appendChild(g);

    var card = g.querySelector(".card"),
        input = g.querySelector("input"),
        no = g.querySelector(".no");
    input.focus();

    /* Enter in the box submits. Implicit submission should do this already,
       but belt and braces costs nothing and nobody should be left clicking. */
    var form = g.querySelector("form");
    input.addEventListener("keydown", function (e) {
      if (e.key === "Enter") { e.preventDefault(); g.querySelector("button").click(); }
    });

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      /* trimmed and case-insensitive: nobody should be locked out by a capital */
      if (input.value.trim().toLowerCase() === WORD) {
        sessionStorage.setItem(KEY, "1");
        document.documentElement.className =
          document.documentElement.className.replace(/\bgated\b/, "");
        g.remove();
        return;
      }
      no.className = "no on";
      card.className = "card";       // restart the animation
      void card.offsetWidth;
      card.className = "card shake";
      input.select();
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", build);
  } else {
    build();
  }
})();
