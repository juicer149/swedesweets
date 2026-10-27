/* Product images retain native browser caching. If a signed media request
   fails, retry once using fresh HTML from its existing authorised page. */
(() => {
  "use strict";
  const attempted = new WeakSet();
  const pages = new Map();
  const selector = "img.tile__image, img.product__image, img.line__image, img.enhanced-product-option__image";
  const path = url => { try { return new URL(url, location.href).pathname; } catch { return ""; } };
  async function freshPage(url) {
    if (!pages.has(url)) {
      const promise = fetch(url, { credentials: "same-origin", cache: "no-store", headers: { Accept: "text/html" }, signal: AbortSignal.timeout(8000) })
        .then(async response => {
          if (!response.ok || new URL(response.url).origin !== location.origin) throw new Error("Image page unavailable");
          return new DOMParser().parseFromString(await response.text(), "text/html");
        });
      pages.set(url, promise);
      setTimeout(() => pages.delete(url), 1000);
    }
    return pages.get(url);
  }
  function warn(image) {
    image.dataset.imageFailed = "";
    // No signed query, credentials or customer/form data in diagnostics.
    console.warn("[SwedeSweets] Product image could not be loaded:", path(image.currentSrc || image.src));
  }
  async function recover(image) {
    if (!image.matches(selector)) return;
    if (attempted.has(image)) { warn(image); return; }
    attempted.add(image);
    const original = image.currentSrc || image.src;
    const linked = image.closest("a[href]");
    const url = new URL(linked?.href || location.href, location.href);
    if (url.origin !== location.origin) { warn(image); return; }
    try {
      const page = await freshPage(url.href);
      const product = page.querySelector("[data-product-page]");
      let fresh;
      if (product && /\/(?:shop\/products|my\/catalog)\/\d+\/?$/.test(url.pathname)) {
        fresh = image.matches(".product__image")
          ? product.querySelector("img.product__image")?.getAttribute("src")
          : product.dataset.productThumbnailUrl;
      } else {
        fresh = [...page.querySelectorAll(selector)].find(candidate => path(candidate.getAttribute("src")) === path(original))?.getAttribute("src");
        // Tom Select renders its pictures from option data, not <img> markup.
        fresh ||= [...page.querySelectorAll("option[data-image]")].find(option => path(option.dataset.image) === path(original))?.dataset.image;
      }
      if (!fresh || !image.isConnected) { if (image.isConnected) warn(image); return; }
      image.loading = "eager";
      image.src = new URL(fresh, url).href;
    } catch { if (image.isConnected) warn(image); }
  }
  document.addEventListener("error", event => { if (event.target instanceof HTMLImageElement) void recover(event.target); }, true);
  document.addEventListener("load", event => {
    if (event.target instanceof HTMLImageElement) delete event.target.dataset.imageFailed;
  }, true);
  for (const image of document.querySelectorAll(selector)) {
    if (image.complete && !image.naturalWidth) void recover(image);
  }
  window.SwedeSweetsProductImages = { async ready(scope) {
    const image = scope.querySelector("img.product__image");
    if (!image) return;
    const preload = new Image();
    preload.src = new URL(image.getAttribute("src"), location.href).href;
    await Promise.race([preload.decode().catch(() => {}), new Promise(resolve => setTimeout(resolve, 900))]);
  } };
})();
