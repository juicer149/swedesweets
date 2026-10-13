// Back to where one came from: a [data-back-link] leads to the page before
// (document.referrer) when that is a page of this site and not this page
// or one under it (its edit form, say: going back there would go round in
// a circle). Otherwise it keeps its own href, the fallback (the list the
// page belongs to). Set on load, so the link shows where it goes and
// opens in a new tab like any other.
(() => {
  const links = document.querySelectorAll("[data-back-link]");

  if (links.length === 0 || !document.referrer) {
    return;
  }

  let from;

  try {
    from = new URL(document.referrer);
  } catch {
    return;
  }

  const here = window.location.pathname;

  if (
    from.origin !== window.location.origin
    || from.pathname === here
    || from.pathname.startsWith(here.endsWith("/") ? here : `${here}/`)
  ) {
    return;
  }

  links.forEach((link) => {
    link.href = from.href;
  });
})();
