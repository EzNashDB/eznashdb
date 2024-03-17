const calculateScrollPercentage = (element) => {
  // Calculate the scrollable height of the element
  const scrollableHeight = element.scrollHeight - element.clientHeight;
  if (scrollableHeight === 0) {
    return 0;
  }
  const scrollPercentage = (element.scrollTop / scrollableHeight) * 100;
  return scrollPercentage / 100;
};

class ScrollShadowInitializer {
  constructor(wrapperEl) {
    this.wrapperEl = wrapperEl;
    this.content = this.wrapperEl.querySelector(".scroll-content");
    this.shadowTop = this.wrapperEl.querySelector(".scroll-shadow--top");
    this.shadowBottom = this.wrapperEl.querySelector(".scroll-shadow--bottom");
  }

  initialize() {
    this.setVisibility();
    this.listenForScroll();
    this.listenForResize();
  }

  setVisibility() {
    const hasVerticalScrollbar =
      this.content.scrollHeight > this.content.clientHeight;
    hasVerticalScrollbar ? this.show() : this.hide();
  }

  show() {
    [this.shadowBottom, this.shadowTop].forEach((el) => {
      el.style.display = "block";
    });
  }

  hide() {
    [this.shadowBottom, this.shadowTop].forEach((el) => {
      el.style.display = "none";
    });
  }

  listenForScroll() {
    this.content.addEventListener("scroll", (e) => {
      const scrollPercentage = calculateScrollPercentage(this.content);
      this.shadowTop.style.opacity = scrollPercentage;
      this.shadowBottom.style.opacity = 1 - scrollPercentage;
    });
  }
  listenForResize() {
    const resizeObserver = new ResizeObserver((entries) => {
      this.setVisibility();
    });
    resizeObserver.observe(this.wrapperEl);
  }
}

export default function initializeScrollShadows() {
  Array.from(document.getElementsByClassName("scroll-shadow-wrapper")).forEach(
    (el) => new ScrollShadowInitializer(el).initialize()
  );
}