const CACHE = "provador-premium-20261106-confianca";
const ASSETS = [
  "/premium.css",
  "/premium.js",
  "/compartilhar.js",
  "/regras-ativos.js",
  "/fonts/cormorant-500.ttf",
  "/fonts/manrope-400.ttf",
  "/fonts/manrope-600.ttf",
  "/img/ritual-face.jpg",
  "/img/cream-texture.jpg",
  "/img/skincare-editorial.jpg",
  "/img/tipo-oleosa.jpg",
  "/img/tipo-seca.jpg",
  "/img/tipo-mista.jpg",
  "/img/tipo-normal.jpg",
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
