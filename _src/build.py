"""Assembles the site pages from _src/pages/*.html.

Each page file starts with a front-matter block:
    ---
    title: Page title
    description: Meta description
    nav: home            (which nav link is current)
    ---
and may use these placeholders:
    {{nav}} {{footer}} {{loader}} {{cta}}   shared partials
    {{i:name}}                               inline SVG icon
    {{img:name|alt|sizes|class}}             responsive <img> from assets/img/<name>-md/-lg.webp
Run: python _src/build.py   -> writes ../<page>.html
"""
import os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

PHONE = "+263 777 913 493"
PHONE_LINK = "+263777913493"
EMAIL = "info@riquid.co.zw"
ADDRESS = "1 Union Avenue, Harare, Zimbabwe"

ICONS = {
    "arrow-ur": '<path d="M7 17 17 7M8 7h9v9"/>',
    "arrow-r": '<path d="M4 12h16M14 6l6 6-6 6"/>',
    "arrow-l": '<path d="M20 12H4M10 6l-6 6 6 6"/>',
    "phone": '<path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
    "pin": '<path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "check": '<circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "star": '<path fill="currentColor" stroke="none" d="m12 2.8 2.8 5.7 6.3.9-4.6 4.4 1.1 6.2L12 17l-5.6 3 1.1-6.2L2.9 9.4l6.3-.9z"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    "bolt": '<path d="M13 2 4 14h7l-1 8 9-12h-7z"/>',
    "battery": '<rect x="3" y="7" width="16" height="10" rx="2"/><path d="M21 10v4M6 10v4M9 10v4"/>',
    "drop": '<path d="M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z"/>',
    "panel": '<path d="M4 6h16l-2 12H2z"/><path d="M3 12h16M9.5 6 8 18M15.5 6 14 18"/>',
    "home": '<path d="M3 11 12 4l9 7"/><path d="M5 10v10h14V10"/><path d="M10 20v-5h4v5"/>',
    "building": '<rect x="4" y="3" width="12" height="18" rx="1"/><path d="M16 9h4v12h-4M8 7h4M8 11h4M8 15h4"/>',
    "shield": '<path d="M12 3 5 6v5c0 5 3 8.5 7 10 4-1.5 7-5 7-10V6z"/><path d="m9 12 2 2 4-4"/>',
    "wrench": '<path d="M14.5 6.5a4 4 0 0 0 5 5L21 13l-8 8-3-3 8-8-1.5-1.5a4 4 0 0 0-5-5l2.5 2.5-2 2-2.5-2.5"/>',
    "leaf": '<path d="M5 19c0-8 5-14 15-14 0 10-6 15-14 15"/><path d="M5 19c3-4 6-6 9-7"/>',
    "chart": '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
    "users": '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0"/><path d="M16 4.5a3.5 3.5 0 0 1 0 7M18 14.5a6.5 6.5 0 0 1 3.5 5.5"/>',
    "chat": '<path d="M4 5h16v11H9l-5 4z"/>',
    "inverter": '<rect x="5" y="3" width="14" height="18" rx="2"/><rect x="8" y="6" width="8" height="4" rx="1"/><path d="M9 14h6M9 17h6"/>',
    "pump": '<path d="M12 3v6"/><rect x="8" y="9" width="8" height="12" rx="2"/><path d="M5 6h14M10 13h4"/>',
    "cert": '<circle cx="12" cy="9" r="5"/><path d="m9 13-2 8 5-3 5 3-2-8"/>',
    "grid": '<path d="M12 2 7 22M12 2l5 20M4 8h16M6 14h12"/>',
}

def icon(name, cls=""):
    body = ICONS[name]
    c = f' class="{cls}"' if cls else ""
    return f'<svg{c} viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{body}</svg>'

def img(spec):
    parts = spec.split("|")
    name, alt = parts[0], parts[1] if len(parts) > 1 else ""
    sizes = parts[2] if len(parts) > 2 and parts[2] else "100vw"
    cls = f' class="{parts[3]}"' if len(parts) > 3 and parts[3] else ""
    eager = len(parts) > 4 and parts[4] == "eager"
    load = 'fetchpriority="high"' if eager else 'loading="lazy" decoding="async"'
    return (f'<img{cls} src="assets/img/{name}-md.webp" srcset="assets/img/{name}-md.webp 900w, assets/img/{name}-lg.webp 1800w" '
            f'sizes="{sizes}" alt="{alt}" {load}>')

NAV_ITEMS = [("home", "index.html", "Home"), ("about", "about.html", "About"), ("services", "services.html", "Services"),
             ("projects", "projects.html", "Projects"), ("pricing", "pricing.html", "Pricing"), ("contact", "contact.html", "Contact")]

