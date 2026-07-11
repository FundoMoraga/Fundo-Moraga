// Service Worker - Fundo Moraga PWA
// Version 1.1.0 - 2026-01-31 (Optimizado)

const CACHE_NAME = 'fundo-moraga-v1.1.0';
const RUNTIME_CACHE = 'fundo-moraga-runtime';
const IMAGE_CACHE = 'fundo-moraga-images';

// Assets to cache on install.
// IMPORTANTE: solo assets del mismo origen. cache.addAll() es atómico: si UN solo recurso
// falla (por ejemplo un recurso cross-origin sin header Access-Control-Allow-Origin, como
// pasaba con el logo servido desde Azure Blob Storage y con Google Fonts), TODO el precache
// falla y skipWaiting() nunca se llama, dejando el sitio sin cache para uso offline. Los
// recursos cross-origin se cachean igual de forma oportunista vía networkFirstStrategy en
// cada fetch normal, solo que no bloquean la instalación del service worker.
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/css/tokens.css',
  '/css/buttons.css',
  '/styles.20260126-1.css',
  '/script.20260126-1.js',
  '/manifest.json',
  '/offline.html',
  '/blog/',
  '/blog/index.html',
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('[SW] Installing service worker...');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[SW] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        console.log('[SW] Skip waiting');
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('[SW] Installation failed:', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating service worker...');
  
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((cacheName) => {
            return cacheName !== CACHE_NAME && 
                   cacheName !== RUNTIME_CACHE && 
                   cacheName !== IMAGE_CACHE;
          })
          .map((cacheName) => {
            console.log('[SW] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          })
      );
    }).then(() => {
      console.log('[SW] Claiming clients');
      return self.clients.claim();
    })
  );
});

// Fetch event - network first, then cache fallback
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Skip API calls (let them fail naturally)
  if (url.pathname.startsWith('/api/')) {
    return;
  }

  // Handle images separately (cache first)
  if (request.destination === 'image') {
    event.respondWith(cacheFirstStrategy(request, IMAGE_CACHE));
    return;
  }

  // Handle navigation requests (network first with offline fallback)
  if (request.mode === 'navigate') {
    event.respondWith(networkFirstWithOffline(request));
    return;
  }

  // Default: network first, cache fallback
  event.respondWith(networkFirstStrategy(request));
});

// Network first strategy
async function networkFirstStrategy(request) {
  const cache = await caches.open(RUNTIME_CACHE);
  
  try {
    const response = await fetch(request);
    
    // Cache successful responses
    if (response && response.status === 200) {
      cache.put(request, response.clone());
    }
    
    return response;
  } catch (error) {
    // Fallback to cache
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
      console.log('[SW] Serving from cache:', request.url);
      return cachedResponse;
    }
    
    // If no cache, return error
    throw error;
  }
}

// Cache first strategy (for images)
async function cacheFirstStrategy(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cachedResponse = await cache.match(request);
  
  if (cachedResponse) {
    console.log('[SW] Image from cache:', request.url);
    return cachedResponse;
  }
  
  try {
    const response = await fetch(request);
    
    if (response && response.status === 200) {
      cache.put(request, response.clone());
    }
    
    return response;
  } catch (error) {
    console.error('[SW] Image fetch failed:', error);

    // No hay un archivo /assets/images/placeholder.png en el proyecto: caches.match() sobre
    // un recurso que nunca se cacheó devuelve undefined, y un fetch handler que devuelve
    // undefined en vez de una Response rompe la carga (error de red genérico en el navegador
    // en vez de degradar a un placeholder). Se devuelve un SVG inline mínimo en su lugar.
    const placeholderSvg =
      '<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200">' +
      '<rect width="100%" height="100%" fill="#e5e7eb"/>' +
      '<text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" ' +
      'font-family="sans-serif" font-size="14" fill="#6b7280">Imagen no disponible</text>' +
      '</svg>';
    return new Response(placeholderSvg, {
      status: 200,
      headers: new Headers({ 'Content-Type': 'image/svg+xml', 'Cache-Control': 'no-store' })
    });
  }
}

// Network first with offline page fallback
async function networkFirstWithOffline(request) {
  try {
    const response = await fetch(request);
    
    // Cache successful navigation responses
    if (response && response.status === 200) {
      const cache = await caches.open(RUNTIME_CACHE);
      cache.put(request, response.clone());
    }
    
    return response;
  } catch (error) {
    // Try cache first
    const cachedResponse = await caches.match(request);
    
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Show offline page
    const offlinePage = await caches.match('/offline.html');
    
    if (offlinePage) {
      return offlinePage;
    }
    
    // Last resort: return error
    return new Response('Offline', {
      status: 503,
      statusText: 'Service Unavailable',
      headers: new Headers({
        'Content-Type': 'text/plain'
      })
    });
  }
}

// Background sync for form submissions (future enhancement)
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-form-submissions') {
    console.log('[SW] Background sync triggered');
    event.waitUntil(syncFormSubmissions());
  }
});

async function syncFormSubmissions() {
  // Implement form submission queue sync
  console.log('[SW] Syncing queued form submissions...');
}

// Push notifications (future enhancement)
self.addEventListener('push', (event) => {
  console.log('[SW] Push notification received');
  
  const options = {
    body: event.data ? event.data.text() : 'Nueva notificación de Fundo Moraga',
    icon: 'https://fundomoragastorage.blob.core.windows.net/assets/images/icon-192.png',
    badge: 'https://fundomoragastorage.blob.core.windows.net/assets/images/icon-72.png',
    vibrate: [200, 100, 200],
    data: {
      url: '/'
    },
    actions: [
      {
        action: 'open',
        title: 'Ver más'
      },
      {
        action: 'close',
        title: 'Cerrar'
      }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification('Fundo Moraga', options)
  );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  if (event.action === 'open' || !event.action) {
    const urlToOpen = event.notification.data.url || '/';
    
    event.waitUntil(
      clients.matchAll({ type: 'window', includeUncontrolled: true })
        .then((clientList) => {
          // Check if there's already a window open
          for (let client of clientList) {
            if (client.url === urlToOpen && 'focus' in client) {
              return client.focus();
            }
          }
          
          // Open new window
          if (clients.openWindow) {
            return clients.openWindow(urlToOpen);
          }
        })
    );
  }
});

console.log('[SW] Service Worker loaded successfully');
