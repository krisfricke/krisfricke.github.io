/* The Australasian Beekeeper website - settings.
   Edit this file and reload the page; nothing needs rebuilding. Everything else the site shows
   comes from data/clubs.json, data/stores.json and data/products.json. */
window.ABK_CONFIG = {

  /* ---- THE SUBSCRIBE FORM ------------------------------------------------------------
     endpoint  where the form is sent: the "form action" address your mailing-list service
               gives you for an embedded sign-up form (or a form service such as Formspree).
               While it is "" the site is in PREVIEW MODE: the form works on screen, the
               browser is remembered as subscribed, and NOTHING IS SENT ANYWHERE.
     method    "form"  - an ordinary form post into a hidden frame. Works with any service's
                         sign-up address. The reply cannot be read, so "the frame loaded" is
                         taken as "sent".
               "fetch" - a background request that reads the reply (Formspree and others that
                         answer with JSON and allow it).
     fields    what your service calls each field (left: this site's name; right: theirs).
               Give "" to leave a field out.
     extra     fixed fields the service wants with every form (a list id, a hidden tag...). */
  subscribe: {
    endpoint: "",
    method: "form",
    fields: { name: "name", email: "email", street: "street", state: "state",
              postcode: "postcode", print: "print_edition", update: "update" },
    extra: {}
  },

  /* A link that carries ?sub=1 (for example https://theabk.com.au/?sub=1) marks the browser
     that opens it as a subscriber's. Use it for the links in the monthly email, so a
     subscriber is recognised on any device, whether or not they signed up on it. */
  subscriberParam: "sub",

  /* Honey sales: how far round a visitor honey sellers are listed, and where a beekeeper's listing is sent. With
     endpoint "" the listing opens as an e-mail to emails.editor in the beekeeper's own e-mail program; put a form
     service's address here to have it sent straight from the page (fields: honey_place, honey_address, honey_state,
     honey_postcode, honey_phone, honey_hours, honey_honey, name, email). Listings are added by hand to
     data/honey.js: {"name", "address", "lat", "lon", "hours", "phone", "honey": ["yellow box", ...]}. */
  honey: { radiusKm: 50, endpoint: "" },
  emails: { advertising: "advertising@theabk.com.au", editor: "editor@theabk.com.au" },

  /* ---- FINDING THE NEAREST CLUB AND STORE --------------------------------------------
     A subscriber's address is turned into a point on the map once, in their own browser, and
     kept there.
     geocoder: "address" - when they give a street address, the browser asks OpenStreetMap
               (Nominatim) for that street, postcode and state, and places them at their door;
               without one, or if OpenStreetMap does not know it, at the middle of their postcode.
               The form tells subscribers this. (Kris, 15 Nov 2026.)
               "postcode" - the middle of the postcode only, and OpenStreetMap is asked only
               about a postcode the table below does not have.
               "none" - the postcode table only: nothing about the reader leaves the browser.
     postcodeTable: data/postcodes.js, every Australian postcode, ships with the site. */
  postcodeTable: true,
  geocoder: "address",
  radiusKm: 50,          /* clubs within this distance are listed with their next meetings */
  storeCount: 5,         /* how many of the nearest stores to show */

  /* ---- ADVERTISING -------------------------------------------------------------------
     price: a number of dollars, or null to show "on request".
     The sizes are the magazine's own (the December 2026 layout, 128.1): every ad sits inside the
     type area on a light blue surround, so a full page is the type area, not the trimmed page. */
  advertising: {
    page: [ ["Page (trim)", "210 × 294 mm"], ["Type area", "184 × 263 mm"], ["Every ad", "is set on a light blue border; supply artwork at the size listed, without bleed"] ],
    display: [
      { name: "Full page",            size: "184 × 263 mm",         price: null },
      { name: "Half page, across",    size: "184 × 129 mm",         price: null },
      { name: "Half page, upright",   size: "90 × 263 mm",          price: null },
      { name: "Quarter page",         size: "90 × 129 mm",          price: null },
      { name: "Business card",        size: "90 × 55 mm",           price: null }
    ],
    classifieds: [
      { name: "Classified, 30 words, with photo", size: "",           price: 35 },
      { name: "Small boxed advert",               size: "60 × 50 mm", price: 55 },
      { name: "Large boxed advert",               size: "60 × 90 mm", price: 95 }
    ],
    artwork: "Press-ready PDF, or JPEG/TIFF at 300 dpi at the printed size."
  }
};
