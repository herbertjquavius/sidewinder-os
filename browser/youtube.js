// Radar on YouTube: hide ad slots, rush through video ads, skip sponsored Shorts
(function () {
  if (window.__radarYT) return;
  window.__radarYT = true;

  // Hide ad boxes in the feed, sidebar and player
  const style = document.createElement("style");
  style.textContent = [
    "ytd-ad-slot-renderer", "ytd-in-feed-ad-layout-renderer", "ytd-promoted-sparkles-web-renderer",
    "ytd-display-ad-renderer", "ytd-banner-promo-renderer", "ytd-statement-banner-renderer",
    "#player-ads", "#masthead-ad", ".ytp-ad-overlay-container", "ytd-merch-shelf-renderer",
    "ytd-reel-video-renderer:has(ytd-ad-slot-renderer)"
  ].join(",") + "{display:none !important}";
  (document.head || document.documentElement).appendChild(style);

  setInterval(function () {
    // Video ads: mute, jump to the end, press skip
    const player = document.querySelector(".html5-video-player");
    if (player && player.classList.contains("ad-showing")) {
      const v = player.querySelector("video");
      if (v) {
        v.muted = true;
        v.playbackRate = 16;
        if (isFinite(v.duration)) v.currentTime = v.duration;
      }
      document.querySelectorAll(".ytp-skip-ad-button, .ytp-ad-skip-button, .ytp-ad-skip-button-modern")
        .forEach(function (b) { b.click(); });
    }
    // Shorts: if the one on screen is an ad, move to the next one
    if (location.pathname.startsWith("/shorts")) {
      const active = document.querySelector("ytd-reel-video-renderer[is-active]");
      if (active && (active.querySelector("ytd-ad-slot-renderer, ad-badge-view-model, .ad-badge") ||
                     /\bSponsored\b/.test(active.innerText || ""))) {
        document.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowDown", code: "ArrowDown", keyCode: 40, bubbles: true }));
      }
    }
  }, 300);

  // Auto-scroll for Shorts mode: go to the next one when this one is almost over
  window.__radarAutoScroll = false;
  setInterval(function () {
    if (!window.__radarAutoScroll || !location.pathname.startsWith("/shorts")) return;
    const v = document.querySelector("ytd-reel-video-renderer[is-active] video");
    if (v && isFinite(v.duration) && v.duration > 0 && v.currentTime > v.duration - 0.4) {
      document.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowDown", code: "ArrowDown", keyCode: 40, bubbles: true }));
    }
  }, 200);
})();
