/**
 * Diet Coach Agent — Service Worker (PWA-02, PWA-03)
 *
 * Strategy:
 *   - On install: pre-cache the offline fallback page.
 *   - On fetch (navigation): network-first; serve offline.html if network fails.
 *   - On activate: remove stale caches from previous versions.
 *
 * Note: PNG icons are referenced in manifest.json.
 * For production, replace icon.svg with proper 192×192 and 512×512 PNGs.
 */

const CACHE_VERSION = 'v1'
const CACHE_NAME = `diet-coach-${CACHE_VERSION}`
const OFFLINE_URL = '/offline.html'

// Assets to pre-cache at install time
const PRECACHE_URLS = [OFFLINE_URL]

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => cache.addAll(PRECACHE_URLS))
      .then(() => self.skipWaiting()),
  )
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keyList) =>
        Promise.all(
          keyList
            .filter((key) => key !== CACHE_NAME)
            .map((key) => caches.delete(key)),
        ),
      )
      .then(() => self.clients.claim()),
  )
})

self.addEventListener('fetch', (event) => {
  // Only intercept same-origin navigation requests
  if (
    event.request.mode === 'navigate' &&
    event.request.url.startsWith(self.location.origin)
  ) {
    event.respondWith(
      fetch(event.request).catch(() =>
        caches.match(OFFLINE_URL).then(
          (cached) =>
            cached ??
            new Response('<h1>Offline</h1>', {
              headers: { 'Content-Type': 'text/html' },
            }),
        ),
      ),
    )
  }
})
