/**
 * Loads GA4 and AdSense after window.load while honoring Google Consent Mode v2.
 * AdSense is gated until ads_storage is granted so pending review does not load empty inventory for users who decline ads.
 */
(function () {
  var GA_ID = 'G-9JFKY1RSL2';
  var ADS_CLIENT = 'ca-pub-5179979583019834';
  var KEY = 'aict_cookie_consent_v1';

  window.dataLayer = window.dataLayer || [];
  window.gtag = window.gtag || function gtag() { window.dataLayer.push(arguments); };
  window.gtag('consent', 'default', {
    analytics_storage: 'denied',
    ad_storage: 'denied',
    ad_user_data: 'denied',
    ad_personalization: 'denied',
    wait_for_update: 500,
  });

  function getConsent() {
    try { return JSON.parse(localStorage.getItem(KEY) || 'null'); } catch (e) { return null; }
  }

  function loadScript(src, opts) {
    var s = document.createElement('script');
    s.src = src;
    s.async = true;
    if (opts && opts.crossOrigin) s.crossOrigin = opts.crossOrigin;
    document.head.appendChild(s);
    return s;
  }

  function applyConsent(consent) {
    var granted = consent && consent.status === 'accepted';
    window.gtag('consent', 'update', {
      analytics_storage: granted ? 'granted' : 'denied',
      ad_storage: granted ? 'granted' : 'denied',
      ad_user_data: granted ? 'granted' : 'denied',
      ad_personalization: granted ? 'granted' : 'denied',
    });
    return granted;
  }

  function initGtag() {
    window.gtag('js', new Date());
    window.gtag('config', GA_ID, { anonymize_ip: true });
  }

  var consent = getConsent();
  var granted = applyConsent(consent);
  var g = loadScript('https://www.googletagmanager.com/gtag/js?id=' + GA_ID);
  g.addEventListener('load', initGtag);

  if (granted) {
    window.__aictAdsLoaded = true;
    loadScript('https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=' + ADS_CLIENT, { crossOrigin: 'anonymous' });
  }

  window.addEventListener('aict:consent-updated', function (event) {
    var updated = event.detail || getConsent();
    if (applyConsent(updated) && !window.__aictAdsLoaded) {
      window.__aictAdsLoaded = true;
      loadScript('https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=' + ADS_CLIENT, { crossOrigin: 'anonymous' });
    }
  });
})();
