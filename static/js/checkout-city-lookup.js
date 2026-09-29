(() => {
  const postalInput = document.querySelector("[data-postal-code-input]");
  const cityInput = document.querySelector("[data-city-input]");

  if (!postalInput || !cityInput) {
    return;
  }

  const lookupUrl = postalInput.dataset.cityLookupUrl;
  const unsupportedMessage = postalInput.dataset.unsupportedMessage || "";
  const cityId = cityInput.id;

  const status = document.createElement("p");
  status.className = "form-help checkout-city-lookup__status";
  status.setAttribute("role", "status");
  status.setAttribute("aria-live", "polite");
  postalInput.closest(".form-field")?.append(status);

  let citySelect = null;
  let lastPostalCode = null;
  let controller = null;

  function removeCitySelect() {
    if (!citySelect) {
      return;
    }

    citySelect.tomselect?.destroy();
    citySelect.remove();
    citySelect = null;
  }

  function useTextInput() {
    removeCitySelect();

    cityInput.id = cityId;
    cityInput.hidden = false;
    cityInput.disabled = false;
    cityInput.readOnly = false;
  }

  function useSingleCity(city) {
    useTextInput();
    cityInput.value = city;
    cityInput.readOnly = true;
  }

  function useCityChoices(cities) {
    useTextInput();

    const current = cityInput.value;
    const selected = cities.includes(current) ? current : cities[0];

    citySelect = document.createElement("select");
    citySelect.name = cityInput.name;
    citySelect.required = true;
    citySelect.autocomplete = "address-level2";
    citySelect.dataset.enhancedSelect = "true";
    citySelect.dataset.enhancedSelectSearch = cities.length > 8 ? "true" : "false";

    cities.forEach((city) => {
      citySelect.add(new Option(city, city, false, city === selected));
    });

    cityInput.id = `${cityId}-text`;
    cityInput.hidden = true;
    cityInput.disabled = true;

    citySelect.id = cityId;
    cityInput.after(citySelect);

    window.enhanceSelects?.(citySelect.parentElement);
  }

  async function lookup() {
    const postalCode = postalInput.value.replace(/\s+/g, "");

    if (!/^\d{5}$/.test(postalCode)) {
      lastPostalCode = null;
      status.textContent = "";
      useTextInput();
      return;
    }

    if (postalCode === lastPostalCode) {
      return;
    }

    lastPostalCode = postalCode;
    controller?.abort();
    controller = new AbortController();

    try {
      const url = new URL(lookupUrl, window.location.origin);
      url.searchParams.set("postal_code", postalCode);

      const response = await fetch(url, {
        headers: {
          Accept: "application/json",
        },
        credentials: "same-origin",
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`City lookup failed: ${response.status}`);
      }

      const { cities } = await response.json();

      if (cities.length === 0) {
        useTextInput();
        status.textContent = unsupportedMessage;
        return;
      }

      status.textContent = "";

      if (cities.length === 1) {
        useSingleCity(cities[0]);
      } else {
        useCityChoices(cities);
      }
    } catch (error) {
      if (error.name !== "AbortError") {
        lastPostalCode = null;
        useTextInput();
      }
    }
  }

  postalInput.addEventListener("input", lookup);
  postalInput.addEventListener("change", lookup);

  lookup();
})();
