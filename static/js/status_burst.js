/*
  The status burst (includes/ui/status_burst.html): show the dots in a
  place while a request runs, then the success mark or the red cross.

    const { ok, value, error } = await window.statusBurst.run(
      place, "catalog", () => fetch(…)
    );

  window.statusBurst.create(name) gives a fresh burst to place yourself
  (submit_burst.js). Its look comes from --feedback-burst-style.

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

  /* Which look: --feedback-burst-style and --feedback-burst-mark, read
     where the burst goes, so the CSS chooses them: the whole site in
     tokens.css, and a place of its own by setting them on its element
     (the end of tokens.css). */
  function token(place, name, fallback) {
    const element = place instanceof Element ? place : document.documentElement;

    return (
      getComputedStyle(element)
        .getPropertyValue(name)
        .trim()
        .replace(/["']/g, "") || fallback
    );
  }

  function create(name, place) {
    const template = document.querySelector(
      `template[data-status-burst="${name}"]`
    );

    if (!template) {
      return null;
    }

    const burst = template.content.firstElementChild.cloneNode(true);
    burst.dataset.style = token(place, "--feedback-burst-style", "ring");
    burst.dataset.mark = token(place, "--feedback-burst-mark", "crown");
    return burst;
  }

  /* Every style but the ring ends on a whole round of its dots
     (--feedback-burst-cycle), never in the middle of one; then the dots
     stop and the crown stands still a moment (--feedback-burst-rest,
     data-state "still") before it glows. */
  async function finishRound(burst, startedAt) {
    if (!burst || burst.dataset.style === "ring") {
      return;
    }

    const round = tokenMs("--feedback-burst-cycle", 1050);
    const left = round - ((performance.now() - startedAt) % round);

    await wait(left < round ? left : 0);
    burst.dataset.state = "still";
    await wait(tokenMs("--feedback-burst-rest", 250));
  }

  async function run(place, name, request) {
    const burst = create(name, place);
    const startedAt = performance.now();

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

    await finishRound(burst, startedAt);

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

  window.statusBurst = { run, create };
})();
