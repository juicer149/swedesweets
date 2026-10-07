/*
  The status burst (includes/ui/status_burst.html): show the dots in a
  place while a request runs, then the success mark or the red cross.

    const { ok, value, error } = await window.statusBurst.run(
      place, "catalog", () => fetch(…)
    );

  The request and a minimum of 0.5 s run side by side, so the dots never
  make anything slower than the server; then the mark stays 0.7 s (0.2 s
  to grow, 0.5 s to be seen) and the place is emptied. ok is whether the
  request resolved; value is what it resolved to, error what it threw.
*/
(() => {
  "use strict";

  const MINIMUM_MS = 500;
  const MARK_MS = 700;

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
      wait(MINIMUM_MS),
    ]);

    if (burst) {
      burst.dataset.state = outcome.ok ? "success" : "error";
      await wait(MARK_MS);
    }

    place.replaceChildren();

    return outcome;
  }

  window.statusBurst = { run };
})();
