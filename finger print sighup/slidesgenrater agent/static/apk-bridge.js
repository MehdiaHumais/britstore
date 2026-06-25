/**
 * ✅ SlideWiz APK Bridge
 * Handles routing and CORS for mobile devices.
 */
(function () {
  const originalFetch = window.fetch;

  function isMobile() {
    return (
      window.location.protocol === "capacitor:" || 
      window.location.hostname === "localhost" && !window.location.port ||
      !!window.Capacitor
    );
  }

  function getServerBase() {
    if (window.location.protocol === "http:" || window.location.protocol === "https:") {
      return window.location.origin;
    }
    // Fallback for APK - Update this to your PC's IP if testing locally
    return window.SLIDEWIZ_CONFIG?.API_URL || "http://localhost:5000";
  }

  window.fetch = async function (url, options = {}) {
    let finalUrl = url;
    const base = getServerBase();
    const mobile = isMobile();

    if (mobile && typeof url === "string" && !url.startsWith('http')) {
      const cleanPath = url.startsWith("/") ? url.slice(1) : url;
      finalUrl = `${base}/${cleanPath}`;
    }

    console.log(`📡 [APK Bridge] Routing: ${url} -> ${finalUrl}`);

    try {
      const res = await originalFetch(finalUrl, options);
      return res;
    } catch (err) {
      console.error("❌ [APK Bridge] NETWORK ERROR:", err);
      throw err;
    }
  };

  window.getServerBase = getServerBase;
})();
