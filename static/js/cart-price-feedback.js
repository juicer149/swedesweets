/* Paint server-confirmed prices only. No parsing of formatted money and no
   optimistic totals; fragment replacement can carry the same brief feedback. */
(() => {
  "use strict";
  const reduced = matchMedia("(prefers-reduced-motion: reduce)");
  const animations = new WeakMap();
  const PULSE_MS = 850;
  const DELTA_MS = 1000;
  let pending = null;
  function pulse(element, record, delta = null) {
    if (record.seen.has(element)) return;
    record.seen.add(element);
    animations.get(element)?.cancel();
    const color = getComputedStyle(document.documentElement).getPropertyValue(record.direction > 0 ? "--cart-price-up" : "--cart-price-down").trim();
    const ink = getComputedStyle(element).color;
    // A refreshed fragment continues the same feedback; it must not hop again.
    const elapsed = performance.now() - record.startedAt;
    if (elapsed < PULSE_MS) {
      const frames = reduced.matches
        ? [{ color }, { color, offset: .4 }, { color: ink }]
        : [
          { color, transform: "translateY(0) scale(1)" },
          { color, transform: `translateY(${record.direction > 0 ? -4 : 4}px) scale(1.12)`, offset: .14 },
          { color, transform: "translateY(0) scale(1)", offset: .34 },
          { color, transform: "translateY(0) scale(1)", offset: .4 },
          { color: ink, transform: "translateY(0) scale(1)" },
        ];
      const motion = element.animate(frames, { duration: PULSE_MS, easing: "ease-out" });
      motion.currentTime = elapsed;
      animations.set(element, motion);
      const done = () => { if (animations.get(element) === motion) animations.delete(element); };
      motion.finished.then(done, done);
    }
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
    const fade = notice.animate([{ opacity: 0 }, { opacity: 1, offset: .15 }, { opacity: 1, offset: .5 }, { opacity: 0 }], { duration: DELTA_MS, easing: "ease-out" });
    fade.currentTime = elapsed;
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
    if (!refreshed && Object.hasOwn(payload, "subtotal_label")) {
      for (const summary of document.querySelectorAll(".cart-summary")) {
        summary.querySelector("[data-cart-summary-money]")?.toggleAttribute("hidden", !payload.subtotal_label);
        summary.querySelector("[data-cart-summary-products]")?.toggleAttribute("hidden", Boolean(payload.subtotal_label));
      }
      for (const total of document.querySelectorAll("[data-business-cart-subtotal]")) {
        total.hidden = !payload.subtotal_label || !total.closest("[data-current-order]")?.querySelector(".cart-line");
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
    const startedAt = performance.now();
    pending = { payload, lineId, direction: payload.change_direction, startedAt, until: startedAt + DELTA_MS, seen: new WeakSet() };
    apply(pending);
  });
  document.addEventListener("navbar-cart-refreshed", () => apply(pending, true));
})();
