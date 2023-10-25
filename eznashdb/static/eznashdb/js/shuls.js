(function setCollapseAllListener() {
  const collapseAllButton = document.getElementById("collapse-all-shuls");
  const shulCollapseToggleButtons = Array.from(
    document.querySelectorAll(
      '[data-bs-toggle="collapse"][data-bs-target^="#shulCollapseHeader"]'
    )
  );
  const shulCollapses = Array.from(
    document.querySelectorAll('.collapse[id^="shulCollapsePanel"]')
  );

  function closeAll() {
    collapseAllButton.classList.add("collapsed");
    shulCollapseToggleButtons.forEach((btn) => {
      btn.classList.add("collapsed");
    });
    shulCollapses.forEach((collapse) => {
      if (collapse.classList.contains("show")) {
        bsCollapse = new bootstrap.Collapse(collapse);
        bsCollapse.hide();
      }
    });
  }

  function openAll() {
    collapseAllButton.classList.remove("collapsed");
    shulCollapseToggleButtons.forEach((btn) => {
      btn.classList.remove("collapsed");
    });
    shulCollapses.forEach((collapse) => {
      if (!collapse.classList.contains("show")) {
        bsCollapse = new bootstrap.Collapse(collapse);
        bsCollapse.show();
      }
    });
  }

  collapseAllButton?.addEventListener("click", (e) => {
    if (collapseAllButton.classList.contains("collapsed")) {
      openAll();
    } else {
      closeAll();
    }
  });
})();

(function setResultsFormatToggle() {
  const resultFormatToggles = Array.from(
    document.getElementsByClassName("js-results-format-toggle")
  );
  resultFormatToggles.forEach((btn) => {
    btn.addEventListener("click", () => {
      const format = btn.dataset["resultsFormat"];
      updateResultsFormat(format);
    });
  });

  function updateResultsFormat(format) {
    const currentURL = new URL(window.location.href);
    const currentFormat = currentURL.searchParams.get("format");
    if (format !== currentFormat) {
      currentURL.searchParams.set("format", format);
      history.pushState({}, "", currentURL);
      location.reload();
    }
  }
})();
