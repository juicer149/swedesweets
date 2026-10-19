/* Translate the live page without replacing its forms, menus or controllers.
   Django remains the source of translations: compare two server renders, then
   change matching text/labels only. Native POST remains the no-JS/error path. */
(() => {
  "use strict";
  let busy = false;
  const skip = "script, style, textarea, [contenteditable]";
  const translatedAttribute = name => /^(title|alt|placeholder|aria-label|aria-description)$/.test(name)
    || /^data-.*(label|message|text|title)$/.test(name);
  const normalize = value => value.replace(/\s+/g, " ").trim();

  function translations(before, after) {
    const pairs = new Map();
    function add(oldValue, newValue) {
      const key = normalize(oldValue);
      const value = normalize(newValue);
      if (!key || key === value || !/\p{L}/u.test(key)) return;
      // A concurrent quantity/price update is data, not a translation.
      if (JSON.stringify(key.match(/\d+/g)) !== JSON.stringify(value.match(/\d+/g))) return;
      // Ambiguous text is left alone, never assigned an arbitrary translation.
      if (pairs.has(key) && pairs.get(key) !== value) pairs.set(key, null);
      else if (!pairs.has(key)) pairs.set(key, value);
    }
    function compare(a, b) {
      if (!b || a.nodeType !== b.nodeType) return;
      if (a.nodeType === Node.TEXT_NODE) { add(a.data, b.data); return; }
      if (a.nodeType !== Node.ELEMENT_NODE || a.tagName !== b.tagName || a.matches(skip)) return;
      for (const attr of a.attributes) {
        if (/^(id|data-.*-id)$/.test(attr.name) && b.getAttribute(attr.name) !== attr.value) return;
      }
      for (const attr of a.attributes) {
        if (translatedAttribute(attr.name) && b.hasAttribute(attr.name)) add(attr.value, b.getAttribute(attr.name));
      }
      const left = a.tagName === "TEMPLATE" ? a.content : a;
      const right = b.tagName === "TEMPLATE" ? b.content : b;
      // Do not pair unrelated rows when server data changed between requests.
      if (left.childNodes.length !== right.childNodes.length) return;
      left.childNodes.forEach((child, index) => compare(child, right.childNodes[index]));
    }
    compare(before.documentElement, after.documentElement);
    return pairs;
  }

  function apply(root, pairs) {
    function translate(value) {
      const replacement = pairs.get(normalize(value));
      return replacement ? value.replace(/\S[\s\S]*\S|\S/, () => replacement) : value;
    }
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        if (node.nodeType === Node.ELEMENT_NODE && node.matches(skip)) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      },
    });
    while (walker.nextNode()) {
      const node = walker.currentNode;
      if (node.nodeType === Node.TEXT_NODE) node.data = translate(node.data);
      else {
        for (const attr of [...node.attributes]) {
          if (translatedAttribute(attr.name)) node.setAttribute(attr.name, translate(attr.value));
        }
        if (node.tagName === "TEMPLATE") apply(node.content, pairs);
      }
    }
  }

  document.addEventListener("submit", async event => {
    const form = event.target.closest("[data-language-preferences]");
    const button = event.submitter;
    if (!form || !button) return;
    event.preventDefault();
    if (busy || button.value === document.documentElement.lang) return;
    busy = true;
    form.setAttribute("aria-busy", "true");
    const url = window.location.href;
    const data = new FormData(form);
    data.set("language", button.value);
    data.set("next", window.location.pathname + window.location.search);
    try {
      const options = { credentials: "same-origin", cache: "no-store", headers: { Accept: "text/html" } };
      const before = await fetch(url, options);
      if (!before.ok) throw new Error("Language source unavailable");
      const parser = new DOMParser();
      const source = parser.parseFromString(await before.text(), "text/html");
      const response = await fetch(form.action, { ...options, method: "POST", body: data });
      if (!response.ok) throw new Error("Language change failed");
      const target = parser.parseFromString(await response.text(), "text/html");
      if (target.documentElement.lang !== button.value || window.location.href !== url) {
        throw new Error("Language destination changed");
      }
      apply(document.documentElement, translations(source, target));
      document.documentElement.lang = button.value;
      for (const option of document.querySelectorAll(".language-switcher__option")) {
        const active = option.value === button.value;
        option.classList.toggle("language-switcher__option--active", active);
        if (active) option.setAttribute("aria-current", "true");
        else option.removeAttribute("aria-current");
      }
      document.dispatchEvent(new CustomEvent("site-language-changed"));
    } catch {
      // Reuse the ordinary CSRF-protected form rather than losing navigation.
      const language = document.createElement("input");
      language.type = "hidden"; language.name = "language"; language.value = button.value;
      form.append(language);
      HTMLFormElement.prototype.submit.call(form);
    } finally {
      busy = false;
      form.removeAttribute("aria-busy");
    }
  });
})();
