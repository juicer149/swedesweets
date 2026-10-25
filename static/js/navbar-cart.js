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
  let quantityRequests = 0;


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
    if (refreshInProgress || quantityRequests) {
      refreshPending = true;
      return;
    }

    refreshInProgress = true;

    const currentCart = (
      cartElement()
    );

    // The fragment URL describes the cart, not the page hosting its icon.
    const isCurrentPage = currentCart?.querySelector("summary")
      ?.getAttribute("aria-current") === "page";


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

      // Read the draft at replacement time: typing and dismissal can happen
      // while this GET is in flight.
      const wasOpen = Boolean(preserveOpenState && currentCart?.open);
      const wasLit = currentCart?.hasAttribute("data-panel-lit");
      const wasLocked = currentCart?.dataset.cartLocked === "true";
      const draftForm = currentCart?.querySelector("[data-checkout-details-form]");
      const draft = [...(draftForm?.elements || [])].map(field => [field.name, field.value]);
      const panelScroll = currentCart?.querySelector("[data-cart-panel-scroll]")?.scrollTop || 0;
      const focusName = draftForm?.contains(document.activeElement) ? document.activeElement.name : null;

      document.dispatchEvent(new Event("navbar-cart-replacing"));
      replaceHtml(
        container,
        html
      );

      if (isCurrentPage) {
        cartElement()?.querySelector("summary")?.setAttribute("aria-current", "page");
      }

      const refreshedCart = cartElement();
      if (wasLit) refreshedCart?.setAttribute("data-panel-lit", "");
      if (wasLocked && refreshedCart) {
        refreshedCart.dataset.cartLocked = "true";
        const trigger = refreshedCart.querySelector("summary");
        // In the focused flow this summary is a return control, not a second
        // cart editor. Server-side cart/payment locks still remain in force.
        if (!document.documentElement.hasAttribute("data-checkout-flow")) {
          trigger?.setAttribute("aria-disabled", "true");
          trigger?.setAttribute("tabindex", "-1");
          trigger?.setAttribute("inert", "");
        }
      }
      const restoredForm = refreshedCart?.querySelector("[data-checkout-details-form]");
      for (const [name, value] of draft) {
        const field = restoredForm?.elements.namedItem(name);
        if (field && field.type !== "hidden") field.value = value;
      }
      if (wasOpen && refreshedCart) refreshedCart.open = true;
      document.dispatchEvent(new CustomEvent("navbar-cart-refreshed", {
        detail: { container },
      }));
      const scroll = refreshedCart?.querySelector("[data-cart-panel-scroll]");
      if (scroll) scroll.scrollTop = panelScroll;
      if (wasOpen && focusName) restoredForm?.elements.namedItem(focusName)?.focus({ preventScroll: true });

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


  async function updateNavbarQuantity(form) {
    const input = form.querySelector("[data-quantity-input]");
    if (!input) return;
    if (!input.checkValidity()) {
      input.value = form.dataset.confirmedQuantity || "1";
      input.dispatchEvent(new Event("input", { bubbles: true }));
      return;
    }
    if (form.dataset.updateInProgress === "true") {
      form.dataset.pendingQuantity = input.value;
      return;
    }
    if (input.value === form.dataset.confirmedQuantity) return;
    quantityRequests += 1;
    form.dataset.updateInProgress = "true";
    document.dispatchEvent(new Event("cart-controls-changed"));
    let bump = null;
    try {
      do {
        delete form.dataset.pendingQuantity;
        const previous = Number(form.dataset.confirmedQuantity);
        const body = new FormData(form);
        const response = await fetch(form.action, {
          method: "POST", body, headers: { Accept: "application/json" }, credentials: "same-origin",
        });
        const payload = await response.json();
        if (response.status === 409) { window.location.reload(); return; }
        if (!response.ok || !payload.ok) throw new Error(payload.message || "Could not update quantity.");
        form.dataset.confirmedQuantity = String(payload.quantity);
        const pending = form.dataset.pendingQuantity;
        input.value = pending || String(payload.quantity);
        const row = form.closest("[data-navbar-cart-line]");
        row.dataset.quantity = String(payload.quantity);
        const status = form.querySelector("[data-current-order-quantity-status]");
        if (status) status.textContent = payload.message || "";
        bump = payload.quantity > previous ? "added" : "removed";
        dispatchCartChanged({ source: "navbar-cart", mutation: "quantity", lineId: Number(row.dataset.lineId), quantity: payload.quantity, payload });
        refreshPending = true;
      } while (form.dataset.pendingQuantity && form.dataset.pendingQuantity !== form.dataset.confirmedQuantity);
    } catch (error) {
      input.value = form.dataset.confirmedQuantity;
      const status = form.querySelector("[data-current-order-quantity-status]");
      if (status) status.textContent = error.message;
    } finally {
      form.dataset.updateInProgress = "false";
      quantityRequests -= 1;
      document.dispatchEvent(new Event("cart-controls-changed"));
      if (!quantityRequests && refreshPending) {
        refreshPending = false;
        await refreshNavbarCart({ preserveOpenState: true });
        if (bump) bumpCart(bump);
      }
    }
  }

  document.addEventListener("change", event => {
    const form = event.target.closest("[data-navbar-cart-quantity-form]");
    if (form) void updateNavbarQuantity(form);
  });
  document.addEventListener("submit", event => {
    if (!event.target.matches("[data-navbar-cart-quantity-form]")) return;
    event.preventDefault();
    void updateNavbarQuantity(event.target);
  });

  /*
   * Remove mutation
   * ------------------------------------------------------------------
   *
   * The trash: a red flash over the line while the request runs, then
   * the line fades and folds away (line_flash.js), and only then the
   * server's fragment comes in (the empty cart, when it was the last),
   * so nothing jumps.
   *
   * Success:
   *   red flash -> fades and folds -> removed -> fragment refresh
   *
   * Failure:
   *   red flash -> the line as it was
   */

  async function removeNavbarCartLine(
    form
  ) {
    const line = lineFromElement(
      form
    );

    if (quantityRequests) return;
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
    document.dispatchEvent(new Event("cart-controls-changed"));

    if (submitButton) {
      submitButton.disabled = true;
    }

    const request = async () => {
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

      return payload;
    };

    try {
      let payload;
      if (window.lineFlash) {
        payload = await window.lineFlash.remove(
          line,
          request
        );
      } else {
        payload = await request();
      }

      navbarCartLineRemove(
        form
      );

      dispatchCartChanged({
        source: "navbar-cart",
        mutation: "remove",
        lineId,
        quantity: 0,
        payload,
      });

      await refreshNavbarCart({
        preserveOpenState: true,
      });

      bumpCart("removed");
    } catch (error) {
      navbarCartLineShow(
        line
      );

      form.dataset.removeInProgress = "false";
      document.dispatchEvent(new Event("cart-controls-changed"));

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
        const kind = event.detail.bump === "removed" ? "removed" : "added";
        void refreshed.then(() => bumpCart(kind));
      }
    }
  );


  /* A little jump and a flash of the cart button (navigation.css): green
     when something just went into it, red when something went out. */
  function bumpCart(kind = "added") {
    const trigger = cartTriggerElement();

    if (!trigger) {
      return;
    }

    trigger.classList.remove("is-bumped", "is-bumped--removed");
    void trigger.offsetWidth; // restart the animation
    trigger.classList.add("is-bumped");
    trigger.classList.toggle("is-bumped--removed", kind === "removed");
    // The theme selects a filled flash or icon glow; both finish after the jump.
    const done = (event) => {
      if (
        event.target !== trigger
        || !["site-nav-cart-flash", "site-nav-cart-glow"].includes(event.animationName)
      ) {
        return;
      }

      trigger.classList.remove("is-bumped", "is-bumped--removed");
      trigger.removeEventListener("animationend", done);
    };

    trigger.addEventListener("animationend", done);
  }


  /* A flash asked for before the page reloaded (cart.js: the last line
     taken out of the cart page). */
  try {
    const kind = window.sessionStorage.getItem("navbar-cart-bump");

    if (kind) {
      window.sessionStorage.removeItem("navbar-cart-bump");
      bumpCart(kind);
    }
  } catch (error) {
    // no storage: no flash
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
