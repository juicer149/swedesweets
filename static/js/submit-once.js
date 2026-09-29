(() => {
  function setSubmitting(form, submitting) {
    form.dataset.submitting = submitting ? "true" : "false";

    form
      .querySelectorAll('button[type="submit"]')
      .forEach((button) => {
        button.disabled = submitting;

        if (button.dataset.submittingLabel) {
          if (submitting) {
            button.dataset.idleLabel = button.textContent;
            button.textContent = button.dataset.submittingLabel;
          } else if (button.dataset.idleLabel) {
            button.textContent = button.dataset.idleLabel;
          }
        }

        if (submitting) {
          button.setAttribute("aria-busy", "true");
        } else {
          button.removeAttribute("aria-busy");
        }
      });
  }

  document.addEventListener("submit", (event) => {
    const form = event.target;

    if (
      !(form instanceof HTMLFormElement)
      || !form.hasAttribute("data-submit-once")
    ) {
      return;
    }

    if (form.dataset.submitting === "true") {
      event.preventDefault();
      return;
    }

    setSubmitting(form, true);
  });

  // Back from the payment provider can restore this page from the
  // back/forward cache with the button still disabled.
  window.addEventListener("pageshow", (event) => {
    if (!event.persisted) {
      return;
    }

    document
      .querySelectorAll("form[data-submit-once]")
      .forEach((form) => setSubmitting(form, false));
  });
})();
