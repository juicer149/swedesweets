// Smooth <details>: opening and closing slide the content's height instead
// of jumping, so whatever sits below glides along. Opt in with
// <details data-smooth> and mark the part that slides with
// data-smooth-content. Without JavaScript, or with reduced motion, the
// details opens and closes as usual.
(() => {
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

  document.querySelectorAll("details[data-smooth]").forEach((details) => {
    const summary = details.querySelector(":scope > summary");
    const content = details.querySelector(":scope > [data-smooth-content]");

    if (!summary || !content) {
      return;
    }

    let expanded = details.open;
    let animation = null;

    summary.addEventListener("click", (event) => {
      if (reducedMotion.matches) {
        return;
      }

      event.preventDefault();

      const running = animation !== null;
      const from = running ? content.getBoundingClientRect().height : null;

      animation?.cancel();
      expanded = !expanded;

      if (expanded) {
        details.open = true;
      }

      const full = content.scrollHeight;
      const start = from ?? (expanded ? 0 : full);
      const end = expanded ? full : 0;

      content.style.overflow = "hidden";
      animation = content.animate(
        [
          { height: `${start}px`, opacity: expanded ? 0 : 1 },
          { height: `${end}px`, opacity: expanded ? 1 : 0 },
        ],
        { duration: 280, easing: "cubic-bezier(0.2, 0, 0, 1)" },
      );

      animation.onfinish = () => {
        animation = null;
        content.style.overflow = "";
        if (!expanded) {
          details.open = false;
        }
      };
    });
  });
})();
