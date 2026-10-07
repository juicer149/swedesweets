/*
  The start page's menu (storefront/landing.html), played like a game's:
  ↓ and ↑ move the crown from link to link (round from the last to the
  first), Home and End jump to the ends, Enter opens the link as usual.
  Before anything has focus the first press takes the crown where it
  stands (the chosen link). Tab still walks the page as everywhere.
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

  const KEYS = new Set(["ArrowDown", "ArrowUp", "Home", "End"]);

  function next(index, key) {
    const last = links.length - 1;

    if (key === "Home") {
      return 0;
    }

    if (key === "End") {
      return last;
    }

    if (index === -1) {
      // Nothing focused yet: the crown is on the first link.
      return 0;
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
    links[next(links.indexOf(active), event.key)].focus();
  });
})();
