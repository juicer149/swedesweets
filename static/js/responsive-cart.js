/* One live cart editor on every screen. Load the existing server-rendered cart
   when first opened; keep its DOM and draft while navbar fragments change. */
(() => {
  "use strict";
  let editor = document.querySelector("[data-responsive-cart-page]");
  const directVisit = Boolean(editor);
  let stale = false;
  let loading = null;
  let focused = null;
  let scrollTop = 0;
  let previousScroll = null;
  const scripts = new Map();
  const cartMenu = () => document.querySelector('details[data-mobile-menu="cart"]');
  if (!cartMenu()) return;

  function preserve() {
    if (editor?.contains(document.activeElement)) focused = document.activeElement;
    if (previousScroll) scrollTop = previousScroll.scrollTop;
  }

  function mount() {
    const scroll = cartMenu()?.querySelector("[data-cart-panel-scroll]");
    if (!editor || !scroll) return;
    preserve();
    if (editor.parentElement !== scroll) scroll.replaceChildren(editor);
    previousScroll = scroll;
    scroll.scrollTop = scrollTop;
    if (cartMenu()?.open) focused?.focus({ preventScroll: true });
  }

  function loadScript(source) {
    const url = new URL(source, location.href);
    // Dependencies are explicitly marked on our same-origin cart response.
    if (url.origin !== location.origin) return Promise.reject(new Error("Invalid cart script"));
    if ([...document.scripts].some(script => script.src === url.href)) return Promise.resolve();
    if (!scripts.has(url.href)) scripts.set(url.href, new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = url.href;
      script.onload = resolve;
      script.onerror = reject;
      document.body.append(script);
    }));
    return scripts.get(url.href);
  }

  async function loadEditor() {
    if (loading) return loading;
    if (editor && !stale) { mount(); return; }
    const url = cartMenu()?.dataset.cartPageUrl;
    if (!url) return;
    const scroll = cartMenu().querySelector("[data-cart-panel-scroll]");
    scroll?.setAttribute("aria-busy", "true");
    loading = (async () => {
      const response = await fetch(url, { credentials: "same-origin" });
      if (!response.ok) throw new Error("Could not load cart");
      const page = new DOMParser().parseFromString(await response.text(), "text/html");
      const next = page.querySelector("[data-responsive-cart-page]");
      if (!next) throw new Error("Cart editor missing");
      const draft = [...(editor?.querySelector("[data-checkout-details-form]")?.elements || [])]
        .filter(field => field.name && field.type !== "hidden")
        .map(field => [field.name, field.value]);
      preserve();
      editor?.remove();
      editor = document.importNode(next, true);
      for (const [name, value] of draft) {
        const field = editor.querySelector("[data-checkout-details-form]")?.elements.namedItem(name);
        if (field) field.value = value;
      }
      stale = false;
      focused = null;
      mount();
      for (const script of page.querySelectorAll("script[data-cart-editor-script][src]")) await loadScript(script.src);
      window.enhanceSelects?.(editor);
      window.enhanceSmoothDetails?.(editor);
      document.dispatchEvent(new Event("cart-editor-ready"));
      document.dispatchEvent(new CustomEvent("navbar-cart-refreshed", { detail: { layoutOnly: true } }));
    })().catch(() => {
      // The ordinary cart URL remains a complete server-rendered fallback.
      if (cartMenu()?.open) window.location.assign(url);
    }).finally(() => {
      cartMenu()?.querySelector("[data-cart-panel-scroll]")?.removeAttribute("aria-busy");
      loading = null;
    });
    return loading;
  }

  function open() {
    const cart = cartMenu();
    if (!cart || cart.dataset.cartLocked === "true") return;
    document.dispatchEvent(new CustomEvent("mobile-menu-request", { detail: { key: "cart" } }));
    void loadEditor();
  }
  document.addEventListener("click", event => {
    const link = event.target.closest("a[href]");
    if (!link || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    if (cartMenu()?.dataset.cartLocked === "true") return;
    if (new URL(link.href).pathname !== cartMenu()?.dataset.cartPageUrl) return;
    event.preventDefault();
    event.stopPropagation();
    open();
  }, true);
  document.addEventListener("toggle", event => {
    if (event.target !== cartMenu()) return;
    if (event.target.open) void loadEditor();
    else if (directVisit && !matchMedia("(max-width: 767px)").matches
        && !document.querySelector('details[data-mobile-menu][open]')) {
      window.location.assign(editor?.dataset.cartReturnUrl || "/");
    }
  }, true);
  document.addEventListener("navbar-cart-replacing", preserve);
  document.addEventListener("navbar-cart-refreshed", event => {
    if (!event.detail?.layoutOnly) mount();
  });
  document.addEventListener("cart-changed", event => {
    if (event.detail?.source !== "current-order") stale = true;
  });
  document.addEventListener("cart-editor-invalidated", () => {
    stale = true;
    if (cartMenu()?.open) void loadEditor();
  });
  document.addEventListener("mobile-menu-settled", event => {
    if (directVisit && !event.detail.key) window.location.assign(editor?.dataset.cartReturnUrl || "/");
  });
  if (editor) { mount(); open(); }
})();
