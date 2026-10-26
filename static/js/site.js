/* SibuyanConnect: small progressive enhancements. Every page works without this file. */
(function () {
  "use strict";

  function store(action, key, value) {
    try { return action === "get" ? localStorage.getItem(key) : localStorage.setItem(key, value); }
    catch (e) { return null; }
  }

  // Offline support: register the service worker (scope = whole site).
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function () {
      navigator.serviceWorker.register("/sw.js").catch(function () {});
    });
  }

  // Slide-in menu on phones.
  var openBtn = document.querySelector("[data-menu-open]");
  var nav = document.getElementById("site-nav");
  function setMenu(open) {
    document.body.classList.toggle("nav-open", open);
    if (openBtn) openBtn.setAttribute("aria-expanded", String(open));
    if (open && nav) { var first = nav.querySelector("a"); if (first) first.focus(); }
    else if (openBtn) openBtn.focus();
  }
  if (openBtn) openBtn.addEventListener("click", function () { setMenu(true); });
  document.querySelectorAll("[data-menu-close]").forEach(function (el) {
    el.addEventListener("click", function () { setMenu(false); });
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && document.body.classList.contains("nav-open")) setMenu(false);
  });

  // Dismissible alert strips (remembered per alert version on this device).
  document.querySelectorAll("[data-alert]").forEach(function (strip) {
    var key = "sc-alert-" + strip.dataset.alert;
    if (store("get", key)) { strip.hidden = true; return; }
    var btn = strip.querySelector("[data-dismiss]");
    if (btn) btn.addEventListener("click", function () { strip.hidden = true; store("set", key, "1"); });
  });

  // Concern form: only show barangays of the chosen town.
  var town = document.getElementById("id_municipality");
  var brgy = document.getElementById("id_barangay");
  if (town && brgy && window.BARANGAY_TOWNS) {
    var all = Array.prototype.slice.call(brgy.options);
    var filter = function () {
      var keep = brgy.value;
      brgy.innerHTML = "";
      all.forEach(function (opt) {
        if (!opt.value || !town.value || String(window.BARANGAY_TOWNS[opt.value]) === town.value) brgy.appendChild(opt);
      });
      brgy.value = Array.prototype.some.call(brgy.options, function (o) { return o.value === keep; }) ? keep : "";
    };
    town.addEventListener("change", filter);
    filter();
  }

  // Step indicator: highlight the step the user is working on.
  var stepper = document.querySelector("[data-stepper]");
  if (stepper && "IntersectionObserver" in window) {
    var items = stepper.querySelectorAll("li");
    var steps = document.querySelectorAll("[data-step]");
    var mark = function (index) {
      items.forEach(function (li, i) {
        li.classList.toggle("done", i < index);
        li.classList.toggle("active", i === index);
      });
    };
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) mark(Array.prototype.indexOf.call(steps, en.target));
      });
    }, { rootMargin: "-35% 0px -55% 0px" });
    steps.forEach(function (step, i) {
      step.addEventListener("focusin", function () { mark(i); });
      observer.observe(step);
    });
    mark(0);
  }

  // Hero crossfade (desktop only). Skipped for reduced motion, Data Saver and very slow
  // connections, so those visitors only ever download the first photo.
  var hero = document.querySelector("[data-hero]");
  if (hero && hero.dataset.slides) {
    var conn = navigator.connection || {};
    var calm = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var wide = window.matchMedia("(min-width: 900px)").matches;
    var slow = conn.saveData || /(^|-)2g$/.test(conn.effectiveType || "");
    if (wide && !calm && !slow) {
      window.addEventListener("load", function () {
        var slides = [hero.querySelector(".hero-slide")];
        var creditLink = hero.querySelector("[data-hero-credit]");
        var credits = [{ text: creditLink.textContent, href: creditLink.href }];
        var data = [];
        try { data = JSON.parse(hero.dataset.slides); } catch (e) { return; }
        data.forEach(function (s) {
          var img = new Image();
          img.className = "hero-slide";
          img.alt = s.alt;
          img.decoding = "async";
          img.sizes = "100vw";
          img.srcset = s.srcset;
          img.src = s.src;
          img.onload = function () {
            hero.querySelector("picture").appendChild(img);
            slides.push(img);
            credits.push({ text: s.credit, href: s.source });
          };
        });
        var current = 0;
        setInterval(function () {
          if (document.hidden || slides.length < 2) return;
          slides[current].classList.remove("is-active");
          current = (current + 1) % slides.length;
          slides[current].classList.add("is-active");
          creditLink.textContent = credits[current].text;
          creditLink.href = credits[current].href;
        }, 7000);
      });
    }
  }

  // Maps (tourism attractions, service office). Leaflet and tiles load only when a map
  // scrolls into view. Tiles come from OpenStreetMap; if its servers refuse them or we are
  // offline, a plain fallback (the list of places) replaces the map instead of broken
  // tiles. Tiles are never pre-cached (OSM tile policy). More keyless providers can be
  // added to this list; CARTO's basemaps were checked in October 2026 and now return an
  // "API key required" image, so they are not used.
  var TILE_PROVIDERS = [
    { url: "https://tile.openstreetmap.org/{z}/{x}/{y}.png", subdomains: "abc", maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' }
  ];

  function loadLeaflet(done, fail) {
    if (window.L) { done(); return; }
    var css = document.createElement("link");
    css.rel = "stylesheet";
    css.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
    css.integrity = "sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=";
    css.crossOrigin = "";
    document.head.appendChild(css);
    var js = document.createElement("script");
    js.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
    js.integrity = "sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=";
    js.crossOrigin = "";
    js.onload = done;
    js.onerror = fail;
    document.head.appendChild(js);
  }

  function showMapFallback(mapEl) {
    var fallback = document.getElementById(mapEl.dataset.fallback);
    mapEl.hidden = true;
    if (fallback) fallback.hidden = false;
  }

  // Probe one tile from each provider and use the first that answers 200. fetch() is used
  // because browsers may defer image load/error events (Edge does), which would leave a
  // refused provider undetected; both providers send CORS headers, so the status is
  // readable. The probe is the first tile the map shows, so the HTTP cache serves it again.
  function pickProvider(lat, lon, zoom, index, done) {
    if (index >= TILE_PROVIDERS.length) { done(null); return; }
    var provider = TILE_PROVIDERS[index];
    var n = Math.pow(2, zoom), rad = lat * Math.PI / 180;
    var x = Math.floor((lon + 180) / 360 * n);
    var y = Math.floor((1 - Math.log(Math.tan(rad) + 1 / Math.cos(rad)) / Math.PI) / 2 * n);
    var url = provider.url.replace("{s}", provider.subdomains.charAt(0)).replace("{z}", zoom)
      .replace("{x}", x).replace("{y}", y).replace("{r}", "");
    var settled = false;
    var settle = function (ok) {
      if (settled) return;
      settled = true;
      if (ok) done(provider); else pickProvider(lat, lon, zoom, index + 1, done);
    };
    // A slow but working connection is not a refusal: after 10 s, use this provider anyway.
    var timer = setTimeout(function () { settle(true); }, 10000);
    fetch(url, { mode: "cors", referrerPolicy: "strict-origin-when-cross-origin", credentials: "omit" })
      .then(function (res) { clearTimeout(timer); settle(res.ok); })
      .catch(function () { clearTimeout(timer); settle(false); });
  }

  function addTiles(map, provider) {
    L.tileLayer(provider.url, {
      subdomains: provider.subdomains,
      maxZoom: provider.maxZoom,
      attribution: provider.attribution,
      referrerPolicy: "strict-origin-when-cross-origin"
    }).addTo(map);
  }

  function initMap(mapEl) {
    if (!navigator.onLine) { showMapFallback(mapEl); return; }
    loadLeaflet(function () {
      var map = L.map(mapEl, { scrollWheelZoom: false, zoomSnap: 0.5 });
      var points = [];
      if (mapEl.dataset.pins) {
        JSON.parse(document.getElementById(mapEl.dataset.pins).textContent).forEach(function (p) {
          var link = document.createElement("a");
          link.href = "#" + p.anchor;
          link.textContent = p.name;
          var popup = document.createElement("div");
          popup.appendChild(link);
          popup.appendChild(document.createTextNode(" · " + p.town));
          L.marker([p.lat, p.lon], { title: p.name, alt: p.name }).addTo(map).bindPopup(popup);
          points.push([p.lat, p.lon]);
        });
      } else {
        var pos = [parseFloat(mapEl.dataset.lat), parseFloat(mapEl.dataset.lon)];
        L.marker(pos, { title: mapEl.dataset.label, alt: mapEl.dataset.label }).addTo(map).bindPopup(mapEl.dataset.label);
        points.push(pos);
      }
      var start = points[0] || [12.40, 122.60], zoom = points.length > 1 ? 11 : 15;
      map.setView(start, zoom);
      pickProvider(start[0], start[1], zoom, 0, function (provider) {
        if (provider) addTiles(map, provider); else showMapFallback(mapEl);
      });
      if (points.length > 1) {
        // Measure after Leaflet's stylesheet has applied, so the fit uses the real map size.
        setTimeout(function () {
          map.invalidateSize();
          map.fitBounds(points, { paddingTopLeft: [24, 52], paddingBottomRight: [24, 24], maxZoom: 12 });
        }, 150);
      }
    }, function () { showMapFallback(mapEl); });
  }

  var maps = document.querySelectorAll("[data-map]");
  if (maps.length && "IntersectionObserver" in window) {
    var mapObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { mapObserver.unobserve(e.target); initMap(e.target); }
      });
    }, { rootMargin: "200px" });
    maps.forEach(function (el) { mapObserver.observe(el); });
  }

  // Share buttons: native share sheet on phones, copy link elsewhere.
  document.querySelectorAll("[data-share]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var data = { title: btn.dataset.title || document.title, url: btn.dataset.url || location.href };
      if (navigator.share) { navigator.share(data).catch(function () {}); return; }
      if (navigator.clipboard) {
        navigator.clipboard.writeText(data.url).then(function () { btn.textContent = btn.dataset.copied || "Link copied"; });
      }
    });
  });

  // Weather from Open-Meteo (free, no API key). Fails quietly when offline.
  var w = document.getElementById("weather");
  if (w) {
    var codes = { 0: "Clear sky", 1: "Mostly clear", 2: "Partly cloudy", 3: "Overcast", 45: "Fog", 48: "Fog",
      51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle", 61: "Light rain", 63: "Rain", 65: "Heavy rain",
      80: "Rain showers", 81: "Rain showers", 82: "Violent showers", 95: "Thunderstorm", 96: "Thunderstorm", 99: "Thunderstorm" };
    var set = function (key, text) { var el = w.querySelector('[data-w="' + key + '"]'); if (el) el.textContent = text; };
    var url = "https://api.open-meteo.com/v1/forecast?latitude=" + w.dataset.lat + "&longitude=" + w.dataset.lon +
      "&current=temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,wind_speed_10m" +
      "&daily=precipitation_probability_max&forecast_days=1&timezone=Asia%2FManila";
    fetch(url).then(function (r) { return r.json(); }).then(function (d) {
      var c = d.current;
      set("temp", Math.round(c.temperature_2m) + "°C");
      set("desc", (codes[c.weather_code] || "Current conditions") + " · Sibuyan Island");
      set("feels", Math.round(c.apparent_temperature) + "°C");
      set("humidity", Math.round(c.relative_humidity_2m) + "%");
      set("wind", Math.round(c.wind_speed_10m) + " km/h");
      var rain = d.daily && d.daily.precipitation_probability_max && d.daily.precipitation_probability_max[0];
      set("rain", rain == null ? "—" : rain + "%");
    }).catch(function () { set("desc", w.dataset.offline || "Weather unavailable offline."); });
  }
})();
