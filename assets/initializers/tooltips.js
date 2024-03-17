export default function initializeTooltips() {
  const tooltipTriggerList = document.querySelectorAll(
    '[data-bs-toggle="tooltip"]'
  );
  Array.from(tooltipTriggerList).map((tooltipTriggerEl) => {
    const isInitialized = tooltipTriggerEl.attributes["aria-describedby"];
    if (!isInitialized) {
      new bootstrap.Tooltip(tooltipTriggerEl);
    }
  });
}
