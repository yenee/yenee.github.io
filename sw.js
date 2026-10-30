const CACHE_PREFIX = `alishan-trip-${new URL(self.registration.scope).pathname}-`;
const CACHE_NAME = `${CACHE_PREFIX}v2`;
const SHELL_URL = new URL("index.html", self.registration.scope).href;
const ASSET_URLS = ["index.html", "manifest.json", "icon-192.png", "icon-512.png", "apple-touch-icon.png"]
  .map(path => new URL(path, self.registration.scope).href);

self.addEventListener("install", event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(ASSET_URLS)));
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
  } else if (ASSET_URLS.includes(assetUrl)) {
    event.respondWith(caches.open(CACHE_NAME).then(async cache => (await cache.match(assetUrl)) || fetch(event.request)));
  }
});