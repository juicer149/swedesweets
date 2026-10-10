/*
  The status burst (includes/ui/status_burst.html): show the dots in a
  place while a request runs, then the success mark or the red cross.

    const { ok, value, error } = await window.statusBurst.run(
      place, "catalog", () => fetch(…)
    );

  window.statusBurst.create(name) gives a fresh burst to place yourself
  (submit_burst.js). Its look comes from --feedback-burst-style.

  The dots go round at one steady speed (--feedback-burst-cycle) for as
  long as it takes: the request and a minimum time (--feedback-min-loading)
  run side by side, so a quick answer still shows the dots that long and a
  slow one shows them until it comes. Then the dots settle
  (--feedback-burst-rest), the mark grows (--feedback-mark-grow) and stays
  (--feedback-mark-hold), and the place is emptied. The times live in tokens.css. ok is whether the
  request resolved; value is what it resolved to, error what it threw.
*/
(() => {
  "use strict";

  /* Timing comes from tokens.css (--feedback-*), shared with the CSS, read
     where the burst goes, so a place can have its own times (the end of
     tokens.css). The numbers here are only the fallback if a token is
     missing. */
  function tokenMs(name, fallback, place) {
    const element = place instanceof Element ? place : document.documentElement;
    const value = getComputedStyle(element)
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

  /* When the answer is in (and the minimum has passed), every style but
     the ring settles: the dots ease back and stand still a moment
     (--feedback-burst-rest, data-state "still") before the mark. */
  async function settle(burst) {
    if (!burst || burst.dataset.style === "ring") {
      return;
    }

    // Wherever the wave is, the dots ease back from there rather than
    // jump: hold each one's pose, stop the wave, then let it go.
    const dots = burst.querySelectorAll(
      ".status-burst__beat, .status-burst__crown-dot, .status-burst__scoop .scoop"
    );
    for (const dot of dots) {
      dot.style.transform = getComputedStyle(dot).transform;
    }

    burst.dataset.state = "still";
    void burst.offsetWidth;

    for (const dot of dots) {
      dot.style.transform = "";
    }

    await wait(tokenMs("--feedback-burst-rest", 250, burst));
  }

  /* options.onMark(ok) is called the moment the mark (or the cross)
     appears, while it still shows: the catalog lets the navbar's cart
     catch the product then, so the two overlap. */
  async function run(place, name, request, options = {}) {
    const burst = create(name, place);

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
      wait(tokenMs("--feedback-min-loading", 500, place)),
    ]);

    await finish(burst, outcome.ok, options.onMark);

    place.replaceChildren();

    return outcome;
  }

  /* The end of a burst: the dots settle, then the mark (or the cross)
     grows and stays its while. submit_burst.js calls it too, before the
     next page. */
  async function finish(burst, ok = true, onMark = null) {
    if (!burst) {
      onMark?.(ok);
      return;
    }

    await settle(burst);
    burst.dataset.state = ok ? "success" : "error";
    onMark?.(ok);
    await wait(
      tokenMs("--feedback-mark-grow", 200, burst)
        + tokenMs("--feedback-mark-hold", 750, burst)
    );
  }

  window.statusBurst = { run, create, finish };
})();