def nav(current):
    links = "".join(f'<a href="{h}"{" aria-current=\"page\"" if k == current else ""}>{t}</a>' for k, h, t in NAV_ITEMS)
    mobile = "".join(f'<li><a class="big" href="{h}">{t}</a></li>' for k, h, t in NAV_ITEMS)
    return f'''<a class="skip" href="#main">Skip to content</a>
<header class="nav" role="banner">
  <a class="brand" href="index.html" aria-label="Riquid Energy home">
    <img class="brand__mark" src="assets/img/logo-mark.png" alt="" width="42" height="42">
    <img class="brand__word" src="assets/img/logo-word.png" alt="Riquid Energy" width="99" height="24">
  </a>
  <nav class="nav__links" aria-label="Main">{links}</nav>
  <div class="nav__right">
    <a class="nav__phone" href="tel:{PHONE_LINK}">{icon("phone")}{PHONE}</a>
    <a class="btn btn--sm" href="contact.html#quote">Get a quote <span class="btn__ic">{icon("arrow-ur")}</span></a>
    <a class="nav__m" href="projects.html"{' aria-current="page"' if current == "projects" else ""}>Projects</a>
    <button class="burger" aria-label="Open menu" aria-expanded="false" aria-controls="mobile-menu"><span></span><span></span><span></span></button>
  </div>
</header>
<div class="mobile-menu" id="mobile-menu">
  <ul>{mobile}</ul>
  <div class="small">{ADDRESS}<br><a href="tel:{PHONE_LINK}">{PHONE}</a> · <a href="mailto:{EMAIL}">{EMAIL}</a></div>
</div>'''

LOADER = '''<div class="loader" aria-hidden="true">
  <svg viewBox="0 0 100 100">
    <circle class="ring-a" cx="50" cy="50" r="42" fill="none" stroke="#e5080f" stroke-width="7" stroke-linecap="round" transform="rotate(-120 50 50)"/>
    <circle class="ring-b" cx="50" cy="50" r="29" fill="none" stroke="#6b7178" stroke-width="5" transform="rotate(60 50 50)"/>
    <g class="core"><circle cx="50" cy="50" r="21" fill="url(#lg)"/><circle cx="43" cy="42" r="6" fill="#fff"/><circle cx="50.5" cy="51" r="3" fill="#fff"/></g>
    <defs><radialGradient id="lg" cx=".38" cy=".35" r=".75"><stop offset="0" stop-color="#ff4b44"/><stop offset=".6" stop-color="#e5080f"/><stop offset="1" stop-color="#9e0309"/></radialGradient></defs>
  </svg>
  <span class="loader__word">Riquid Energy</span>
  <span class="loader__count">000</span>
</div>'''

def cta():
    return f'''<section class="section section--tight">
  <div class="container">
    <div class="cta" data-reveal="clip">
      {img("sun-sky|Sun shining in a clear blue sky||")}
      <img class="obj" src="assets/img/obj/obj-sun.webp" alt="" aria-hidden="true" data-parallax="-.08">
      <div>
        <span class="eyebrow" style="color:#fff;border-color:rgba(255,255,255,.3)">Go Riquid</span>
        <h2 class="h1" style="margin-top:20px" data-split>Turn up the brightness.</h2>
      </div>
      <div style="display:grid;gap:16px;justify-items:start;max-width:300px">
        <p style="color:rgba(255,255,255,.8)">A free survey and a fixed quote, no obligation.</p>
        <a class="btn btn--light" href="contact.html#quote">Book a free survey <span class="btn__ic">{icon("arrow-ur")}</span></a>
      </div>
    </div>
  </div>
</section>'''

