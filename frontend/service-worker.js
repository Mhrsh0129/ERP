// Service Worker for Jay Shree Traders ERP
// Version 1.0.0

const CACHE_NAME = 'jst-erp-v2';
const OFFLINE_URL = '/offline.html';

// Files to cache immediately on install
const PRECACHE_URLS = [
    '/',
    '/index.html',
    '/incoming-stock.html',
    '/outgoing-stock.html',
    '/inventory.html',
    '/offline.html',
    '/css/styles.css',
    '/js/app.js',
    '/js/bill-scanner.js',
    '/js/sw-register.js',
    '/manifest.json',
    '/icons/icon-192.png',
    '/icons/icon-512.png',
    '/favicon.png'
];

// Install event - cache critical assets
self.addEventListener('install', (event) => {
    console.log('[Service Worker] Installing...');

    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('[Service Worker] Precaching app shell');
                return cache.addAll(PRECACHE_URLS);
            })
            .then(() => self.skipWaiting())
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('[Service Worker] Activating...');

    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('[Service Worker] Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip cross-origin requests
    if (url.origin !== location.origin) {
        return;
    }

    // API requests - Network first, fallback to cache
    if (url.pathname.startsWith('/api/')) {
        // Only cache GET requests
        if (request.method !== 'GET') {
            event.respondWith(fetch(request));
            return;
        }

        event.respondWith(
            fetch(request)
                .then((response) => {
                    // Clone and cache successful API responses
                    if (response.ok) {
                        const responseClone = response.clone();
                        caches.open(CACHE_NAME).then((cache) => {
                            cache.put(request, responseClone);
                        });
                    }
                    return response;
                })
                .catch(() => {
                    // Fallback to cache if network fails
                    return caches.match(request).then((cachedResponse) => {
                        return cachedResponse || new Response(
                            JSON.stringify({ success: false, error: 'Offline - no cached data available' }),
                            { headers: { 'Content-Type': 'application/json' } }
                        );
                    });
                })
        );
        return;
    }

    // Static assets - Cache first, fallback to network
    // Only handle GET requests
    if (request.method !== 'GET') {
        return;
    }

    event.respondWith(
        caches.match(request)
            .then((cachedResponse) => {
                if (cachedResponse) {
                    return cachedResponse;
                }

                return fetch(request)
                    .then((response) => {
                        // Don't cache non-successful responses
                        if (!response || response.status !== 200 || response.type === 'error') {
                            return response;
                        }

                        // Clone and cache the response
                        const responseClone = response.clone();
                        caches.open(CACHE_NAME).then((cache) => {
                            cache.put(request, responseClone);
                        });

                        return response;
                    })
                    .catch(() => {
                        // If both cache and network fail, show offline page for navigation requests
                        if (request.mode === 'navigate') {
                            return caches.match(OFFLINE_URL);
                        }

                        // For other requests, return a basic error response
                        return new Response('Offline', {
                            status: 503,
                            statusText: 'Service Unavailable',
                            headers: new Headers({
                                'Content-Type': 'text/plain'
                            })
                        });
                    });
            })
    );
});

// Background sync event (for future use)
self.addEventListener('sync', (event) => {
    console.log('[Service Worker] Background sync:', event.tag);

    if (event.tag === 'sync-data') {
        event.waitUntil(
            // Future: Sync offline data when connection is restored
            Promise.resolve()
        );
    }
});

// Push notification event (for future use)
self.addEventListener('push', (event) => {
    console.log('[Service Worker] Push notification received');

    const options = {
        body: event.data ? event.data.text() : 'New notification',
        icon: '/icons/icon-192.png',
        badge: '/icons/icon-192.png',
        vibrate: [200, 100, 200]
    };

    event.waitUntil(
        self.registration.showNotification('Jay Shree Traders', options)
    );
});

// Message event - handle messages from clients
self.addEventListener('message', (event) => {
    console.log('[Service Worker] Message received:', event.data);

    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }

    if (event.data && event.data.type === 'CACHE_URLS') {
        event.waitUntil(
            caches.open(CACHE_NAME).then((cache) => {
                return cache.addAll(event.data.urls);
            })
        );
    }
});
