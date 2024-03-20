class ShadowScrollInitializer {
  constructor(wrapperEl) {
    this.parentEl = wrapperEl;
    this.scrollBox = this.parentEl.querySelector(".shadow-scroll__scroll-box");
    this.content = this.parentEl.querySelector(".shadow-scroll__content");
    this.shadowWrapper = this.parentEl.querySelector(
      ".shadow-scroll__shadow-wrapper"
    );
    this.shadowTop = this.parentEl.querySelector(".shadow-scroll__top-shadow");
    this.shadowBottom = this.parentEl.querySelector(
      ".shadow-scroll__bottom-shadow"
    );
  }

  initialize() {
    this.setVisibility();
    this.listenForScroll();
    this.listenForResize();
  }

  setVisibility() {
    const isOverflowing =
      this.content.offsetHeight > this.parentEl.offsetHeight;
    isOverflowing ? this.show() : this.hide();
  }

  setShadows() {
    const scrollPercentage = this.calculateScrollPercentage(this.scrollBox);
    this.shadowTop.style.opacity = scrollPercentage;
    this.shadowBottom.style.opacity = 1 - scrollPercentage;
  }

  calculateScrollPercentage(element) {
    const scrollableHeight = element.scrollHeight - element.clientHeight;
    if (scrollableHeight === 0) return 0;
    const scrollPercentage = (element.scrollTop / scrollableHeight) * 100;
    return scrollPercentage / 100;
  }

  show() {
    this.setShadows();
    this.shadowWrapper.style.display = "block";
    this.shadowWrapper.style.borderWidth = "var(--bs-border-width)";
    this.scrollBox.appendChild(this.content);
  }

  hide() {
    this.shadowWrapper.style.display = "none";
    this.shadowWrapper.style.borderWidth = "0";
    this.parentEl.appendChild(this.content);
  }

  listenForScroll() {
    this.scrollBox.addEventListener("scroll", (e) => this.setShadows());
  }

  listenForResize() {
    const observer = new ResizeObserver((entries) => this.setVisibility());
    [this.parentEl, this.content].forEach((el) => observer.observe(el));
  }
}

export default function initializeShadowScrolls() {
  Array.from(document.getElementsByClassName("shadow-scroll")).forEach((el) =>
    new ShadowScrollInitializer(el).initialize()
  );
}
