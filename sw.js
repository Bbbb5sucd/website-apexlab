/* ========================================
   APEX LABS — Service Worker
   Cache-first strategy for fast repeat visits
   and offline resilience (important for WB
   where connectivity can be intermittent).
======================================== */

const CACHE_NAME = 'apex-labs-v3';
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/css/style.css',
  '/css/product-page.css',
  '/js/main.js',
  '/js/product-page.js',
  '/assets/favicon.svg'
];

/**
 * Strip query string from a URL for cache-key normalisation.
 * style.css?v=3 → style.css so pre-cached assets always match.
 */
function stripQuery(url) {
  const u = new URL(url);
  u.search = '';
  return u.toString();
}

// Install: Pre-cache essential files
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

// Activate: Clean old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    })
  );
  self.clients.claim();
});

// Fetch: Stale-while-revalidate for HTML, cache-first for assets
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Only handle same-origin requests
  if (url.origin !== location.origin) return;

  // For HTML pages: network-first with cache fallback
  if (request.headers.get('accept')?.includes('text/html')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
          return response;
        })
        .catch(() => caches.match(request) || caches.match('/index.html'))
    );
    return;
  }

  // For CSS, JS, images: cache-first with network fallback (normalise URL)
  const cacheKey = stripQuery(request.url);
  event.respondWith(
    caches.match(cacheKey).then((cached) => {
      if (cached) {
        // Return cached, but also update cache in background
        fetch(request).then((response) => {
          caches.open(CACHE_NAME).then((cache) => cache.put(cacheKey, response));
        }).catch(() => {});
        return cached;
      }
      return fetch(request).then((response) => {
        const clone = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(cacheKey, clone));
        return response;
      });
    })
  );
});
