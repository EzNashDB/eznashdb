class ShadowScrollInitializer {
  constructor(wrapperEl) {
    this.isScrollable = false;
    this.parentEl = wrapperEl;
    this.scrollBox = this.parentEl.querySelector(".shadow-scroll__scroll-box");
    this.content = this.parentEl.querySelector(".shadow-scroll__content");
    this.shadowWrapper = this.parentEl.querySelector(
      ".shadow-scroll__shadow-wrapper"
    );
  }

  initialize() {
    this.setVisibility();
    this.listenForResize();
  }

  setVisibility() {
    const isOverflowing =
      this.content.offsetHeight > this.parentEl.offsetHeight;
    if (this.isScrollable !== isOverflowing) {
      const activeElement = document.activeElement;
      isOverflowing ? this.show() : this.hide();
      activeElement.focus();
    }
  }

  show() {
    this.shadowWrapper.style.display = "block";
    this.shadowWrapper.style.borderWidth = "var(--bs-border-width)";
    this.scrollBox.appendChild(this.content);
    this.isScrollable = true;
  }

  hide() {
    this.shadowWrapper.style.display = "none";
    this.shadowWrapper.style.borderWidth = "0";
    this.parentEl.appendChild(this.content);
    this.isScrollable = false;
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
