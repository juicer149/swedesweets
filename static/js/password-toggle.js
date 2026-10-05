// Show / hide password: a button inside .password-field switches the input
// between type=password and type=text. Without JavaScript the button stays
// hidden and the field works as a normal password field.
(() => {
  document.querySelectorAll("[data-password-toggle]").forEach((button) => {
    const input = button
      .closest(".password-field")
      ?.querySelector("input");

    if (!input) {
      return;
    }

    button.hidden = false;

    button.addEventListener("click", () => {
      const showing = input.type === "text";

      input.type = showing ? "password" : "text";
      button.setAttribute("aria-pressed", showing ? "false" : "true");
      button.setAttribute(
        "aria-label",
        showing ? button.dataset.labelShow : button.dataset.labelHide,
      );
      input.focus();
    });
  });
})();
