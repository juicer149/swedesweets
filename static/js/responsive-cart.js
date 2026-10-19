/* Desktop has a quick cart and a full cart page. Mobile hosts the same live
   cart/review/result DOM in one sheet; viewport changes preserve its fields. */
(() => {
  "use strict";
  const app = window.SwedeSweets = window.SwedeSweets || {};
  const mobile = matchMedia("(max-width: 767px)");
  const originUrl = location.href;
  const cartMenu = () => document.querySelector('details[data-mobile-menu="cart"]');
  if (!cartMenu()) return;
  let root = document.querySelector("[data-order-flow-page]");
  const directVisit = Boolean(root);
  let flowUrl = root ? location.href : null;
  let slot = null;
  let hosted = false;
  let preview = null;
  let scrollBox = null;
  let scrollTop = 0;
  let focused = null;
  let stale = false;
  let loading = null;
  let lastMenuKey = null;
  const scripts = new Map();
  if (root) { slot = document.createComment("order flow"); root.before(slot); }

  function preserve() {
    if (root?.contains(document.activeElement)) focused = document.activeElement;
    if (hosted && scrollBox) scrollTop = scrollBox.scrollTop;
  }
  function controls() {
    const menu = cartMenu();
    if (!menu) return;
    menu.dataset.flowHost = String(hosted);
    const trigger = menu.querySelector("summary");
    const fullPage = flowUrl && new URL(flowUrl).pathname === location.pathname;
    if (fullPage) {
      menu.dataset.cartLocked = "true";
      trigger?.setAttribute("aria-current", "page");
      for (const other of document.querySelectorAll('.site-nav__link[aria-current], .account-menu > summary[aria-current]')) {
        other.removeAttribute("aria-current"); other.classList.remove("site-nav__link--active");
      }
    }
    const locked = menu.dataset.cartLocked === "true" && !hosted;
    trigger?.toggleAttribute("inert", locked);
    if (locked) { trigger?.setAttribute("aria-disabled", "true"); trigger?.setAttribute("tabindex", "-1"); }
    else { trigger?.removeAttribute("aria-disabled"); trigger?.removeAttribute("tabindex"); }
    const button = menu.querySelector("[data-close-details]");
    const back = hosted && root?.dataset.flowStep === "review" && root.dataset.flowBackUrl;
    button?.querySelector("[data-panel-close-icon]")?.toggleAttribute("hidden", Boolean(back));
    button?.querySelector("[data-panel-back-icon]")?.toggleAttribute("hidden", !back);
    if (button) button.setAttribute("aria-label", back ? button.dataset.backLabel : button.dataset.closeLabel);
  }
  function mount({ open = false } = {}) {
    const menu = cartMenu(), scroll = menu?.querySelector("[data-cart-panel-scroll]");
    if (!root || !scroll) return;
    preserve();
    if (mobile.matches) {
      if (root.parentElement !== scroll) {
        preview = document.createDocumentFragment();
        preview.append(...scroll.childNodes);
        scroll.replaceChildren(root);
      }
      hosted = true;
      scrollBox = scroll;
      scroll.scrollTop = scrollTop;
      controls();
      if (open && !menu.open) document.dispatchEvent(new CustomEvent("mobile-menu-request", { detail: { key: "cart" } }));
    } else {
      if (!root.closest("main")) {
        if (!slot?.isConnected) {
          const main = document.querySelector("main > .container");
          slot = document.createComment("order flow");
          main.replaceChildren(slot);
        }
        slot.after(root);
        if (flowUrl && location.href !== flowUrl) history.replaceState({ orderFlow: true }, "", flowUrl);
      }
      if (hosted && preview) scroll.replaceChildren(preview);
      if (hosted) menu.open = false;
      hosted = false;
      controls();
    }
    if (focused?.isConnected && (menu.open || !mobile.matches)) focused.focus({ preventScroll: true });
  }
  async function dependencies(page, scope) {
    for (const source of page.querySelectorAll("script[data-cart-editor-script][src]")) {
      const url = new URL(source.getAttribute("src"), location.origin);
      if (url.origin !== location.origin) throw new Error("Invalid flow script");
      if ([...document.scripts].some(script => script.src === url.href)) continue;
      if (!scripts.has(url.href)) scripts.set(url.href, new Promise((resolve, reject) => {
        const script = document.createElement("script");
        script.src = url.href; script.onload = resolve; script.onerror = reject;
        document.body.append(script);
      }));
      await scripts.get(url.href);
    }
    window.enhanceSelects?.(scope);
    window.enhanceSmoothDetails?.(scope);
    document.dispatchEvent(new Event("cart-editor-ready"));
    document.dispatchEvent(new CustomEvent("navbar-cart-refreshed", { detail: { layoutOnly: true } }));
    document.dispatchEvent(new Event("order-flow-ready"));
  }
  async function adopt(next, page, url, { preserveSurface = false } = {}) {
    preserve();
    app.orderFlow?.prepare(next);
    const old = root;
    const surface = old?.querySelector(":scope > .order-flow-surface");
    const nextSurface = next.querySelector(":scope > .order-flow-surface");
    if (preserveSurface && surface && nextSurface && old.isConnected) {
      // Keep the timeline and its containing geometry mounted throughout.
      for (const [target, source] of [[old, next], [surface, nextSurface]]) {
        for (const attr of [...target.attributes]) target.removeAttribute(attr.name);
        for (const attr of source.attributes) target.setAttribute(attr.name, attr.value);
      }
      surface.querySelector(":scope > .order-flow-content").replaceWith(nextSurface.querySelector(":scope > .order-flow-content"));
      root = old;
    } else root = next;
    flowUrl = url;
    focused = null;
    scrollTop = 0;
    if (old !== root && old?.isConnected) old.replaceWith(root);
    mount({ open: mobile.matches });
    controls();
    await dependencies(page, root);
    return root;
  }
  async function loadCart() {
    if (loading) return loading;
    if (root && !stale) { mount({ open: true }); return root; }
    const url = cartMenu()?.dataset.cartPageUrl;
    if (!url) return null;
    loading = (async () => {
      const response = await fetch(url, { credentials: "same-origin" });
      if (!response.ok) throw new Error("Cart unavailable");
      const page = new DOMParser().parseFromString(await response.text(), "text/html");
      const next = page.querySelector("[data-order-flow-page]");
      if (!next) throw new Error("Missing cart");
      const draft = [...(root?.querySelector("[data-checkout-details-form]")?.elements || [])].filter(e => e.name && e.type !== "hidden").map(e => [e.name, e.value]);
      const imported = document.importNode(next, true);
      for (const [name, value] of draft) {
        const field = imported.querySelector("[data-checkout-details-form]")?.elements.namedItem(name);
        if (field) field.value = value;
      }
      stale = false;
      return adopt(imported, page, response.url);
    })().catch(() => { if (cartMenu()?.open) location.assign(url); return null; }).finally(() => { loading = null; });
    return loading;
  }
  document.addEventListener("toggle", event => {
    if (event.target === cartMenu() && event.target.open && mobile.matches && !hosted) void loadCart();
  }, true);
  document.addEventListener("navbar-cart-replacing", preserve);
  document.addEventListener("navbar-cart-refreshed", event => { if (!event.detail?.layoutOnly && hosted) mount(); });
  document.addEventListener("cart-changed", event => { if (event.detail?.source !== "current-order") stale = true; });
  document.addEventListener("cart-editor-invalidated", () => { stale = true; if (hosted) void loadCart(); });
  document.addEventListener("click", event => {
    const link = event.target.closest("a[href]");
    if (!mobile.matches || !link || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    if (cartMenu()?.dataset.cartLocked === "true" && !hosted) return;
    if (new URL(link.href).pathname !== cartMenu()?.dataset.cartPageUrl) return;
    event.preventDefault(); event.stopPropagation();
    if (hosted && root?.dataset.flowStep !== "cart") void app.orderFlow?.visit(link.href);
    else void loadCart().then(() => mount({ open: true }));
  }, true);
  document.addEventListener("panel-close-request", event => {
    if (event.target !== cartMenu() || !hosted) return;
    if (app.orderFlow?.busy()) { event.preventDefault(); return; }
    if (root?.dataset.flowStep === "review" && root.dataset.flowBackUrl) {
      event.preventDefault(); void app.orderFlow?.visit(root.dataset.flowBackUrl);
    }
  });
  document.addEventListener("mobile-menu-settled", event => {
    const previous = lastMenuKey;
    lastMenuKey = event.detail.key;
    if (!hosted || event.detail.key) return;
    if (previous && previous !== "cart" && flowUrl && new URL(flowUrl).pathname === location.pathname) {
      // Settings/account can cover the mobile journey; dismissing them brings
      // back that journey rather than abandoning its current stage.
      mount({ open: true });
      return;
    }
    if (directVisit || location.href !== originUrl || root?.dataset.flowStep === "placed") location.assign(root?.dataset.flowCloseUrl || originUrl);
  });
  mobile.addEventListener("change", () => mount({ open: mobile.matches && Boolean(root) }));
  app.cartPanel = { getRoot: () => root, adopt, dependencies, loadCart, mount };
  if (root) mount({ open: mobile.matches });
})();
