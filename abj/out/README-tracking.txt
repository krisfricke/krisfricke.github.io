AD CLICKTHROUGH TRACKING - how it works and how to read the numbers
==================================================================

Every advertisement in the reader links to  /reader/out/<slug>/  rather than
straight to the advertiser's site. Apache answers with a 302 redirect to the
real website, so the reader notices no delay, but the hit is written to your
normal server access log on the way through.

TO SEE THE COUNTS
  cPanel > Metrics > AWStats, or cPanel > Metrics > Raw Access Logs
  Look for URLs beginning  /reader/out/
  One hit = one click on that advertisement.

WHY THIS WAY
  * No cookies, no Google, no third-party service, no monthly fee.
  * Nothing is recorded about the visitor beyond what your web server already
    logs for every page request.
  * It is a 302, so browsers do not cache it and repeat clicks all count.

ADVERTISERS
  kelvin-trading         https://ktbeekeeping.com.au/                    Yarra Bee / Kelvin Trading
  aussie-cti             https://aussiecti.com.au/                       Aussie CTI Systems
  prestige-stainless     https://www.prestigestainless.com.au/           Prestige Stainless
  lyson                  https://www.lysonau.com.au/                     Lyson Australia
  beeplas                https://www.danbar.com.au/                      Beeplas Australia (Danbar Plastics)
  buzzbee                https://buzzbee.com.au/                         Buzz Bee
  veto-pharma            https://www.veto-pharma.com/                    Veto-pharma
  air-cti                https://aircti.com/                             AIR CTI
  whirrakee-woodware     https://whirrakeewoodware.com.au/               Whirrakee Woodware
  steritech              https://www.steritech.com.au/                   Steritech
  aluen-cap              https://www.capproducts.com.au/                 Aluen CAP
  dalrymple-view         https://www.dalrympleview.com.au/               Dalrymple View Apiary Supplies
  ezyloader              https://www.ezyloader.com/                      EzyLoader / M & K Stafford Engineering
  aust-queen-bee-line    https://www.australianqueenbeeline.com.au/      Australian Queen Bee Line

VAA HOUSE ADS (tracked the same way)
  cvaa-conference        https://vicbeekeepers.com.au/Upcoming-Events    CVAA Conference (Central Victorian Apiarists Association)
  bendigo-field-day      https://vicbeekeepers.com.au/BendigoBranch      Bendigo Branch Field Day
  hivemeet               https://www.youtube.com/@VictorianApiaristsAssociation/streams  VAA HiveMeet
  royal-show             https://vicbeekeepers.com.au/Upcoming-Events    VAA at the Melbourne Royal Show

NOT LINKED - no website found
  Denmar Apiaries (p24)
  Australian Queen Bee Exporters (p8)
  Whirrakee Honey (p42)
  Jeeralang Apiary Supplies (p42, business for sale)

MAINTENANCE
  To add an advertiser: add one RewriteRule to out/.htaccess, create
  out/<slug>/index.html as a fallback, and point the ad hotspot at it.
  Hotspots live either in html/<issue>/<page>.html (pages with live text)
  or in the LINKS table inside index.html (pages still shown as images).
