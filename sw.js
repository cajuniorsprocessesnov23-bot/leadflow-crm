// LeadFlow CRM service worker: makes the CRM installable as a phone app.
// It does not cache pages or data, so everyone always sees the latest version.
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (e) => e.waitUntil(self.clients.claim()));
