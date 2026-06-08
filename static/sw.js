const CACHE_NAAM = 'studybuddy-v2';
const BESTANDEN = [
  '/dashboard',
  '/static/css/style.css',
  '/static/js/timer.js',
  '/static/media/home.png',
  '/static/media/calendar.png',
  '/static/media/books.png',
  '/static/media/settings.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAAM).then((cache) => cache.addAll(BESTANDEN))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((namen) =>
      Promise.all(
        namen.filter((naam) => naam !== CACHE_NAAM)
             .map((naam) => caches.delete(naam))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});