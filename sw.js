const CACHE = "provador-premium-20261103-final";
const ASSETS = [
  "/premium.css",
  "/img/skincare-editorial.jpg",
  "/",
  "/index.html",
  "/provador/",
  "/provador/index.html",
  "/quiz.json",
  "/produtos.json",
  "/pele/oleosa/",
  "/pele/seca/",
  "/pele/mista/",
  "/pele/normal/"
];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)));
  self.skipWaiting();
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", e => {
  if (e.request.method !== "GET" || new URL(e.request.url).origin !== location.origin) return;
  // Rede primeiro: preços e produtos atualizados aparecem logo; cache só quando offline.
  e.respondWith(
    fetch(e.request).then(r => {
      const copia = r.clone();
      caches.open(CACHE).then(c => c.put(e.request, copia));
      return r;
    }).catch(() => caches.match(e.request).then(c => c || caches.match("/")))
  );
});
