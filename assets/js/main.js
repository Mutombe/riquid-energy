/* Riquid Energy: interactions, motion and charts. No framework; Lenis is optional. */
(() => {
  "use strict";
  const doc = document.documentElement;
  doc.classList.remove("no-js");
  const $ = (s, c = document) => c.querySelector(s);
  const $$ = (s, c = document) => [...c.querySelectorAll(s)];
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const touch = matchMedia("(hover: none)").matches;
  const NS = "http://www.w3.org/2000/svg";
  const svgEl = (tag, attrs = {}, parent) => {
    const el = document.createElementNS(NS, tag);
    for (const k in attrs) el.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(el);
    return el;
  };
  const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
  const lerp = (a, b, t) => a + (b - a) * t;
  const store = {
    get(k) { try { return sessionStorage.getItem(k); } catch (e) { return null; } },
    set(k, v) { try { sessionStorage.setItem(k, v); } catch (e) { /* private mode */ } },
  };
  const css = (name) => getComputedStyle(doc).getPropertyValue(name).trim();

  /* ---------------------------------------------------------------- loader */
  const loader = $(".loader");
  const ready = () => requestAnimationFrame(() => doc.classList.add("is-ready"));
  if (loader) {
    const first = !store.get("rq-seen");
    store.set("rq-seen", "1");
    const count = $(".loader__count", loader);
    const dur = reduce ? 0 : first ? 1500 : 450;
    const t0 = performance.now();
    const tick = (t) => {
      const p = clamp((t - t0) / Math.max(dur, 1), 0, 1);
      if (count) count.textContent = String(Math.round(p * 100)).padStart(3, "0");
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
    const done = () => setTimeout(() => {
      loader.classList.add("is-done");
      ready();
      setTimeout(() => loader.remove(), 1100);
    }, dur);
    if (document.readyState === "complete") done(); else addEventListener("load", done, { once: true });
    setTimeout(() => { if (!loader.classList.contains("is-done")) { loader.classList.add("is-done"); ready(); } }, 4500);
  } else ready();

  /* ---------------------------------------------------------------- smooth scroll */
  let lenis = null;
  if (window.Lenis && !reduce && !touch) {
    lenis = new window.Lenis({ duration: 1.15, easing: (t) => 1 - Math.pow(1 - t, 4), smoothWheel: true });
    const raf = (t) => { lenis.raf(t); requestAnimationFrame(raf); };
    requestAnimationFrame(raf);
  }
  $$('a[href^="#"]').forEach((a) => a.addEventListener("click", (e) => {
    const id = a.getAttribute("href");
    if (id.length < 2) return;
    const target = $(id);
    if (!target) return;
    e.preventDefault();
    if (lenis) lenis.scrollTo(target, { offset: -110 });
    else window.scrollTo({ top: target.getBoundingClientRect().top + scrollY - 110, behavior: reduce ? "auto" : "smooth" });
  }));

  /* ---------------------------------------------------------------- nav */
  const nav = $(".nav");
  let lastY = scrollY;
  const onNav = () => {
    const y = scrollY;
    if (!nav) return;
    nav.classList.toggle("is-scrolled", y > 30);
    nav.classList.toggle("is-hidden", y > 500 && y > lastY + 4 && !doc.classList.contains("menu-open"));
    if (y < lastY - 4) nav.classList.remove("is-hidden");
    lastY = y;
  };
  const burger = $(".burger");
  if (burger) burger.addEventListener("click", () => {
    const open = doc.classList.toggle("menu-open");
    burger.setAttribute("aria-expanded", open);
    if (lenis) open ? lenis.stop() : lenis.start();
  });
  const closeMenu = () => {
    doc.classList.remove("menu-open");
    if (burger) burger.setAttribute("aria-expanded", false);
    if (lenis) lenis.start();
  };
  $$(".mobile-menu a").forEach((a) => a.addEventListener("click", closeMenu));
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && doc.classList.contains("menu-open")) { closeMenu(); burger && burger.focus(); }
  });

  /* ---------------------------------------------------------------- reveal observer */
  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
      if (!e.isIntersecting) return;
      e.target.classList.add("is-visible", "is-drawn");
      e.target.dispatchEvent(new CustomEvent("reveal"));
      io.unobserve(e.target);
    });
  }, { rootMargin: "0px 0px -12% 0px", threshold: 0.01 });
  $$("[data-reveal], [data-draw]").forEach((el) => io.observe(el));
  // A fast flick or the End key can skip past an element between observer callbacks; sweep anything already above the fold.
  let sweepT = 0;
  addEventListener("scroll", () => {
    clearTimeout(sweepT);
    sweepT = setTimeout(() => $$("[data-reveal]:not(.is-visible), [data-draw]:not(.is-drawn)").forEach((el) => {
      if (el.getBoundingClientRect().top < innerHeight) { el.classList.add("is-visible", "is-drawn"); el.dispatchEvent(new CustomEvent("reveal")); io.unobserve(el); }
    }), 150);
  }, { passive: true });

  /* ---------------------------------------------------------------- split lines */
  // Wraps each visual line of a heading so lines can slide up one after another.
  const splitAll = () => $$("[data-split]").forEach((el) => {
    const words = el.innerHTML.trim().split(/\s+(?![^<]*>)/);
    el.innerHTML = words.map((w) => `<span class="sw">${w}</span>`).join(" ");
    const spans = $$(".sw", el);
    const lines = [];
    let top = null;
    spans.forEach((s) => {
      const t = Math.round(s.offsetTop);
      if (t !== top) { lines.push([]); top = t; }
      lines[lines.length - 1].push(s.innerHTML);
    });
    el.innerHTML = lines.map((l, i) => `<span class="line" style="--l:${i}"><span>${l.join(" ")}</span></span>`).join("");
    el.classList.add("split-lines");
    io.observe(el);
  });

  (document.fonts && document.fonts.ready ? document.fonts.ready : Promise.resolve()).then(splitAll);


  /* ---------------------------------------------------------------- counters */
  const fmt = (v, dec, group = true) => v.toLocaleString("en-US", { minimumFractionDigits: dec, maximumFractionDigits: dec, useGrouping: group });
  $$("[data-count]").forEach((el) => {
    const end = parseFloat(el.dataset.count);
    const dec = (el.dataset.count.split(".")[1] || "").length;
    const pre = el.dataset.prefix || "", suf = el.dataset.suffix || "", grp = !("nogroup" in el.dataset);
    el.textContent = pre + fmt(reduce ? end : 0, dec, grp) + suf;
    const run = () => {
      if (reduce) return;
      const t0 = performance.now(), d = 1800;
      const step = (t) => {
        const p = clamp((t - t0) / d, 0, 1), k = 1 - Math.pow(1 - p, 4);
        el.textContent = pre + fmt(end * k, dec, grp) + suf;
        if (p < 1) requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
    };
    const o = new IntersectionObserver(([e]) => { if (e.isIntersecting) { run(); o.disconnect(); } }, { threshold: 0.6 });
    o.observe(el);
  });

  /* ---------------------------------------------------------------- statement fill */
  const statements = $$("[data-fill]").map((el) => {
    const hl = (el.dataset.fill || "").split("|").map((s) => s.trim().toLowerCase()).filter(Boolean);
    const words = el.textContent.trim().split(/\s+/);
    el.innerHTML = words.map((w) => {
      const bare = w.toLowerCase().replace(/[^a-z0-9%]/g, "");
      return `<span class="w${hl.includes(bare) ? " hl" : ""}">${w}</span>`;
    }).join(" ");
    return { el, words: $$(".w", el) };
  });
  const onFill = () => {
    statements.forEach(({ el, words }) => {
      const r = el.getBoundingClientRect();
      const p = clamp((innerHeight * 0.85 - r.top) / (r.height + innerHeight * 0.35), 0, 1);
      const n = Math.round(p * words.length);
      words.forEach((w, i) => w.classList.toggle("is-on", i < n || reduce));
    });
  };

  /* ---------------------------------------------------------------- parallax */
  const parallax = $$("[data-parallax]").map((el) => ({ el, s: parseFloat(el.dataset.parallax) || 0.1 }));
  const hero = $(".hero__frame");
  const heroLayers = hero ? { bg: $(".hero__bg", hero), fg: $(".hero__fg", hero), word: $(".hero__word", hero), content: $(".hero__content", hero) } : null;
  const pageHeroImg = $(".page-hero__frame > img");
  const onParallax = () => {
    if (reduce) return;
    const y = scrollY;
    if (heroLayers && y < innerHeight * 1.2) {
      heroLayers.bg && (heroLayers.bg.style.translate = `0 ${y * 0.18}px`);
      heroLayers.word && (heroLayers.word.style.translate = `0 ${y * 0.42}px`);
      heroLayers.fg && (heroLayers.fg.style.translate = `0 ${y * 0.06}px`);
      heroLayers.content && (heroLayers.content.style.translate = `0 ${y * -0.08}px`);
    }
    if (pageHeroImg && y < innerHeight * 1.2) pageHeroImg.style.translate = `0 ${y * 0.2}px`;
    tiltTouch.forEach((el) => {
      const d = (parseFloat(el.dataset.tilt) || 20) * 0.5;
      el.style.transform = `translate3d(${(Math.sin(y / 160) * d).toFixed(1)}px, ${(Math.cos(y / 200) * d).toFixed(1)}px, 0)`;
    });
    parallax.forEach(({ el, s }) => {
      const r = el.getBoundingClientRect();
      if (r.bottom < -200 || r.top > innerHeight + 200) return;
      const c = r.top + r.height / 2 - innerHeight / 2;
      el.style.translate = `0 ${(-c * s).toFixed(1)}px`;
    });
  };

  // pointer parallax for glass chips and floating objects
  if (!touch && !reduce) {
    const tilt = $$("[data-tilt]");
    let mx = 0, my = 0, cx = 0, cy = 0;
    addEventListener("pointermove", (e) => { mx = e.clientX / innerWidth - 0.5; my = e.clientY / innerHeight - 0.5; }, { passive: true });
    const loop = () => {
      cx = lerp(cx, mx, 0.06); cy = lerp(cy, my, 0.06);
      tilt.forEach((el) => {
        const d = parseFloat(el.dataset.tilt) || 20;
        el.style.transform = `translate3d(${cx * d}px, ${cy * d}px, 0)`;
      });
      requestAnimationFrame(loop);
    };
    if (tilt.length) loop();
    // magnetic buttons
    $$(".btn, .round-btn").forEach((b) => {
      b.addEventListener("pointermove", (e) => {
        const r = b.getBoundingClientRect();
        b.style.transform = `translate(${(e.clientX - r.left - r.width / 2) * 0.12}px, ${(e.clientY - r.top - r.height / 2) * 0.2}px)`;
      });
      b.addEventListener("pointerleave", () => { b.style.transform = ""; });
    });
  }

  /* ---------------------------------------------------------------- touch: hover effects play in view */
  // On phones and tablets there is no hover, so anything with a hover effect gets .is-inview
  // while it crosses the middle band of the screen, and the glass chips drift with the scroll.
  const tiltTouch = touch && !reduce ? $$("[data-tilt]") : [];
  if (touch) {
    const sel = ".svc, .b-photo, .sol-card, .feat, .scard, .pcard, .ccard, .value, .link-arrow, .btn, .num-card, .t-card";
    const o = new IntersectionObserver((es) => es.forEach((e) => e.target.classList.toggle("is-inview", e.isIntersecting)), { rootMargin: "-38% 0px -38% 0px" });
    $$(sel).forEach((c) => o.observe(c));
  }

  /* ---------------------------------------------------------------- scroll loop */
  let ticking = false;
  const onScroll = () => {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(() => { onNav(); onFill(); onParallax(); onStack(); onIndex(); ticking = false; });
  };
  addEventListener("scroll", onScroll, { passive: true });
  addEventListener("resize", onScroll);

  /* ---------------------------------------------------------------- stacked solution cards */
  const stack = $$(".sol-card");
  function onStack() {
    if (reduce || innerWidth < 700) return;
    stack.forEach((c, i) => {
      const next = stack[i + 1];
      if (!next) return;
      const r = c.getBoundingClientRect(), n = next.getBoundingClientRect();
      const p = clamp(1 - (n.top - r.top) / r.height, 0, 1);
      c.style.transform = `scale(${1 - p * 0.05})`;
      c.style.filter = `brightness(${1 - p * 0.12})`;
    });
  }

  /* ---------------------------------------------------------------- services index highlight */
  const idxLinks = $$(".svc-index a");
  const idxTargets = idxLinks.map((a) => $(a.getAttribute("href"))).filter(Boolean);
  function onIndex() {
    if (!idxTargets.length) return;
    let cur = 0;
    idxTargets.forEach((t, i) => { if (t.getBoundingClientRect().top < innerHeight * 0.4) cur = i; });
    idxLinks.forEach((a, i) => a.classList.toggle("is-active", i === cur));
  }

  /* ---------------------------------------------------------------- hero live chip */
  const spark = $("[data-spark]");
  if (spark) {
    const val = $("[data-spark-value]");
    const W = 200, H = 38, N = 28;
    const pts = Array.from({ length: N }, (_, i) => 3.6 + Math.sin(i / 3) * 0.5 + Math.random() * 0.3);
    svgEl("defs", {}, spark).innerHTML = '<linearGradient id="sg" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".45"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>';
    const area = svgEl("path", { fill: "url(#sg)" }, spark);
    const line = svgEl("path", { fill: "none", stroke: "#fff", "stroke-width": 2, "stroke-linecap": "round", "stroke-linejoin": "round" }, spark);
    const dot = svgEl("circle", { r: 3.5, fill: "#fff" }, spark);
    spark.setAttribute("viewBox", `0 0 ${W} ${H}`);
    spark.setAttribute("preserveAspectRatio", "none");
    const draw = () => {
      const x = (i) => (i / (N - 1)) * W, y = (v) => H - ((v - 2.8) / 2) * H;
      const d = pts.map((v, i) => `${i ? "L" : "M"}${x(i).toFixed(1)} ${y(v).toFixed(1)}`).join("");
      line.setAttribute("d", d);
      area.setAttribute("d", `${d}L${W} ${H}L0 ${H}Z`);
      dot.setAttribute("cx", W); dot.setAttribute("cy", y(pts[N - 1]));
      if (val) val.textContent = pts[N - 1].toFixed(2);
    };
    draw();
    if (!reduce) setInterval(() => { pts.shift(); const l = pts[pts.length - 1]; pts.push(clamp(l + (Math.random() - 0.48) * 0.35, 3, 4.6)); draw(); }, 1400);
  }

  /* ---------------------------------------------------------------- dot-matrix chart (bento) */
  // Monthly bill index after switching (illustrative): 12 columns of dots, filled dots = what you still pay.
  $$("[data-dotchart]").forEach((svg) => {
    const vals = svg.dataset.dotchart.split(",").map(Number);
    const rows = 9, W = 300, H = 170, padB = 18;
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    svg.setAttribute("role", "img");
    const cw = W / vals.length, rh = (H - padB) / rows;
    const ink = css("--ink"), red = css("--red"), off = "rgba(14,15,17,.10)";
    const dots = [];
    vals.forEach((v, c) => {
      const filled = Math.round(v * rows);
      for (let r = 0; r < rows; r++) {
        const on = r < filled;
        const top = r === filled - 1;
        const el = svgEl("circle", { cx: cw * c + cw / 2, cy: H - padB - rh * r - rh / 2, r: 0, fill: on ? (top && c === vals.length - 1 ? red : ink) : off }, svg);
        dots.push({ el, on, c, r, rad: on ? 4.2 : 3 });
      }
    });
    ["Jan", "Apr", "Jul", "Oct", "Dec"].forEach((m, i, a) => {
      const t = svgEl("text", { x: (i / (a.length - 1)) * (W - cw) + cw / 2, y: H - 2, "text-anchor": "middle", class: "ax" }, svg);
      t.textContent = m;
    });
    const show = () => dots.forEach((d) => setTimeout(() => d.el.setAttribute("r", d.rad), reduce ? 0 : d.c * 60 + d.r * 25));
    svg.addEventListener("reveal", show);
    io.observe(svg);
  });

  /* ---------------------------------------------------------------- projects carousel */
  $$("[data-carousel]").forEach((root) => {
    const track = $(".proj-track", root), view = $(".proj-viewport", root);
    const cards = $$(".proj-card", root);
    const prev = $("[data-prev]", root), next = $("[data-next]", root), count = $(".projects__count", root);
    let i = 0;
    const go = (n) => {
      i = clamp(n, 0, cards.length - 1);
      const x = cards[i].offsetLeft - cards[0].offsetLeft;
      track.style.transform = `translateX(${-x}px)`;
      cards.forEach((c, k) => c.classList.toggle("is-active", k === i));
      prev && (prev.disabled = i === 0);
      next && (next.disabled = i === cards.length - 1);
      if (count) count.textContent = `${String(i + 1).padStart(2, "0")} / ${String(cards.length).padStart(2, "0")}`;
    };
    prev && prev.addEventListener("click", () => go(i - 1));
    next && next.addEventListener("click", () => go(i + 1));
    let sx = 0, dx = 0, drag = false;
    view.addEventListener("pointerdown", (e) => { drag = true; sx = e.clientX; dx = 0; view.classList.add("is-drag"); track.style.transition = "none"; view.setPointerCapture(e.pointerId); });
    view.addEventListener("pointermove", (e) => {
      if (!drag) return;
      dx = e.clientX - sx;
      track.style.transform = `translateX(${-(cards[i].offsetLeft - cards[0].offsetLeft) + dx}px)`;
    });
    const end = () => {
      if (!drag) return;
      drag = false; view.classList.remove("is-drag"); track.style.transition = "";
      if (Math.abs(dx) > 60) go(i + (dx < 0 ? 1 : -1)); else go(i);
    };
    view.addEventListener("pointerup", end);
    view.addEventListener("pointercancel", end);
    root.addEventListener("keydown", (e) => { if (e.key === "ArrowRight") go(i + 1); if (e.key === "ArrowLeft") go(i - 1); });
    addEventListener("resize", () => go(i));
    go(0);
  });

  /* ---------------------------------------------------------------- filters (projects page) */
  $$("[data-filter-group]").forEach((g) => {
    const items = $$(g.dataset.filterGroup);
    $$("button", g).forEach((b) => b.addEventListener("click", () => {
      $$("button", g).forEach((x) => x.setAttribute("aria-pressed", x === b));
      const f = b.dataset.filter;
      items.forEach((it) => it.classList.toggle("is-hidden", f !== "all" && !it.dataset.cat.split(" ").includes(f)));
    }));
  });

  /* ---------------------------------------------------------------- FAQ: one open at a time */
  $$(".faq").forEach((f) => {
    const items = $$("details", f);
    items.forEach((d) => d.addEventListener("toggle", () => { if (d.open) items.forEach((o) => o !== d && (o.open = false)); }));
  });

  /* ---------------------------------------------------------------- forms (no backend yet: hand off to email) */
  $$("form[data-mailto]").forEach((form) => {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      if (!form.reportValidity()) return;
      const data = new FormData(form);
      const lines = [];
      data.forEach((v, k) => { if (String(v).trim()) lines.push(`${k}: ${v}`); });
      const subject = encodeURIComponent(form.dataset.subject || "Solar quote request");
      location.href = `mailto:${form.dataset.mailto}?subject=${subject}&body=${encodeURIComponent(lines.join("\n"))}`;
      form.classList.add("is-sent");
    });
  });
  $$(".news").forEach((f) => f.addEventListener("submit", (e) => {
    e.preventDefault();
    const b = $("button", f);
    if (b) b.textContent = "Subscribed";
  }));

  /* ---------------------------------------------------------------- charts */
  const C = {
    red: () => (doc.dataset.theme === "dark" ? "#f23a33" : css("--red")),
    sky: () => css("--sky"),
  };

  // Generic responsive line/area chart with crosshair tooltip and a table view.
  const chartW = (host) => Math.round(clamp(host.clientWidth || 720, 280, 900));
  const charts = [];
  // Draws a chart now and again whenever its container width changes noticeably.
  function mount(host, draw) {
    const run = () => {
      host.innerHTML = "";
      let n = host.nextElementSibling;
      while (n && (n.classList.contains("table-toggle") || n.classList.contains("data-table"))) { const x = n.nextElementSibling; n.remove(); n = x; }
      draw();
    };
    run();
    charts.push({ host, run, w: host.clientWidth });
  }
  let rz;
  addEventListener("resize", () => {
    clearTimeout(rz);
    rz = setTimeout(() => charts.forEach((c) => { if (Math.abs(c.host.clientWidth - c.w) > 40) { c.w = c.host.clientWidth; c.run(); } }), 200);
  });

  function lineChart(host, cfg) {
    const W = chartW(host), H = Math.round((cfg.h || 300) * clamp(W / 720, 0.75, 1)), m = { t: 16, r: 16, b: 30, l: 44 };
    const iw = W - m.l - m.r, ih = H - m.t - m.b;
    const svg = svgEl("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": cfg.label }, host);
    const xs = cfg.x, n = xs.length;
    const max = cfg.max || Math.max(...cfg.series.flatMap((s) => s.data)) * 1.12;
    const X = (i) => m.l + (i / (n - 1)) * iw, Y = (v) => m.t + ih - (v / max) * ih;
    const grid = svgEl("g", { class: "grid" }, svg), axis = svgEl("g", { class: "axis" }, svg);
    const ticks = cfg.ticks || 4;
    for (let k = 0; k <= ticks; k++) {
      const v = (max / ticks) * k, y = Y(v);
      svgEl("line", { x1: m.l, x2: W - m.r, y1: y, y2: y }, grid);
      const t = svgEl("text", { x: m.l - 10, y: y + 3, "text-anchor": "end" }, axis);
      t.textContent = cfg.yfmt ? cfg.yfmt(v) : Math.round(v);
    }
    (cfg.xticks || xs.map((_, i) => i)).forEach((i) => {
      const t = svgEl("text", { x: X(i), y: H - 8, "text-anchor": "middle" }, axis);
      t.textContent = cfg.xfmt ? cfg.xfmt(xs[i], i) : xs[i];
    });
    const paths = [];
    cfg.series.forEach((s, si) => {
      const col = s.color();
      const d = s.data.map((v, i) => `${i ? "L" : "M"}${X(i).toFixed(1)} ${Y(v).toFixed(1)}`).join("");
      if (s.area) {
        const gid = `g${Math.random().toString(36).slice(2, 7)}`;
        svgEl("defs", {}, svg).innerHTML = `<linearGradient id="${gid}" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="${col}" stop-opacity=".22"/><stop offset="1" stop-color="${col}" stop-opacity="0"/></linearGradient>`;
        svgEl("path", { d: `${d}L${X(n - 1)} ${Y(0)}L${X(0)} ${Y(0)}Z`, fill: `url(#${gid})`, class: "draw-area" }, svg);
      }
      const p = svgEl("path", { d, fill: "none", stroke: col, "stroke-width": 2, "stroke-linejoin": "round", "stroke-linecap": "round", class: "draw-line" }, svg);
      if (s.dash) p.setAttribute("stroke-dasharray", s.dash);
      paths.push({ p, s });
      if (s.label) { // direct label at the series' max point
        const mi = s.labelAt != null ? s.labelAt : s.data.indexOf(Math.max(...s.data));
        const t = svgEl("text", { x: X(mi), y: Y(s.data[mi]) - 12, "text-anchor": "middle", class: "lbl" }, svg);
        t.textContent = s.label;
      }
    });
    requestAnimationFrame(() => paths.forEach(({ p, s }) => { if (!s.dash) { const L = p.getTotalLength(); p.style.setProperty("--len", Math.ceil(L)); } else p.classList.remove("draw-line"); }));
    // hover layer
    const xh = svgEl("line", { class: "xhair", y1: m.t, y2: m.t + ih }, svg);
    const marks = cfg.series.map((s) => svgEl("circle", { r: 5, fill: s.color(), stroke: "#fff", "stroke-width": 2, opacity: 0 }, svg));
    const tip = document.createElement("div");
    tip.className = "tip";
    host.appendChild(tip);
    const hit = svgEl("rect", { x: m.l, y: 0, width: iw, height: H, fill: "transparent" }, svg);
    const move = (e) => {
      const r = svg.getBoundingClientRect();
      const px = ((e.clientX - r.left) / r.width) * W;
      const i = clamp(Math.round(((px - m.l) / iw) * (n - 1)), 0, n - 1);
      xh.setAttribute("x1", X(i)); xh.setAttribute("x2", X(i));
      marks.forEach((c, k) => { c.setAttribute("cx", X(i)); c.setAttribute("cy", Y(cfg.series[k].data[i])); c.setAttribute("opacity", 1); });
      tip.innerHTML = `<b>${cfg.tipTitle ? cfg.tipTitle(xs[i], i) : xs[i]}</b>` + cfg.series.map((s) => `<div class="row" style="--c:${s.color()}"><span><i></i>${s.name}</span><span>${cfg.vfmt(s.data[i])}</span></div>`).join("");
      tip.style.left = `${(X(i) / W) * 100}%`;
      tip.style.top = `${(Math.min(...cfg.series.map((s) => Y(s.data[i]))) / H) * r.height}px`;
      tip.classList.add("is-on"); host.classList.add("is-hover");
    };
    hit.addEventListener("pointermove", move);
    hit.addEventListener("pointerdown", move);
    hit.addEventListener("pointerleave", () => { tip.classList.remove("is-on"); host.classList.remove("is-hover"); marks.forEach((c) => c.setAttribute("opacity", 0)); });
    tableToggle(host, ["", ...cfg.series.map((s) => s.name)], xs.map((x, i) => [cfg.tipTitle ? cfg.tipTitle(x, i) : x, ...cfg.series.map((s) => cfg.vfmt(s.data[i]))]));
    return svg;
  }

  function barChart(host, cfg) {
    const W = chartW(host), H = Math.round((cfg.h || 280) * clamp(W / 720, 0.8, 1)), m = { t: 26, r: 10, b: 30, l: 42 };
    const iw = W - m.l - m.r, ih = H - m.t - m.b, n = cfg.data.length;
    const svg = svgEl("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": cfg.label }, host);
    const max = Math.max(...cfg.data) * 1.15;
    const Y = (v) => m.t + ih - (v / max) * ih;
    const grid = svgEl("g", { class: "grid" }, svg), axis = svgEl("g", { class: "axis" }, svg);
    for (let k = 0; k <= 4; k++) {
      const v = (max / 4) * k;
      svgEl("line", { x1: m.l, x2: W - m.r, y1: Y(v), y2: Y(v) }, grid);
      svgEl("text", { x: m.l - 10, y: Y(v) + 3, "text-anchor": "end" }, axis).textContent = cfg.yfmt(v);
    }
    const slot = iw / n, bw = Math.min(slot - 2, 34);
    const tip = document.createElement("div");
    tip.className = "tip";
    host.appendChild(tip);
    const hi = cfg.data.indexOf(Math.max(...cfg.data));
    cfg.data.forEach((v, i) => {
      const x = m.l + slot * i + (slot - bw) / 2;
      const h = Math.max(ih - (Y(v) - m.t), 1);
      // rounded data-end, square at the baseline
      const r = 4, y = Y(v);
      const d = `M${x} ${y + h}V${y + r}Q${x} ${y} ${x + r} ${y}H${x + bw - r}Q${x + bw} ${y} ${x + bw} ${y + r}V${y + h}Z`;
      const bar = svgEl("path", { d, fill: i === hi ? C.red() : cfg.color ? cfg.color() : css("--ink"), class: "grow-bar", style: `--i:${i}` }, svg);
      svgEl("text", { x: x + bw / 2, y: H - 8, "text-anchor": "middle" }, axis).textContent = cfg.x[i];
      if (i === hi) svgEl("text", { x: x + bw / 2, y: y - 8, "text-anchor": "middle", class: "lbl" }, svg).textContent = cfg.vfmt(v);
      const hit = svgEl("rect", { x: m.l + slot * i, y: m.t, width: slot, height: ih, fill: "transparent" }, svg);
      hit.addEventListener("pointerenter", () => {
        tip.innerHTML = `<b>${cfg.full ? cfg.full[i] : cfg.x[i]}</b><div class="row"><span>${cfg.name}</span><span>${cfg.vfmt(v)}</span></div>`;
        tip.style.left = `${((x + bw / 2) / W) * 100}%`;
        tip.style.top = `${(y / H) * svg.getBoundingClientRect().height}px`;
        tip.classList.add("is-on");
        bar.style.opacity = 0.75;
      });
      hit.addEventListener("pointerleave", () => { tip.classList.remove("is-on"); bar.style.opacity = 1; });
    });
    tableToggle(host, ["Month", cfg.name], cfg.data.map((v, i) => [cfg.full ? cfg.full[i] : cfg.x[i], cfg.vfmt(v)]));
  }

  function tableToggle(host, head, rows) {
    const btn = document.createElement("button");
    btn.className = "table-toggle";
    btn.type = "button";
    btn.textContent = "View as table";
    btn.setAttribute("aria-expanded", "false");
    let table = null;
    btn.addEventListener("click", () => {
      if (!table) {
        table = document.createElement("table");
        table.className = "data-table";
        table.innerHTML = `<thead><tr>${head.map((h) => `<th>${h}</th>`).join("")}</tr></thead><tbody>${rows.map((r) => `<tr>${r.map((c) => `<td>${c}</td>`).join("")}</tr>`).join("")}</tbody>`;
        table.hidden = true;
        host.after(table);
      }
      table.hidden = !table.hidden;
      btn.textContent = table.hidden ? "View as table" : "Hide table";
      btn.setAttribute("aria-expanded", String(!table.hidden));
    });
    host.after(btn);
  }

  // Typical day for a 5 kWp hybrid home system in Harare (illustrative model).
  const hours = Array.from({ length: 25 }, (_, h) => h);
  const solarDay = hours.map((h) => (h < 6.5 || h > 17.8 ? 0 : +(4.15 * Math.pow(Math.sin(Math.PI * (h - 6.5) / 11.3), 1.6)).toFixed(2)));
  const loadDay = hours.map((h) => +(0.35 + 1.4 * Math.exp(-((h - 7) ** 2) / 1.6) + 0.45 * Math.exp(-((h - 13) ** 2) / 6) + 2.0 * Math.exp(-((h - 19.2) ** 2) / 3)).toFixed(2));
  $$("[data-chart='day']").forEach((host) => mount(host, () => lineChart(host, {
    label: "Solar production versus household demand over a typical day, in kilowatts",
    x: hours, xticks: [0, 6, 12, 18, 24], xfmt: (h) => `${String(h).padStart(2, "0")}:00`,
    tipTitle: (h) => `${String(h).padStart(2, "0")}:00`, vfmt: (v) => `${v.toFixed(2)} kW`, yfmt: (v) => `${v.toFixed(0)} kW`, max: 5,
    series: [
      { name: "Solar production", data: solarDay, color: C.red, area: true, label: "Solar" },
      { name: "Home demand", data: loadDay, color: C.sky, label: "Demand", labelAt: 19 },
    ],
  })));

  // Modelled monthly output for the 12 kW Mount Pleasant system (Harare peak-sun-hours x 0.78 PR).
  const psh = [5.6, 5.7, 5.9, 6.0, 5.7, 5.3, 5.6, 6.3, 6.9, 7.0, 6.4, 5.6];
  const days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  const monthsShort = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"];
  const monthsFull = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  $$("[data-chart='monthly']").forEach((host) => {
    const kw = parseFloat(host.dataset.kw || "12");
    mount(host, () => barChart(host, {
      label: `Modelled monthly generation for a ${kw} kW system in Harare`, name: "Generation",
      data: psh.map((p, i) => Math.round(kw * p * days[i] * 0.78)), x: monthsShort, full: monthsFull,
      vfmt: (v) => `${v.toLocaleString()} kWh`, yfmt: (v) => `${Math.round(v / 100) * 100}`,
    }));
  });

  // Average daily peak-sun-hours in Harare by month (approximate climatology).
  $$("[data-chart='psh']").forEach((host) => mount(host, () => barChart(host, {
    label: "Average daily peak sun hours in Harare by month", name: "Peak sun hours",
    data: psh, x: monthsShort, full: monthsFull, h: 240,
    vfmt: (v) => `${v.toFixed(1)} h/day`, yfmt: (v) => v.toFixed(0),
  })));

  // Gauges
  $$("[data-gauge]").forEach((g) => {
    const v = parseFloat(g.dataset.gauge);
    const c = $(".val", g);
    const L = 2 * Math.PI * 64;
    const set = () => c.setAttribute("stroke-dasharray", `${(v / 100) * L} ${L}`);
    g.addEventListener("reveal", set);
    io.observe(g);
  });

  /* ---------------------------------------------------------------- savings calculator */
  const calc = $("[data-calc]");
  if (calc) {
    const bill = $("#bill", calc), backup = $("#backup", calc), host = $("[data-chart='savings']", calc.parentElement);
    const out = (id) => $(`[data-out='${id}']`, calc.parentElement);
    const TARIFF = 0.14, PSH = 5.9, PR = 0.78, COST_KWP = 520, COST_KWH_BATT = 300, ESC = 0.08;
    const paint = (inp) => inp.style.setProperty("--p", `${((inp.value - inp.min) / (inp.max - inp.min)) * 100}%`);
    const update = () => {
      [bill, backup].forEach(paint);
      const b = +bill.value, h = +backup.value;
      const type = ($("input[name='ptype']:checked", calc) || {}).value || "home";
      const kwh = b / TARIFF;
      const kwp = Math.max(1.5, Math.round((kwh / (30 * PSH * PR)) * 2) / 2);
      const avgLoad = kwh / 30 / 24 * (type === "business" ? 1.6 : 1.25);
      const batt = Math.max(2.5, Math.round(avgLoad * h * 2) / 2);
      const cost = Math.round((kwp * COST_KWP + batt * COST_KWH_BATT + (type === "business" ? 900 : 450)) / 10) * 10;
      const offset = type === "business" ? 0.82 : 0.88;
      const yearSave = b * 12 * offset;
      const payback = cost / yearSave;
      $("output[for='bill']", calc).textContent = `$${b}`;
      $("output[for='backup']", calc).textContent = `${h} h`;
      out("kwp").textContent = `${kwp} kWp`;
      out("batt").textContent = `${batt} kWh`;
      out("cost").textContent = `$${cost.toLocaleString()}`;
      out("payback").textContent = `${payback.toFixed(1)} yrs`;
      // 10-year cumulative spend: grid only vs Riquid solar (upfront + residual grid + upkeep)
      const yrs = Array.from({ length: 11 }, (_, i) => i);
      let g = 0, s = cost;
      const grid = [0], solar = [cost];
      for (let y = 1; y <= 10; y++) {
        const yearBill = b * 12 * Math.pow(1 + ESC, y - 1);
        g += yearBill; s += yearBill * (1 - offset) + 60;
        grid.push(Math.round(g)); solar.push(Math.round(s));
      }
      out("save10").textContent = `$${Math.max(0, grid[10] - solar[10]).toLocaleString()}`;
      if (host) {
        host.innerHTML = "";
        host.parentElement.querySelectorAll(".table-toggle, .data-table").forEach((n) => n.remove());
        lineChart(host, {
          label: "Cumulative spend over ten years: grid only versus solar", h: 320,
          x: yrs, xfmt: (y) => (y === 0 ? "Now" : `Y${y}`), tipTitle: (y) => (y === 0 ? "Today" : `Year ${y}`),
          vfmt: (v) => `$${v.toLocaleString()}`, yfmt: (v) => (v >= 1000 ? `$${Math.round(v / 1000)}k` : `$${Math.round(v)}`),
          series: [
            { name: "Grid only", data: grid, color: C.sky, label: "Grid only", labelAt: 10 },
            { name: "With Riquid solar", data: solar, color: C.red, area: true, label: "With solar", labelAt: 9 },
          ],
        });
        host.classList.add("is-drawn");
      }
    };
    calc.addEventListener("input", update);
    update();
    if (host) charts.push({ host, run: update, w: host.clientWidth });
  }

  /* ---------------------------------------------------------------- Zimbabwe map */
  $$("[data-zmap]").forEach((host) => {
    const M = window.RIQUID_MAP;
    if (!M) return;
    const svg = svgEl("svg", { viewBox: `-40 -40 ${M.w + 80} ${M.h + 80}`, role: "img", "aria-label": "Map of Zimbabwe showing Riquid service areas, with Harare as head office" }, host);
    const sites = (host.dataset.sites || "Harare,Bulawayo,Mutare,Gweru,Masvingo,Victoria Falls,Kariba,Chinhoyi,Marondera,Kwekwe").split(",");
    const hq = M.cities.Harare;
    const near = (x, y) => sites.some((s) => { const c = M.cities[s]; return c && Math.hypot(c[0] - x, c[1] - y) < 70; });
    const g = svgEl("g", {}, svg);
    M.dots.forEach(([x, y]) => svgEl("circle", { cx: x, cy: y, r: 4.2, class: near(x, y) ? "dot lit" : "dot" }, g));
    const routes = svgEl("g", {}, svg);
    sites.forEach((s, i) => {
      const c = M.cities[s];
      if (!c || s === "Harare") return;
      const mx = (hq[0] + c[0]) / 2, my = (hq[1] + c[1]) / 2 - Math.hypot(c[0] - hq[0], c[1] - hq[1]) * 0.25;
      const p = svgEl("path", { d: `M${hq[0]} ${hq[1]}Q${mx} ${my} ${c[0]} ${c[1]}`, class: "route route-draw", style: `--i:${i}` }, routes);
      requestAnimationFrame(() => p.style.setProperty("--len", Math.ceil(p.getTotalLength())));
    });
    const tip = document.createElement("div");
    tip.className = "tip";
    host.appendChild(tip);
    sites.forEach((s, i) => {
      const c = M.cities[s];
      if (!c) return;
      const pin = svgEl("g", { class: `pin${s === "Harare" ? " hq" : ""}`, style: `--i:${i}`, tabindex: 0, "aria-label": s }, svg);
      svgEl("circle", { cx: c[0], cy: c[1], r: 9, class: "pulse" }, pin);
      svgEl("circle", { cx: c[0], cy: c[1], r: s === "Harare" ? 11 : 8, class: "core" }, pin);
      const right = c[0] < 820;
      const t = svgEl("text", { x: c[0] + (right ? 18 : -18), y: c[1] + 7, "text-anchor": right ? "start" : "end" }, pin);
      t.textContent = s === "Harare" ? "Harare · HQ" : s;
      const info = (host.dataset[`info${s.replace(/\s/g, "")}`]) || (s === "Harare" ? "Head office · 1 Union Avenue" : "Installations & site surveys");
      const on = () => {
        tip.innerHTML = `<b>${s}</b>${info}`;
        tip.style.left = `${((c[0] + 40) / (M.w + 80)) * 100}%`;
        tip.style.top = `${((c[1] + 40) / (M.h + 80)) * host.getBoundingClientRect().height}px`;
        tip.classList.add("is-on");
      };
      pin.addEventListener("pointerenter", on); pin.addEventListener("focus", on); pin.addEventListener("click", on);
      pin.addEventListener("pointerleave", () => tip.classList.remove("is-on")); pin.addEventListener("blur", () => tip.classList.remove("is-on"));
    });
    document.addEventListener("pointerdown", (e) => { if (!e.target.closest(".pin")) tip.classList.remove("is-on"); });
    io.observe(host);
    host.addEventListener("reveal", () => host.classList.add("is-drawn"));
  });

  /* ---------------------------------------------------------------- energy flow modes */
  $$("[data-flow]").forEach((root) => {
    const caption = $(".flow-caption", root);
    const modes = {
      day: { on: ["sun", "pv-inv", "inv-home", "inv-batt"], text: "Panels power the home and charge the battery." },
      night: { on: ["batt-inv", "inv-home"], text: "The battery runs the house. No generator." },
      outage: { on: ["sun", "pv-inv", "batt-inv", "inv-home"], text: "Solar and battery carry you through load-shedding." },
      grid: { on: ["grid-inv", "inv-home", "inv-batt"], text: "The grid tops up the battery on cloudy days." },
    };
    const set = (k) => {
      $$("[data-mode]", root).forEach((b) => b.setAttribute("aria-pressed", b.dataset.mode === k));
      $$("[data-wire]", root).forEach((w) => w.classList.toggle("is-off", !modes[k].on.includes(w.dataset.wire)));
      if (caption) caption.textContent = modes[k].text;
    };
    $$("[data-mode]", root).forEach((b) => b.addEventListener("click", () => set(b.dataset.mode)));
    set("day");
  });

  /* ---------------------------------------------------------------- footer year */
  $$("[data-year]").forEach((el) => { el.textContent = new Date().getFullYear(); });

  onScroll();
})();
