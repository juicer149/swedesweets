/* A cart URL has one editor: a normal page on desktop and the same DOM inside
   the mobile sheet. Moving it keeps form values, quick-add and mutation handlers. */
(() => {
  "use strict";
  const mobile = matchMedia("(max-width: 767px)");
  const editor = document.querySelector("[data-responsive-cart-page]");
  const landing = document.querySelector(".landing__cart-mobile");
  if (!editor && !landing) return;
  const slot = document.createComment("desktop cart editor");
  if (editor) editor.before(slot);
  let hosted = false;
  let quickContents = null;
  let quickScroll = null;
  let focused = null;
  let scrollTop = 0;
  let desktopScroll = 0;
  const cartMenu = () => document.querySelector('details[data-mobile-menu="cart"]');
  const openCart = () => document.dispatchEvent(new CustomEvent("mobile-menu-request", { detail: { key: "cart" } }));

  function preserveFocus() {
    if (editor?.contains(document.activeElement)) focused = document.activeElement;
    if (hosted) scrollTop = quickScroll?.scrollTop || 0;
  }

  function syncEditor({ open = false } = {}) {
    if (!editor) return;
    const cart = cartMenu();
    const scroll = cart?.querySelector("[data-cart-panel-scroll]");
    if (!cart || !scroll) return;
    preserveFocus();
    if (mobile.matches) {
      const shouldOpen = open || !hosted;
      if (!hosted) desktopScroll = window.scrollY;
      if (editor.parentElement !== scroll) {
        // New fragments refresh the quick preview; retain the live editor.
        quickContents = document.createDocumentFragment();
        quickContents.append(...scroll.childNodes);
        quickScroll = scroll;
        scroll.append(editor);
        scroll.scrollTop = scrollTop;
      }
      hosted = true;
      focused?.focus({ preventScroll: true });
      if (shouldOpen && !document.querySelector('details[data-mobile-menu][open]')) openCart();
    } else if (hosted) {
      slot.after(editor);
      if (quickContents) scroll.replaceChildren(quickContents);
      hosted = false;
      cart.open = false;
      focused?.focus({ preventScroll: true });
      window.scrollTo(0, desktopScroll);
      document.dispatchEvent(new CustomEvent("navbar-cart-refreshed", { detail: { layoutOnly: true } }));
    }
  }

  document.addEventListener("navbar-cart-replacing", preserveFocus);
  document.addEventListener("navbar-cart-refreshed", event => {
    if (!event.detail?.layoutOnly) syncEditor();
    const count = landing?.querySelectorAll("[data-navbar-cart-line]").length;
    const badge = document.querySelector(".landing__cart-count");
    if (badge && count !== undefined) badge.textContent = String(count);
  });
  document.addEventListener("mobile-menu-settled", event => {
    if (hosted && mobile.matches && !event.detail.key) {
      // A directly visited cart URL has no other mobile cart page to uncover.
      window.location.assign(editor.dataset.cartReturnUrl || "/");
    }
  });
  mobile.addEventListener("change", () => {
    if (landing && !mobile.matches) {
      const cart = cartMenu();
      if (cart) cart.open = false;
    }
    syncEditor();
  });
  window.addEventListener("pageshow", () => syncEditor({ open: true }));
  syncEditor();
})();
