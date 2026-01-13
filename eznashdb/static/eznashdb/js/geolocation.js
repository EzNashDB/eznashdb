/**
 * Geolocation utility for getting user's current position.
 * Used by both React components and vanilla JS.
 */
window.GeolocationUtils = (() => {
  const DEFAULT_OPTIONS = {
    enableHighAccuracy: false,
    timeout: 10000,
    maximumAge: 300000,
  };

  /**
   * Get the user's current geolocation.
   * @param {Object} options
   * @param {function} options.onSuccess - Called with {latitude, longitude}
   * @param {function} options.onError - Called with error message string (optional)
   * @param {number} options.timeout - Timeout in ms (default 10000)
   * @param {boolean} options.enableHighAccuracy - Use high accuracy (default false)
   * @param {number} options.maximumAge - Max age of cached position in ms (default 300000)
   */
  const getCurrentPosition = (options = {}) => {
    const { onSuccess, onError } = options;

    if (!navigator.geolocation) {
      const msg = "Geolocation is not supported by your browser";
      if (onError) onError(msg);
      else alert(msg);
      return;
    }

    if (!window.isSecureContext) {
      const msg = "Location requires a secure connection (HTTPS)";
      if (onError) onError(msg);
      else alert(msg);
      return;
    }

    const geolocationOptions = {
      enableHighAccuracy:
        options.enableHighAccuracy ?? DEFAULT_OPTIONS.enableHighAccuracy,
      timeout: options.timeout ?? DEFAULT_OPTIONS.timeout,
      maximumAge: options.maximumAge ?? DEFAULT_OPTIONS.maximumAge,
    };

    navigator.geolocation.getCurrentPosition(
      (position) => {
        if (onSuccess) {
          onSuccess({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy,
          });
        }
      },
      (error) => {
        let message;
        switch (error.code) {
          case error.PERMISSION_DENIED:
            message =
              "Location access was denied. Check your browser's site settings to enable location.";
            break;
          case error.POSITION_UNAVAILABLE:
            message = "Location information is unavailable. Please try again.";
            break;
          case error.TIMEOUT:
            message = "Location request timed out. Please try again.";
            break;
          default:
            message = "Unable to retrieve your location.";
        }
        if (onError) onError(message);
        else alert(message);
      },
      geolocationOptions
    );
  };

  return {
    getCurrentPosition,
  };
})();
