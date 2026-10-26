/* A persistent position marker for overflowing navbar panels, including mobile
   browsers whose native scrollbars fade away. Native scrolling stays intact. */
(() => {
  "use strict";
  const records = new Map();

  function initialize() {
    for (const [scroll, record] of records) {
      if (!scroll.isConnected) {
        record.resize.disconnect();
        record.mutations.disconnect();
        records.delete(scroll);
      }
    }
    for (const scroll of document.querySelectorAll("[data-menu-panel-scroll]")) {
      if (records.has(scroll)) continue;
      const panel = scroll.closest(".mobile-menu-panel");
      const track = document.createElement("span");
      track.className = "menu-scroll-track";
      track.hidden = true;
      track.setAttribute("aria-hidden", "true");
      const thumb = document.createElement("span");
      thumb.className = "menu-scroll-thumb";
      track.append(thumb);
      panel.append(track);
      scroll.classList.add("menu-scroll-ready");

      function update() {
        // The desktop cart's transparent overhang stops above its sticky footer.
        const footer = scroll.querySelector(":scope > .site-nav-cart__actions");
        scroll.style.setProperty("--cart-actions-height", `${footer?.offsetHeight || 0}px`);
        const overflow = scroll.scrollHeight - scroll.clientHeight;
        const scrolls = ["auto", "scroll"].includes(getComputedStyle(scroll).overflowY);
        track.hidden = !scrolls || scroll.clientHeight === 0 || overflow <= 1;
        // More below the fold: the cart's summary row then marks its edge.
        scroll.toggleAttribute("data-more-below", !track.hidden && scroll.scrollTop < overflow - 1);
        if (track.hidden) return;
        const height = track.clientHeight;
        const size = Math.min(height, Math.max(24, height * scroll.clientHeight / scroll.scrollHeight));
        const position = Math.max(0, Math.min(1, scroll.scrollTop / overflow));
        thumb.style.height = `${size}px`;
        thumb.style.transform = `translateY(${position * (height - size)}px)`;
      }
      const resize = new ResizeObserver(update);
      resize.observe(scroll);
      resize.observe(panel);
      function watchContents() {
        resize.disconnect();
        resize.observe(scroll);
        resize.observe(panel);
        for (const child of scroll.children) resize.observe(child);
        update();
      }
      const mutations = new MutationObserver(watchContents);
      mutations.observe(scroll, { childList: true });
      scroll.addEventListener("scroll", update, { passive: true });
      records.set(scroll, { resize, mutations, update });
      watchContents();
    }
    for (const record of records.values()) record.update();
  }

  document.addEventListener("navbar-cart-refreshed", initialize);
  document.addEventListener("toggle", event => {
    if (event.target.matches?.("details[data-mobile-menu]")) initialize();
  }, true);
  window.addEventListener("resize", initialize);
  initialize();
})();
