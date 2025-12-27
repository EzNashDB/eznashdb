/**
 * Scrolls an element into view within its nearest scrollable container only,
 * without scrolling the page or other ancestor containers.
 *
 * @param {HTMLElement} element - The element to scroll into view
 * @param {Object} options - Scroll options
 * @param {string} options.behavior - 'smooth' or 'auto' (default: 'smooth')
 * @param {string} options.block - 'start', 'center', 'end', or 'nearest' (default: 'start')
 * @param {number} options.offset - Additional offset in pixels (default: 0)
 */
function scrollIntoViewWithinContainer(element, options = {}) {
  const { behavior = "smooth", block = "start", offset = 0 } = options;

  // Find the nearest scrollable container by checking computed styles
  let scrollContainer = null;
  let parent = element.parentElement;

  while (parent) {
    const style = window.getComputedStyle(parent);
    if (
      style.overflowY === "auto" ||
      style.overflowY === "scroll" ||
      style.overflow === "auto" ||
      style.overflow === "scroll"
    ) {
      scrollContainer = parent;
      break;
    }
    parent = parent.parentElement;
  }

  if (!scrollContainer) {
    // No scrollable container found, fall back to regular scrollIntoView
    element.scrollIntoView({ behavior, block });
    return;
  }

  const containerRect = scrollContainer.getBoundingClientRect();
  const elementRect = element.getBoundingClientRect();

  // Calculate position relative to scroll container
  const relativeTop = elementRect.top - containerRect.top;
  const relativeBottom = elementRect.bottom - containerRect.bottom;

  let scrollTarget;

  switch (block) {
    case "start":
      scrollTarget = scrollContainer.scrollTop + relativeTop - offset;
      break;
    case "center":
      const containerHeight = containerRect.height;
      const elementHeight = elementRect.height;
      scrollTarget =
        scrollContainer.scrollTop +
        relativeTop -
        containerHeight / 2 +
        elementHeight / 2 -
        offset;
      break;
    case "end":
      scrollTarget = scrollContainer.scrollTop + relativeBottom + offset;
      break;
    case "nearest":
      // Only scroll if element is not fully visible
      if (relativeTop < 0) {
        scrollTarget = scrollContainer.scrollTop + relativeTop - offset;
      } else if (relativeBottom > 0) {
        scrollTarget = scrollContainer.scrollTop + relativeBottom + offset;
      } else {
        return; // Already in view, no need to scroll
      }
      break;
    default:
      scrollTarget = scrollContainer.scrollTop + relativeTop - offset;
  }

  scrollContainer.scrollTo({
    top: scrollTarget,
    behavior: behavior,
  });
}
