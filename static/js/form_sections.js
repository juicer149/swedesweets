/*
  A form of sections (the product and catalog forms): rows that slide open
  one at a time, like the dashboard's queues (smooth-details.js, loaded
  after this one). This script

  - opens the right section first: the first with an error, else the one
    the URL names (#pricing, from the product page), else the first;
  - brings the first error into view and puts the cursor in its field;
  - gives a section the class form-disclosure--changed while something in
    it differs from how the page came (its dot, products.css). Hidden
    fields count (a variant's order or deletion); [data-section-ignore]
    does not (the variants' lock);
  - keeps the open section across a save: the form posts to the page with
    the section's #, and the browser keeps that # through the redirect
    back to the page.
*/
(function () {
  "use strict";

  const sections = [...document.querySelectorAll("[data-form-section]")];

  if (sections.length === 0) {
    return;
  }

  const errorSelector =
    ".form-field--error, .form-errors, .variant-row--error";

  const withError = sections.find(
    (section) => section.querySelector(errorSelector)
  );
  const named = sections.find(
    (section) => section.id === window.location.hash.slice(1)
  );
  const first = withError ?? named ?? sections[0];

  for (const section of sections) {
    section.open = section === first;
  }

  function signature(section) {
    return [
      ...section.querySelectorAll("input[name], select[name], textarea[name]"),
    ]
      .filter((field) => !field.hasAttribute("data-section-ignore"))
      .map((field) => (
        field.type === "checkbox" || field.type === "radio"
          ? `${field.name}:${field.checked}`
          : `${field.name}=${field.value}`
      ))
      .join("\n");
  }

  const initial = new Map(
    sections.map((section) => [section, signature(section)])
  );

  function markChanged() {
    for (const section of sections) {
      section.classList.toggle(
        "form-disclosure--changed",
        signature(section) !== initial.get(section)
      );
    }
  }

  const form = sections[0].closest("form");

  if (form) {
    form.addEventListener("input", markChanged);
    form.addEventListener("change", markChanged);
    form.addEventListener("dirty-form:refresh", markChanged);

    form.addEventListener("submit", () => {
      const open = sections.find((section) => section.open);

      if (open) {
        form.action = `${window.location.pathname}${window.location.search}#${open.id}`;
      }
    });

    // Rows added, removed or moved (the variants) send no input event.
    new MutationObserver(markChanged).observe(form, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ["hidden"],
    });
  }

  const error = withError?.querySelector(errorSelector);

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
