// Behaviour for the quantum portfolio. Everything here is optional: the site is fully
// readable and navigable without JavaScript.
(function () {
  "use strict";

  var reduceMotion = window.matchMedia ? window.matchMedia("(prefers-reduced-motion: reduce)") : { matches: false };

  /* ---------- 1. Header: transparent over the scene, solid after scrolling ---------- */
  var header = document.querySelector("[data-header]");
  function updateHeader() {
    if (header) header.classList.toggle("is-scrolled", window.scrollY > 40);
  }
  updateHeader();
  window.addEventListener("scroll", updateHeader, { passive: true });

  /* ---------- 2. Mobile menu (two-line button) ---------- */
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.getElementById("site-nav");
  if (toggle && nav) {
    var setOpen = function (open) {
      toggle.setAttribute("aria-expanded", String(open));
      nav.classList.toggle("is-open", open);
      if (header) header.classList.toggle("menu-open", open);
    };
    toggle.addEventListener("click", function () {
      setOpen(toggle.getAttribute("aria-expanded") !== "true");
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && toggle.getAttribute("aria-expanded") === "true") {
        setOpen(false);
        toggle.focus();
      }
    });
    nav.addEventListener("click", function (event) {
      if (event.target.closest("a")) setOpen(false);
    });
  }

  /* ---------- 3. Discreet reveal of cards below the fold ---------- */
  if (!reduceMotion.matches && "IntersectionObserver" in window) {
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    }, { rootMargin: "0px 0px -6% 0px" });
    document.querySelectorAll(".reveal").forEach(function (element) {
      if (element.getBoundingClientRect().top > window.innerHeight) {
        element.classList.add("reveal--pending");
        observer.observe(element);
      }
    });
    // An element reached with the keyboard must never stay invisible.
    document.addEventListener("focusin", function (event) {
      var pending = event.target.closest && event.target.closest(".reveal--pending");
      if (pending) pending.classList.add("is-visible");
    });
  }

  /* ---------- 4. Animated quantum scene ----------
     A rotating Bloch sphere (poles |0⟩ and |1⟩) with a precessing state vector and its trail,
     qubits on tilted orbits, out-of-focus particles for depth, drifting light and probability
     waves. One static frame when the visitor prefers reduced motion; paused when off-screen
     or when the tab is hidden. */
  document.querySelectorAll(".scene-canvas").forEach(function (canvas) {
    if (canvas.getContext) quantumScene(canvas);
  });

  function quantumScene(canvas) {
    var ctx = canvas.getContext("2d");
    var host = canvas.parentElement;
    var CYAN = [95, 211, 230], BLUE = [79, 140, 255], VIOLET = [167, 139, 250], WHITE = [235, 245, 255];
    var width = 0, height = 0, radius = 0, cx = 0, cy = 0;
    var time = 2, last = 0, frame = null, onScreen = true;
    var particles = [], trail = [];

    // Soft round "bokeh" sprites, pre-rendered once per colour.
    function sprite(rgb) {
      var s = document.createElement("canvas");
      s.width = s.height = 128;
      var g = s.getContext("2d");
      var grad = g.createRadialGradient(64, 64, 0, 64, 64, 64);
      grad.addColorStop(0, "rgba(" + rgb + ",1)");
      grad.addColorStop(0.35, "rgba(" + rgb + ",0.45)");
      grad.addColorStop(1, "rgba(" + rgb + ",0)");
      g.fillStyle = grad;
      g.fillRect(0, 0, 128, 128);
      return s;
    }
    var sprites = [sprite(CYAN), sprite(BLUE), sprite(VIOLET), sprite(WHITE)];

    function rgba(rgb, a) { return "rgba(" + rgb[0] + "," + rgb[1] + "," + rgb[2] + "," + a.toFixed(3) + ")"; }
    function random(min, max) { return min + Math.random() * (max - min); }

    function setup() {
      var ratio = Math.min(window.devicePixelRatio || 1, 1.75);
      width = host.clientWidth;
      height = host.clientHeight;
      canvas.width = Math.round(width * ratio);
      canvas.height = Math.round(height * ratio);
      ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
      // Centre the sphere in the space below the fixed header, keeping the |0⟩ / |1⟩ labels clear of it.
      var headerSpace = 80;
      cx = width / 2;
      cy = headerSpace + (height - headerSpace) / 2;
      radius = Math.min(width * (width < 700 ? 0.36 : 0.3), (height - headerSpace) * 0.36);
      trail = [];
      particles = [];
      var count = Math.round(Math.min(70, (width * height) / 22000));
      for (var i = 0; i < count; i++) {
        var depth = Math.random();
        particles.push({
          x: random(0, width), y: random(0, height), depth: depth,
          size: 6 + Math.pow(depth, 2) * 90,
          sprite: sprites[Math.floor(Math.random() * sprites.length)],
          vx: random(-6, 6) * (0.3 + depth), vy: random(-4, 4) * (0.3 + depth),
          phase: random(0, Math.PI * 2),
        });
      }
    }

    // 3D -> 2D: rotate around the vertical axis, then tilt towards the viewer.
    var yaw = 0, tilt = 0.38;
    function project(x, y, z) {
      var x1 = x * Math.cos(yaw) - z * Math.sin(yaw);
      var z1 = x * Math.sin(yaw) + z * Math.cos(yaw);
      var y2 = y * Math.cos(tilt) - z1 * Math.sin(tilt);
      var z2 = y * Math.sin(tilt) + z1 * Math.cos(tilt);
      return { x: cx + radius * x1, y: cy - radius * y2, z: z2 };
    }

    // A closed 3D curve drawn in short segments, brighter in front, dimmer behind.
    function curve(pointAt, rgb, alpha, lineWidth) {
      var steps = 72, prev = null;
      ctx.lineWidth = lineWidth;
      for (var i = 0; i <= steps; i++) {
        var p = pointAt((i / steps) * Math.PI * 2);
        if (prev) {
          var depth = (p.z + prev.z) / 2; // -1 (back) .. 1 (front)
          ctx.strokeStyle = rgba(rgb, alpha * (0.25 + 0.75 * (depth + 1) / 2));
          ctx.beginPath(); ctx.moveTo(prev.x, prev.y); ctx.lineTo(p.x, p.y); ctx.stroke();
        }
        prev = p;
      }
    }

    function glow(x, y, size, spriteIndex, alpha) {
      ctx.globalAlpha = alpha;
      ctx.drawImage(sprites[spriteIndex], x - size / 2, y - size / 2, size, size);
      ctx.globalAlpha = 1;
    }

    function draw(dt) {
      time += dt;
      yaw = time * 0.18;

      // Deep background with slowly drifting light.
      ctx.globalCompositeOperation = "source-over";
      ctx.fillStyle = "#050b16";
      ctx.fillRect(0, 0, width, height);
      ctx.globalCompositeOperation = "lighter";
      var big = Math.max(width, height);
      glow(width * (0.25 + 0.08 * Math.sin(time * 0.07)), height * (0.35 + 0.1 * Math.cos(time * 0.05)), big * 1.1, 1, 0.22);
      glow(width * (0.78 + 0.06 * Math.cos(time * 0.06)), height * (0.6 + 0.08 * Math.sin(time * 0.08)), big * 0.95, 0, 0.16);
      glow(width * (0.55 + 0.1 * Math.sin(time * 0.04)), height * (0.15 + 0.05 * Math.sin(time * 0.09)), big * 0.7, 2, 0.12);

      // Out-of-focus particles (far ones small and sharp, near ones large and soft).
      particles.forEach(function (p) {
        p.x += p.vx * dt; p.y += p.vy * dt;
        var m = p.size;
        if (p.x < -m) p.x = width + m; if (p.x > width + m) p.x = -m;
        if (p.y < -m) p.y = height + m; if (p.y > height + m) p.y = -m;
        var twinkle = 0.75 + 0.25 * Math.sin(time * 0.8 + p.phase);
        ctx.globalAlpha = (0.42 - p.depth * 0.3) * twinkle;
        ctx.drawImage(p.sprite, p.x - m / 2, p.y - m / 2, m, m);
      });
      ctx.globalAlpha = 1;

      // Probability waves near the bottom: two interfering wave packets.
      var base = height * 0.82;
      for (var k = 0; k < 3; k++) {
        ctx.beginPath();
        for (var x = 0; x <= width; x += 6) {
          var u = x / width;
          var envelope = Math.exp(-Math.pow((u - 0.5 - 0.25 * Math.sin(time * 0.15 + k)) / 0.28, 2));
          var y = base + k * 14 + envelope * 26 * Math.sin(u * 18 - time * (1.1 + k * 0.25)) * Math.cos(u * 5 + time * 0.3);
          if (x === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        }
        ctx.strokeStyle = rgba(k === 1 ? BLUE : CYAN, 0.22 - k * 0.05);
        ctx.lineWidth = 1.2;
        ctx.stroke();
      }

      ctx.globalCompositeOperation = "source-over";

      // Bloch sphere: outline, meridians, latitudes.
      ctx.strokeStyle = rgba(CYAN, 0.35);
      ctx.lineWidth = 1.2;
      ctx.beginPath(); ctx.arc(cx, cy, radius, 0, Math.PI * 2); ctx.stroke();
      for (var m = 0; m < 6; m++) {
        var lon = (m / 6) * Math.PI;
        curve(function (a) {
          return project(Math.cos(lon) * Math.sin(a), Math.cos(a), Math.sin(lon) * Math.sin(a));
        }, CYAN, 0.28, 1);
      }
      [-0.55, 0, 0.55].forEach(function (lat) {
        var r = Math.cos(lat), h = Math.sin(lat);
        curve(function (a) { return project(r * Math.cos(a), h, r * Math.sin(a)); }, lat === 0 ? BLUE : CYAN, lat === 0 ? 0.5 : 0.22, lat === 0 ? 1.4 : 1);
      });

      // Vertical axis with the basis states.
      var top = project(0, 1.18, 0), bottom = project(0, -1.18, 0);
      ctx.strokeStyle = rgba(WHITE, 0.25);
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 6]);
      ctx.beginPath(); ctx.moveTo(top.x, top.y); ctx.lineTo(bottom.x, bottom.y); ctx.stroke();
      ctx.setLineDash([]);
      ctx.font = "500 " + Math.max(13, Math.round(radius * 0.09)) + "px ui-monospace, SFMono-Regular, Menlo, monospace";
      ctx.textAlign = "center";
      ctx.fillStyle = rgba(WHITE, 0.6);
      ctx.fillText("|0⟩", top.x, top.y - 10);
      ctx.fillText("|1⟩", bottom.x, bottom.y + 24);

      // Qubits on tilted orbits around the sphere.
      for (var o = 0; o < 3; o++) {
        var inclination = 0.5 + o * 0.75, orbit = 1.32 + o * 0.1, speed = 0.5 - o * 0.12;
        var pointOnOrbit = function (a) {
          var ox = orbit * Math.cos(a), oz = orbit * Math.sin(a);
          return project(ox, oz * Math.sin(inclination), oz * Math.cos(inclination));
        };
        curve(pointOnOrbit, VIOLET, 0.16, 1);
        var q = pointOnOrbit(time * speed + o * 2.1);
        ctx.globalCompositeOperation = "lighter";
        glow(q.x, q.y, 34 + 14 * (q.z + 1), 3, 0.55 + 0.3 * (q.z + 1) / 2);
        ctx.globalCompositeOperation = "source-over";
      }

      // State vector precessing around the vertical axis, with a fading trail.
      var theta = 1.0 + 0.35 * Math.sin(time * 0.35), phi = time * 0.9;
      var tip = project(Math.sin(theta) * Math.cos(phi), Math.cos(theta), Math.sin(theta) * Math.sin(phi));
      trail.push(tip);
      if (trail.length > 140) trail.shift();
      ctx.lineWidth = 2;
      for (var t = 1; t < trail.length; t++) {
        ctx.strokeStyle = rgba(CYAN, (t / trail.length) * 0.7);
        ctx.beginPath(); ctx.moveTo(trail[t - 1].x, trail[t - 1].y); ctx.lineTo(trail[t].x, trail[t].y); ctx.stroke();
      }
      var origin = project(0, 0, 0);
      ctx.strokeStyle = rgba(CYAN, 0.9);
      ctx.lineWidth = 2.5;
      ctx.beginPath(); ctx.moveTo(origin.x, origin.y); ctx.lineTo(tip.x, tip.y); ctx.stroke();
      ctx.globalCompositeOperation = "lighter";
      glow(tip.x, tip.y, 70, 0, 0.95);
      glow(tip.x, tip.y, 18, 3, 1);
      glow(origin.x, origin.y, 26, 1, 0.6);
      ctx.globalCompositeOperation = "source-over";
    }

    function loop(now) {
      var dt = Math.min((now - last) / 1000, 0.05);
      last = now;
      draw(dt);
      frame = window.requestAnimationFrame(loop);
    }
    function start() {
      if (frame || document.hidden || !onScreen) return;
      if (reduceMotion.matches) { trail = []; draw(0); return; }
      last = performance.now();
      frame = window.requestAnimationFrame(loop);
    }
    function stop() {
      if (frame) window.cancelAnimationFrame(frame);
      frame = null;
    }

    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (entries) {
        onScreen = entries[0].isIntersecting;
        if (onScreen) start(); else stop();
      }).observe(host);
    }
    var resizeTimer = null;
    window.addEventListener("resize", function () {
      window.clearTimeout(resizeTimer);
      resizeTimer = window.setTimeout(function () { setup(); if (!frame) draw(0); }, 150);
    });
    document.addEventListener("visibilitychange", function () { if (document.hidden) stop(); else start(); });
    if (reduceMotion.addEventListener) reduceMotion.addEventListener("change", function () { stop(); start(); });

    setup();
    draw(0);
    start();
  }
})();
