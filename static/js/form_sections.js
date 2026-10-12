/*
  A form of sections on one page (the product form): when it comes back
  with errors, bring the first one into view and put the cursor in its
  field, so nothing wrong is left unseen further down. Links to a section
  (#pricing) scroll there on their own.
*/
(function () {
  "use strict";

  const error = document.querySelector(
    ".form-section .form-field--error, .form-section .form-errors, .form-section .variant-row--error"
  );

  if (!error) {
    return;
  }

  const reducedMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)"
  ).matches;

  error.scrollIntoView({
    behavior: reducedMotion ? "auto" : "smooth",
    block: "center",
  });

  const field = error.querySelector("input, select, textarea");

  if (field && !field.disabled) {
    field.focus({ preventScroll: true });
  }
})();
