document.addEventListener("DOMContentLoaded", function () {
  const toggle = document.querySelector(".menu-toggle");
  const nav = document.querySelector(".nav-links");

  if (toggle && nav) {
    function closeMenu() {
      nav.classList.remove("open");
      toggle.textContent = "☰";
      toggle.setAttribute("aria-expanded", "false");
    }

    function openMenu() {
      nav.classList.add("open");
      toggle.textContent = "✕";
      toggle.setAttribute("aria-expanded", "true");
    }

    toggle.addEventListener("click", function (event) {
      event.stopPropagation();

      if (nav.classList.contains("open")) {
        closeMenu();
      } else {
        openMenu();
      }
    });

    document.querySelectorAll(".nav-link").forEach(function (link) {
      link.addEventListener("click", closeMenu);
    });

    document.addEventListener("click", function (event) {
      if (!nav.contains(event.target) && !toggle.contains(event.target)) {
        closeMenu();
      }
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        closeMenu();
      }
    });
  }

  document.addEventListener("click", function (event) {
    const button = event.target.closest("[data-action][data-target]");
    if (!button) {
      return;
    }

    const input = document.getElementById(button.dataset.target);
    if (!input) {
      return;
    }

    const currentValue = input.value === "" ? 0 : Number.parseInt(input.value, 10);
    if (Number.isNaN(currentValue)) {
      input.value = "0";
      return;
    }

    if (button.dataset.action === "increment") {
      input.value = String(currentValue + 1);
      input.dispatchEvent(new Event("change", { bubbles: true }));
      return;
    }

    if (button.dataset.action === "decrement") {
      input.value = String(Math.max(0, currentValue - 1));
      input.dispatchEvent(new Event("change", { bubbles: true }));
    }
  });
});
