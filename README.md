# Riquid Energy website

A static, six-page marketing site for Riquid Energy Solutions (Harare, Zimbabwe). It is plain HTML, CSS and JS with no build step needed to host it. Upload the folder to any static host.

| Page | File | Highlights |
|---|---|---|
| Home | `index.html` | Skyline hero with the wordmark *behind* the buildings, scroll-fill statement, dot-matrix chart, stacking solution cards, six 3D service objects, project carousel, glass stat cards, shape cards, pricing, glass orb testimonials, Zimbabwe dot map, FAQ, quote form |
| About | `about.html` | Story, mission, values, Harare sun-hours chart, self-sufficiency gauge, timeline, map |
| Services | `services.html` | Sticky service index, six service blocks, interactive energy-flow diagram (4 scenarios), 24-hour production vs demand chart, process |
| Projects | `projects.html` | Mount Pleasant 12 kW case study (KPIs, monthly generation chart, gauge), filterable portfolio, project map |
| Pricing | `pricing.html` | Packages, savings calculator with 10-year spend chart, inclusions, FAQ |
| Contact | `contact.html` | Call/WhatsApp/email cards, quote form, Google map, coverage map, FAQ |

## Editing pages

Pages are assembled from `_src/pages/*.html`. They share one nav, footer, loader and CTA, defined in `_src/build.py`. Edit the source, then rebuild:

```
python _src/build.py
```

Do not edit the root `*.html` files directly, because the next build overwrites them. Phone, email and address are set once at the top of `build.py`.

## Design system

- **Colours** (`assets/css/style.css`, `:root`): `--red #e5080f` (logo red), `--ink #0e0f11`, `--charcoal #3f474f` (logo grey), `--bone #f4f3f0` (card surface), `--sky #2f6fb8` (second chart series only). The chart pair red/sky was checked for colour-blind separation and contrast.
- **Type:** Geist and Geist Mono (Google Fonts). Headings are weight 400 with tight negative tracking.
- **Motion:** `[data-reveal]` fades and rises elements in, `[data-reveal="clip"]` opens an image from a rounded inset, `[data-split]` slides headings in line by line, `[data-fill]` colours a statement word by word while scrolling, `[data-count]` counts numbers up, and `[data-parallax]` and `[data-tilt]` add scroll and pointer depth. Lenis provides smooth scrolling on desktop. Everything respects `prefers-reduced-motion`.
- **Touch devices:** every hover effect has a touch equivalent. `.is-inview` is toggled as an element crosses the middle of the screen, glass chips drift with the scroll instead of following the cursor, and buttons scale down on press. Phones get a vertical energy-flow diagram, charts redrawn at the real screen width, and map labels reduced to the HQ (tap any pin for details).
- **Copy:** keep headlines to 2–6 words and card text to one short line. The layout is tuned for short text.
- **Patterns** (`style.css` section 14): drawn in CSS, no images. A PV cell tile (chamfered cells, two busbars) on dark surfaces, dots on light cards, a hatch on red tiles and sun rays in the footer, each masked into a corner at 8–20% strength. Change `--pat-ink` / `--pat-white` to tune them all at once.
- **Glass:** `.glass` / `.glass--dark` (backdrop blur over photos), `.testi-orb` (glass sphere over a red bloom), and `.glass-tile`.
- **Charts** (`main.js`): hand-built SVG line, area, bar, dot-matrix and gauge charts, each with hover tooltips and a "View as table" option.

## Generated assets (`_src/tools/`)

| Script | Output |
|---|---|
| `build_images.py <photos folder>` | `assets/img/*-md.webp` (900px) and `*-lg.webp` (1800px), plus the logo split into mark and wordmark, with light variants for dark backgrounds |
| `hero_cutout.py <skyline.jpg>` | `hero-bg.webp` and `hero-fg.webp` (the skyline with transparency) for the layered hero |
| `render3d.py [names]` | `assets/img/obj/obj-*.webp`: eight ray-marched 3D objects (panel, ribbon/inverter, battery, droplet, impeller, gear, ring and sun) in brand red, chrome, charcoal, pearl and black |
| `build_map.py` | `assets/js/map-data.js`: the Zimbabwe dot grid and city positions |

To change an object's angle or material, edit `OBJECTS` or `shade()` in `render3d.py` and re-run it with that object's name. It needs Python with numpy and Pillow; the hero and map scripts also need scipy.

## Before launch: confirm with Riquid

Search the source for `CONFIRM` and `PLACEHOLDER`.

1. **Photo licences.** The `istockphoto-*` images are watermarked comps. License them, re-run `build_images.py` on the clean files, and the site picks them up automatically.
2. **Testimonials.** The three quotes, names and the 4.9 rating are placeholders.
3. **Numbers.** "350+ systems" and the "up to 80%" saving claim need sign-off. Real facts used: founded 2020, the 12 kW Mount Pleasant project, 2,800+ Facebook followers, 1 Union Avenue, +263 777 913 493 and info@riquid.co.zw.
4. **Prices.** $1,690 and $3,450 are indicative, as are the calculator's assumptions ($0.14/kWh, $520/kWp, $300/kWh of storage).
5. **Projects.** Only Mount Pleasant is a named real project. The other portfolio titles are descriptive. The case-study output and solar share are modelled.
6. **Timeline** milestones for 2021–2023.
7. **Hours.** The old site listed both Mon–Sat 9–6:30 and Mon–Sun 8–6:30. The new site uses Mon–Sat 08:00–18:30.
8. **Address.** Google Maps resolves Union Avenue to its current name, Kwame Nkrumah Avenue.
9. **Forms.** There is no backend yet. Submitting opens the visitor's email app with the request pre-filled. Connect a form service (Formspree, Netlify Forms, or similar) for direct submissions.