def footer():
    return f'''<footer class="footer" role="contentinfo">
  <div class="bloom bloom--red" aria-hidden="true"></div>
  <div class="footer__top">
    <div style="display:grid;gap:22px;justify-items:start">
      <a class="brand" href="index.html" aria-label="Riquid Energy home">
        <img class="brand__mark" src="assets/img/logo-mark-light.png" alt="" width="42" height="42">
        <img class="brand__word" src="assets/img/logo-word-light.png" alt="Riquid Energy" width="99" height="24">
      </a>
      <p class="h3">Clean, safe, renewable energy for Zimbabwe.</p>
      <a class="btn btn--light btn--sm" href="contact.html#quote">Get a quote <span class="btn__ic">{icon("arrow-ur")}</span></a>
    </div>
    <div class="socials">
      <a href="https://www.facebook.com/riquides" target="_blank" rel="noopener">Facebook{icon("arrow-ur")}</a>
      <a href="https://twitter.com/RiquidEnergySol" target="_blank" rel="noopener">X / Twitter{icon("arrow-ur")}</a>
      <a href="https://wa.me/{PHONE_LINK.lstrip('+')}" target="_blank" rel="noopener">WhatsApp{icon("arrow-ur")}</a>
      <a href="https://www.linkedin.com/search/results/all/?keywords=Riquid%20Energy" target="_blank" rel="noopener">LinkedIn{icon("arrow-ur")}</a>
    </div>
  </div>
  <div class="footer__cols">
    <div><h4>Company</h4><ul><li><a href="about.html">About us</a></li><li><a href="projects.html">Projects</a></li><li><a href="pricing.html">Pricing &amp; packages</a></li><li><a href="contact.html">Contact</a></li></ul></div>
    <div><h4>Services</h4><ul><li><a href="services.html#panels">Solar panels</a></li><li><a href="services.html#inverters">Hybrid inverters</a></li><li><a href="services.html#batteries">Lithium batteries</a></li><li><a href="services.html#dc-pumps">Borehole pumps</a></li><li><a href="services.html#maintenance">Maintenance</a></li></ul></div>
    <div><h4>Visit</h4><ul><li><a href="contact.html">1 Union Ave, Harare</a></li><li><a href="tel:{PHONE_LINK}">{PHONE}</a></li><li><a href="mailto:{EMAIL}">{EMAIL}</a></li><li><a href="contact.html">Mon to Sat</a></li><li><a href="contact.html">08:00 to 18:30</a></li></ul></div>
    <div><h4>Newsletter</h4><p class="small" style="color:rgba(255,255,255,.55);margin-bottom:14px">Tips and offers, once a month.</p>
      <form class="news"><label class="sr-only" for="nl-{{{{page}}}}">Email address</label><input id="nl-{{{{page}}}}" type="email" placeholder="Your email" required><button type="submit">Subscribe</button></form></div>
  </div>
  <div class="footer__word" aria-hidden="true">Riquid</div>
  <div class="footer__bar"><span>© <span data-year>2026</span> Riquid Energy Solutions. All rights reserved.</span><span class="fclock" data-clock><i></i><span>Harare, Zimbabwe</span></span><a class="totop" href="#main">Back to top {icon("arrow-r")}</a></div>
</footer>'''

HEAD = '''<!doctype html>
<html lang="en" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<meta name="theme-color" content="#0e0f11">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:image" content="assets/img/{og}-lg.webp">
<meta property="og:type" content="website">
<link rel="icon" type="image/png" href="assets/img/logo-mark.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@300..700&family=Geist+Mono:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/css/style.css">
{extra_head}</head>
<body data-page="{page}">
'''

TAIL = '''<script src="https://unpkg.com/lenis@1.1.13/dist/lenis.min.js" defer></script>
{extra_js}<script src="assets/js/main.js" defer></script>
</body>
</html>
'''

def build():
    src = os.path.join(HERE, "pages")
    for fn in sorted(os.listdir(src)):
        if not fn.endswith(".html"):
            continue
        raw = open(os.path.join(src, fn), encoding="utf8").read()
        m = re.match(r"---\n(.*?)\n---\n", raw, re.S)
        meta = dict(l.split(": ", 1) for l in m.group(1).splitlines())
        body = raw[m.end():]
        page = fn[:-5]
        body = (body.replace("{{nav}}", nav(meta.get("nav", page))).replace("{{footer}}", footer())
                .replace("{{loader}}", LOADER).replace("{{cta}}", cta()).replace("{{page}}", page)
                .replace("{{phone}}", PHONE).replace("{{phone_link}}", PHONE_LINK)
                .replace("{{email}}", EMAIL).replace("{{address}}", ADDRESS))
        body = re.sub(r"\{\{i:([\w-]+)\}\}", lambda mm: icon(mm.group(1)), body)
        body = re.sub(r"\{\{img:([^}]+)\}\}", lambda mm: img(mm.group(1)), body)
        extra_js = '<script src="assets/js/map-data.js" defer></script>\n' if "data-zmap" in body else ""
        extra_head = meta.get("preload", "")
        if extra_head:
            extra_head = f'<link rel="preload" as="image" href="{extra_head}">\n'
        html = HEAD.format(title=meta["title"], description=meta["description"], og=meta.get("og", "harare-skyline"),
                           extra_head=extra_head, page=page) + body + TAIL.format(extra_js=extra_js)
        left = re.findall(r"\{\{[^}]*\}\}", html)
        if left:
            raise SystemExit(f"{fn}: unreplaced placeholders {left}")
        open(os.path.join(ROOT, fn), "w", encoding="utf8").write(html)
        print("built", fn, len(html) // 1024, "KB")

if __name__ == "__main__":
    build()
