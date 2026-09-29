(() => {
  const subtotal = document.querySelector(
    "[data-cart-subtotal]"
  );

  document.addEventListener(
    "cart-changed",
    (event) => {
      const detail = event.detail || {};

      if (
        detail.source !== "current-order"
        || !detail.payload
      ) {
        return;
      }

      const {
        payload,
        lineId,
      } = detail;

      if (
        subtotal
        && payload.subtotal_label
      ) {
        subtotal.textContent = payload.subtotal_label;
      }

      if (
        lineId != null
        && payload.line_total_label
      ) {
        const lineTotal = document.querySelector(
          `[data-cart-line-total="${lineId}"]`
        );

        if (lineTotal) {
          lineTotal.textContent = payload.line_total_label;
        }
      }
    }
  );
})();
