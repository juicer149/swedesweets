/*
  Logging in (registration/login.html), shown rather than waited for.

  Pressing Login: the fields and the button fade out and the status burst's
  yellow dots take their place, at least --feedback-min-loading (tokens.css)
  while the form is sent in the background. If it worked, the crown grows
  in, and then the next page opens. If not, a cream cross, and the form
  comes back as the server answered it: with the problem said above the
  fields.

  The answer tells which: a login that worked is redirected away from the
  login page (to after_login and on); a wrong password is the login page
  again. Anything else (an expired form, a server error) falls back to
  sending the form the ordinary way, so the browser shows that page.

  Without JavaScript the form is sent as usual.
*/
(() => {
  "use strict";

  if (!window.fetch || !window.DOMParser) {
    return;
  }

  const loginPath = (form) => new URL(form.action, window.location.href).pathname;

  class LoginFailed extends Error {
    constructor(html) {
      super("login failed");
      this.html = html;
    }
  }

  async function send(form) {
    const response = await fetch(form.action, {
      method: "POST",
      body: new FormData(form),
      credentials: "same-origin",
    });

    const landedOn = new URL(response.url, window.location.href);

    if (response.ok && response.redirected && landedOn.pathname !== loginPath(form)) {
      return landedOn.href;
    }

    if (response.ok && landedOn.pathname === loginPath(form)) {
      throw new LoginFailed(await response.text());
    }

    // An expired form (403) or a server error: let the browser show it.
    throw new Error(`login answered ${response.status}`);
  }

  function formFrom(html) {
    const page = new DOMParser().parseFromString(html, "text/html");
    return page.querySelector("form[data-login]");
  }

  document.addEventListener("submit", async (event) => {
    const form = event.target;

    if (!(form instanceof HTMLFormElement) || !form.hasAttribute("data-login")) {
      return;
    }

    if (event.defaultPrevented || form.dataset.sending === "true") {
      event.preventDefault();
      return;
    }

    const place = form.querySelector("[data-login-burst]");

    if (!place || !window.statusBurst) {
      return;
    }

    event.preventDefault();
    form.dataset.sending = "true";
    form.setAttribute("aria-busy", "true");
    form.classList.add("is-sending");

    const { ok, value, error } = await window.statusBurst.run(
      place,
      "default",
      () => send(form)
    );

    if (ok) {
      // The crown has shown; the next page.
      window.location.assign(value);
      return;
    }

    const answered = error instanceof LoginFailed ? formFrom(error.html) : null;

    if (!answered) {
      delete form.dataset.sending;
      HTMLFormElement.prototype.submit.call(form);
      return;
    }

    // Back as the server answered it: the problem above the fields.
    form.replaceWith(answered);
    window.passwordToggles?.(answered);
    (answered.querySelector(".form-field--error input")
      || answered.querySelector("input:not([type=hidden])"))?.focus();
  });
})();
