const calculateScrollPercentage = (element) => {
  // Calculate the scrollable height of the element
  const scrollableHeight = element.scrollHeight - element.clientHeight;
  if (scrollableHeight === 0) {
    return 0;
  }
  const scrollPercentage = (element.scrollTop / scrollableHeight) * 100;
  return scrollPercentage / 100;
};

class ShadowScrollInitializer {
  constructor(wrapperEl) {
    this.wrapperEl = wrapperEl;
    this.scrollBox = this.wrapperEl.querySelector(".shadow-scroll__scroll-box");
    this.content = this.wrapperEl.querySelector(".shadow-scroll__content");
    this.shadowWrapper = this.wrapperEl.querySelector(
      ".shadow-scroll__shadow-wrapper"
    );
    this.shadowTop = this.wrapperEl.querySelector(".shadow-scroll__top");
    this.shadowBottom = this.wrapperEl.querySelector(".shadow-scroll__bottom");
  }

  initialize() {
    this.setVisibility();
    this.listenForScroll();
    this.listenForResize();
  }

  setVisibility() {
    const isOverflowing =
      this.content.offsetHeight > this.wrapperEl.offsetHeight;
    isOverflowing ? this.show() : this.hide();
  }

  setShadows() {
    const scrollPercentage = calculateScrollPercentage(this.scrollBox);
    this.shadowTop.style.opacity = scrollPercentage;
    this.shadowBottom.style.opacity = 1 - scrollPercentage;
  }

  show() {
    [this.shadowBottom, this.shadowTop, this.shadowWrapper].forEach((el) => {
      el.style.display = "block";
    });
    this.shadowWrapper.style.borderWidth = "var(--bs-border-width)";
    this.scrollBox.appendChild(this.content);
  }

  hide() {
    [this.shadowBottom, this.shadowTop, this.shadowWrapper].forEach((el) => {
      el.style.display = "none";
    });
    this.shadowWrapper.style.borderWidth = "0";
    this.wrapperEl.appendChild(this.content);
  }

  listenForScroll() {
    this.scrollBox.addEventListener("scroll", (e) => this.setShadows());
  }

  listenForResize() {
    const resizeObserver = new ResizeObserver((entries) =>
      this.setVisibility()
    );
    [
      this.wrapperEl,
      this.content,
      ...Array.from(this.scrollBox.children),
    ].forEach((el) => {
      resizeObserver.observe(el);
    });
  }
}

export default function initializeShadowScrolls() {
  Array.from(document.getElementsByClassName("shadow-scroll")).forEach((el) =>
    new ShadowScrollInitializer(el).initialize()
  );
}
