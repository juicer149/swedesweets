/* The save action stays at the phone's foot, behind the software keyboard.
   VisualViewport is used only to detect occlusion, never to lift the action. */
(() => {
  const page = document.querySelector("[data-account-edit]");
  if (!page) return;
  const root = document.documentElement;
  const viewport = window.visualViewport;
  let baseline = viewport?.height || innerHeight;
  let occluded = false;
  function update() {
    const height = viewport?.height || innerHeight;
    const editing = page.contains(document.activeElement) && document.activeElement.matches("input:not([type=checkbox]), textarea, select, [contenteditable]");
    if (!occluded && !editing) baseline = height;
    baseline = Math.max(baseline, height);
    occluded = (editing || occluded) && baseline - height > 120;
    root.classList.toggle("account-edit-keyboard", occluded);
  }
  viewport?.addEventListener("resize", update);
  window.addEventListener("resize", update);
  document.addEventListener("focusin", update);
  document.addEventListener("focusout", () => requestAnimationFrame(update));
  window.addEventListener("pageshow", update);
  window.addEventListener("orientationchange", () => { baseline = viewport?.height || innerHeight; occluded = false; update(); });
  update();
})();
