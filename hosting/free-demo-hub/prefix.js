// Keep root-relative requests and links inside each demo without editing its files.
(() => {
  const prefix = document.currentScript.dataset.prefix;
  const resolve = (value) => {
    if (typeof value !== 'string' || !value.startsWith('/') || value.startsWith('//')
      || value === prefix || value.startsWith(prefix + '/') || value.startsWith('/_hosting/')) return value;
    return prefix + value;
  };
  const originalFetch = window.fetch;
  window.fetch = (input, init) => {
    if (typeof input === 'string') input = resolve(input);
    else if (input instanceof Request) {
      const url = new URL(input.url);
      if (url.origin === location.origin) input = new Request(resolve(url.pathname) + url.search, input);
    }
    return originalFetch.call(window, input, init);
  };
  const originalOpen = XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open = function (method, url, ...args) {
    return originalOpen.call(this, method, resolve(url), ...args);
  };
  const fixLinks = () => {
    for (const element of document.querySelectorAll('[href], [src], [action]')) {
      for (const attr of ['href', 'src', 'action']) {
        const value = element.getAttribute(attr);
        const resolved = resolve(value);
        if (resolved !== value) element.setAttribute(attr, resolved);
      }
    }
  };
  document.addEventListener('DOMContentLoaded', () => {
    fixLinks();
    new MutationObserver(fixLinks).observe(document.documentElement, {childList: true, subtree: true});
  });
})();
