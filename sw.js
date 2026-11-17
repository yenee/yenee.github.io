const CACHE_PREFIX = `alishan-trip-${new URL(self.registration.scope).pathname}-`;
const CACHE_NAME = `${CACHE_PREFIX}v24`;
const SHELL_URL = new URL("index.html", self.registration.scope).href;
const SUNRISE_STATUS_URL = new URL("sunrise-status.json", self.registration.scope).href;
const ASSET_URLS = [
  "index.html", "manifest.json", "sunrise-status.json", "icon-192.png", "icon-512.png", "apple-touch-icon.png",
  "vendor/leaflet/leaflet.js", "vendor/leaflet/leaflet.css", "vendor/leaflet/LICENSE",
  "vendor/leaflet/images/layers.png", "vendor/leaflet/images/layers-2x.png",
  "vendor/leaflet/images/marker-icon.png", "vendor/leaflet/images/marker-icon-2x.png", "vendor/leaflet/images/marker-shadow.png"
]
  .map(path => new URL(path, self.registration.scope).href);
const REFERENCE_IMAGE_URLS = new Set([
  "https://www.94iprofun.com/upload/images/MAP%E9%98%BF%E9%87%8C%E5%B1%B1%E5%9C%92%E5%8D%80%E5%85%A7-%E9%A3%AF%E5%BA%97%E4%B8%80%E8%A6%BD%E5%9C%96.jpg",
  "https://www.94iprofun.com/upload/images/%E5%9C%B0%E5%9C%96_%E9%98%BF%E9%87%8C%E5%B1%B1%E6%A3%AE%E6%9E%97%E5%9C%92%E5%8D%80%E5%9C%B0%E5%9C%96001.jpg",
  "https://www.94iprofun.com/upload/images/%E5%9C%B0%E5%9C%96_%E9%98%BF%E9%87%8C%E5%B1%B1%E6%A3%AE%E6%9E%97%E5%9C%92%E5%8D%80%E5%9C%B0%E5%9C%96.jpg",
  "https://www.94iprofun.com/upload/images/Map_%E5%A5%AE%E8%B5%B7%E6%B9%96001%20(1170%20x%20772).jpg",
  "https://static-assets.oen.tw/images/img-33BAFiaFOGz92cZTk4dAilqfq4c.jpg",
  "https://margaret.tw/wp-content/uploads/2013/11/%E6%B0%B4%E5%B1%B1%E7%99%82%E7%99%92%E6%AD%A5%E9%81%93photo6.jpg"
]);

async function cacheReferenceImage(cache, imageUrl) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 12000);
  try {
    const response = await fetch(imageUrl, { mode: "no-cors", signal: controller.signal });
    await cache.put(imageUrl, response.clone());
  } catch {
    // Keep service worker installation available when an external image host is unreachable.
  } finally {
    clearTimeout(timeout);
  }
}

self.addEventListener("install", event => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE_NAME);
    await cache.addAll(ASSET_URLS);
    await Promise.all([...REFERENCE_IMAGE_URLS].map(imageUrl => cacheReferenceImage(cache, imageUrl)));
  })());
});

self.addEventListener("activate", event => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(key => key.startsWith(CACHE_PREFIX) && key !== CACHE_NAME).map(key => caches.delete(key)));
    await self.clients.claim();
  })());
});

self.addEventListener("message", event => {
  if (event.data?.type === "SKIP_WAITING") self.skipWaiting();
});

self.addEventListener("fetch", event => {
  if (event.request.method !== "GET") return;
  const url = new URL(event.request.url);
  const scope = new URL(self.registration.scope);
  if (REFERENCE_IMAGE_URLS.has(url.href)) {
    event.respondWith((async () => {
      const cache = await caches.open(CACHE_NAME);
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 10000);
      try {
        const response = await fetch(event.request, { mode: "no-cors", signal: controller.signal });
        await cache.put(event.request, response.clone());
        return response;
      } catch {
        return (await cache.match(event.request)) || new Response("Offline image is not cached yet.", { status: 503, headers: { "Content-Type": "text/plain; charset=utf-8" } });
      } finally {
        clearTimeout(timeout);
      }
    })());
    return;
  }
  if (url.origin !== scope.origin) return;
  const assetUrl = `${url.origin}${url.pathname}`;
  if (event.request.mode === "navigate" && (url.pathname === scope.pathname || assetUrl === SHELL_URL)) {
    event.respondWith((async () => {
      const cache = await caches.open(CACHE_NAME);
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 4000);
      try {
        const response = await fetch(event.request, { signal: controller.signal, cache: "no-store" });
        if (!response.ok) throw new Error("Navigation unavailable");
        await cache.put(SHELL_URL, response.clone());
        return response;
      } catch {
        return (await cache.match(SHELL_URL)) || new Response("Offline page not cached yet.", { status: 503, headers: { "Content-Type": "text/plain; charset=utf-8" } });
      } finally {
        clearTimeout(timeout);
      }
    })());
  } else if (assetUrl === SUNRISE_STATUS_URL) {
    event.respondWith((async () => {
      const cache = await caches.open(CACHE_NAME);
      try {
        const response = await fetch(event.request);
        if (!response.ok) throw new Error("Sunrise notice unavailable");
        await cache.put(SUNRISE_STATUS_URL, response.clone());
        return response;
      } catch {
        return (await cache.match(SUNRISE_STATUS_URL)) || new Response("{}", { status: 503, headers: { "Content-Type": "application/json" } });
      }
    })());
  } else if (ASSET_URLS.includes(assetUrl)) {
    event.respondWith(caches.open(CACHE_NAME).then(async cache => (await cache.match(assetUrl)) || fetch(event.request)));
  }
});