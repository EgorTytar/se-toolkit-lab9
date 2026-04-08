/* eslint-disable no-restricted-globals */

self.addEventListener('install', function(event) {
  console.log('[SW] Service worker installed');
  self.skipWaiting();
});

self.addEventListener('activate', function(event) {
  console.log('[SW] Service worker activated');
  event.waitUntil(self.clients.claim());
});

self.addEventListener('push', function (event) {
  console.log('[SW] Push event received!');
  
  if (!event.data) {
    console.log('[SW] No push data');
    return;
  }

  let title = 'F1 Assistant';
  let body = 'Test notification';

  try {
    const data = event.data.json();
    console.log('[SW] Push data:', data);
    title = data.title || 'F1 Assistant';
    body = data.body || '';
  } catch (e) {
    console.log('[SW] Parse error:', e);
    body = event.data.text() || body;
  }

  const options = {
    body: body,
    tag: 'f1-test',
    renotify: true,
  };

  console.log('[SW] Showing notification:', title, body);
  event.waitUntil(
    self.registration.showNotification(title, options)
      .then(() => console.log('[SW] Notification shown'))
      .catch(err => console.error('[SW] Notification error:', err))
  );
});

self.addEventListener('notificationclick', function (event) {
  console.log('[SW] Notification clicked');
  event.notification.close();
  event.waitUntil(
    self.clients.openWindow('/')
  );
});
