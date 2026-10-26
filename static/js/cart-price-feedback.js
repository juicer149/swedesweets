/* Paint server-confirmed prices only. No parsing of formatted money and no
   optimistic totals; fragment replacement can carry the same brief feedback. */
(() => {
  "use strict";
  const reduced = matchMedia("(prefers-reduced-motion: reduce)");
  const animations = new WeakMap();
  let pending = null;
  function pulse(element, record, delta = null) {
    if (record.seen.has(element)) return;
    record.seen.add(element);
    animations.get(element)?.cancel();
    const color = getComputedStyle(document.documentElement).getPropertyValue(record.direction > 0 ? "--cart-price-up" : "--cart-price-down").trim();
    const ink = getComputedStyle(element).color;
    const frames = reduced.matches
      ? [{ color: ink }, { color, offset: .25 }, { color: ink }]
      : [{ color: ink, transform: "translateY(0) scale(1)" }, { color, transform: `translateY(${record.direction > 0 ? -2 : 2}px) scale(1.06)`, offset: .25 }, { color: ink, transform: "translateY(0) scale(1)" }];
    const motion = element.animate(frames, { duration: 650, easing: "ease-out" });
    animations.set(element, motion);
    const done = () => { if (animations.get(element) === motion) animations.delete(element); };
    motion.finished.then(done, done);
    if (!delta) return;
    let parent = element.parentElement;
    if (!parent.classList.contains("cart-price-host")) {
      const wrapper = document.createElement("span");
      wrapper.className = "cart-price-host";
      element.before(wrapper);
      wrapper.append(element);
      parent = wrapper;
    }
    parent.querySelector(".cart-price-delta")?.remove();
    const notice = document.createElement("span");
    notice.className = "cart-price-delta";
    notice.setAttribute("aria-hidden", "true");
    notice.textContent = delta;
    notice.style.color = color;
    element.classList.add("cart-price-value");
    element.after(notice);
    parent.classList.add("cart-price-host");
    const fade = notice.animate([{ opacity: 0 }, { opacity: 1, offset: .15 }, { opacity: 1, offset: .5 }, { opacity: 0 }], { duration: 1000, easing: "ease-out" });
    fade.finished.then(() => notice.remove(), () => notice.remove());
  }
  function apply(record, refreshed = false) {
    if (!record || performance.now() > record.until) return;
    const { payload, lineId } = record;
    if (Number.isInteger(Number(lineId)) && payload.line_total_label != null) {
      for (const line of document.querySelectorAll(`[data-cart-line-total="${Number(lineId)}"]`)) {
        if (refreshed && line.textContent.trim() !== payload.line_total_label) continue;
        if (!refreshed) line.textContent = payload.line_total_label;
        pulse(line, record);
      }
    }
    if (payload.subtotal_label != null) {
      for (const total of document.querySelectorAll("[data-cart-subtotal]")) {
        if (refreshed && total.textContent.trim() !== payload.subtotal_label) continue;
        if (!refreshed) total.textContent = payload.subtotal_label;
        const inUpperMobileSummary = matchMedia("(max-width: 767px)").matches && total.closest(".lines-total");
        pulse(total, record, inUpperMobileSummary ? null : payload.subtotal_delta_label);
      }
    }
  }
  document.addEventListener("cart-changed", event => {
    const { payload, lineId } = event.detail || {};
    if (!payload?.ok || ![-1, 1].includes(payload.change_direction)) return;
    pending = { payload, lineId, direction: payload.change_direction, until: performance.now() + 1000, seen: new WeakSet() };
    apply(pending);
  });
  document.addEventListener("navbar-cart-refreshed", () => apply(pending, true));
})();
