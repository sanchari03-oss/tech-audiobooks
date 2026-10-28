// TechBooks • Audio - Service Worker
const CACHE_NAME = 'techbooks-cache-v1';

const STATIC_ASSETS = [
  './',
  './index.html',
  './manifest.json',
  './books.json'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);

  // Audio files / Range requests: Never cache in SW; handled by browser audio tag and IndexedDB
  if (e.request.destination === 'audio' || /\.(mp3|m4a|aac|ogg|wav)($|\?)/i.test(url.pathname)) {
    return;
  }

  // Navigation: Network first, fallback to cached index.html
  if (e.request.mode === 'navigate') {
    e.respondWith(
      fetch(e.request)
        .then((res) => {
          if (res.ok) {
            const clone = res.clone();
            caches.open(CACHE_NAME).then((c) => c.put(e.request, clone));
          }
          return res;
        })
        .catch(async () => {
          return (await caches.match('./index.html')) || 
                 (await caches.match('./')) || 
                 (await caches.match(e.request));
        })
    );
    return;
  }

  // books.json and manifest.json: Network first, fallback to cached JSON
  if (url.pathname.endsWith('/books.json') || url.pathname.endsWith('/manifest.json')) {
    e.respondWith(
      fetch(e.request)
        .then((res) => {
          if (res.ok) {
            const clone = res.clone();
            caches.open(CACHE_NAME).then((c) => c.put(e.request, clone));
          }
          return res;
        })
        .catch(async () => {
          return (await caches.match(e.request)) ||
                 (await caches.match('./books.json')) ||
                 new Response('{"books":[]}', { headers: { 'Content-Type': 'application/json' } });
        })
    );
    return;
  }

  // Static images, covers, icons: Cache first, fetch fresh if updated
  if (/\.(jpg|jpeg|png|webp|svg|ico)($|\?)/i.test(url.pathname)) {
    e.respondWith(
      caches.match(e.request).then((cached) => {
        const fetchPromise = fetch(e.request)
          .then((networkRes) => {
            if (networkRes.ok) {
              const clone = networkRes.clone();
              caches.open(CACHE_NAME).then((c) => c.put(e.request, clone));
            }
            return networkRes;
          })
          .catch(() => cached || (url.search ? caches.match(url.pathname, { ignoreSearch: true }) : null));
        return cached || fetchPromise;
      })
    );
    return;
  }
});
