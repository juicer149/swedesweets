/*
  A short green glow on a line just added, or one that just got one more
  (lines.css, .line--added): a shop's cart and the ops order form.

    window.glowLine(line)

  The class goes when the glow's own animation ends (a stepper's bump
  inside the line ends too, and is not it).
*/
(() => {
  "use strict";

  function glowLine(line) {
    if (!line) {
      return;
    }

    line.classList.remove("line--added");
    void line.offsetWidth; // restart the animation
    line.classList.add("line--added");

    const done = (event) => {
      if (event.animationName !== "line-added") {
        return;
      }

      line.classList.remove("line--added");
      line.removeEventListener("animationend", done);
    };

    line.addEventListener("animationend", done);
  }

  window.glowLine = glowLine;
})();
