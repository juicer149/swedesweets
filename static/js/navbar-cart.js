"use strict";


(() => {
  const app = window.SwedeSweets;

  if (
    !app
    || !app.dom
  ) {
    console.error(
      "navbar-cart.js requires ui-dom.js"
    );

    return;
  }

  const container = document.querySelector(
    "[data-navbar-cart-container]"
  );

  if (!container) {
    return;
  }

  const fragmentUrl = (
    container.dataset.navbarCartUrl
  );

  if (!fragmentUrl) {
    return;
  }

  const {
    closest,
    hide,
    remove,
    replaceHtml,
    show,
  } = app.dom;


  let refreshInProgress = false;
  let refreshPending = false;


  /*
   * DOM lookup API
   * ------------------------------------------------------------------
   */


  function cartElement() {
    return container.querySelector(
      ".site-nav-cart"
    );
  }


  function cartTriggerElement() {
    const cart = cartElement();

    if (!cart) {
      return null;
    }

    return cart.querySelector(
      ".site-nav-cart__trigger"
    );
  }


  function lineFromElement(
    element
  ) {
    return closest(
      element,
      "[data-navbar-cart-line]"
    );
  }


  function lineIdFromElement(
    element
  ) {
    const line = lineFromElement(
      element
    );

    if (!line) {
      return null;
    }

    const lineId = Number(
      line.dataset.lineId
    );

    return Number.isInteger(
      lineId
    )
      ? lineId
      : null;
  }


  /*
   * Navbar-cart presentation API
   * ------------------------------------------------------------------
   */


  function closeNavbarCart({
    restoreFocus = false,
  } = {}) {
    const cart = cartElement();

    if (
      !cart
      || !cart.open
    ) {
      return;
    }

    cart.open = false;

    if (restoreFocus) {
      cartTriggerElement()?.focus();
    }
  }


  function navbarCartLineShow(
    element
  ) {
    show(
      lineFromElement(
        element
      )
    );
  }


  function navbarCartLineHide(
    element
  ) {
    hide(
      lineFromElement(
        element
      )
    );
  }


  function navbarCartLineRemove(
    element
  ) {
    remove(
      lineFromElement(
        element
      )
    );
  }


  /*
   * Cross-component event
   * ------------------------------------------------------------------
   */


  function dispatchCartChanged(
    detail = {}
  ) {
    document.dispatchEvent(
      new CustomEvent(
        "cart-changed",
        {
          detail,
        }
      )
    );
  }


  /*
   * Cart fragment refresh
   * ------------------------------------------------------------------
   *
   * The server remains source of truth.
   */


  async function refreshNavbarCart({
    preserveOpenState = false,
  } = {}) {
    if (refreshInProgress) {
      refreshPending = true;
      return;
    }

    refreshInProgress = true;

    const currentCart = (
      cartElement()
    );

    const wasOpen = Boolean(
      preserveOpenState
      && currentCart?.open
    );

    try {
      const response = await fetch(
        fragmentUrl,
        {
          method: "GET",
          headers: {
            Accept: "text/html",
          },
          credentials: "same-origin",
          // Always the cart as it is now, never a copy the browser kept.
          cache: "no-store",
        }
      );

      if (!response.ok) {
        throw new Error(
          "Could not refresh cart."
        );
      }

      const html = await response.text();

      replaceHtml(
        container,
        html
      );

      if (wasOpen) {
        const refreshedCart = (
          cartElement()
        );

        if (refreshedCart) {
          refreshedCart.open = true;
        }
      }
    } catch (error) {
      console.error(
        "Navbar cart refresh failed:",
        error
      );
    } finally {
      refreshInProgress = false;

      if (refreshPending) {
        refreshPending = false;

        void refreshNavbarCart({
          preserveOpenState: true,
        });
      }
    }
  }


  /*
   * Remove mutation
   * ------------------------------------------------------------------
   *
   * The line is first hidden optimistically.
   *
   * Success:
   *   hidden -> removed -> server fragment refresh
   *
   * Failure:
   *   hidden -> shown again
   */


  async function removeNavbarCartLine(
    form
  ) {
    const line = lineFromElement(
      form
    );

    if (!line) {
      return;
    }

    if (
      form.dataset.removeInProgress
      === "true"
    ) {
      return;
    }

    const lineId = lineIdFromElement(
      form
    );

    const submitButton = (
      form.querySelector(
        'button[type="submit"]'
      )
    );

    form.dataset.removeInProgress = "true";

    if (submitButton) {
      submitButton.disabled = true;
    }

    navbarCartLineHide(
      form
    );

    try {
      const response = await fetch(
        form.action,
        {
          method: "POST",
          body: new FormData(form),
          headers: {
            Accept: "application/json",
          },
          credentials: "same-origin",
        }
      );

      const payload = (
        await response.json()
      );

      if (
        !response.ok
        || !payload.ok
      ) {
        throw new Error(
          payload.message
          || "Could not remove product."
        );
      }

      navbarCartLineRemove(
        form
      );

      dispatchCartChanged({
        source: "navbar-cart",
        mutation: "remove",
        lineId,
      });

      await refreshNavbarCart({
        preserveOpenState: true,
      });
    } catch (error) {
      navbarCartLineShow(
        line
      );

      form.dataset.removeInProgress = "false";

      if (submitButton) {
        submitButton.disabled = false;
      }

      console.error(
        "Navbar cart remove failed:",
        error
      );
    }
  }


  /*
   * Event delegation
   * ------------------------------------------------------------------
   *
   * Delegation is required because navbar contents can
   * be replaced by server-rendered fragments.
   */


  document.addEventListener(
    "submit",
    (event) => {
      const removeForm = closest(
        event.target,
        "[data-navbar-cart-remove-form]"
      );

      if (!removeForm) {
        return;
      }

      event.preventDefault();

      void removeNavbarCartLine(
        removeForm
      );
    }
  );


  document.addEventListener(
    "cart-changed",
    (event) => {
      if (
        event.detail?.source
        === "navbar-cart"
      ) {
        return;
      }

      const refreshed = refreshNavbarCart({
        preserveOpenState: true,
      });

      if (event.detail?.bump) {
        void refreshed.then(bumpCart);
      }
    }
  );


  /* A little jump and a green flash of the cart button: something just
     went into it (navigation.css). */
  function bumpCart() {
    const trigger = cartTriggerElement();

    if (!trigger) {
      return;
    }

    trigger.classList.remove("is-bumped");
    void trigger.offsetWidth; // restart the animation
    trigger.classList.add("is-bumped");
    // Done when the green flash (the longer of the two) has ended.
    const done = (event) => {
      if (event.target !== trigger || event.animationName !== "site-nav-cart-flash") {
        return;
      }

      trigger.classList.remove("is-bumped");
      trigger.removeEventListener("animationend", done);
    };

    trigger.addEventListener("animationend", done);
  }


  /*
   * Back and forward: the browser may show this page as it was when it
   * was left (the back/forward cache, or its HTTP cache), with the cart
   * as it was then, though products were added since (add on a product
   * page, which lands on the catalog, then Back). Ask the server again.
   */
  function cameBackOrForward(event) {
    if (event.persisted) {
      return true;
    }

    const [navigation] = performance.getEntriesByType("navigation");

    return navigation?.type === "back_forward";
  }

  window.addEventListener(
    "pageshow",
    (event) => {
      if (cameBackOrForward(event)) {
        void refreshNavbarCart();
      }
    }
  );


  /*
   * Public navbar-cart UI API
   * ------------------------------------------------------------------
   */


  app.navbarCart = Object.freeze({
    close: closeNavbarCart,
    refresh: refreshNavbarCart,

    line: Object.freeze({
      show: navbarCartLineShow,
      hide: navbarCartLineHide,
      remove: navbarCartLineRemove,
    }),
  });
})();
