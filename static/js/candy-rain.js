/* Shared day-cloud easter egg: landing's logo and repeated activation of
   the current navbar link. Normal navigation keeps its existing owner. */
(() => {
  "use strict";
  const root = document.documentElement;
  if (root.dataset.siteZone === "ops") return;
  const images = document.currentScript?.dataset.candyRainImages?.split("|").filter(Boolean);
  if (!images?.length) return;
  const reduced = matchMedia("(prefers-reduced-motion: reduce)");
  const rain = document.createElement("div");
  rain.className = "candy-rain";
  rain.setAttribute("aria-hidden", "true");
  const active = new Set();
  const hops = new Map();
  const isDay = () => root.dataset.theme === "light";

  function nudgeCloud(cloud, pseudoElement) {
    if (reduced.matches) return;
    const current = getComputedStyle(cloud, pseudoElement).marginTop;
    hops.get(cloud)?.cancel();
    const motion = cloud.animate([
      { marginTop: current },
      { marginTop: "calc(-1 * var(--landing-cloud-hop-height))", offset: 0.32 },
      { marginTop: "2px", offset: 0.72 },
      { marginTop: "0px" },
    ], { duration: 360, easing: "ease-out", pseudoElement });
    hops.set(cloud, motion);
    const done = () => { if (hops.get(cloud) === motion) hops.delete(cloud); };
    motion.finished.then(done, done);
  }

  function burst(trigger, cloud, pseudoElement) {
    if (!isDay()) return;
    if (!rain.isConnected) document.body.append(rain);
    nudgeCloud(cloud, pseudoElement);
    const box = trigger.getBoundingClientRect();
    const calm = reduced.matches;
    const count = Math.min(calm ? 3 : 7, 48 - active.size);
    for (let i = 0; i < count; i++) {
      const sweet = document.createElement("img");
      sweet.className = "candy-rain__sweet";
      sweet.src = images[Math.floor(Math.random() * images.length)];
      sweet.alt = "";
      const size = 22 + Math.random() * 16;
      sweet.style.setProperty("--sweet-size", `${size}px`);
      sweet.style.left = `${box.left + box.width * (0.1 + Math.random() * 0.8) - size / 2}px`;
      sweet.style.top = `${box.bottom - box.height * 0.2}px`;
      rain.append(sweet);
      const spread = (Math.random() - 0.5) * Math.min(innerWidth, 320);
      const fall = innerHeight - box.bottom + box.height * 0.2 + size;
      const turn = (Math.random() - 0.5) * 540;
      const motion = sweet.animate(calm
        ? [{ opacity: 0 }, { opacity: 1, offset: 0.25 }, { opacity: 0 }]
        : [
          { transform: "translate(0, 0) rotate(0deg) scale(.6)", opacity: 0 },
          { transform: `translate(${spread * 0.2}px, 20px) rotate(${turn * 0.1}deg) scale(1)`, opacity: 1, offset: 0.15 },
          { transform: `translate(${spread}px, ${fall}px) rotate(${turn}deg) scale(1)`, opacity: 0.8 },
        ], { duration: calm ? 600 : 1500 + Math.random() * 1100, easing: "ease-in", fill: "both" });
      active.add(motion);
      const done = () => { active.delete(motion); sweet.remove(); };
      motion.finished.then(done, done);
    }
  }

  function clear() {
    for (const motion of hops.values()) motion.cancel();
    hops.clear();
    for (const motion of active) motion.cancel();
    active.clear();
    rain.replaceChildren();
    rain.remove();
  }

  document.addEventListener("click", event => {
    if (!isDay() || event.defaultPrevented || event.button !== 0
      || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    const logo = event.target.closest(".landing__logo-trigger");
    if (logo) {
      burst(logo, logo.closest(".landing__logo"), "::before");
      return;
    }
    const link = event.target.closest('.site-header .site-nav__link[aria-current="page"][href]');
    if (!link || link.download || (link.target && link.target !== "_self")
      || link.matches(".is-nav-arriving, .is-nav-leaving")
      || window.SwedeSweets?.publicNavigation?.busy()
      || root.classList.contains("catalog--detail-open")
      || document.querySelector('details[data-mobile-menu][open], dialog[open], [data-public-page] [data-state="adding"]')) return;
    const url = new URL(link.href, location.href);
    if (url.origin !== location.origin || url.pathname !== location.pathname || url.hash
      || (url.search && url.search !== location.search)) return;
    event.preventDefault();
    burst(link, link, "::after");
  });
  reduced.addEventListener("change", clear);
  window.addEventListener("pagehide", clear);
  document.addEventListener("public-page-ready", clear);
  new MutationObserver(() => { if (!isDay()) clear(); }).observe(root, {
    attributes: true, attributeFilter: ["data-theme"],
  });
})();
