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
        const complete = [...form.elements].filter(element => element.required && !element.disabled).every(element => element.value.trim() && element.validity.valid);
        const busy = document.querySelector('[data-update-in-progress="true"], [data-remove-in-progress="true"], [data-removing="true"]');
        const cart = form.closest(".site-nav-cart, .cart-page");
        const quantitiesValid = [...(cart?.querySelectorAll("[data-quantity-input]") || [])].every(input => input.validity.valid);
        button.disabled = !complete || !quantitiesValid || Boolean(busy);
        if (help) help.textContent = complete ? help.dataset.ready : help.dataset.incomplete;
      }
      form.addEventListener("input", validate);
      form.addEventListener("change", validate);
      confirm.addEventListener("blur", () => { touched = true; validate(); });
      for (const type of ["paste", "drop"]) confirm.addEventListener(type, event => event.preventDefault());
      form.addEventListener("submit", event => {
        validate();
        if (button.disabled || !form.reportValidity()) event.preventDefault();
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
