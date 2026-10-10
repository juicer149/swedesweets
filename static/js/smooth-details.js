// Smooth <details>: opening and closing slide the content's height instead
// of jumping, so whatever sits below glides along. Opt in with
// <details data-smooth> and mark the part that slides with
// data-smooth-content. Details that share data-smooth-group="name" form an
// accordion: opening one closes the others (they slide shut too).
// Details added later: window.enhanceSmoothDetails(container).
// Without JavaScript, or with reduced motion, details open and close as
// usual.
(() => {
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const items = new Map();

  function slide(item, expand) {
    const { details, content } = item;

    if (item.expanded === expand && item.animation === null) {
      return;
    }

    const running = item.animation !== null;
    const from = running ? content.getBoundingClientRect().height : null;

    item.animation?.cancel();
    item.expanded = expand;

    if (expand) {
      details.open = true;
    }

    if (reducedMotion.matches) {
      item.animation = null;
      details.open = expand;
      return;
    }

    const full = content.scrollHeight;
    const start = from ?? (expand ? 0 : full);
    const end = expand ? full : 0;

    content.style.overflow = "hidden";
    const animation = content.animate(
      [
        { height: `${start}px`, opacity: expand ? 0 : 1 },
        { height: `${end}px`, opacity: expand ? 1 : 0 },
      ],
      { duration: 280, easing: "cubic-bezier(0.2, 0, 0, 1)" },
    );
    item.animation = animation;

    animation.onfinish = () => {
      item.animation = null;
      content.style.overflow = "";
      if (!item.expanded) {
        details.open = false;
      }
    };
  }

  function enhance(root = document) {
  root.querySelectorAll("details[data-smooth]").forEach((details) => {
    if (items.has(details)) {
      return;
    }

    const summary = details.querySelector(":scope > summary");
    const content = details.querySelector(":scope > [data-smooth-content]");

    if (!summary || !content) {
      return;
    }

    const item = {
      details,
      content,
      group: details.dataset.smoothGroup || null,
      expanded: details.open,
      animation: null,
    };
    items.set(details, item);

    summary.addEventListener("click", (event) => {
      event.preventDefault();

      const expand = !item.expanded;

      if (expand && item.group) {
        items.forEach((other) => {
          if (other !== item && other.group === item.group) {
            slide(other, false);
          }
        });
      }

      slide(item, expand);
    });
  });
  }

  enhance();

  // Details put in the page later (the ops order form's previous
  // orders) ask for the same: window.enhanceSmoothDetails(container).
  window.enhanceSmoothDetails = enhance;
})();
