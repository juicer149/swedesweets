(() => {
  const groups = document.querySelectorAll(
    "[data-tabs]"
  );

  for (const group of groups) {
    initializeTabs(group);
  }

  function initializeTabs(group) {
    // A group's own tabs and panels, not those of a group inside one of
    // its panels (the language tabs in the Shop text tab, say).
    const ownedByGroup = (element) => (
      element.closest("[data-tabs]") === group
    );

    const tabs = [
      ...group.querySelectorAll(
        "[data-tab]"
      ),
    ].filter(ownedByGroup);

    const panels = [
      ...group.querySelectorAll(
        "[data-tab-panel]"
      ),
    ].filter(ownedByGroup);

    // Actions at the nav's right (page_tabs.html): each shown while its
    // tab is open.
    const actions = [
      ...group.querySelectorAll(
        "[data-tab-action]"
      ),
    ].filter(ownedByGroup);

    if (
      tabs.length === 0
      || panels.length === 0
    ) {
      return;
    }

    function activateTab(
      tabKey,
      { focus = false } = {}
    ) {
      for (const tab of tabs) {
        const isActive =
          tab.dataset.tab === tabKey;

        tab.classList.toggle(
          "section-nav__link--active",
          isActive
        );

        tab.setAttribute(
          "aria-selected",
          String(isActive)
        );

        tab.tabIndex = isActive ? 0 : -1;

        if (isActive && focus) {
          tab.focus();
        }
      }

      for (const panel of panels) {
        const isActive =
          panel.dataset.tabPanel === tabKey;

        panel.hidden = !isActive;
      }

      for (const action of actions) {
        action.hidden =
          action.dataset.tabAction !== tabKey;
      }
    }

    function panelContainsErrors(panel) {
      return Boolean(
        panel.querySelector(
          ".form-field--error, .form-errors"
        )
      );
    }

    function initialTabKey() {
      const panelWithErrors = panels.find(
        panelContainsErrors
      );

      if (panelWithErrors) {
        return panelWithErrors.dataset.tabPanel;
      }

      // A link can open a tab: /products/7/edit/#pricing.
      const hashKey = window.location.hash.slice(1);

      if (tabs.some((tab) => tab.dataset.tab === hashKey)) {
        return hashKey;
      }

      const selectedTab = tabs.find(
        (tab) => (
          tab.getAttribute("aria-selected")
          === "true"
        )
      );

      return (
        selectedTab?.dataset.tab
        ?? tabs[0].dataset.tab
      );
    }

    function moveFocus(
      currentTab,
      eventKey
    ) {
      const currentIndex =
        tabs.indexOf(currentTab);

      let nextIndex = currentIndex;

      if (eventKey === "ArrowRight") {
        nextIndex =
          (currentIndex + 1)
          % tabs.length;
      }

      if (eventKey === "ArrowLeft") {
        nextIndex =
          (
            currentIndex
            - 1
            + tabs.length
          )
          % tabs.length;
      }

      if (eventKey === "Home") {
        nextIndex = 0;
      }

      if (eventKey === "End") {
        nextIndex =
          tabs.length - 1;
      }

      activateTab(
        tabs[nextIndex].dataset.tab,
        {
          focus: true,
        }
      );
    }

    for (const tab of tabs) {
      tab.addEventListener(
        "click",
        () => {
          activateTab(
            tab.dataset.tab
          );
        }
      );

      tab.addEventListener(
        "keydown",
        (event) => {
          const supportedKeys = [
            "ArrowLeft",
            "ArrowRight",
            "Home",
            "End",
          ];

          if (
            !supportedKeys.includes(
              event.key
            )
          ) {
            return;
          }

          event.preventDefault();

          moveFocus(
            tab,
            event.key
          );
        }
      );
    }

    activateTab(
      initialTabKey()
    );
  }
})();
