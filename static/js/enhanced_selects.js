(function () {
  function isTouchLikeDevice() {
    return (
      window.matchMedia("(pointer: coarse)").matches ||
      window.matchMedia("(hover: none)").matches
    );
  }

  function optionText(option) {
    return option.textContent.trim();
  }

  function optionSearchText(option) {
    return (
      option.getAttribute("search") ||
      option.dataset.search ||
      optionText(option)
    );
  }

  function buildOptionData(option) {
    return {
      value: option.value,
      text: optionText(option),
      code: option.dataset.code || "",
      name: option.dataset.name || "",
      weight: option.dataset.weight || "",
      offerDetail: option.dataset.offerDetail || "",
      image: option.dataset.image || "",
      price: option.dataset.price || "",
      stock: option.dataset.stock || "",
      search: optionSearchText(option),
    };
  }

  function buildOptions(select) {
    return Array.from(select.options).map(buildOptionData);
  }

  function buildItems(select) {
    return select.value ? [select.value] : [];
  }

  function hasProductData(data) {
    return Boolean(
      data.code ||
      data.name ||
      data.weight ||
      data.offerDetail
    );
  }

  function productTitle(data, escape) {
    const code = data.code || "";
    const name = data.name || data.text || "";

    if (code && name) {
      return `${escape(code)} · ${escape(name)}`;
    }

    return escape(code || name);
  }

  // A product option reads like a line of a cart: the picture circle
  // (an empty one when there is none, so the names line up), the name,
  // and under it the weight, the price (a shop's cart) and how many are
  // left, then the offer when it is not the standard one. The code stays
  // searchable but is not shown.
  function renderOption(data, escape) {
    if (!hasProductData(data)) {
      return `
        <div class="enhanced-select-option">
          ${escape(data.text)}
        </div>
      `;
    }

    const picture = data.image
      ? `<img class="enhanced-product-option__image" src="${escape(data.image)}" alt="" width="40" height="40" loading="lazy" decoding="async">`
      : `<span class="enhanced-product-option__image enhanced-product-option__image--empty" aria-hidden="true"></span>`;

    const meta = [
      data.weight,
      data.price,
      data.stock,
    ]
      .filter(Boolean)
      .map(escape)
      .join(" · ");

    const offer = data.offerDetail
      ? `<span class="enhanced-product-option__offer">${escape(data.offerDetail)}</span>`
      : "";

    return `
      <div class="enhanced-product-option">
        ${picture}

        <div class="enhanced-product-option__text">
          <div class="enhanced-product-option__main">
            ${escape(data.name || data.text)}
          </div>

          ${
            meta || offer
              ? `
                <div class="enhanced-product-option__meta">
                  ${meta}${meta && offer ? " · " : ""}${offer}
                </div>
              `
              : ""
          }
        </div>
      </div>
    `;
  }

  function renderItem(data, escape) {
    if (!hasProductData(data)) {
      return `<div>${escape(data.text)}</div>`;
    }

    const offerDetail = data.offerDetail
      ? ` · ${escape(data.offerDetail)}`
      : "";

    return `
      <div class="enhanced-product-selected">
        <span>
          ${productTitle(data, escape)}${offerDetail}
        </span>
      </div>
    `;
  }

  function enhanceSelects(root = document, options = {}) {
    if (!window.TomSelect) {
      return;
    }

    const shouldOpenAfterEnhance =
      options.openAfterEnhance === true;

    const selects = root.querySelectorAll(
      "select[data-enhanced-select]"
    );

    selects.forEach((select) => {
      if (select.tomselect) {
        return;
      }

      const hasSearch =
        select.dataset.enhancedSelectSearch !== "false";

      const tomSelect = new TomSelect(select, {
        options: buildOptions(select),
        items: buildItems(select),
        create: false,
        allowEmptyOption: true,
        closeAfterSelect: true,
        maxOptions: 500,
        placeholder:
          select.getAttribute("placeholder") || "",
        controlInput: hasSearch
          ? (
              '<input type="text" ' +
              'autocomplete="off" ' +
              'autocapitalize="none" ' +
              'spellcheck="false" />'
            )
          : null,
        searchField: ["search"],
        sortField: [
          {
            field: "$order",
            direction: "asc",
          },
        ],
        render: {
          option: renderOption,
          item: renderItem,
        },
      });

      tomSelect.wrapper.classList.add(
        hasSearch
          ? "enhanced-select--searchable"
          : "enhanced-select--static"
      );

      if (!shouldOpenAfterEnhance) {
        tomSelect.close();

        if (isTouchLikeDevice()) {
          tomSelect.blur();
        }
      }
    });
  }

  window.enhanceSelects = enhanceSelects;

  document.addEventListener(
    "DOMContentLoaded",
    () => {
      enhanceSelects();
    }
  );
})();
