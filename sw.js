// esm.business – Service Worker: App-Hülle aus dem Cache, Daten immer frisch mit Offline-Rückfall
const CACHE = "esm-business-v5";
const SHELL = ["./", "index.html", "article-search.js", "manifest.webmanifest", "fonts/SchibstedGrotesk.woff2",
  "icons/favicon.svg", "icons/icon-192.png", "icons/icon-512.png"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  if (url.origin !== location.origin || e.request.method !== "GET") return;
  if (url.pathname.includes("/data/")) {
    // Netzwerk zuerst, damit neue Artikel sofort erscheinen
    e.respondWith(fetch(e.request).then(r => {
      if(!r.ok) throw new Error("HTTP "+r.status);
      const copy = r.clone(); e.waitUntil(caches.open(CACHE).then(c => c.put(url.pathname, copy))); return r;
    }).catch(() => caches.match(url.pathname)));
    return;
  }
  e.respondWith(caches.match(e.request).then(hit => hit || fetch(e.request)));
});
