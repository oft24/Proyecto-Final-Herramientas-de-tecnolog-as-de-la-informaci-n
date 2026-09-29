(() => {
  "use strict";

  const root = document.documentElement;
  const width = window.innerWidth;
  const compact = width <= 1100;
  const coarsePointer = window.matchMedia("(pointer: coarse)").matches;
  const phone = width <= 960;
  const lightweight = phone || (coarsePointer && compact);

  root.dataset.device = phone ? "mobile" : compact ? "tablet" : "desktop";
  root.classList.toggle("is-mobile-device", lightweight);
})();
