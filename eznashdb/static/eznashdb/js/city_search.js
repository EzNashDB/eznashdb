// Alpine component for the homepage map's "search by city" box.
// Defined globally (not via alpine:init) because Alpine starts on DOMContentLoaded,
// after this script has already run.
window.citySearch = () => {
  const MIN_QUERY_LENGTH = 3;
  const DEBOUNCE_MS = 300;
  const REGION_ZOOM = 9; // metro scale

  return {
    query: "",
    results: [],
    isOpen: false,
    status: null, // null | "empty" | "error"
    activeIndex: -1,
    // False from the moment the query changes until results for it arrive, so Enter can't
    // select a city from the previous query's results
    resultsAreCurrent: false,
    _timer: null,
    _controller: null,

    init() {
      // Keep interactions with the box from reaching the map (panning, zooming, and closing
      // an open shul popup). Leaflet's helpers, like the zoom buttons use, flag the element
      // instead of stopping the click, so other document-level click handlers, like a
      // Bootstrap dropdown closing when you click elsewhere, still see it.
      if (window.L) {
        L.DomEvent.disableClickPropagation(this.$root);
        L.DomEvent.disableScrollPropagation(this.$root);
      }
    },

    // Read out by the screen-reader-only live region, for the states that have no option to announce
    get announcement() {
      if (!this.isOpen) return "";
      if (this.status === "empty") return this.$root.dataset.emptyMessage;
      if (this.status === "error") return this.$root.dataset.errorMessage;
      return "";
    },

    onInput() {
      clearTimeout(this._timer);
      this._controller?.abort();
      this.activeIndex = -1;
      this.resultsAreCurrent = false;
      if (this.query.trim().length < MIN_QUERY_LENGTH) {
        this.results = [];
        this.status = null;
        this.isOpen = false;
        return;
      }
      this._timer = setTimeout(() => this.search(), DEBOUNCE_MS);
    },

    async search() {
      const controller = new AbortController();
      this._controller = controller;
      const url = `${this.$root.dataset.url}?q=${encodeURIComponent(
        this.query.trim()
      )}`;
      try {
        const response = await fetch(url, { signal: controller.signal });
        if (!response.ok)
          throw new Error(`City lookup failed: ${response.status}`);
        const { results } = await response.json();
        this.results = results;
        this.status = results.length ? null : "empty";
      } catch (error) {
        if (error.name === "AbortError") return; // superseded by a newer query
        console.error(error);
        this.results = [];
        this.status = "error";
      }
      this.resultsAreCurrent = true;
      this.isOpen = true;
    },

    clear() {
      clearTimeout(this._timer);
      this._controller?.abort();
      this.query = "";
      this.results = [];
      this.status = null;
      this.activeIndex = -1;
      this.resultsAreCurrent = false;
      this.isOpen = false;
      this.$refs.input.focus();
    },

    move(step) {
      if (!this.results.length) return;
      this.isOpen = true;
      const count = this.results.length;
      // With nothing highlighted (-1), ArrowUp should wrap to the last row; going from -1
      // would land on the second-to-last
      const from = this.activeIndex === -1 && step < 0 ? 0 : this.activeIndex;
      this.activeIndex = (from + step + count) % count;
      this.$nextTick(() =>
        this.$refs.list
          .querySelector(".active")
          ?.scrollIntoView({ block: "nearest" })
      );
    },

    selectActive() {
      if (!this.isOpen || !this.resultsAreCurrent) return;
      const city = this.results[this.activeIndex] ?? this.results[0];
      if (city) this.select(city);
    },

    select(city) {
      clearTimeout(this._timer);
      this._controller?.abort();
      this.query = city.display_name;
      this.isOpen = false;
      this.$refs.input.blur();
      const map = window.SHUL_MAP_API?.map;
      if (city.bounds) {
        map?.fitBounds(city.bounds, { padding: [20, 20] });
      } else {
        // Regions (e.g. Tokyo) have no usable bounds - see OSMClient.search_cities
        map?.setView([city.lat, city.lon], REGION_ZOOM);
      }
    },
  };
};
