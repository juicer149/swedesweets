/*
  A flash behind a line (lines.css, .line-flash): green as a line comes
  in, then fading out; red while it goes, then the line fades and folds
  away. One look for every list of lines: a shop's cart, the ops order
  form and the navbar cart.

    window.lineFlash.added(line)
        the green glow on a line just added (or one that got more)

    const value = await window.lineFlash.remove(line, request)
        the red burst while request() runs (at least REMOVE_BURST_MS);
        if it resolves, the line fades and folds to nothing (the caller
        then takes it out); if it throws, the line is as it was and the
        error goes on to the caller

  With reduced motion the waits are skipped; the colours still show.
*/
(() => {
  "use strict";

  const REMOVE_BURST_MS = 450;
  const FOLD_MS = 280;

  const reducedMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)"
  );

  const pause = (ms) => new Promise((resolve) => {
    window.setTimeout(resolve, reducedMotion.matches ? 0 : ms);
  });

  function added(line) {
    if (!line) {
      return;
    }

    line.classList.remove("line-flash--added");
    void line.offsetWidth; // restart the animation
    line.classList.add("line-flash", "line-flash--added");

    // Only the flash's own end (a stepper's bump inside the line ends too).
    const done = (event) => {
      if (event.animationName !== "line-flash-out") {
        return;
      }

      line.classList.remove("line-flash--added");
      line.removeEventListener("animationend", done);
    };

    line.addEventListener("animationend", done);
  }

  // The line's height runs from what it is to nothing, so what is below
  // (the next lines, or the empty cart) moves up smoothly.
  async function foldAway(line) {
    line.style.height = `${line.offsetHeight}px`;
    void line.offsetHeight;
    line.classList.add("line-flash--folding");
    line.style.height = "0px";
    await pause(FOLD_MS);
  }

  async function remove(line, request) {
    line.classList.add("line-flash", "line-flash--removed");

    const burst = pause(REMOVE_BURST_MS);

    try {
      const value = await request();
      await burst;
      await foldAway(line);
      return value;
    } catch (error) {
      line.classList.remove("line-flash--removed", "line-flash--folding");
      line.style.height = "";
      throw error;
    }
  }

  window.lineFlash = { added, remove };
})();
