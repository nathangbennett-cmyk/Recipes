/* WMGP29 shared app layer — progressive enhancement only.
   Core content works with JS disabled; this adds the fun. */
(function () {
  "use strict";

  var GAMES_OPEN = new Date("2029-10-12T18:00:00+08:00");
  var GAMES_CLOSE = new Date("2029-10-23T21:00:00+08:00");

  /* ---------- storage helpers (demo persistence; swap for CRM/API) ---------- */
  function store(key, val) {
    try { localStorage.setItem("wmgp29." + key, JSON.stringify(val)); } catch (e) {}
  }
  function load(key, fallback) {
    try {
      var v = localStorage.getItem("wmgp29." + key);
      return v ? JSON.parse(v) : fallback;
    } catch (e) { return fallback; }
  }
  window.WMGP29 = window.WMGP29 || {};
  window.WMGP29.store = store;
  window.WMGP29.load = load;

  /* ---------- age category: age as at 12 Oct 2029, 5-year bands ---------- */
  function ageAtGames(dobStr) {
    var dob = new Date(dobStr);
    if (isNaN(dob.getTime())) return null;
    var age = GAMES_OPEN.getFullYear() - dob.getFullYear();
    var m = GAMES_OPEN.getMonth() - dob.getMonth();
    if (m < 0 || (m === 0 && GAMES_OPEN.getDate() < dob.getDate())) age--;
    return age;
  }
  function ageBand(age, minAge) {
    var floor = minAge || 30;
    if (age < floor) return null;
    var lo = Math.floor(age / 5) * 5;
    if (lo < floor) lo = floor;
    return lo + "–" + (lo + 4);
  }
  window.WMGP29.ageAtGames = ageAtGames;
  window.WMGP29.ageBand = ageBand;

  /* ---------- nav toggle ---------- */
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.querySelector(".main-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  /* ---------- profile greeting chip ---------- */
  var profile = load("profile", null);
  var chip = document.querySelector(".profile-chip");
  if (chip && profile && profile.firstName) {
    var bits = "👋 " + profile.firstName;
    if (profile.age2029) bits += " · " + profile.age2029 + " at the Games";
    chip.textContent = bits;
    chip.classList.add("show");
  }

  /* ---------- image fallback: if a photo fails, show styled emoji panel ---------- */
  document.querySelectorAll(".media img, .hero-media img, .audience-card img, .band-media img").forEach(function (img) {
    img.addEventListener("error", function () {
      var wrap = img.closest(".media");
      if (wrap) wrap.classList.remove("has-img");
      img.remove();
    });
    if (img.complete && img.naturalWidth === 0) {
      img.dispatchEvent(new Event("error"));
    }
  });

  /* ---------- countdown ---------- */
  var cd = document.querySelector("[data-countdown]");
  if (cd) {
    var funMode = false;
    var funBtn = document.querySelector("[data-countdown-fun]");
    function renderCountdown() {
      var now = new Date();
      var diff = GAMES_OPEN - now;
      if (diff < 0) {
        cd.innerHTML = now < GAMES_CLOSE
          ? '<div class="unit"><span class="num">LIVE</span><span class="lbl">games on now</span></div>'
          : '<div class="unit"><span class="num">🏅</span><span class="lbl">see you next Games</span></div>';
        return;
      }
      var days = Math.floor(diff / 864e5);
      if (funMode) {
        var saturdays = Math.floor(days / 7);
        var sleeps = days;
        cd.innerHTML =
          '<div class="unit"><span class="num">' + saturdays.toLocaleString() + '</span><span class="lbl">training Saturdays</span></div>' +
          '<div class="unit"><span class="num">' + sleeps.toLocaleString() + '</span><span class="lbl">sleeps</span></div>' +
          '<div class="unit"><span class="num">' + Math.floor(days / 30.44) + '</span><span class="lbl">months of PBs</span></div>';
        return;
      }
      var h = Math.floor(diff % 864e5 / 36e5);
      var m = Math.floor(diff % 36e5 / 6e4);
      var s = Math.floor(diff % 6e4 / 1e3);
      cd.innerHTML =
        '<div class="unit"><span class="num">' + days.toLocaleString() + '</span><span class="lbl">days</span></div>' +
        '<div class="unit"><span class="num">' + h + '</span><span class="lbl">hours</span></div>' +
        '<div class="unit"><span class="num">' + m + '</span><span class="lbl">mins</span></div>' +
        '<div class="unit"><span class="num">' + s + '</span><span class="lbl">secs</span></div>';
    }
    renderCountdown();
    setInterval(renderCountdown, 1000);
    if (funBtn) funBtn.addEventListener("click", function () {
      funMode = !funMode;
      funBtn.textContent = funMode ? "Show the boring countdown" : "Show it in training Saturdays →";
      renderCountdown();
    });
  }

  /* ---------- animated stat counters ---------- */
  var stats = document.querySelectorAll("[data-count-to]");
  if (stats.length && "IntersectionObserver" in window && !matchMedia("(prefers-reduced-motion: reduce)").matches) {
    var seen = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        seen.unobserve(en.target);
        var el = en.target, target = parseInt(el.getAttribute("data-count-to"), 10);
        var suffix = el.getAttribute("data-count-suffix") || "";
        var t0 = performance.now(), dur = 1600;
        (function tick(t) {
          var p = Math.min(1, (t - t0) / dur);
          var eased = 1 - Math.pow(1 - p, 3);
          el.textContent = Math.round(target * eased).toLocaleString() + suffix;
          if (p < 1) requestAnimationFrame(tick);
        })(t0);
      });
    }, { threshold: 0.4 });
    stats.forEach(function (el) { seen.observe(el); });
  }

  /* ---------- registered counter (demo social proof, deterministic growth) ---------- */
  document.querySelectorAll("[data-interest-counter]").forEach(function (el) {
    var base = 18437; // demo seed: pre-registrations of interest
    var daysSinceLaunch = Math.max(0, Math.floor((Date.now() - new Date("2026-05-01")) / 864e5));
    el.setAttribute("data-count-to", String(base + daysSinceLaunch * 41));
  });

  /* ---------- confetti ---------- */
  window.WMGP29.confetti = function () {
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    var bits = ["🎉", "🎊", "⭐", "🏅", "💛", "💙"];
    for (var i = 0; i < 28; i++) {
      var s = document.createElement("span");
      s.className = "confetto";
      s.textContent = bits[i % bits.length];
      s.style.left = Math.random() * 100 + "vw";
      s.style.animationDelay = Math.random() * 0.9 + "s";
      s.setAttribute("aria-hidden", "true");
      document.body.appendChild(s);
      setTimeout(function (el) { el.remove(); }.bind(null, s), 4000);
    }
  };

  /* ---------- live DOB → age band fields ---------- */
  document.querySelectorAll("[data-dob-field]").forEach(function (input) {
    var out = document.querySelector(input.getAttribute("data-dob-field"));
    if (!out) return;
    input.addEventListener("change", function () {
      var age = ageAtGames(input.value);
      if (age === null) { out.classList.remove("show"); return; }
      if (age < 25) {
        out.textContent = "You'll be " + age + " in October 2029 — just under the minimum age (most sports 30+, some 25+). The Games will still need supporters and volunteers!";
      } else if (age < 30) {
        out.textContent = "🎉 You'll be " + age + " at the Games — eligible for sports with a 25+ minimum age (swimming, diving, artistic swimming, open water and more).";
      } else {
        var lo = Math.floor(age / 5) * 5;
        out.textContent = "🎉 You'll be " + age + " at the Games — that's the " + lo + "–" + (lo + 4) + " age group. Game on.";
      }
      out.classList.add("show");
    });
  });
})();
