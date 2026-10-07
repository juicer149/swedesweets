/*
  A form that leads to the next step (Review order, Place order, Pay…):
  when it is sent, its yellow button gives way to the status burst's dots,
  in the same place; they show at least --feedback-min-loading (tokens.css)
  before the form goes, and stay until the next page arrives. The next
  page is the answer (the crown on "Thank you" and on an order just
  placed), so there is no crown or cross here.

    <form method="post" data-submit-burst> … <button class="page__submit">

  Also sends it only once: a second press while the dots show does
  nothing. The button is not disabled, and its name/value (e.g.
  intent=place_order) is carried in a hidden field, since the delayed
  send would otherwise drop it. Back from another page (the back/forward
  cache) shows the button again.
*/
(() => {
  "use strict";

  function dots() {
    const burst = document.createElement("span");
    burst.className = "status-burst submit-burst__dots";
    burst.dataset.state = "loading";
    burst.setAttribute("aria-hidden", "true");

    for (let i = 0; i < 8; i += 1) {
      const dot = document.createElement("span");
      dot.className = "status-burst__dot";
      dot.style.setProperty("--i", String(i));
      burst.append(dot);
    }

    return burst;
  }

  /* Timing from tokens.css, as in status_burst.js. */
  function tokenMs(name, fallback) {
    const value = getComputedStyle(document.documentElement)
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
    button.append(dots());
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
    show(form, button);

    const submitter = event.submitter;
    if (submitter?.name) {
      const carried = document.createElement("input");
      carried.type = "hidden";
      carried.name = submitter.name;
      carried.value = submitter.value;
      carried.dataset.submitBurstCarried = "";
      form.append(carried);
    }

    window.setTimeout(
      () => HTMLFormElement.prototype.submit.call(form),
      tokenMs("--feedback-min-loading", 500)
    );
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
