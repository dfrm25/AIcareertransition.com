/**
 * Loads GA4 and AdSense after window.load to reduce main-thread work during first paint.
 * Included from a tiny inline bootstrap in each page (see PERFORMANCE.md).
 */
(function () {
  function loadScript(src, opts) {
    var s = document.createElement('script');
    s.src = src;
    s.async = true;
    if (opts && opts.crossOrigin) s.crossOrigin = opts.crossOrigin;
    document.head.appendChild(s);
    return s;
  }

  function initGtag() {
    window.dataLayer = window.dataLayer || [];
    window.gtag = function gtag() {
      window.dataLayer.push(arguments);
    };
    gtag('js', new Date());
    gtag('config', 'G-9JFKY1RSL2');
  }

  var g = loadScript('https://www.googletagmanager.com/gtag/js?id=G-9JFKY1RSL2');
  g.addEventListener('load', initGtag);
  loadScript('https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5179979583019834', {
    crossOrigin: 'anonymous',
  });
})();
