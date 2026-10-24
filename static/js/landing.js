/*
  The start page's menu (storefront/landing.html), played like a game's.

  The crown marks the chosen link, the first one to begin with. Pointing
  at a link, or focusing it (Tab, or the arrow keys), makes it the chosen
  one, and it stays chosen when the pointer moves on: the crown stays
  where it was last put, as a game's cursor does.

  ↓ and ↑ move from link to link (round from the last to the first), Home
  and End jump to the ends, Enter opens the link as usual. Before anything
  has focus the first press takes the crown where it stands. Tab still
  walks the page as everywhere.
*/
(() => {
  "use strict";

  const menu = document.querySelector("[data-landing-menu]");

  if (!menu) {
    return;
  }

  const links = Array.from(menu.querySelectorAll("a"));

  if (links.length === 0) {
    return;
  }

  const CHOSEN = "landing-menu__link--chosen";
  const KEYS = new Set(["ArrowDown", "ArrowUp", "Home", "End"]);

  menu.dataset.landingLive = "";

  function choose(link) {
    for (const other of links) {
      other.classList.toggle(CHOSEN, other === link);
    }
  }

  function chosenIndex() {
    return links.findIndex((link) => link.classList.contains(CHOSEN));
  }

  for (const link of links) {
    link.addEventListener("pointerenter", () => choose(link));
    link.addEventListener("focus", () => choose(link));
  }

  menu.addEventListener("pointerleave", () => {
    if (links.includes(document.activeElement)) choose(document.activeElement);
  });

  function next(index, key) {
    const last = links.length - 1;

    if (key === "Home") {
      return 0;
    }

    if (key === "End") {
      return last;
    }

    if (key === "ArrowDown") {
      return index === last ? 0 : index + 1;
    }

    return index === 0 ? last : index - 1;
  }

  document.addEventListener("keydown", (event) => {
    if (!KEYS.has(event.key) || event.altKey || event.ctrlKey || event.metaKey) {
      return;
    }

    const active = document.activeElement;
    const inMenu = links.includes(active);
    const onPage = !active || active === document.body;

    // Only from the menu, or before anything else has the focus (the
    // language buttons and the login keep their own keys).
    if (!inMenu && !onPage) {
      return;
    }

    event.preventDefault();

    // The first arrow, before the menu has the focus, takes the crown
    // where it stands.
    const index = Math.max(chosenIndex(), 0);
    const arrowIntoMenu = !inMenu && event.key.startsWith("Arrow");
    links[arrowIntoMenu ? index : next(index, event.key)].focus();
  });
})();

/* A small, bounded easter egg: native button activation works with pointer,
   touch, Enter and Space. Repeated clicks add rain, never unbounded nodes. */
(() => {
  const trigger = document.querySelector("[data-candy-images]");
  if (!trigger) return;
  const images = trigger.dataset.candyImages.split("|");
  const reduced = matchMedia("(prefers-reduced-motion: reduce)");
  const rain = document.createElement("div");
  rain.className = "landing__rain";
  rain.setAttribute("aria-hidden", "true");
  document.querySelector(".landing").append(rain);
  const active = new Set();
  const logo = trigger.closest(".landing__logo");
  let hop = null;
  function nudgeCloud() {
    if (reduced.matches || document.documentElement.dataset.theme !== "light") return;
    // Margin moves only the cloud pseudo-element; its CSS transform keeps
    // breathing underneath, and the wordmark never moves. Restart from the
    // current height so repeated clicks do not snap it back to the baseline.
    const current = getComputedStyle(logo, "::before").marginTop;
    hop?.cancel();
    const motion = logo.animate([
      { marginTop: current },
      { marginTop: "calc(-1 * var(--landing-cloud-hop-height))", offset: 0.32 },
      { marginTop: "2px", offset: 0.72 },
      { marginTop: "0px" },
    ], { duration: 360, easing: "ease-out", pseudoElement: "::before" });
    hop = motion;
    const done = () => { if (hop === motion) hop = null; };
    motion.finished.then(done, done);
  }
  const clear = () => {
    hop?.cancel();
    hop = null;
    for (const motion of active) motion.cancel();
    active.clear();
    rain.replaceChildren();
  };
  function syncTheme() {
    trigger.disabled = document.documentElement.dataset.theme !== "light";
    if (trigger.disabled) clear();
  }
  new MutationObserver(syncTheme).observe(document.documentElement, {
    attributes: true, attributeFilter: ["data-theme"],
  });
  syncTheme();
  trigger.addEventListener("click", () => {
    if (trigger.disabled || document.documentElement.dataset.theme !== "light") return;
    nudgeCloud();
    const box = trigger.getBoundingClientRect();
    const calm = reduced.matches;
    const count = Math.min(calm ? 3 : 7, 48 - active.size);
    for (let i = 0; i < count; i++) {
      const sweet = document.createElement("img");
      sweet.className = "landing__sweet";
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
  });
  reduced.addEventListener("change", clear);
  window.addEventListener("pagehide", clear);
})();
