/* The same form appears on the cart page and inside its mobile sheet.
   Browser validation improves feedback; Django remains authoritative. */
(() => {
  "use strict";
  const initialized = new WeakSet();
  function initialize() {
    document.querySelectorAll("[data-checkout-details-form]").forEach(form => {
      if (initialized.has(form)) return;
      initialized.add(form);
      const email = form.querySelector('[name$="email"]:not([data-confirm-email])');
      const confirm = form.querySelector("[data-confirm-email]");
      const button = form.querySelector("[data-checkout-continue]");
      const help = form.querySelector("[data-checkout-help]");
      if (!email || !confirm || !button) return;
      const status = document.createElement("p");
      status.className = "form-help checkout-email-status";
      status.id = `${confirm.id}-match`;
      status.setAttribute("role", "status");
      confirm.closest(".form-field").append(status);
      confirm.setAttribute("aria-describedby", `${confirm.getAttribute("aria-describedby") || ""} ${status.id}`.trim());
      let touched = false;
      function validate() {
        const mismatch = confirm.value && email.value.trim().toLowerCase() !== confirm.value.trim().toLowerCase();
        confirm.setCustomValidity(mismatch ? confirm.dataset.mismatchMessage : "");
        status.textContent = mismatch && touched ? confirm.dataset.mismatchMessage : "";
        if (mismatch && touched) confirm.setAttribute("aria-invalid", "true");
        else confirm.removeAttribute("aria-invalid");
        const fields = [...form.elements].filter(element => element.required && !element.disabled);
        const complete = fields.every(element => element.value.trim() && element.validity.valid);
        const busy = document.querySelector('[data-update-in-progress="true"], [data-remove-in-progress="true"], [data-removing="true"]');
        const cart = form.closest(".site-nav-cart, .cart-page");
        const quantitiesValid = [...(cart?.querySelectorAll("[data-quantity-input]") || [])].every(input => input.validity.valid);
        // An unfinished form keeps its button pressable (it then shows what
        // is missing); only a cart that is busy or wrong disables it.
        const buttons = [button, ...document.querySelectorAll(`[form="${form.id}"][type="submit"]`)];
        for (const each of buttons) {
          each.disabled = !quantitiesValid || Boolean(busy);
          each.classList.toggle("is-incomplete", !complete);
        }
        form.dataset.checkoutIncomplete = String(!complete);
        if (help) help.textContent = complete ? help.dataset.ready : help.dataset.incomplete;
        if (form.hasAttribute("data-attempted")) mark(fields);
      }
      // After a press on an unfinished form: a yellow dot by each empty
      // field, a red one by each that is filled in but wrong (forms.css).
      function mark(fields) {
        for (const element of fields) {
          const field = element.closest(".form-field");
          if (!field) continue;
          const missing = !element.value.trim();
          field.classList.toggle("form-field--missing", missing);
          field.classList.toggle("form-field--invalid", !missing && !element.validity.valid);
        }
      }
      // Show it, and take the visitor to the first field still to do.
      function reveal() {
        form.setAttribute("data-attempted", "");
        validate();
        const first = [...form.elements].find(element => element.required && !element.disabled
          && !(element.value.trim() && element.validity.valid));
        if (!first) return;
        first.scrollIntoView({ block: "center", behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
        first.focus({ preventScroll: true });
      }
      form.addEventListener("checkout-reveal", reveal);
      form.addEventListener("input", validate);
      form.addEventListener("change", validate);
      confirm.addEventListener("blur", () => { touched = true; validate(); });
      for (const type of ["paste", "drop"]) confirm.addEventListener(type, event => event.preventDefault());
      form.addEventListener("submit", event => {
        validate();
        if (button.disabled) { event.preventDefault(); return; }
        if (form.dataset.checkoutIncomplete === "true") { event.preventDefault(); reveal(); return; }
        if (!form.reportValidity()) event.preventDefault();
      });
      form.addEventListener("checkout-validate", validate);
      validate();
      const invalid = form.querySelector('.form-field--error input, .form-field--error select, .form-field--error textarea');
      if (invalid && form.offsetParent !== null) requestAnimationFrame(() => invalid.focus());
    });
  }
  document.addEventListener("navbar-cart-refreshed", initialize);
  function revalidate() {
    document.querySelectorAll("[data-checkout-details-form]").forEach(form => form.dispatchEvent(new Event("checkout-validate")));
  }
  document.addEventListener("cart-controls-changed", revalidate);
  document.addEventListener("cart-changed", revalidate);
  document.addEventListener("input", event => { if (event.target.matches("[data-quantity-input]")) revalidate(); });
  window.addEventListener("pageshow", () => {
    initialize();
    document.querySelectorAll("[data-checkout-details-form]").forEach(form => form.dispatchEvent(new Event("checkout-validate")));
  });
  initialize();
})();
