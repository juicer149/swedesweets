document.addEventListener("DOMContentLoaded", function () {
  const toggle = document.querySelector(".menu-toggle");
  const nav = document.querySelector(".nav-links");

  if (!toggle || !nav) return;

  // Toggle menu
  toggle.addEventListener("click", (e) => {
    e.stopPropagation(); // viktigt för click-outside
    nav.classList.toggle("open");

    // switch icon based on menu state
    toggle.textContent = nav.classList.contains("open") ? "✕" : "☰";
  });

  // Close menu when clicking a link
  document.querySelectorAll(".nav-link").forEach(link => {
    link.addEventListener("click", () => {
      nav.classList.remove("open");
      toggle.textContent = "☰";
    });
  });

  // Close menu when clicking outside
  document.addEventListener("click", (e) => {
    if (!nav.contains(e.target) && !toggle.contains(e.target)) {
      nav.classList.remove("open");
      toggle.textContent = "☰";
    }
  });

  // ESC key to close menu
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      nav.classList.remove("open");
      toggle.textContent = "☰";
    }
  });
});
