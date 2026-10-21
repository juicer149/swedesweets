/* Animate verified server-rendered steps. POSTs are never retried automatically;
   hosted payment uses a normal browser submission rather than cross-origin fetch. */
(() => {
  "use strict";
  const app = window.SwedeSweets = window.SwedeSweets || {};
  const reduced = matchMedia("(prefers-reduced-motion: reduce)");
  const stages = ["cart", "review", "placed"];
  let busy = false;
  const current = () => app.cartPanel?.getRoot() || document.querySelector("[data-order-flow-page]");
  function prepare(root) {
    if (!root) return null;
    root.classList.add("order-flow-page");
    const surface = root.querySelector(".page");
    const progress = surface?.querySelector("[data-order-progress]");
    if (!surface || !progress) return null;
    surface.classList.add("order-flow-surface");
    if (!surface.querySelector(":scope > .order-flow-content")) {
      const content = document.createElement("div"); content.className = "order-flow-content";
      for (const node of [...surface.childNodes]) if (node !== progress) content.append(node);
      surface.append(content);
    }
    const content = surface.querySelector(":scope > .order-flow-content");
    const messages = root.previousElementSibling;
    if (messages?.matches(".messages")) content.prepend(messages);
    // Editors initialize against the replaceable content, not the persistent
    // journey shell. Returning to cart gets fresh handlers for its new rows.
    for (const name of ["data-current-order", "data-current-order-error-message"]) {
      if (root.hasAttribute(name)) { content.setAttribute(name, root.getAttribute(name)); root.removeAttribute(name); }
    }
    return { surface, progress, content };
  }
  function loading(root) {
    const parts = prepare(root);
    if (!parts) return null;
    root.classList.add("is-loading"); root.setAttribute("aria-busy", "true");
    parts.content.hidden = true; parts.content.inert = true;
    const loader = document.createElement("div"); loader.className = "order-flow-loader";
    loader.setAttribute("role", "status"); loader.setAttribute("aria-live", "polite");
    const label = document.createElement("span"); label.className = "visually-hidden";
    label.textContent = parts.progress.dataset.flowLoading;
    const spinner = document.createElement("div"); spinner.className = "order-flow-spinner";
    loader.append(label, spinner); parts.surface.append(loader);
    document.documentElement.classList.add("order-flow-busy");
    const scroll = root.closest("[data-cart-panel-scroll]");
    if (scroll) scroll.scrollTop = 0;
    else window.scrollTo({ top: Math.max(0, root.getBoundingClientRect().top + scrollY - 70), behavior: "instant" });
    return { ...parts, loader, spinner };
  }
  function reset(root) {
    if (!root) return;
    root.classList.remove("is-loading"); root.removeAttribute("aria-busy");
    root.querySelectorAll(".order-flow-loader").forEach(e => e.remove());
    const content = root.querySelector(".order-flow-content");
    if (content) { content.hidden = false; content.inert = false; }
    document.documentElement.classList.remove("order-flow-busy");
  }
  async function advance(progress, step) {
    const items = [...progress.querySelectorAll(".order-progress__step")];
    const to = stages.indexOf(step), from = stages.indexOf(progress.dataset.orderProgress);
    progress.classList.remove("is-complete");
    if (to > from) for (let index = from + 1; index <= to; index++) {
      const travel = document.createElement("span"); travel.className = "order-progress__travel";
      travel.setAttribute("aria-hidden", "true"); items[index].append(travel);
      if (!reduced.matches) await travel.animate([{ transform: "scaleX(0)" }, { transform: "scaleX(1)" }], { duration: 450, easing: "ease-in-out", fill: "forwards" }).finished;
      items[index].classList.add("is-lit");
      items[index - 1]?.removeAttribute("aria-current");
      items[index].setAttribute("aria-current", "step");
      travel.remove();
      if (!reduced.matches) await items[index].querySelector(".order-progress__dot").animate([{ filter: "brightness(1)" }, { filter: "brightness(2.2)" }, { filter: "brightness(1)" }], { duration: 280 }).finished;
    }
    if (to < from) for (let index = from; index > to; index--) {
      const travel = document.createElement("span"); travel.className = "order-progress__travel";
      travel.setAttribute("aria-hidden", "true"); items[index].append(travel);
      items[index].classList.remove("is-lit"); items[index].removeAttribute("aria-current");
      if (!reduced.matches) await travel.animate([{ transform: "scaleX(1)" }, { transform: "scaleX(0)" }], { duration: 450, easing: "ease-in-out", fill: "forwards" }).finished;
      travel.remove();
    }
    items.forEach((item, index) => {
      item.classList.toggle("is-lit", index <= to);
      if (index === to) item.setAttribute("aria-current", "step"); else item.removeAttribute("aria-current");
    });
    progress.dataset.orderProgress = step;
    if (step === "placed") {
      progress.classList.add("is-complete");
      // The last point first arrives in gold, then the whole journey confirms
      // success in green. Keep that verified state on reload as well.
      if (!reduced.matches) await progress.querySelector(".order-progress__steps").animate([
        { filter: "brightness(1)" }, { filter: "brightness(1.65)", offset: 0.45 }, { filter: "brightness(1)" },
      ], { duration: 460, easing: "ease-out" }).finished;
    }
  }
  function chrome(page) {
    const source = page.querySelector('details[data-mobile-menu="cart"]');
    const cart = document.querySelector('details[data-mobile-menu="cart"]');
    if (source && cart) {
      cart.dataset.cartLocked = source.dataset.cartLocked;
      const target = cart.querySelector("summary"), original = source.querySelector("summary");
      for (const attr of ["aria-current", "aria-disabled", "tabindex", "inert"]) {
        if (original.hasAttribute(attr)) target.setAttribute(attr, original.getAttribute(attr)); else target.removeAttribute(attr);
      }
    }
    if (source?.querySelector('summary[aria-current="page"]')) {
      for (const link of document.querySelectorAll('.site-nav__link[aria-current], .site-menu > summary[aria-current]')) {
        link.removeAttribute("aria-current"); link.classList.remove("site-nav__link--active");
      }
    }
    document.title = page.title;
  }
  async function render(envelope, parts, { push = true } = {}) {
    const { page, next, url } = envelope;
    const imported = document.importNode(next, true);
    const nextParts = prepare(imported);
    const messages = page.querySelector(".messages");
    if (messages && !next.contains(messages)) nextParts.content.prepend(document.importNode(messages, true));
    parts.progress.removeAttribute("inert");
    if (push && location.href !== url) history.pushState({ orderFlow: true }, "", url);
    chrome(page);
    nextParts.content.hidden = true;
    const mounted = await app.cartPanel.adopt(imported, page, url, { preserveSurface: true });
    parts.loader.remove();
    nextParts.content.hidden = false;
    nextParts.content.inert = false;
    if (!reduced.matches) await nextParts.content.animate([{ clipPath: "inset(0 0 100% 0)", opacity: 0 }, { clipPath: "inset(0)", opacity: 1 }], { duration: 350, easing: "ease-out" }).finished;
    mounted.querySelector("h1")?.setAttribute("tabindex", "-1");
    mounted.querySelector("h1")?.focus({ preventScroll: true });
    void app.navbarCart?.refresh({ preserveOpenState: true });
  }
  async function transition(url, options = {}, historyOptions = {}) {
    if (busy || !current()) return;
    const root = current(), parts = loading(root);
    if (!parts) return;
    busy = true;
    let envelope = null;
    try {
      const request = async () => {
        const response = await fetch(url, { credentials: "same-origin", ...options });
        const page = new DOMParser().parseFromString(await response.text(), "text/html");
        const next = page.querySelector("[data-order-flow-page]");
        if (!next) { location.assign(response.url); throw new Error("Different destination"); }
        envelope = { page, next, url: response.url };
        if (!response.ok || next.querySelector(".form-field--error") || page.querySelector(".message--error")) throw new Error("Server validation");
        return envelope;
      };
      const outcome = window.statusBurst ? await window.statusBurst.run(parts.spinner, "default", request) : await request().then(value => ({ ok: true, value })).catch(error => ({ ok: false, error }));
      if (envelope) {
        if (outcome.ok || stages.indexOf(envelope.next.dataset.flowStep) <= stages.indexOf(parts.progress.dataset.orderProgress)) await advance(parts.progress, envelope.next.dataset.flowStep);
        await render(envelope, parts, historyOptions);
      } else {
        reset(root);
        const message = document.createElement("p"); message.className = "message message--error"; message.setAttribute("role", "alert");
        message.textContent = parts.progress.dataset.flowError;
        const reload = document.createElement("a"); reload.className = "quiet-link"; reload.href = location.href; reload.textContent = parts.progress.dataset.flowReload;
        prepare(root).content.prepend(message, reload);
      }
    } catch (error) {
      // A response may already have committed the order: recover with GET only.
      reset(current());
      const content = prepare(current())?.content;
      if (content) {
        const message = document.createElement("p"); message.className = "message message--error";
        message.setAttribute("role", "alert"); message.textContent = parts.progress.dataset.flowError;
        const reload = document.createElement("a"); reload.className = "quiet-link";
        reload.href = location.href; reload.textContent = parts.progress.dataset.flowReload;
        content.prepend(message, reload);
      }
    } finally {
      busy = false; document.documentElement.classList.remove("order-flow-busy");
    }
  }
  document.addEventListener("submit", event => {
    const form = event.target, root = current();
    if (!form.matches?.("[data-order-flow-submit]") || !root?.contains(form)) return;
    event.preventDefault(); event.stopImmediatePropagation();
    if (busy) return;
    form.dispatchEvent(new Event("checkout-validate"));
    if (!form.reportValidity() || form.querySelector("[data-checkout-continue]")?.disabled) return;
    const button = event.submitter;
    if (form.hasAttribute("data-order-flow-external")) {
      // A real browser navigation preserves the provider redirect and all
      // existing payment recovery rules. Never fetch/retry this POST.
      try { sessionStorage.setItem("order-flow-arrival", root.dataset.flowStep); } catch {}
      busy = true;
      const parts = loading(root), burst = window.statusBurst?.create("default", parts?.spinner);
      if (burst) parts.spinner.append(burst);
      if (button?.name) { const carried = document.createElement("input"); carried.type = "hidden"; carried.name = button.name; carried.value = button.value; form.append(carried); }
      HTMLFormElement.prototype.submit.call(form);
      return;
    }
    const data = new FormData(form);
    if (button?.name) data.append(button.name, button.value);
    void transition(form.action, { method: "POST", body: data });
  }, true);
  document.addEventListener("click", event => {
    const link = event.target.closest("[data-order-flow-back]");
    if (!link || !current()?.contains(link) || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    event.preventDefault(); event.stopImmediatePropagation(); void transition(link.href);
  }, true);
  window.addEventListener("popstate", () => { if (current()) { if (busy) location.reload(); else void transition(location.href, {}, { push: false }); } });
  window.addEventListener("pageshow", event => { if (event.persisted) { busy = false; reset(current()); } });
  document.addEventListener("order-flow-ready", () => prepare(current()));
  app.orderFlow = { visit: url => transition(url), busy: () => busy, prepare };
  const initial = prepare(current());
  if (initial) {
    // Page navigation has no sliding sheet; light its timeline after first paint.
    if (!reduced.matches && !current().closest(".mobile-menu-panel")) {
      const arriving = current(); arriving.classList.add("is-arriving");
      requestAnimationFrame(() => requestAnimationFrame(() => arriving.classList.remove("is-arriving")));
    }
    let arrival = null;
    try { arrival = sessionStorage.getItem("order-flow-arrival"); sessionStorage.removeItem("order-flow-arrival"); } catch {}
    if (arrival && stages.indexOf(current().dataset.flowStep) > stages.indexOf(arrival)) {
      const step = current().dataset.flowStep;
      initial.progress.dataset.orderProgress = arrival;
      const items = initial.progress.querySelectorAll(".order-progress__step");
      items.forEach((item, i) => item.classList.toggle("is-lit", i <= stages.indexOf(arrival)));
      initial.content.hidden = true;
      void advance(initial.progress, step).then(async () => {
        initial.content.hidden = false;
        if (!reduced.matches) await initial.content.animate([{ clipPath: "inset(0 0 100% 0)" }, { clipPath: "inset(0)" }], { duration: 350 }).finished;
      });
    }
  }
})();
