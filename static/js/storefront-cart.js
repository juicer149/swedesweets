(() => {

  document.addEventListener(
    "cart-changed",
    (event) => {
      const detail = event.detail || {};

      if (
        !["current-order", "navbar-cart"].includes(detail.source)
        || !detail.payload
      ) {
        return;
      }

      const {
        payload,
        lineId,
      } = detail;

      if (
        payload.subtotal_label
      ) {
        document.querySelectorAll("[data-cart-subtotal]").forEach(subtotal => { subtotal.textContent = payload.subtotal_label; });
      }

      if (
        lineId != null
        && payload.line_total_label
      ) {
        const lineTotals = document.querySelectorAll(
          `[data-cart-line-total="${lineId}"]`
        );

        lineTotals.forEach(lineTotal => { lineTotal.textContent = payload.line_total_label; });
      }
    }
  );
})();
