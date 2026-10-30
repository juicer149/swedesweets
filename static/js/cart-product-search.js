/* Keep the native form/select inside its cart owner. Only its presentation
   enters the dialog's top layer; the cart and its scroll position stay put. */
(() => {
  "use strict";
  const initialized = new WeakSet();
  const reduced = matchMedia("(prefers-reduced-motion: reduce)");
  let active = null, last = null, sequence = 0;
  function size(entry) {
    entry.width = innerWidth;
    entry.dialog.style.setProperty("--search-viewport-height", `${innerHeight}px`);
  }
  function fitList(entry = active) {
    if (!entry?.dialog.open) return;
    const viewport = window.visualViewport;
    const bottom = viewport ? viewport.offsetTop + viewport.height : innerHeight;
    const top = entry.content.getBoundingClientRect().top;
    entry.content.style.maxHeight = `${Math.max(96, bottom - top - 24)}px`;
  }
  function open(entry, push = true) {
    if (active || !entry.dialog.isConnected) return;
    active = last = entry;
    entry.closing = entry.dismissing = false;
    entry.error.hidden = true;
    entry.note.hidden = true;
    size(entry);
    entry.dialog.showModal();
    document.documentElement.classList.add("cart-search-open");
    if (push) history.pushState({ ...(history.state || {}), cartSearch: entry.id }, "", location.href);
    entry.motion?.cancel();
    if (!reduced.matches) entry.motion = entry.surface.animate([
      { opacity: 0, transform: "scale(.96)" }, { opacity: 1, transform: "none" },
    ], { duration: 180, easing: "cubic-bezier(.22,.7,.2,1)" });
    // The complete list is visible without activating a search field or keyboard.
    entry.add.focus({ preventScroll: true });
    if (entry.add.disabled) entry.dialog.querySelector("[data-cart-search-close]").focus({ preventScroll: true });
    fitList(entry);
  }
  async function finishClose(entry) {
    if (!entry || entry.closing) return;
    entry.closing = true;
    entry.motion?.cancel();
    if (!reduced.matches && entry.dialog.isConnected) {
      entry.motion = entry.surface.animate([
        { opacity: 1, transform: "none" }, { opacity: 0, transform: "scale(.96)" },
      ], { duration: 140, easing: "ease-out" });
      await entry.motion.finished.catch(() => {});
    }
    entry.select.tomselect?.close();
    entry.select.tomselect?.blur();
    entry.dialog.close();
    entry.motion?.cancel();
    if (active === entry) active = null;
    if (!active) document.documentElement.classList.remove("cart-search-open");
    if (!active && entry.button.isConnected) entry.button.focus({ preventScroll: true });
    // A quick Forward during the close animation may already point back at
    // this search entry. Finish its visual close, then restore that state.
    if (!active && history.state?.cartSearch === entry.id && entry.dialog.isConnected) open(entry, false);
  }
  function close() {
    if (!active || active.closing || active.dismissing) return;
    active.dismissing = true;
    if (history.state?.cartSearch === active.id) history.back();
    else void finishClose(active);
  }
  function init() {
    for (const form of document.querySelectorAll("[data-cart-quick-add]")) {
      if (initialized.has(form)) continue;
      const select = form.querySelector("select"), dialog = form.querySelector("[data-cart-product-search]");
      if (!select?.tomselect || !dialog?.showModal) continue;
      initialized.add(form);
      dialog.dataset.enhanced = "true";
      const button = form.querySelector("[data-cart-search-open]");
      const title = dialog.querySelector("[data-cart-search-title]");
      title.id = `cart-product-search-${++sequence}`;
      dialog.setAttribute("aria-labelledby", title.id);
      const entry = {
        id: title.id, dialog, select, button, surface: dialog.firstElementChild,
        error: dialog.querySelector("[data-cart-search-error]"),
        content: dialog.querySelector("[data-cart-search-content]"),
        note: form.querySelector("[data-cart-search-note]"),
      };
      entry.filter = dialog.querySelector("[data-cart-search-filter]");
      entry.list = dialog.querySelector("[data-cart-search-list]");
      entry.add = dialog.querySelector("[data-cart-search-add]");
      entry.count = dialog.querySelector("[data-cart-search-count]");
      entry.filter.id = `${title.id}-filter`;
      dialog.querySelector("[data-cart-search-label]").htmlFor = entry.filter.id;
      entry.selected = new Set();
      entry.rows = [];
      const normalize = value => value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase();
      const update = () => {
        entry.add.disabled = entry.selected.size === 0 || Boolean(form.dataset.submitting);
        entry.count.textContent = entry.selected.size ? String(entry.selected.size) : "";
        entry.content.inert = Boolean(form.dataset.submitting);
        entry.filter.disabled = Boolean(form.dataset.submitting);
      };
      for (const option of select.options) {
        if (!option.value) continue;
        const row = document.createElement("label");
        row.className = "cart-product-search__row";
        const check = document.createElement("input");
        check.type = "checkbox"; check.value = option.value; check.disabled = option.disabled;
        const rendered = select.tomselect.render("option", select.tomselect.options[option.value]);
        row.append(check, rendered); entry.list.append(row);
        entry.rows.push({ row, search: normalize(option.getAttribute("search") || option.textContent) });
        check.addEventListener("change", () => {
          if (check.checked) entry.selected.add(check.value); else entry.selected.delete(check.value);
          update();
        });
      }
      const filter = () => {
        const terms = normalize(entry.filter.value).trim().split(/\s+/).filter(Boolean);
        for (const item of entry.rows) item.row.hidden = !terms.every(term => item.search.includes(term));
        dialog.querySelector("[data-cart-search-empty]").hidden = entry.rows.some(item => !item.row.hidden);
        entry.content.scrollTop = 0;
      };
      entry.filter.addEventListener("input", filter);
      entry.filter.addEventListener("keydown", event => { if (event.key === "Enter") event.preventDefault(); });
      entry.add.addEventListener("click", () => {
        if (form.dataset.submitting || !entry.selected.size) return;
        form.dispatchEvent(new CustomEvent("cart-search-submit", { bubbles: true, detail: { ids: [...entry.selected] } }));
        update();
      });
      // Hide, but retain the native form owner and its non-dialog fallback.
      select.tomselect.wrapper.hidden = true;
      dialog.append(select, select.tomselect.wrapper);
      button.hidden = false;
      button.addEventListener("click", () => open(entry));
      dialog.querySelector("[data-cart-search-close]").addEventListener("click", close);
      dialog.addEventListener("cancel", event => { event.preventDefault(); close(); });
      // The dialog has no padding; a backdrop hit is outside its rectangle.
      dialog.addEventListener("click", event => {
        if (event.target !== dialog) return;
        const box = dialog.getBoundingClientRect();
        if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) close();
      });
      form.addEventListener("cart-search-added", () => {
        entry.selected.clear();
        for (const check of entry.list.querySelectorAll("input")) check.checked = false;
        entry.filter.value = ""; filter(); update();
        if (active === entry) close();
      });
      form.addEventListener("cart-search-error", () => {
        entry.error.hidden = false;
        update();
        if (active !== entry) entry.note.hidden = false;
      });
    }
  }
  document.addEventListener("keydown", event => {
    if (!active || event.key !== "Escape") return;
    event.preventDefault(); event.stopImmediatePropagation(); close();
  }, true);
  window.addEventListener("popstate", event => {
    if (active) {
      event.stopImmediatePropagation();
      void finishClose(active);
    } else if (last?.dialog.isConnected && event.state?.cartSearch === last.id) {
      event.stopImmediatePropagation(); open(last, false);
    }
  }, true);
  window.addEventListener("resize", () => {
    // A keyboard height change must not lift the panel. Rotation may reflow it.
    if (active && innerWidth !== active.width) size(active);
    fitList();
  });
  window.visualViewport?.addEventListener("resize", () => fitList());
  window.visualViewport?.addEventListener("scroll", () => fitList());
  // A cart/review replacement can discard the owning form while a GET/POST
  // finishes. Never leave the document locked by a detached modal.
  new MutationObserver(() => {
    if (active && !active.dialog.isConnected) {
      active.motion?.cancel(); active = null;
      document.documentElement.classList.remove("cart-search-open");
      if (history.state?.cartSearch) {
        const { cartSearch, ...state } = history.state;
        history.replaceState(state, "", location.href);
      }
    }
  }).observe(document.body, { childList: true, subtree: true });
  document.addEventListener("DOMContentLoaded", init);
  document.addEventListener("cart-editor-ready", init);
  init();
})();
