/*
  A form that leads to the next step (Review order, Place order, Pay…):
  when it is sent, its yellow button gives way to the status burst, in the
  same place: the crown's wave for --feedback-min-loading (tokens.css, read
  on the button), then the crown settles and glows a moment (on to the
  next step), then the form goes. The next page is the real answer (the
  crown hero on "Thank you" and on an order just placed).

    <form method="post" data-submit-burst> … <button class="page__submit">

  Also sends it only once: a second press while the dots show does
  nothing. The button is not disabled, and its name/value (e.g.
  intent=place_order) is carried in a hidden field, since the delayed
  send would otherwise drop it. Back from another page (the back/forward
  cache) shows the button again.
*/
(() => {
  "use strict";

  /* The burst from base.html's template, in the look --feedback-burst-style
     chooses (status_burst.js). */
  function dots(button) {
    const burst = window.statusBurst?.create("default", button);

    if (!burst) {
      return document.createElement("span");
    }

    burst.classList.add("submit-burst__dots");
    burst.setAttribute("aria-hidden", "true");
    return burst;
  }

  /* Timing from tokens.css, read on the button, as in status_burst.js. */
  function tokenMs(name, fallback, element = document.documentElement) {
    const value = getComputedStyle(element)
      .getPropertyValue(name)
      .trim();
    const number = parseFloat(value);

    if (Number.isNaN(number)) {
      return fallback;
    }

    return value.endsWith("ms") ? number : number * 1000;
  }

  function show(form, button) {
    form.dataset.submitting = "true";
    button.classList.add("is-submitting");
    button.setAttribute("aria-busy", "true");
    const burst = dots(button);
    button.append(burst);
    return burst;
  }

  function reset(form) {
    delete form.dataset.submitting;
    form
      .querySelectorAll("[data-submit-burst-carried]")
      .forEach((input) => input.remove());

    for (const button of form.querySelectorAll(".is-submitting")) {
      button.classList.remove("is-submitting");
      button.removeAttribute("aria-busy");
      button.querySelector(".submit-burst__dots")?.remove();
    }
  }

  document.addEventListener("submit", (event) => {
    const form = event.target;

    if (
      !(form instanceof HTMLFormElement)
      || !form.hasAttribute("data-submit-burst")
    ) {
      return;
    }

    if (form.dataset.submitting === "true") {
      event.preventDefault();
      return;
    }

    // A form a script cancelled (dirty-form, a confirm) is not sent.
    if (event.defaultPrevented) {
      return;
    }

    const button =
      event.submitter?.closest(".page__submit")
      || form.querySelector(".page__submit");

    if (!button) {
      return;
    }

    // Show the dots for at least --feedback-min-loading, then send. The
    // browser's own send would drop the pressed button's name/value
    // (intent=place_order), so it is carried in a hidden field.
    event.preventDefault();
    const burst = show(form, button);

    const submitter = event.submitter;
    if (submitter?.name) {
      const carried = document.createElement("input");
      carried.type = "hidden";
      carried.name = submitter.name;
      carried.value = submitter.value;
      carried.dataset.submitBurstCarried = "";
      form.append(carried);
    }

    // The dots their while, then the crown settles and glows a moment
    // (on to the next step), then the form goes. Without the burst
    // script it simply goes after the while.
    window.setTimeout(async () => {
      if (window.statusBurst?.finish && burst.classList.contains("status-burst")) {
        await window.statusBurst.finish(burst, true);
      }

      HTMLFormElement.prototype.submit.call(form);
    }, tokenMs("--feedback-min-loading", 500, button));
  });

  window.addEventListener("pageshow", (event) => {
    if (!event.persisted) {
      return;
    }

    document
      .querySelectorAll("form[data-submit-burst]")
      .forEach(reset);
  });
})();
