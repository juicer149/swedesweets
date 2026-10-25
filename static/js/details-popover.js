"use strict";


(() => {
  const DISMISSABLE_DETAILS_SELECTOR = (
    "details[data-dismiss-on-outside-click]"
  );


  function openDismissableDetails() {
    return document.querySelectorAll(
      `${DISMISSABLE_DETAILS_SELECTOR}[open]`
    );
  }


  function triggerElement(
    details
  ) {
    return details.querySelector(
      ":scope > summary"
    );
  }


  function closeDetails(
    details,
    {
      restoreFocus = false,
    } = {}
  ) {
    if (
      !details
      || !details.open
    ) {
      return;
    }

    // Mobile sheets keep their details open until the exit motion finishes.
    if (!details.dispatchEvent(new CustomEvent("details-request-close", {
      cancelable: true,
      detail: { restoreFocus },
    }))) return;

    details.open = false;

    if (!restoreFocus) {
      return;
    }

    const trigger = triggerElement(
      details
    );

    if (
      trigger instanceof HTMLElement
    ) {
      trigger.focus();
    }
  }


  document.addEventListener(
    "click",
    (event) => {
      const target = event.target;

      if (!(target instanceof Node)) {
        return;
      }

      // Let the brand's native navigation leave immediately. Closing a sheet
      // first would animate and history.back() before the browser follows it.
      if (target instanceof Element && target.closest("a.site-brand[href], a.entrance-header__brand[href]")) return;

      // A confirmation opened by the panel is a separate top-layer dialog,
      // not an outside click dismissing its underlying cart.
      if (target instanceof Element && target.closest("dialog")) return;

      for (
        const details
        of openDismissableDetails()
      ) {
        if (
          details.contains(
            target
          )
        ) {
          continue;
        }

        closeDetails(
          details
        );
      }
    }
  );


  document.addEventListener(
    "keydown",
    (event) => {
      if (
        event.key !== "Escape"
      ) {
        return;
      }

      if (document.querySelector("dialog[open]")) return;

      const openDetails = (
        openDismissableDetails()
      );

      if (
        openDetails.length === 0
      ) {
        return;
      }

      event.preventDefault();

      for (
        const details
        of openDetails
      ) {
        closeDetails(
          details,
          {
            restoreFocus: true,
          }
        );
      }
    }
  );
})();
