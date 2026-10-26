{% load static %}/* SibuyanConnect service worker (generated). Keeps key pages usable offline. */
const CACHE = "sc-{{ version }}";
const PRECACHE = {{ offline_urls|safe }}.concat([
  "{% static 'css/site.css' %}",
  "{% static 'js/site.js' %}",
  "{% static 'vendor/htmx.min.js' %}",
  "{% static 'img/icons.svg' %}",
  "{% static 'fonts/inter-latin-400-normal.woff2' %}",
  "{% static 'fonts/inter-latin-600-normal.woff2' %}",
  "{% static 'fonts/fraunces-latin-500-normal.woff2' %}",
  "{% static 'icons/icon-192.png' %}"
]);
// Never cache private or staff pages.
const NO_CACHE = ["/admin/", "/concerns/t/", "/concerns/mine/", "/accounts/"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) =>
      // Add one by one so a single failure does not abort the whole install.
      Promise.all(PRECACHE.map((url) => cache.add(new Request(url, { credentials: "same-origin" })).catch(() => {})))
    ).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  const req = event.request;
  const url = new URL(req.url);
  // Other sites (map tiles, weather, CDN scripts) go straight to the network and are never
  // cached here: OpenStreetMap's tile policy forbids bulk or offline tile caching.
  if (req.method !== "GET" || url.origin !== location.origin) return;
  if (NO_CACHE.some((p) => url.pathname.startsWith(p))) return;

  if (url.pathname.startsWith("/static/")) {
    // Static files: cache first.
    event.respondWith(caches.match(req).then((hit) => hit || fetch(req).then((res) => {
      const copy = res.clone();
      caches.open(CACHE).then((c) => c.put(req, copy));
      return res;
    })));
    return;
  }

  if (req.mode === "navigate") {
    // Pages: network first, fall back to the cached copy, then to /offline/.
    event.respondWith(
      fetch(req).then((res) => {
        if (res.ok) {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(req, copy));
        }
        return res;
      }).catch(() =>
        caches.match(req, { ignoreSearch: false })
          .then((hit) => hit || caches.match(url.pathname))
          .then((hit) => hit || caches.match("{% url 'offline' %}"))
      )
    );
  }
});
