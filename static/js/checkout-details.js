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
        const busy = document.querySelector('[data-update-in-progress="true"], [data-remove-in-progress="true"]');
        button.disabled = !complete || Boolean(busy);
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
    });
  }
  document.addEventListener("navbar-cart-refreshed", initialize);
  document.addEventListener("cart-controls-changed", () => {
    document.querySelectorAll("[data-checkout-details-form]").forEach(form => form.dispatchEvent(new Event("checkout-validate")));
  });
  window.addEventListener("pageshow", () => {
    initialize();
    document.querySelectorAll("[data-checkout-details-form]").forEach(form => form.dispatchEvent(new Event("checkout-validate")));
  });
  initialize();
})();
