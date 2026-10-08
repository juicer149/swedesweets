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
