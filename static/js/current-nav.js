/* Keep the phone's current destination inside the sticky header, rather than
   fixed to a second viewport from inside the bottom navigation. */
(() => {
  "use strict";
  const header = document.querySelector(".site-header");
  if (!header || document.documentElement.dataset.siteZone === "ops") return;
  const mobile = matchMedia("(max-width: 767px)");
  const slots = new Map();
  for (const [index, link] of [...header.querySelectorAll(".site-nav__links .site-nav__link")].entries()) {
    link.dataset.navIndex = index;
    const slot = document.createComment("navigation slot");
    link.before(slot); slots.set(link, slot);
  }
  const host = document.createElement("div"); host.className = "site-nav-current"; header.querySelector(".site-nav").append(host);
  function sync() {
    const active = mobile.matches && !document.documentElement.hasAttribute("data-checkout-flow")
      ? [...slots.keys()].find(link => link.getAttribute("aria-current") === "page") : null;
    for (const [link, slot] of slots) {
      if (link === active) { if (link.parentElement !== host) host.append(link); }
      else if (link.parentElement === host) slot.after(link);
    }
  }
  mobile.addEventListener("change", sync);
  document.addEventListener("navigation-current-changed", sync);
  document.addEventListener("order-flow-chrome", sync);
  window.addEventListener("pageshow", sync);
  window.SwedeSweetsCurrentNav = { sync };
  sync();
})();
