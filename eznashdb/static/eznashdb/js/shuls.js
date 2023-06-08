(function setCollapseAllListener() {
  const collapseAllButton = document.getElementById("collapse-all-shuls");
  const shulCollapseToggleButtons = Array.from(
    document.querySelectorAll(
      '[data-bs-toggle="collapse"][data-bs-target^="#collapseShul"]'
    )
  );
  const shulCollapses = Array.from(
    document.querySelectorAll('.collapse[id^="collapseShul"]')
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

  collapseAllButton.addEventListener("click", (e) => {
    if (collapseAllButton.classList.contains("collapsed")) {
      openAll();
    } else {
      closeAll();
    }
  });
})();
