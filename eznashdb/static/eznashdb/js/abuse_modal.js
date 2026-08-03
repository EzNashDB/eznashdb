(function () {
  let pendingRequestConfig = null;
  const container = () => document.getElementById("abuse-modal-container");
  const showAbuseModal = () => {
    const el = container().querySelector(".modal");
    if (el) bootstrap.Modal.getOrCreateInstance(el).show();
  };

  // Handle abuse-prevention 429/captcha responses (excluding e.g. infra-level 429 responses).
  document.body.addEventListener("htmx:beforeSwap", (e) => {
    const xhr = e.detail.xhr;
    const enforcementType = xhr && xhr.getResponseHeader("X-Abuse-Enforcement");

    if (enforcementType && xhr.status === 429) {
      // Override htmx's default 4xx error handling.
      e.detail.shouldSwap = true;
      e.detail.isError = false;
    }

    if (enforcementType === "captcha") {
      const rc = e.detail.requestConfig;
      pendingRequestConfig = { elt: rc.elt, verb: rc.verb, path: rc.path };
    }

    // A failed retry replaces the shown modal without hide() - dispose
    // its backdrop (success uses plain HX-Trigger, so it's excluded).
    if (xhr && xhr.getResponseHeader("HX-Trigger-After-Swap")) {
      const staleModal = container().querySelector(".modal");
      if (staleModal) {
        bootstrap.Modal.getInstance(staleModal)?.dispose();
        document.body.classList.remove("modal-open");
        document.body.style.removeProperty("padding-right");
        document.body.style.removeProperty("padding-left");
      }
    }
  });

  document.body.addEventListener("abuseBlocked", showAbuseModal);
  document.body.addEventListener("abuseCaptchaRequired", showAbuseModal);

  document.body.addEventListener("abuseCaptchaVerified", () => {
    const el = document.getElementById("abuse-captcha-modal");
    const next = el && el.dataset.next;
    const hasModal = !!el;
    const requestConfigSnapshot = pendingRequestConfig; // snapshot to use for modals after hidden.bs.modal event
    pendingRequestConfig = null;
    const proceed = () => {
      container().innerHTML = ""; // fresh reCAPTCHA markup next time it's needed
      if (
        requestConfigSnapshot &&
        requestConfigSnapshot.elt &&
        document.body.contains(requestConfigSnapshot.elt)
      ) {
        htmx.ajax(requestConfigSnapshot.verb, requestConfigSnapshot.path, {
          source: requestConfigSnapshot.elt,
        });
      } else if (next) {
        window.location = next;
      }
    };
    if (!hasModal) return proceed();
    el.addEventListener("hidden.bs.modal", proceed, { once: true });
    bootstrap.Modal.getOrCreateInstance(el).hide();
  });
})();
