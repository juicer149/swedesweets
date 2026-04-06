document.addEventListener("DOMContentLoaded", function () {
  const toggle = document.querySelector(".menu-toggle");
  const nav = document.querySelector(".nav-links");

  if (!toggle || !nav) return;

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
});
