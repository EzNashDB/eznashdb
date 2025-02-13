/*! leaflet-history 10-04-2017 */
!(function () {
  L.HistoryControl = L.Control.extend({
    options: {
      position: "topright",
      maxMovesToSave: 10,
      useExternalControls: !1,
      backImage: "fa fa-caret-left",
      backText: "",
      backTooltip: "Go to Previous Extent",
      backImageBeforeText: !0,
      forwardImage: "fa fa-caret-right",
      forwardText: "",
      forwardTooltip: "Go to Next Extent",
      forwardImageBeforeText: !1,
      orientation: "horizontal",
      shouldSaveMoveInHistory: function (a) {
        return !0;
      },
    },
    initialize: function (a) {
      L.Util.setOptions(this, a),
        (this._state.maxMovesToSave = this.options.maxMovesToSave);
    },
    onAdd: function (a) {
      this._map = a;
      var b = L.DomUtil.create(
        "div",
        "history-control leaflet-bar leaflet-control " +
          this.options.orientation
      );
      return (
        this.options.useExternalControls ||
          ((this._backButton = this._createButton(
            "back",
            b,
            this.goBack,
            this
          )),
          (this._forwardButton = this._createButton(
            "forward",
            b,
            this.goForward,
            this
          ))),
        this._updateDisabled(),
        this._addMapListeners(),
        b
      );
    },
    onRemove: function (a) {
      a.off("movestart");
    },
    performActionWithoutTriggeringEvent: function (a) {
      (this._state.ignoringEvents = !0), "function" == typeof a && a();
    },
    moveWithoutTriggeringEvent: function (a) {
      var b = this;
      this.performActionWithoutTriggeringEvent(function () {
        b._map.setView(a.centerPoint, a.zoom);
      });
    },
    goBack: function () {
      return this._invokeBackOrForward(
        "historyback",
        this._state.history,
        this._state.future
      );
    },
    goForward: function () {
      return this._invokeBackOrForward(
        "historyforward",
        this._state.future,
        this._state.history
      );
    },
    clearHistory: function () {
      (this._state.history.items = []), this._updateDisabled();
    },
    clearFuture: function () {
      (this._state.future.items = []), this._updateDisabled();
    },
    _map: null,
    _backButton: null,
    _forwardButton: null,
    _state: {
      backDisabled: null,
      forwardDisabled: null,
      ignoringEvents: !1,
      maxMovesToSave: 0,
      history: { items: [] },
      future: { items: [] },
    },
    _createButton: function (a, b, c, d) {
      var e = this.options[a + "Text"] || "",
        f = this.options[a + "Image"] || "",
        g = this.options[a + "Tooltip"] || "",
        h = L.DomUtil.create("a", "history-" + a + "-button", b);
      if (f) {
        var i = '<i class="' + f + '"></i>';
        this.options[a + "ImageBeforeText"]
          ? (e = i + " " + e)
          : (e += " " + i);
      }
      (h.innerHTML = e), (h.href = "#"), (h.title = g);
      var j = L.DomEvent.stopPropagation;
      return (
        L.DomEvent.on(h, "click", j)
          .on(h, "mousedown", j)
          .on(h, "dblclick", j)
          .on(h, "click", L.DomEvent.preventDefault)
          .on(h, "click", c, d)
          .on(h, "click", this._refocusOnMap, d),
        h
      );
    },
    _updateDisabled: function () {
      var a = 0 === this._state.history.items.length,
        b = 0 === this._state.future.items.length;
      a !== this._state.backDisabled &&
        ((this._state.backDisabled = a),
        this._map.fire("historyback" + (a ? "disabled" : "enabled"))),
        b !== this._state.forwardDisabled &&
          ((this._state.forwardDisabled = b),
          this._map.fire("historyforward" + (b ? "disabled" : "enabled"))),
        this.options.useExternalControls ||
          (this._setButtonDisabled(this._backButton, a),
          this._setButtonDisabled(this._forwardButton, b));
    },
    _setButtonDisabled: function (a, b) {
      var c = "leaflet-disabled";
      b ? L.DomUtil.addClass(a, c) : L.DomUtil.removeClass(a, c);
    },
    _pop: function (a) {
      return (
        (a = a.items),
        L.Util.isArray(a) && a.length > 0
          ? a.splice(a.length - 1, 1)[0]
          : void 0
      );
    },
    _push: function (a, b) {
      var c = this._state.maxMovesToSave;
      (a = a.items),
        L.Util.isArray(a) &&
          (a.push(b), c > 0 && a.length > c && a.splice(0, 1));
    },
    _invokeBackOrForward: function (a, b, c) {
      var d = this._popStackAndUseLocation(b, c);
      return d ? (this._map.fire(a, d), !0) : !1;
    },
    _popStackAndUseLocation: function (a, b) {
      if (L.Util.isArray(a.items) && a.items.length > 0) {
        var c = this._buildZoomCenterObjectFromCurrent(this._map),
          d = this._pop(a);
        return (
          this._push(b, c),
          this.moveWithoutTriggeringEvent(d),
          { previousLocation: d, currentLocation: c }
        );
      }
    },
    _buildZoomCenterObjectFromCurrent: function (a) {
      return new L.ZoomCenter(a.getZoom(), a.getCenter());
    },
    _addMapListeners: function () {
      var a = this;
      this._map.on("movestart", function (b) {
        if (a._state.ignoringEvents) a._state.ignoringEvents = !1;
        else {
          var c = a._buildZoomCenterObjectFromCurrent(b.target);
          a.options.shouldSaveMoveInHistory(c) &&
            ((a._state.future.items = []), a._push(a._state.history, c));
        }
        a._updateDisabled();
      });
    },
  });
})(),
  (function () {
    L.ZoomCenter = L.Class.extend({
      initialize: function (a, b) {
        (this.zoom = a), (this.centerPoint = b);
      },
    });
  })();
