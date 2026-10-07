/*
  The status burst (includes/ui/status_burst.html): show the dots in a
  place while a request runs, then the success mark or the red cross.

    const { ok, value, error } = await window.statusBurst.run(
      place, "catalog", () => fetch(…)
    );

  The request and a minimum time (--feedback-min-loading) run side by
  side, so the dots never make anything slower than the server; then the
  mark grows (--feedback-mark-grow) and stays (--feedback-mark-hold), and
  the place is emptied. The times live in tokens.css. ok is whether the
  request resolved; value is what it resolved to, error what it threw.
*/
(() => {
  "use strict";

  /* Timing comes from tokens.css (--feedback-*), shared with the CSS. The
     numbers here are only the fallback if a token is missing. */
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

  const wait = (ms) => new Promise((resolve) => window.setTimeout(resolve, ms));

  function create(name) {
    const template = document.querySelector(
      `template[data-status-burst="${name}"]`
    );

    return template
      ? template.content.firstElementChild.cloneNode(true)
      : null;
  }

  async function run(place, name, request) {
    const burst = create(name);

    if (burst) {
      place.replaceChildren(burst);
    }

    const outcome = { ok: false, value: undefined, error: undefined };

    await Promise.all([
      Promise.resolve()
        .then(request)
        .then(
          (value) => {
            outcome.ok = true;
            outcome.value = value;
          },
          (error) => {
            outcome.error = error;
          }
        ),
      wait(tokenMs("--feedback-min-loading", 500)),
    ]);

    if (burst) {
      burst.dataset.state = outcome.ok ? "success" : "error";
      await wait(
        tokenMs("--feedback-mark-grow", 200)
          + tokenMs("--feedback-mark-hold", 750)
      );
    }

    place.replaceChildren();

    return outcome;
  }

  window.statusBurst = { run };
})();
