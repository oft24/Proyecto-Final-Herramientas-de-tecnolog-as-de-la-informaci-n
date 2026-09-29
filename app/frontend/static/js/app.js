(() => {
  "use strict";

  const productData = document.querySelector("#product-data");
  if (!productData) return;

  const i18n = window.BuldakI18n;
  if (!i18n?.locales) return;
  const payload = JSON.parse(productData.textContent);
  const featuredProducts = payload.featured;
  const catalogProducts = payload.catalog;
  const catalogById = new Map(catalogProducts.map((product) => [String(product.id), product]));
  const carouselProducts = (payload.carousel_ids || [])
    .map((id) => catalogById.get(String(id)))
    .filter(Boolean);
  if (!carouselProducts.length) carouselProducts.push(...catalogProducts);
  const root = document.documentElement;
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const phoneViewport = window.matchMedia("(max-width: 960px)");
  const compactViewport = window.matchMedia("(max-width: 1100px)");
  const coarsePointer = window.matchMedia("(pointer: coarse)");
  let mobileMode = root.classList.contains("is-mobile-device");

  function syncDevicePresentation() {
    const phone = phoneViewport.matches;
    const lightweight = phone || (coarsePointer.matches && compactViewport.matches);
    const device = phone ? "mobile" : compactViewport.matches ? "tablet" : "desktop";
    const changed = mobileMode !== lightweight || root.dataset.device !== device;

    mobileMode = lightweight;
    root.dataset.device = device;
    root.classList.toggle("is-mobile-device", lightweight);
    return changed;
  }

  syncDevicePresentation();

  function revealLoadedImage(image) {
    image.classList.add("is-loaded");
  }

  function activateDeferredImage(image) {
    const sourceUrl = image.dataset.deferredSrc;
    if (!sourceUrl) return;
    image.closest("picture")?.querySelectorAll("source[data-deferred-srcset]").forEach((source) => {
      source.srcset = source.dataset.deferredSrcset;
      delete source.dataset.deferredSrcset;
    });
    image.addEventListener("load", () => revealLoadedImage(image), { once: true });
    image.src = sourceUrl;
    delete image.dataset.deferredSrc;
    if (image.complete) revealLoadedImage(image);
  }

  function activateCarouselImage(card, priority = "low") {
    const image = card?.querySelector("img");
    if (!image) return;
    image.fetchPriority = priority;
    card.querySelectorAll("source[data-carousel-srcset]").forEach((source) => {
      source.srcset = source.dataset.carouselSrcset;
      delete source.dataset.carouselSrcset;
    });
    const sourceUrl = image.dataset.carouselSrc;
    if (!sourceUrl) return;
    image.src = sourceUrl;
    delete image.dataset.carouselSrc;
  }

  function preloadCarouselWindow(cards, selectedIndex) {
    const connection = navigator.connection;
    const conserveData = connection?.saveData || /(?:^|-)2g$/.test(connection?.effectiveType || "");
    const radius = conserveData ? 1 : mobileMode ? 2 : 3;
    const count = cards.length;
    if (!count) return;
    for (let offset = -radius; offset <= radius; offset += 1) {
      const index = modulo(selectedIndex + offset, count);
      activateCarouselImage(cards[index], offset === 0 ? "high" : "low");
    }
  }

  const deferredImages = [...document.querySelectorAll("img[data-deferred-src]")];
  if ("IntersectionObserver" in window) {
    const imageObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        activateDeferredImage(entry.target);
        observer.unobserve(entry.target);
      });
    }, { rootMargin: "520px 0px" });
    deferredImages.forEach((image) => imageObserver.observe(image));
  } else {
    deferredImages.forEach(activateDeferredImage);
  }
  const catalogThemes = Object.freeze({
    "811140": { bgA: "#f5d9e1", bgB: "#fff8f4", glow: "#ffc1d2", ink: "#2b171e", accent: "#b3123f" },
    "811130": { bgA: "#e9f3f5", bgB: "#fff7f8", glow: "#f6cadb", ink: "#251b20", accent: "#cf527b" },
    "811200": { bgA: "#f6cf42", bgB: "#fff3b8", glow: "#ffe36a", ink: "#2c2110", accent: "#ce4b17" },
    "811150": { bgA: "#ee8a24", bgB: "#ffd27b", glow: "#ffb53c", ink: "#2b170e", accent: "#a51c19" },
    "811270": { bgA: "#f2b6c4", bgB: "#ffe9ed", glow: "#ff92ae", ink: "#351921", accent: "#b72453" },
    "811320": { bgA: "#d9c0ef", bgB: "#f7eafb", glow: "#d997e7", ink: "#2d1b35", accent: "#9e2878" },
    "811000": { bgA: "#e95a17", bgB: "#ffb248", glow: "#ff7d26", ink: "#2a130b", accent: "#8e1a13" },
    "811340": { bgA: "#4b2418", bgB: "#9b4f2d", glow: "#d05a2f", ink: "#fff4ed", accent: "#ff7a35" },
    "811220": { bgA: "#4f8a2f", bgB: "#dbe75a", glow: "#b7df44", ink: "#14240f", accent: "#df481a" },
    "811120": { bgA: "#1e1413", bgB: "#5c271d", glow: "#d94620", ink: "#fff4ef", accent: "#ff572e" },
    "811210": { bgA: "#220f10", bgB: "#8d121c", glow: "#f02b2b", ink: "#fff4f0", accent: "#ff493d" },
    "811616": { bgA: "#d9c0ef", bgB: "#f7eafb", glow: "#d997e7", ink: "#2d1b35", accent: "#9e2878" },
    "811618": { bgA: "#ee8a24", bgB: "#ffd27b", glow: "#ffb53c", ink: "#2b170e", accent: "#a51c19" },
    "811622": { bgA: "#f5d9e1", bgB: "#fff8f4", glow: "#ffc1d2", ink: "#2b171e", accent: "#b3123f" },
    "811624": { bgA: "#1e1413", bgB: "#5c271d", glow: "#d94620", ink: "#fff4ef", accent: "#ff572e" },
    "811640": { bgA: "#f2b6c4", bgB: "#ffe9ed", glow: "#ff92ae", ink: "#351921", accent: "#b72453" },
    "811650": { bgA: "#e7c9e9", bgB: "#fceff5", glow: "#eca9d5", ink: "#311b30", accent: "#a83172" },
    "811612": { bgA: "#1e1413", bgB: "#5c271d", glow: "#d94620", ink: "#fff4ef", accent: "#ff572e" },
    "811710": { bgA: "#f5d9e1", bgB: "#fff8f4", glow: "#ffc1d2", ink: "#2b171e", accent: "#b3123f" },
    "811720": { bgA: "#1e1413", bgB: "#5c271d", glow: "#d94620", ink: "#fff4ef", accent: "#ff572e" },
    "811910": { bgA: "#6e8f31", bgB: "#d3dc59", glow: "#b8d347", ink: "#17220e", accent: "#df481a" },
    "811920": { bgA: "#b51f25", bgB: "#ff7950", glow: "#ed3c2e", ink: "#fff8f2", accent: "#ffd15c" }
  });
  const featuredById = new Map(featuredProducts.map((product) => [String(product.id), product]));
  const products = carouselProducts.map((catalogProduct, index) => ({
    number: String(index + 1).padStart(2, "0"),
    description: "",
    heat: 0,
    heat_label: "—",
    ...catalogProduct,
    ...(featuredById.get(String(catalogProduct.id)) || {}),
    id: String(catalogProduct.id),
    sku: String(catalogProduct.sku)
  }));
  const productById = new Map(products.map((product) => [product.id, product]));
  const initialProductIndex = Math.max(0, products.findIndex((product) => product.id === "811140"));

  const drinkProducts = (payload.refrescos || []).map((product, index) => ({
    number: String(index + 1).padStart(2, "0"),
    description: "",
    ...product,
    id: String(product.id),
    sku: String(product.sku)
  }));
  drinkProducts.forEach((product) => productById.set(product.id, product));

  const dom = {
    header: document.querySelector("[data-header]"),
    carousel: document.querySelector("[data-carousel]"),
    cards: [...document.querySelectorAll("[data-card]")],
    tabs: [...document.querySelectorAll("[data-select]")],
    lines: [...document.querySelectorAll("[data-flavor-line]")],
    productType: document.querySelector("[data-product-type]"),
    number: document.querySelector("[data-number]"),
    sku: document.querySelector("[data-sku]"),
    name: document.querySelector("[data-name]"),
    description: document.querySelector("[data-description]"),
    price: document.querySelector("[data-price]"),
    unitPrice: document.querySelector("[data-unit-price]"),
    weight: document.querySelector("[data-weight]"),
    heroHeat: document.querySelector("[data-hero-heat]"),
    heatFill: document.querySelector("[data-heat-fill]"),
    heatLabel: document.querySelector("[data-heat-label]"),
    heroSweetness: document.querySelector("[data-hero-sweetness]"),
    sweetnessFill: document.querySelector("[data-sweetness-fill]"),
    sweetnessLabel: document.querySelector("[data-sweetness-label]"),
    heroKcal: document.querySelector("[data-hero-kcal]"),
    heroKcalBasis: document.querySelector("[data-hero-kcal-basis]"),
    quantity: document.querySelector("[data-quantity]"),
    addSelected: document.querySelector("[data-add-selected]"),
    storyTitle: document.querySelector("[data-story-title]"),
    storySection: document.querySelector("[data-story-section]"),
    storyCopy: document.querySelector("[data-story-copy]"),
    storyImage: document.querySelector("[data-story-image]"),
    storyHeatStat: document.querySelector("[data-story-heat-stat]"),
    storyHeatStatLabel: document.querySelector("[data-story-heat-stat-label]"),
    storySweetnessStat: document.querySelector("[data-story-sweetness-stat]"),
    storySweetness: document.querySelector("[data-story-sweetness]"),
    storyCookStat: document.querySelector("[data-story-cook-stat]"),
    shu: document.querySelector("[data-shu]"),
    kcal: document.querySelector("[data-kcal]"),
    storyKcalBasis: document.querySelector("[data-story-kcal-basis]"),
    cookTime: document.querySelector("[data-cook-time]"),
    storyWeight: document.querySelector("[data-story-weight]"),
    storyNote: document.querySelector("[data-story-note]"),
    nutritionSource: document.querySelector("[data-nutrition-source]"),
    ritualSection: document.querySelector("#ritual"),
    preparedSection: document.querySelector("#prepared"),
    directionsTitle: document.querySelector("[data-directions-title]"),
    directionsIntro: document.querySelector("[data-directions-intro]"),
    directionTitles: [...document.querySelectorAll("[data-direction-title]")],
    directionTexts: [...document.querySelectorAll("[data-direction-text]")],
    preparedName: document.querySelector("[data-prepared-name]"),
    preparedImage: document.querySelector("[data-prepared-image]"),
    pairingTitles: [...document.querySelectorAll("[data-pairing-title]")],
    pairingTexts: [...document.querySelectorAll("[data-pairing-text]")],
    language: document.querySelector("[data-language]"),
    authDialog: document.querySelector("[data-auth-dialog]"),
    authForm: document.querySelector("[data-auth-form]"),
    authNameField: document.querySelector("[data-auth-name-field]"),
    authTitle: document.querySelector("[data-auth-title]"),
    authCopy: document.querySelector("[data-auth-copy]"),
    authSubmit: document.querySelector("[data-auth-submit]"),
    authError: document.querySelector("[data-auth-error]"),
    authLabel: document.querySelector("[data-auth-label]"),
    authSession: document.querySelector("[data-auth-session]"),
    authSessionCopy: document.querySelector("[data-auth-session-copy]"),
    authLogout: document.querySelector("[data-auth-logout]"),
    cartTrigger: document.querySelector("[data-cart-trigger]"),
    cartCount: document.querySelector("[data-cart-count]"),
    cartTitleCount: document.querySelector("[data-cart-title-count]"),
    cartDrawer: document.querySelector("[data-cart-drawer]"),
    cartScrim: document.querySelector("[data-cart-scrim]"),
    cartItems: document.querySelector("[data-cart-items]"),
    clearCart: document.querySelector("[data-clear-cart]"),
    cartEmpty: document.querySelector("[data-cart-empty]"),
    subtotal: document.querySelector("[data-subtotal]"),
    shippingMessage: document.querySelector("[data-shipping-message]"),
    checkoutButton: document.querySelector("[data-open-checkout]"),
    searchDialog: document.querySelector("[data-search-dialog]"),
    searchInput: document.querySelector("[data-search-input]"),
    searchResultsContainer: document.querySelector("[data-search-results]"),
    searchResults: [],
    noResults: document.querySelector("[data-no-results]"),
    checkoutDialog: document.querySelector("[data-checkout-dialog]"),
    checkoutForm: document.querySelector("[data-checkout-form]"),
    checkoutFormView: document.querySelector("[data-checkout-form-view]"),
    checkoutSuccess: document.querySelector("[data-checkout-success]"),
    checkoutError: document.querySelector("[data-checkout-error]"),
    checkoutSubmitLabel: document.querySelector("[data-checkout-submit-label]"),
    checkoutSuccessCopy: document.querySelector("[data-checkout-success-copy]"),
    legalDialog: document.querySelector("[data-legal-dialog]"),
    toast: document.querySelector("[data-toast]"),
    nav: document.querySelector("[data-nav]"),
    navToggle: document.querySelector("[data-nav-toggle]"),
    shopView: document.querySelector("[data-shop-view]"),
    refrescosView: document.querySelector("[data-refrescos-view]"),
    viewToggles: [...document.querySelectorAll("[data-view-toggle]")],
    catalogFilters: [...document.querySelectorAll("[data-catalog-filter]")],
    catalogCards: [...document.querySelectorAll("[data-catalog-card]")],
    catalogAdds: [...document.querySelectorAll("[data-catalog-add]")],
    catalogSteppers: [...document.querySelectorAll("[data-catalog-stepper]")],
    catalogQuantityOutputs: [...document.querySelectorAll("[data-catalog-quantity]")],
    catalogQuantityMinuses: [...document.querySelectorAll("[data-catalog-qty-minus]")],
    catalogQuantityPluses: [...document.querySelectorAll("[data-catalog-qty-plus]")],
    catalogDetailButtons: [...document.querySelectorAll("[data-catalog-detail]")],
    catalogDetailLabels: [...document.querySelectorAll("[data-catalog-detail-label]")],
    catalogCategories: [...document.querySelectorAll("[data-catalog-category]")],
    catalogNames: [...document.querySelectorAll("[data-catalog-name]")],
    catalogImages: [...document.querySelectorAll("[data-catalog-image]")],
    catalogStatuses: [...document.querySelectorAll("[data-catalog-status]")],
    catalogMetas: [...document.querySelectorAll("[data-catalog-meta]")],
    catalogHeats: [...document.querySelectorAll("[data-catalog-heat]")],
    catalogSweetnesses: [...document.querySelectorAll("[data-catalog-sweetness], [data-refresco-catalog-sweetness]")],
    catalogCalories: [...document.querySelectorAll("[data-catalog-calories], [data-refresco-catalog-calories]")],
  };

  const state = {
    selected: initialProductIndex,
    quantity: 1,
    angle: initialProductIndex,
    target: initialProductIndex,
    velocity: 0,
    dragging: false,
    dragStartX: 0,
    dragStartAngle: 0,
    lastX: 0,
    moved: 0,
    lookX: 0,
    lookY: 0,
    lookTargetX: 0,
    lookTargetY: 0,
    language: loadLanguage(),
    cart: loadCart(),
    catalogQuantities: new Map(catalogProducts.map((product) => [String(product.id), 1])),
    detailProductId: String(products[initialProductIndex].id),
    toastTimer: null,
    cartAnimationTimer: null,
    currentView: "shop",
    lastCartFocus: null,
    lastOrder: null,
    currentUser: null,
    authMode: "login",
  };

  function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
  }

  function modulo(value, size) {
    return ((value % size) + size) % size;
  }

  const CAROUSEL_STIFFNESS = 0.24;
  const CAROUSEL_DAMPING = 0.54;
  const CAROUSEL_MAX_ANIMATED_DISTANCE = 2;

  function setCarouselTarget(motion, target) {
    motion.target = target;
    const travel = target - motion.angle;
    if (reducedMotion || Math.abs(travel) > CAROUSEL_MAX_ANIMATED_DISTANCE) {
      motion.angle = target;
      motion.velocity = 0;
      return;
    }
    motion.velocity = clamp(motion.velocity + travel * 0.015, -0.24, 0.24);
  }

  function advanceCarouselMotion(motion, frameScale) {
    if (reducedMotion) {
      motion.angle = motion.target;
      motion.velocity = 0;
      return;
    }
    const steps = Math.max(1, Math.ceil(frameScale));
    const stepScale = frameScale / steps;
    for (let step = 0; step < steps; step += 1) {
      const delta = motion.target - motion.angle;
      motion.velocity += delta * CAROUSEL_STIFFNESS * stepScale;
      motion.velocity *= Math.pow(CAROUSEL_DAMPING, stepScale);
      motion.angle += motion.velocity * stepScale;
    }
    const remaining = motion.target - motion.angle;
    if (Math.abs(remaining) < 0.0008 && Math.abs(motion.velocity) < 0.0008) {
      motion.angle = motion.target;
      motion.velocity = 0;
    }
  }

  function loadLanguage() {
    try {
      const saved = localStorage.getItem("buldak-language");
      if (["es", "en", "zh"].includes(saved)) return saved;
    } catch {
      // Language preference remains available for this visit.
    }
    const browserLanguage = navigator.language?.toLowerCase() || "es";
    if (browserLanguage.startsWith("zh")) return "zh";
    if (browserLanguage.startsWith("en")) return "en";
    return "es";
  }

  function t(key, values = {}) {
    const table = i18n.locales[state.language] || i18n.locales.es;
    const fallback = i18n.locales.es[key] || key;
    return String(table[key] || fallback).replace(/\{(\w+)\}/g, (_, name) => values[name] ?? `{${name}}`);
  }

  function localizedProduct(product) {
    if (!product) return product;
    const translated = i18n.productContent?.[state.language]?.[product.id];
    const name = i18n.productNames?.[state.language]?.[product.id]
      || product[`name_${state.language}`]
      || product.name;
    const description = translated?.description
      || product[`description_${state.language}`]
      || product.description
      || "";
    const heat_label = product[`heat_label_${state.language}`] || product.heat_label || "";
    const sweetness_label = product[`sweetness_label_${state.language}`] || product.sweetness_label || "";
    const kcal_basis = product[`kcal_basis_${state.language}`] || product.kcal_basis || "";
    return { ...product, ...(translated || {}), name, description, heat_label, sweetness_label, kcal_basis };
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function translateWeight(weight) {
    return state.language === "zh" ? String(weight).replace(/\s*g\b/gi, " 克") : weight;
  }

  function translateCase(caseSize) {
    if (state.language === "es") return caseSize;
    const value = String(caseSize);
    if (state.language === "en") {
      return value
        .replace(/paquetes/gi, "packs")
        .replace(/bolsas/gi, "bags")
        .replace(/SKU alterno/gi, "alternate SKU");
    }
    return value
      .replace(/paquetes/gi, "袋")
      .replace(/bolsas/gi, "袋")
      .replace(/bowls?/gi, "碗")
      .replace(/SKU alterno/gi, "备用 SKU");
  }

  // Set once the drinks section initialises; lets applyLanguage re-render it.
  let refreshRefrescos = null;
  let stepActiveRefresco = null;

  function centerTabInScroller(tab) {
    const scroller = tab?.parentElement;
    if (!scroller) return;
    const left = tab.offsetLeft - (scroller.clientWidth - tab.offsetWidth) / 2;
    scroller.scrollTo({
      left: Math.max(0, left),
      behavior: reducedMotion ? "auto" : "smooth"
    });
  }

  function documentOffsetTop(element) {
    let top = 0;
    for (let node = element; node; node = node.offsetParent) top += node.offsetTop;
    return top;
  }

  function formatMoney(value) {
    return `$${Number(value).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }

  const UNIT_NOUNS = {
    en: { "paquetes": "packs", "bolsas": "bags", "botellas": "bottles", "latas": "cans",
          "vasos": "cups", "sobres": "sticks", "cajas": "boxes", "bowls grandes": "big bowls", "bowls": "bowls" },
    zh: { "paquetes": "袋", "bolsas": "袋", "botellas": "瓶", "latas": "罐",
          "vasos": "杯", "sobres": "条", "cajas": "盒", "bowls grandes": "大碗", "bowls": "碗" }
  };

  // Naive de-pluralising turns "bottles" into "bottl", so spell the forms out.
  const UNIT_SINGULAR = {
    es: { "botellas": "botella", "latas": "lata", "vasos": "vaso", "paquetes": "paquete",
          "bolsas": "bolsa", "sobres": "sobre", "cajas": "caja", "bowls": "bowl", "bowls grandes": "bowl grande" },
    en: { "bottles": "bottle", "cans": "can", "cups": "cup", "packs": "pack",
          "bags": "bag", "sticks": "stick", "boxes": "box", "bowls": "bowl", "big bowls": "big bowl" }
  };

  /** The unit noun in singular, for "480 ml · botella". */
  function unitNounSingular(product) {
    const noun = product.unit_noun || "";
    if (state.language === "es") return UNIT_SINGULAR.es[noun] || noun;
    const word = UNIT_NOUNS[state.language]?.[noun] || noun;
    if (state.language === "zh") return word;
    return UNIT_SINGULAR.en[word] || word;
  }

  /** "24 latas de 330 ml" / "4 paquetes de 6 latas de 330 ml", localised. */
  function packLabel(product) {
    const { units_per_case: units, inner_packs: inner, unit_size: size, unit_noun: noun } = product;
    if (!units || !size || !noun) return translateWeight(product.weight || "");
    const lang = state.language;
    const word = lang === "es" ? noun : (UNIT_NOUNS[lang]?.[noun] || noun);
    const gram = lang === "zh" ? String(size).replace(/\s*g\b/gi, " 克") : size;
    if (inner) {
      const outer = units / inner;
      if (lang === "en") return `${outer} packs of ${inner} ${word} of ${gram}`;
      if (lang === "zh") return `${outer} 包 × ${inner} ${word} × ${gram}`;
      return `${outer} paquetes de ${inner} ${word} de ${gram}`;
    }
    if (lang === "en") return `${units} ${word} of ${gram}`;
    if (lang === "zh") return `${units} ${word} × ${gram}`;
    return `${units} ${word} de ${gram}`;
  }

  function productDetail(product) {
    return i18n.productDetails?.[state.language]?.[product.id] || {};
  }

  function storyThemeFor(product) {
    return catalogThemes[product.id] || {
      bgA: product.colors?.bg_a || "#f5d9e1",
      bgB: product.colors?.bg_b || "#fff8f4",
      glow: product.colors?.glow || "#ffc1d2",
      ink: product.colors?.ink || "#2b171e",
      accent: product.colors?.accent || "#b3123f"
    };
  }

  function isDarkColor(hex) {
    const normalized = String(hex).replace("#", "");
    if (!/^[0-9a-f]{6}$/i.test(normalized)) return false;
    const [red, green, blue] = [0, 2, 4].map((offset) => Number.parseInt(normalized.slice(offset, offset + 2), 16));
    return (red * 299 + green * 587 + blue * 114) / 255000 < .48;
  }

  function setStoryStat(element, value) {
    const available = value !== undefined && value !== null && String(value).trim() !== "";
    element.textContent = available ? value : "—";
    element.closest("div")?.classList.toggle("is-unavailable", !available);
  }

  function storyStatsFor(product) {
    return {
      hasHeat: product.heat_applicable === true,
      heat: product.shu || product.heat_label,
      heatLabel: product.shu ? "Scoville" : t("hero.heat"),
      hasSweetness: product.sweetness_applicable === true,
      sweetness: `${product.sweetness_level}/5`,
      hasCookTime: product.cook_time_applicable === true && Boolean(product.cook_time),
      cookTime: product.cook_time,
      kcal: product.kcal,
      kcalBasis: product.kcal_basis,
    };
  }

  const catalogDetailButtonById = new Map(
    dom.catalogDetailButtons.map((button) => [button.dataset.catalogDetail, button])
  );
  const catalogDetailLabelById = new Map(
    dom.catalogDetailLabels.map((label) => [label.dataset.catalogDetailLabel, label])
  );

  function updateCatalogDetailButtons(previousId, activeId) {
    new Set([previousId, activeId].filter(Boolean)).forEach((id) => {
      const active = id === activeId;
      const button = catalogDetailButtonById.get(id);
      const label = catalogDetailLabelById.get(id);
      button?.setAttribute("aria-pressed", String(active));
      button?.closest("[data-catalog-card]")?.classList.toggle("is-detail-selected", active);
      if (label) label.textContent = t(active ? "catalog.selected" : "catalog.details");
    });
  }

  function renderSupplementalSections(product) {
    const hasDirections = Array.isArray(product.directions) && product.directions.length === dom.directionTitles.length;
    const hasPreparedServing = Boolean(product.prepared_image && Array.isArray(product.recommendations));
    dom.ritualSection.hidden = !hasDirections;
    dom.preparedSection.hidden = !hasPreparedServing;

    if (hasDirections) {
      dom.directionsTitle.innerHTML = product.directions_title.join("<br>");
      dom.directionsIntro.textContent = product.directions_intro;
      dom.directionTitles.forEach((element, directionIndex) => {
        element.textContent = product.directions[directionIndex].title;
      });
      dom.directionTexts.forEach((element, directionIndex) => {
        element.textContent = product.directions[directionIndex].text;
      });
    }

    if (hasPreparedServing) {
      dom.preparedName.textContent = product.name;
      if (dom.preparedImage.getAttribute("src") !== product.prepared_image) dom.preparedImage.src = product.prepared_image;
      dom.preparedImage.alt = product.prepared_alt;
      dom.pairingTitles.forEach((element, pairingIndex) => {
        element.textContent = product.recommendations[pairingIndex].title;
      });
      dom.pairingTexts.forEach((element, pairingIndex) => {
        element.textContent = product.recommendations[pairingIndex].text;
      });
    }
  }

  function renderStoryById(id) {
    const baseProduct = productById.get(String(id));
    if (!baseProduct) return;
    const previousDetailId = state.detailProductId;
    const product = localizedProduct(baseProduct);
    const detail = productDetail(product);
    const storyStats = storyStatsFor(product);
    const nameEnding = state.language === "zh" ? "。" : ".";
    const title = Array.isArray(product.story_title)
      ? product.story_title
      : [`${product.name}${nameEnding}`, t("story.profile")];
    const theme = storyThemeFor(product);

    dom.storySection.dataset.detailId = String(product.id);
    dom.storySection.style.setProperty("--detail-bg-a", theme.bgA);
    dom.storySection.style.setProperty("--detail-bg-b", theme.bgB);
    dom.storySection.style.setProperty("--detail-glow", theme.glow);
    dom.storySection.style.setProperty("--detail-ink", theme.ink);
    dom.storySection.style.setProperty("--detail-accent", theme.accent);
    dom.storySection.classList.toggle("is-dark", isDarkColor(theme.bgA));
    dom.storySection.classList.remove("is-changing");
    requestAnimationFrame(() => dom.storySection.classList.add("is-changing"));

    dom.storyTitle.innerHTML = title.map(escapeHtml).join("<br>");
    dom.storyCopy.textContent = product.story || detail.description || product.description || "";
    dom.storyImage.src = product.image;
    dom.storyImage.alt = state.language === "zh"
      ? `${product.name} 产品包装`
      : state.language === "en"
        ? `${product.name} product pack`
        : `Empaque de ${product.name}`;
    dom.storyHeatStat.hidden = !storyStats.hasHeat;
    dom.storySweetnessStat.hidden = !storyStats.hasSweetness;
    dom.storyCookStat.hidden = !storyStats.hasCookTime;
    if (storyStats.hasHeat) setStoryStat(dom.shu, storyStats.heat);
    if (storyStats.hasSweetness) setStoryStat(dom.storySweetness, storyStats.sweetness);
    dom.storyHeatStatLabel.textContent = storyStats.heatLabel;
    setStoryStat(dom.kcal, storyStats.kcal);
    dom.storyKcalBasis.textContent = storyStats.kcalBasis;
    if (storyStats.hasCookTime) setStoryStat(dom.cookTime, storyStats.cookTime);
    setStoryStat(dom.storyWeight, translateWeight(product.weight).split(" · ")[0]);
    dom.storyNote.innerHTML = escapeHtml(product.story_note || detail.note || product.name).replace("\n", "<br>");
    dom.nutritionSource.href = product.nutrition_source_url || product.source_url || "#";
    renderSupplementalSections(product);
    state.detailProductId = String(product.id);
    document.title = `${t("meta.title").split("—")[0].trim()} — ${product.name}`;
    updateCatalogDetailButtons(previousDetailId, state.detailProductId);
    invalidateHeaderMetrics();
    queueHeaderUpdate();
  }

  function showProductDetail(id) {
    renderStoryById(id);
    dom.storySection.scrollIntoView({ behavior: reducedMotion ? "auto" : "smooth", block: "start" });
    window.setTimeout(() => dom.storyTitle.focus({ preventScroll: true }), reducedMotion ? 0 : 650);
  }

  function changeCatalogQuantity(id, delta) {
    id = String(id);
    const next = clamp((state.catalogQuantities.get(id) || 1) + delta, 1, 20);
    state.catalogQuantities.set(id, next);
    const output = dom.catalogQuantityOutputs.find((element) => element.dataset.catalogQuantity === id);
    if (output) output.textContent = String(next);
  }

  function applyLanguage(language, { persist = true, initial = false } = {}) {
    state.language = ["es", "en", "zh"].includes(language) ? language : "es";
    root.lang = state.language === "zh" ? "zh-CN" : state.language;
    dom.language.value = state.language;
    if (persist) {
      try {
        localStorage.setItem("buldak-language", state.language);
      } catch {
        // A blocked storage API should not prevent translation.
      }
    }

    // The server already renders the default Spanish interface. Avoid rewriting
    // thousands of off-screen catalog nodes before the first meaningful paint.
    if (initial && state.language === "es") {
      document.title = `dangoko — ${products[state.selected].name}`;
      renderCart({ animate: false });
      return;
    }

    document.querySelectorAll("[data-i18n]").forEach((element) => {
      element.textContent = t(element.dataset.i18n, { count: catalogProducts.length });
    });
    document.querySelectorAll("[data-i18n-html]").forEach((element) => {
      element.innerHTML = t(element.dataset.i18nHtml, { count: catalogProducts.length });
    });
    document.querySelectorAll("[data-i18n-aria]").forEach((element) => {
      element.setAttribute("aria-label", t(element.dataset.i18nAria));
    });
    document.querySelectorAll("[data-i18n-placeholder]").forEach((element) => {
      element.setAttribute("placeholder", t(element.dataset.i18nPlaceholder));
    });
    document.querySelector('[data-i18n-meta="meta.description"]')?.setAttribute("content", t("meta.description"));

    dom.catalogCategories.forEach((element) => {
      element.textContent = t(`category.${element.dataset.catalogCategory}`);
    });
    dom.catalogNames.forEach((element) => {
      const product = localizedProduct(productById.get(element.dataset.catalogName));
      element.textContent = product.name;
    });
    dom.catalogImages.forEach((element) => {
      const product = localizedProduct(productById.get(element.dataset.catalogImage));
      element.alt = state.language === "zh"
        ? `${product.name}，SKU ${product.sku}`
        : `${product.name}, SKU ${product.sku}`;
    });
    dom.catalogMetas.forEach((element) => {
      element.textContent = packLabel(productById.get(element.dataset.catalogMeta));
    });
    dom.catalogHeats.forEach((element) => {
      const product = localizedProduct(productById.get(element.dataset.catalogHeat));
      const label = product.heat_label || t("catalog.notSpicy");
      const text = element.querySelector("small");
      if (text) text.textContent = label;
      element.setAttribute("aria-label", `${t("hero.heat")}: ${label}`);
    });
    dom.catalogSweetnesses.forEach((element) => {
      const id = element.dataset.catalogSweetness || element.dataset.refrescoCatalogSweetness;
      const product = localizedProduct(productById.get(id));
      if (!product) return;
      const text = element.querySelector("small");
      if (text) text.textContent = product.sweetness_label;
      element.setAttribute("aria-label", product.sweetness_label);
    });
    dom.catalogCalories.forEach((element) => {
      const id = element.dataset.catalogCalories || element.dataset.refrescoCatalogCalories;
      const product = localizedProduct(productById.get(id));
      if (!product) return;
      const value = element.querySelector("strong");
      const basis = element.querySelector("small");
      if (value) value.textContent = `${product.kcal} kcal`;
      if (basis) basis.textContent = product.kcal_basis;
    });
    dom.catalogStatuses.forEach((element) => {
      const product = productById.get(element.dataset.catalogStatus);
      element.textContent = t(product.is_available === false ? "catalog.soldOut" : "catalog.available");
    });
    dom.catalogAdds.forEach((button) => {
      const product = productById.get(button.dataset.catalogAdd);
      button.textContent = t(product.is_available === false ? "catalog.soldOut" : "catalog.add");
    });
    dom.catalogSteppers.forEach((stepper) => {
      const product = localizedProduct(productById.get(stepper.dataset.catalogStepper));
      stepper.setAttribute("aria-label", t("catalog.quantity", { name: product.name }));
    });
    dom.catalogQuantityMinuses.forEach((button) => {
      const product = localizedProduct(productById.get(button.dataset.catalogQtyMinus));
      button.setAttribute("aria-label", t("catalog.reduce", { name: product.name }));
    });
    dom.catalogQuantityPluses.forEach((button) => {
      const product = localizedProduct(productById.get(button.dataset.catalogQtyPlus));
      button.setAttribute("aria-label", t("catalog.increase", { name: product.name }));
    });
    dom.searchResults.forEach((result, index) => {
      const product = localizedProduct(products[index]);
      const name = result.querySelector("strong");
      const detail = result.querySelector("small");
      if (name) name.textContent = product.name;
      if (detail) {
        detail.textContent = product.heat_label && product.heat_label !== "—"
          ? `${product.heat_label} · ${product.price_label}`
          : `${t(`category.${product.category}`)} · ${product.price_label}`;
      }
    });
    dom.cards.forEach((card, index) => {
      const product = localizedProduct(products[index]);
      card.setAttribute("aria-label", t("hero.selectFlavor", { name: product.name }));
      const image = card.querySelector("img");
      if (image) image.alt = state.language === "zh"
        ? `${product.name} 产品包装`
        : state.language === "en"
          ? `${product.name} product pack`
          : `Empaque de ${product.name}`;
    });
    dom.tabs.forEach((tab, index) => {
      tab.textContent = localizedProduct(products[index]).name;
    });
    const suggestions = {
      es: [["carbonara", "carbonara"], ["picante", "picante"], ["queso", "queso"]],
      en: [["carbonara", "carbonara"], ["spicy", "spicy"], ["cheese", "cheese"]],
      zh: [["carbonara", "carbonara"], ["辣", "辣"], ["芝士", "芝士"]]
    }[state.language];
    document.querySelectorAll("[data-suggestion]").forEach((button, index) => {
      button.dataset.suggestion = suggestions[index][0];
      button.textContent = suggestions[index][1];
    });

    document.querySelectorAll("[data-refresco-catalog-meta]").forEach((element) => {
      const product = productById.get(element.dataset.refrescoCatalogMeta);
      if (product) element.textContent = packLabel(product);
    });
    document.querySelectorAll("[data-refresco-catalog-name]").forEach((element) => {
      const product = productById.get(element.dataset.refrescoCatalogName);
      if (product) element.textContent = localizedProduct(product).name;
    });
    document.querySelectorAll("[data-refresco-catalog-description]").forEach((element) => {
      const product = productById.get(element.dataset.refrescoCatalogDescription);
      if (product) element.textContent = localizedProduct(product).description || "";
    });
    refreshRefrescos?.();

    setTheme(state.selected, { syncDetail: false, centerTab: false });
    renderStoryById(state.detailProductId);
    renderCart({ animate: false });
    filterSearch(dom.searchInput.value);
    if (state.lastOrder) {
      dom.checkoutSuccessCopy.textContent = t("checkout.successCopy", {
        id: state.lastOrder.id,
        total: state.lastOrder.total
      });
    }
  }

  function carouselDistance(value) {
    return modulo(value + products.length / 2, products.length) - products.length / 2;
  }

  let carouselFrame = 0;
  let carouselInView = true;
  let carouselPrepared = false;
  let lastCarouselFrameTime = performance.now();
  let lastCarouselCandidates = new Set();
  let pendingStoryProductId = null;
  let pendingTabIndex = null;
  let storySyncHandle = 0;
  let storySyncUsesIdleCallback = false;

  function applyCarouselTheme(theme) {
    root.style.setProperty("--bg-a", theme.bgA);
    root.style.setProperty("--bg-b", theme.bgB);
    root.style.setProperty("--glow", theme.glow);
    root.style.setProperty("--ink", theme.ink);
    root.style.setProperty("--accent", theme.accent);
    document.querySelector('meta[name="theme-color"]')?.setAttribute("content", theme.bgA);
  }

  function cancelScheduledStorySync() {
    if (!storySyncHandle) return;
    if (storySyncUsesIdleCallback) window.cancelIdleCallback?.(storySyncHandle);
    else window.clearTimeout(storySyncHandle);
    storySyncHandle = 0;
  }

  function schedulePendingStorySync() {
    if (!pendingStoryProductId) return;
    const productId = pendingStoryProductId;
    pendingStoryProductId = null;
    cancelScheduledStorySync();
    const render = () => {
      storySyncHandle = 0;
      renderStoryById(productId);
    };
    storySyncUsesIdleCallback = "requestIdleCallback" in window;
    storySyncHandle = storySyncUsesIdleCallback
      ? window.requestIdleCallback(render, { timeout: 500 })
      : window.setTimeout(render, 32);
  }

  function flushCarouselSideEffects() {
    if (pendingTabIndex !== null) {
      centerTabInScroller(dom.tabs[pendingTabIndex]);
      pendingTabIndex = null;
    }
    schedulePendingStorySync();
  }

  function queueCarouselDraw() {
    if (!carouselFrame && carouselInView && !document.hidden) {
      carouselFrame = requestAnimationFrame(drawCarousel);
    }
  }

  function cycleTo(index) {
    const rounded = Math.round(state.target);
    const current = modulo(rounded, products.length);
    return rounded + carouselDistance(index - current);
  }

  function setTheme(index, { syncDetail = true, centerTab = true } = {}) {
    const baseProduct = products[index];
    const product = localizedProduct(baseProduct);
    const detail = productDetail(product);
    const theme = storyThemeFor(product);
    const previousIndex = state.selected;
    state.selected = index;
    // Keep the selected pack and its palette in the same interaction frame.
    // Waiting for the carousel inertia to settle made the old color linger.
    preloadCarouselWindow(dom.cards, index);
    applyCarouselTheme(theme);

    dom.productType.textContent = t(`category.${product.category}`);
    dom.number.textContent = product.number;
    dom.sku.textContent = product.sku;
    dom.name.textContent = product.name;
    dom.description.textContent = detail.description || product.description || "";
    dom.price.textContent = product.price_label;
    if (dom.unitPrice) dom.unitPrice.textContent = product.unit_price_label || "";
    dom.weight.textContent = packLabel(product);
    const hasHeat = product.heat_applicable === true;
    const hasSweetness = product.sweetness_applicable === true;
    dom.heroHeat.hidden = !hasHeat;
    dom.heroSweetness.hidden = !hasSweetness;
    if (hasHeat) {
      dom.heatFill.style.width = `${product.heat || 0}%`;
      dom.heatLabel.textContent = product.heat_label;
    }
    if (hasSweetness) {
      dom.sweetnessFill.style.width = `${product.sweetness || 0}%`;
      dom.sweetnessLabel.textContent = product.sweetness_label;
    }
    dom.heroKcal.textContent = product.kcal;
    dom.heroKcalBasis.textContent = product.kcal_basis;
    dom.addSelected.disabled = product.is_available === false;
    const addLabel = dom.addSelected.querySelector("[data-i18n]");
    if (addLabel) addLabel.textContent = t(product.is_available === false ? "catalog.soldOut" : "wholesale.addCase");

    document.title = `${t("meta.title").split("—")[0].trim()} — ${product.name}`;

    new Set([previousIndex, index]).forEach((cardIndex) => {
      const active = cardIndex === index;
      dom.cards[cardIndex]?.classList.toggle("is-active", active);
      dom.cards[cardIndex]?.setAttribute("aria-pressed", String(active));
      dom.tabs[cardIndex]?.classList.toggle("is-active", active);
      dom.tabs[cardIndex]?.setAttribute("aria-pressed", String(active));
      dom.lines[cardIndex]?.classList.toggle("is-active", active);
    });
    if (centerTab) pendingTabIndex = index;
    if (syncDetail) {
      pendingStoryProductId = String(baseProduct.id);
      cancelScheduledStorySync();
    }
    queueCarouselDraw();
    if (!carouselInView) flushCarouselSideEffects();
  }

  function goTo(index, options = {}) {
    const normalized = modulo(index, products.length);
    setCarouselTarget(state, cycleTo(normalized));
    setTheme(normalized);
    queueCarouselDraw();
    if (options.scrollTop) {
      if (dom.refrescosView && state.currentView !== "shop") setView("shop");
      document.querySelector("#top").scrollIntoView({ behavior: reducedMotion ? "auto" : "smooth" });
    }
  }

  function step(direction) {
    goTo(state.selected + direction);
  }

  function drawCarousel(frameTime = performance.now()) {
    carouselFrame = 0;
    const frameScale = clamp((frameTime - lastCarouselFrameTime) / 16.667, 0.25, 3);
    lastCarouselFrameTime = frameTime;
    if (!state.dragging) advanceCarouselMotion(state, frameScale);

    if (!carouselPrepared) {
      carouselPrepared = true;
    }

    const radius = clamp(window.innerWidth * 0.29, 260, 445);
    const depth = clamp(window.innerWidth * 0.25, 230, 390);
    if (!mobileMode) {
      state.lookX += (state.lookTargetX - state.lookX) * 0.18;
      state.lookY += (state.lookTargetY - state.lookY) * 0.18;
    }
    const candidates = new Set([-1, 0, 1].map((offset) => modulo(state.selected + offset, products.length)));
    lastCarouselCandidates.forEach((index) => {
      if (candidates.has(index)) return;
      const card = dom.cards[index];
      card.classList.remove("is-rendered");
      card.style.opacity = "0";
      card.style.pointerEvents = "none";
      card.tabIndex = -1;
      card.setAttribute("aria-hidden", "true");
    });
    candidates.forEach((index) => {
      const card = dom.cards[index];
      if (!lastCarouselCandidates.has(index)) card.classList.add("is-rendered");
      const distance = carouselDistance(index - state.angle);
      const absoluteDistance = Math.abs(distance);
      const selectedDistance = Math.abs(carouselDistance(index - state.selected));
      const isVisible = selectedDistance <= 1;
      if (isVisible) activateCarouselImage(card, index === state.selected ? "high" : "low");
      const theta = clamp(distance, -4, 4) * 0.52;
      const x = Math.sin(theta) * radius;
      const z = (Math.cos(theta) - 1) * depth;
      const proximity = clamp(1 + z / (depth * 2.8), 0, 1);
      const scale = 0.68 + proximity * 0.32;
      const lookStrength = Math.pow(proximity, 8);
      const rotationY = distance * -24 + state.lookX * 14 * lookStrength;
      const rotationX = state.lookY * -8.5 * lookStrength;
      const float = reducedMotion || mobileMode ? 0 : Math.sin(frameTime / 2100 + index * 2.1) * 3 * proximity;
      card.style.transform = `translate3d(${x.toFixed(1)}px, ${float.toFixed(1)}px, ${z.toFixed(1)}px) rotateY(${rotationY.toFixed(1)}deg) rotateX(${rotationX.toFixed(1)}deg) scale(${scale.toFixed(3)})`;
      card.style.opacity = isVisible ? String(0.22 + proximity * 0.78) : "0";
      card.style.zIndex = String(1000 + Math.round(z));
      const pointerEvents = isVisible ? "auto" : "none";
      const tabIndex = absoluteDistance < 0.55 ? 0 : -1;
      const ariaHidden = String(!isVisible);
      if (card.style.pointerEvents !== pointerEvents) card.style.pointerEvents = pointerEvents;
      if (card.tabIndex !== tabIndex) card.tabIndex = tabIndex;
      if (card.getAttribute("aria-hidden") !== ariaHidden) card.setAttribute("aria-hidden", ariaHidden);
    });
    lastCarouselCandidates = candidates;

    const carouselMoving = state.dragging
      || Math.abs(state.target - state.angle) > 0.0008
      || Math.abs(state.velocity) > 0.0008
      || (!mobileMode && (Math.abs(state.lookTargetX - state.lookX) > 0.002 || Math.abs(state.lookTargetY - state.lookY) > 0.002));
    if (carouselMoving) queueCarouselDraw();
    else flushCarouselSideEffects();
  }

  function nearestSelectionFromAngle() {
    const selected = modulo(Math.round(state.angle), products.length);
    if (selected !== state.selected) setTheme(selected);
  }

  function onPointerDown(event) {
    if (event.pointerType === "mouse" && event.button !== 0) return;
    state.dragging = true;
    state.dragStartX = event.clientX;
    state.lastX = event.clientX;
    state.dragStartAngle = state.angle;
    state.moved = 0;
    state.velocity = 0;
    dom.carousel.classList.add("is-dragging");
    dom.carousel.setPointerCapture?.(event.pointerId);
    queueCarouselDraw();
  }

  function onPointerMove(event) {
    if (!mobileMode && event.pointerType === "mouse") {
      state.lookTargetX = clamp((event.clientX / window.innerWidth) * 2 - 1, -1, 1);
      state.lookTargetY = clamp((event.clientY / window.innerHeight) * 2 - 1, -1, 1);
      state.lookX += (state.lookTargetX - state.lookX) * 0.68;
      state.lookY += (state.lookTargetY - state.lookY) * 0.68;
      queueCarouselDraw();
    }

    if (!state.dragging) return;
    const delta = event.clientX - state.dragStartX;
    state.moved = Math.max(state.moved, Math.abs(delta));
    state.angle = state.dragStartAngle - delta / clamp(window.innerWidth * 0.25, 210, 340);
    state.velocity = -(event.clientX - state.lastX) / 310;
    state.lastX = event.clientX;
    nearestSelectionFromAngle();
    queueCarouselDraw();
  }

  function onPointerUp(event) {
    if (!state.dragging) return;
    state.dragging = false;
    dom.carousel.classList.remove("is-dragging");
    dom.carousel.releasePointerCapture?.(event.pointerId);
    state.target = Math.round(state.angle + state.velocity * 2.4);
    goTo(modulo(state.target, products.length));
  }

  function loadCart() {
    try {
      const stored = JSON.parse(localStorage.getItem("buldak-cart") || "[]");
      if (!Array.isArray(stored)) return [];
      const legacyIds = { carbonara: "811140", original: "811120", quattro: "811150" };
      return stored
        .map((item) => ({ id: legacyIds[item.id] || String(item.id), quantity: Number(item.quantity) }))
        .filter((item) => productById.has(item.id) && productById.get(item.id).is_available !== false && Number.isInteger(item.quantity) && item.quantity > 0 && item.quantity <= 20);
    } catch {
      return [];
    }
  }

  function saveCart() {
    try {
      localStorage.setItem("buldak-cart", JSON.stringify(state.cart));
    } catch {
      // A blocked storage API should not prevent shopping during this visit.
    }
  }

  function cartCount() {
    return state.cart.reduce((total, item) => total + item.quantity, 0);
  }

  function celebrateCart() {
    dom.cartTrigger.classList.remove("is-celebrating");
    requestAnimationFrame(() => dom.cartTrigger.classList.add("is-celebrating"));
    window.clearTimeout(state.cartAnimationTimer);
    state.cartAnimationTimer = window.setTimeout(() => dom.cartTrigger.classList.remove("is-celebrating"), 650);
  }

  function animateAddToCart(source, product) {
    celebrateCart();
    if (!source || reducedMotion) return;
    source.classList.remove("is-added");
    requestAnimationFrame(() => source.classList.add("is-added"));
    window.setTimeout(() => source.classList.remove("is-added"), 650);

    const sourceRect = source.getBoundingClientRect();
    const targetRect = dom.cartTrigger.getBoundingClientRect();
    const flyer = document.createElement("img");
    flyer.className = "cart-flyer";
    flyer.src = product.image;
    flyer.alt = "";
    flyer.style.left = `${sourceRect.left + sourceRect.width / 2 - 31}px`;
    flyer.style.top = `${sourceRect.top + sourceRect.height / 2 - 31}px`;
    document.body.append(flyer);

    const deltaX = targetRect.left + targetRect.width / 2 - (sourceRect.left + sourceRect.width / 2);
    const deltaY = targetRect.top + targetRect.height / 2 - (sourceRect.top + sourceRect.height / 2);
    const animation = flyer.animate([
      { transform: "translate3d(0, 0, 0) scale(.72) rotate(-5deg)", opacity: 0 },
      { transform: "translate3d(0, -22px, 0) scale(1) rotate(3deg)", opacity: 1, offset: .18 },
      { transform: `translate3d(${deltaX}px, ${deltaY}px, 0) scale(.18) rotate(14deg)`, opacity: .2 }
    ], { duration: 720, easing: "cubic-bezier(.2,.75,.2,1)", fill: "forwards" });
    animation.finished.finally(() => flyer.remove());
  }

  function addToCart(id, quantity = 1, source = null) {
    id = String(id);
    const product = productById.get(id);
    if (!product || product.is_available === false) return;
    const amount = clamp(Number(quantity) || 1, 1, 20);
    const existing = state.cart.find((item) => item.id === id);
    if (existing?.quantity === 20) {
      showToast(t("cart.limit"));
      celebrateCart();
      return;
    }
    if (existing) existing.quantity = Math.min(20, existing.quantity + amount);
    else state.cart.push({ id, quantity: amount });
    saveCart();
    renderCart({ highlightId: id });
    animateAddToCart(source, product);
    showToast(t("cart.added", { name: localizedProduct(product).name }));
  }

  function changeCartQuantity(id, amount, source = null) {
    const item = state.cart.find((entry) => entry.id === id);
    if (!item) return;
    if (amount > 0 && item.quantity === 20) {
      showToast(t("cart.limit"));
      celebrateCart();
      return;
    }
    item.quantity = clamp(item.quantity + amount, 0, 20);
    if (item.quantity === 0) state.cart = state.cart.filter((entry) => entry.id !== id);
    saveCart();
    renderCart({ highlightId: id });
    if (amount > 0) {
      celebrateCart();
      source?.closest(".cart-item")?.classList.add("is-updated");
    }
  }

  function removeCartItem(id) {
    state.cart = state.cart.filter((item) => item.id !== id);
    saveCart();
    renderCart();
  }

  function clearCart() {
    if (state.cart.length === 0) return;
    state.cart = [];
    saveCart();
    renderCart();
    showToast(t("cart.cleared"));
  }

  function renderCart({ animate = true, highlightId = null } = {}) {
    const count = cartCount();
    dom.cartCount.textContent = String(count);
    dom.cartTitleCount.textContent = String(count);
    const subtotal = state.cart.reduce((total, item) => {
      const product = productById.get(item.id);
      return total + Number(product.price) * item.quantity;
    }, 0);
    dom.subtotal.textContent = formatMoney(subtotal);
    dom.checkoutButton.disabled = count === 0;
    dom.clearCart.hidden = count === 0;
    dom.cartEmpty.classList.toggle("is-visible", count === 0);
    dom.cartItems.hidden = count === 0;
    dom.shippingMessage.textContent = count === 0
      ? t("cart.shippingEmpty")
      : t(count === 1 ? "cart.shippingOne" : "cart.shippingMany", { count });

    dom.cartItems.innerHTML = state.cart.map((item) => {
      const product = localizedProduct(productById.get(item.id));
      const safeId = escapeHtml(product.id);
      const safeName = escapeHtml(product.name);
      return `
        <article class="cart-item${highlightId === product.id ? " is-updated" : ""}" data-cart-item="${safeId}">
          <div class="cart-item__image"><img src="${escapeHtml(product.image)}" alt=""></div>
          <div class="cart-item__details">
            <div class="cart-item__top"><h3>${safeName}</h3><strong>${escapeHtml(formatMoney(Number(product.price) * item.quantity))}</strong></div>
            <p>${escapeHtml(packLabel(product))} · ${escapeHtml(product.price_label)} ${escapeHtml(t("wholesale.perCaseShort"))}</p>
            <div class="cart-item__actions">
              <div class="mini-stepper" aria-label="${escapeHtml(t("cart.quantity", { name: product.name }))}">
                <button type="button" data-cart-minus="${safeId}" aria-label="${escapeHtml(t("cart.reduce", { name: product.name }))}">−</button>
                <span>${item.quantity}</span>
                <button type="button" data-cart-plus="${safeId}" aria-label="${escapeHtml(t("cart.increase", { name: product.name }))}">+</button>
              </div>
              <button class="remove-item" type="button" data-cart-remove="${safeId}">${escapeHtml(t("cart.remove"))}</button>
            </div>
          </div>
        </article>`;
    }).join("");

    if (animate) {
      dom.cartCount.classList.remove("is-bumping");
      requestAnimationFrame(() => dom.cartCount.classList.add("is-bumping"));
      window.setTimeout(() => dom.cartCount.classList.remove("is-bumping"), 420);
    }
  }

  function openCart() {
    if (dom.searchDialog.open) dom.searchDialog.close();
    state.lastCartFocus = document.activeElement;
    dom.cartDrawer.inert = false;
    dom.cartDrawer.classList.add("is-open");
    dom.cartScrim.classList.add("is-open");
    dom.cartDrawer.setAttribute("aria-hidden", "false");
    document.body.classList.add("is-locked");
    window.setTimeout(() => dom.cartDrawer.querySelector("[data-close-cart]")?.focus(), 100);
  }

  function closeCart({ restoreFocus = true } = {}) {
    dom.cartDrawer.classList.remove("is-open");
    dom.cartScrim.classList.remove("is-open");
    dom.cartDrawer.setAttribute("aria-hidden", "true");
    dom.cartDrawer.inert = true;
    if (!dom.searchDialog.open && !dom.checkoutDialog.open && !dom.legalDialog.open) document.body.classList.remove("is-locked");
    if (restoreFocus) state.lastCartFocus?.focus?.();
  }

  function showToast(message) {
    dom.toast.textContent = message;
    dom.toast.classList.add("is-visible");
    window.clearTimeout(state.toastTimer);
    state.toastTimer = window.setTimeout(() => dom.toast.classList.remove("is-visible"), 2200);
  }

  function openSearch() {
    closeCart({ restoreFocus: false });
    if (!dom.searchDialog.open) dom.searchDialog.showModal();
    document.body.classList.add("is-locked");
    filterSearch("");
    window.setTimeout(() => dom.searchInput.focus(), 80);
  }

  function closeSearch() {
    if (dom.searchDialog.open) dom.searchDialog.close();
    if (!dom.checkoutDialog.open && !dom.legalDialog.open) document.body.classList.remove("is-locked");
  }

  function filterSearch(query) {
    const terms = query.trim().toLowerCase().split(/\s+/).filter(Boolean);
    const matches = [];
    products.forEach((baseProduct, index) => {
      const product = localizedProduct(baseProduct);
      const detail = productDetail(product);
      const haystack = [product.name, product.name_en, product.name_zh, product.category, product.category_label,
        product.tagline, product.description, product.story, detail.description]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      const isMatch = terms.length === 0 || terms.every((term) => haystack.includes(term));
      if (isMatch) matches.push({ product, index });
    });
    dom.searchResultsContainer.innerHTML = matches.slice(0, 12).map(({ product, index }) => `
      <button class="search-result" type="button" data-search-result="${index}" data-search-product="${escapeHtml(product.id)}">
        <img src="/assets/mobile-catalog/${encodeURIComponent(product.sku)}.webp?v=1" alt="" loading="lazy" decoding="async">
        <span><strong>${escapeHtml(product.name)}</strong><small>${escapeHtml(product.heat_label && product.heat_label !== "—"
          ? `${product.heat_label} · ${product.price_label}`
          : `${t(`category.${product.category}`)} · ${product.price_label}`)}</small></span>
        <b aria-hidden="true">↗</b>
      </button>`).join("");
    dom.searchResults = [...dom.searchResultsContainer.querySelectorAll("[data-search-result]")];
    dom.noResults.hidden = matches.length > 0;
  }

  function selectSearchResult(index) {
    goTo(index, { scrollTop: true });
    closeSearch();
  }

  function openCheckout() {
    if (cartCount() === 0) return;
    closeCart({ restoreFocus: false });
    dom.checkoutFormView.hidden = false;
    dom.checkoutSuccess.hidden = true;
    dom.checkoutError.textContent = "";
    const nameInput = dom.checkoutForm.elements.namedItem("name");
    if (nameInput && state.currentUser?.name) nameInput.value = state.currentUser.name;
    if (!dom.checkoutDialog.open) dom.checkoutDialog.showModal();
    document.body.classList.add("is-locked");
  }

  function renderAuthState(user) {
    state.currentUser = user || null;
    const signedIn = Boolean(state.currentUser);
    dom.authLabel.textContent = signedIn ? `Hola, ${state.currentUser.name}` : "Entrar / Registrarse";
    dom.authForm.hidden = signedIn;
    dom.authSession.hidden = !signedIn;
    if (signedIn) {
      dom.authSessionCopy.textContent = `${state.currentUser.email} · tus pedidos se guardarán en RDS.`;
    }
  }

  function setAuthMode(mode) {
    state.authMode = mode === "register" ? "register" : "login";
    const registering = state.authMode === "register";
    document.querySelectorAll("[data-auth-mode]").forEach((tab) => {
      const active = tab.dataset.authMode === state.authMode;
      tab.classList.toggle("is-active", active);
      tab.setAttribute("aria-selected", String(active));
    });
    dom.authNameField.hidden = !registering;
    dom.authNameField.querySelector("input").required = registering;
    dom.authTitle.textContent = registering ? "Crea tu cuenta." : "Inicia sesión.";
    dom.authCopy.textContent = registering
      ? "Regístrate para asociar tus pedidos a tu usuario en la base de datos."
      : "Accede a tu cuenta y consulta tus pedidos guardados.";
    dom.authSubmit.textContent = registering ? "Registrarme" : "Entrar";
    dom.authError.textContent = "";
  }

  function openAuth() {
    closeCart({ restoreFocus: false });
    if (dom.searchDialog.open) dom.searchDialog.close();
    if (!dom.authDialog.open) dom.authDialog.showModal();
    document.body.classList.add("is-locked");
    if (!state.currentUser) setAuthMode(state.authMode);
  }

  function closeAuth() {
    if (dom.authDialog.open) dom.authDialog.close();
    if (!dom.checkoutDialog.open && !dom.searchDialog.open) document.body.classList.remove("is-locked");
  }

  async function loadCurrentUser() {
    try {
      const response = await fetch("/api/auth/me", { headers: { Accept: "application/json" } });
      const payload = await response.json();
      renderAuthState(payload.authenticated ? payload.user : null);
    } catch {
      renderAuthState(null);
    }
  }

  async function submitAuth(event) {
    event.preventDefault();
    const submitButton = dom.authForm.querySelector('button[type="submit"]');
    const formData = new FormData(dom.authForm);
    const registering = state.authMode === "register";
    dom.authError.textContent = "";
    submitButton.disabled = true;
    try {
      const response = await fetch(registering ? "/api/auth/register" : "/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({
          ...(registering ? { name: formData.get("name") } : {}),
          email: formData.get("email"),
          password: formData.get("password"),
        }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || "No se pudo completar la operación.");
      renderAuthState(payload.user);
      dom.authForm.reset();
      showToast(registering ? "Cuenta creada en la base de datos." : "Sesión iniciada.");
    } catch (error) {
      dom.authError.textContent = error.message;
    } finally {
      submitButton.disabled = false;
    }
  }

  async function logout() {
    await fetch("/api/auth/logout", { method: "POST", headers: { Accept: "application/json" } });
    renderAuthState(null);
    setAuthMode("login");
    showToast("Sesión cerrada.");
  }

  function openLegal() {
    closeCart({ restoreFocus: false });
    if (dom.searchDialog.open) dom.searchDialog.close();
    if (!dom.legalDialog.open) dom.legalDialog.showModal();
    document.body.classList.add("is-locked");
  }

  function closeLegal() {
    if (dom.legalDialog.open) dom.legalDialog.close();
    if (!dom.checkoutDialog.open && !dom.searchDialog.open) document.body.classList.remove("is-locked");
  }

  function setCatalogFilter(category) {
    const departments = {
      noodles: new Set(["soups", "bowls", "tteokbokki", "sauces"]),
      snacks: new Set(["chips", "cookies", "candy", "bakery"]),
    };
    dom.catalogFilters.forEach((button) => {
      const active = button.dataset.catalogFilter === category;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-pressed", String(active));
    });
    dom.catalogCards.forEach((card) => {
      const grouped = departments[category];
      card.hidden = category !== "all" && card.dataset.category !== category && !grouped?.has(card.dataset.category);
    });
    invalidateHeaderMetrics();
  }

  function closeCheckout() {
    if (dom.checkoutDialog.open) dom.checkoutDialog.close();
    if (!dom.legalDialog.open && !dom.searchDialog.open) document.body.classList.remove("is-locked");
  }

  async function submitCheckout(event) {
    event.preventDefault();
    const submitButton = dom.checkoutForm.querySelector('button[type="submit"]');
    const formData = new FormData(dom.checkoutForm);
    dom.checkoutError.textContent = "";
    submitButton.disabled = true;
    dom.checkoutSubmitLabel.textContent = t("checkout.submitting");

    try {
      const response = await fetch("/api/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          customer: {
            name: formData.get("name"),
            email: state.currentUser?.email || "",
            privacy_consent: formData.get("privacy_consent") === "on"
          },
          cart: state.cart,
        }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || t("checkout.error"));

      state.lastOrder = { id: payload.order_id, total: formatMoney(payload.total) };
      dom.checkoutSuccessCopy.textContent = t("checkout.successCopy", {
        id: state.lastOrder.id,
        total: state.lastOrder.total
      });
      dom.checkoutFormView.hidden = true;
      dom.checkoutSuccess.hidden = false;
      state.cart = [];
      saveCart();
      renderCart();
    } catch (error) {
      dom.checkoutError.textContent = error.message;
    } finally {
      submitButton.disabled = false;
      dom.checkoutSubmitLabel.textContent = t("checkout.submit");
    }
  }

  function toggleNavigation(force) {
    const open = typeof force === "boolean" ? force : !dom.nav.classList.contains("is-open");
    dom.nav.classList.toggle("is-open", open);
    dom.header.classList.toggle("menu-open", open);
    dom.navToggle.setAttribute("aria-expanded", String(open));
    document.body.classList.toggle("is-locked", open);
  }

  function setView(view, { scrollTargetId } = {}) {
    if (!dom.refrescosView) return;
    const showRefrescos = view === "refrescos";
    const changed = state.currentView !== view;
    state.currentView = showRefrescos ? "refrescos" : "shop";
    dom.shopView.hidden = showRefrescos;
    dom.refrescosView.hidden = !showRefrescos;
    dom.viewToggles.forEach((toggle) => {
      if (toggle.dataset.viewToggle === "refrescos") toggle.classList.toggle("is-active", showRefrescos);
    });

    const target = scrollTargetId ? document.getElementById(scrollTargetId) : null;
    if (target) {
      target.scrollIntoView({ behavior: changed || reducedMotion ? "auto" : "smooth", block: "start" });
    } else {
      window.scrollTo({ top: 0, behavior: "auto" });
    }
    invalidateHeaderMetrics();
    queueHeaderUpdate();
  }

  const headerSections = {
    catalog: document.querySelector("#catalog"),
    story: document.querySelector("#story"),
    ritual: document.querySelector("#ritual"),
    prepared: document.querySelector("#prepared"),
    footer: document.querySelector(".site-footer"),
  };
  let headerMetrics = null;

  function invalidateHeaderMetrics() {
    headerMetrics = null;
  }

  function measureHeaderSections() {
    const ritualVisible = !headerSections.ritual.hidden;
    const preparedVisible = !headerSections.prepared.hidden;
    headerMetrics = {
      catalogTop: headerSections.catalog.offsetTop,
      storyTop: headerSections.story.offsetTop,
      ritualTop: headerSections.ritual.offsetTop,
      preparedTop: headerSections.prepared.offsetTop,
      footerTop: headerSections.footer.offsetTop,
      ritualVisible,
      preparedVisible,
    };
    return headerMetrics;
  }

  function updateHeader() {
    const y = window.scrollY;
    dom.header.classList.toggle("is-scrolled", y > 20);
    if (state.currentView === "refrescos") {
      dom.header.classList.remove("force-light");
      dom.header.classList.add("force-dark");
      return;
    }
    if (!headerMetrics && y <= 20) {
      dom.header.classList.remove("force-dark", "force-light");
      return;
    }
    const metrics = headerMetrics || measureHeaderSections();
    const headerLine = y + 45;
    const storyEnd = metrics.ritualVisible ? metrics.ritualTop : metrics.preparedVisible ? metrics.preparedTop : metrics.footerTop;
    const ritualEnd = metrics.preparedVisible ? metrics.preparedTop : metrics.footerTop;
    const overCatalog = headerLine >= metrics.catalogTop && headerLine < metrics.storyTop;
    const overStory = headerLine >= metrics.storyTop && headerLine < storyEnd;
    const overRitual = metrics.ritualVisible && headerLine >= metrics.ritualTop && headerLine < ritualEnd;
    const overPrepared = metrics.preparedVisible && headerLine >= metrics.preparedTop && headerLine < metrics.footerTop;
    const overFooter = headerLine >= metrics.footerTop;
    dom.header.classList.toggle("force-dark", overPrepared || (overStory && !headerSections.story.classList.contains("is-dark")));
    dom.header.classList.toggle("force-light", overCatalog || overFooter || overRitual || (overStory && headerSections.story.classList.contains("is-dark")));
  }

  dom.carousel.addEventListener("pointerdown", onPointerDown);
  window.addEventListener("pointermove", onPointerMove, { passive: true });
  window.addEventListener("pointerup", onPointerUp);
  window.addEventListener("pointercancel", onPointerUp);
  document.documentElement.addEventListener("pointerleave", () => {
    state.lookTargetX = 0;
    state.lookTargetY = 0;
  });
  window.addEventListener("blur", () => {
    state.lookTargetX = 0;
    state.lookTargetY = 0;
  });
  dom.carousel.addEventListener("wheel", (event) => {
    if (Math.abs(event.deltaX) <= Math.abs(event.deltaY)) return;
    event.preventDefault();
    state.target += event.deltaX / 450;
    state.target = Math.round(state.target);
    goTo(modulo(state.target, products.length));
  }, { passive: false });

  document.querySelector("[data-previous]").addEventListener("click", () => step(-1));
  document.querySelector("[data-next]").addEventListener("click", () => step(1));
  dom.tabs.forEach((tab, index) => tab.addEventListener("click", () => goTo(index)));
  dom.cards.forEach((card, index) => card.addEventListener("click", () => {
    if (state.moved < 7) goTo(index);
  }));
  dom.lines.forEach((line, index) => line.addEventListener("click", () => goTo(index, { scrollTop: true })));
  document.querySelectorAll("[data-shop-select]").forEach((button) => {
    button.addEventListener("click", () => goTo(Number(button.dataset.shopSelect), { scrollTop: true }));
  });

  document.querySelector("[data-quantity-minus]").addEventListener("click", () => {
    state.quantity = clamp(state.quantity - 1, 1, 20);
    dom.quantity.textContent = String(state.quantity);
  });
  document.querySelector("[data-quantity-plus]").addEventListener("click", () => {
    state.quantity = clamp(state.quantity + 1, 1, 20);
    dom.quantity.textContent = String(state.quantity);
  });
  document.querySelector("[data-add-selected]").addEventListener("click", (event) => addToCart(products[state.selected].id, state.quantity, event.currentTarget));
  document.querySelectorAll("[data-quick-add]").forEach((button) => button.addEventListener("click", (event) => addToCart(button.dataset.quickAdd, 1, event.currentTarget)));

  document.querySelectorAll("[data-open-cart]").forEach((button) => button.addEventListener("click", openCart));
  document.querySelector("[data-close-cart]").addEventListener("click", () => closeCart());
  dom.clearCart.addEventListener("click", clearCart);
  dom.cartScrim.addEventListener("click", () => closeCart());
  document.querySelector("[data-cart-shop]").addEventListener("click", () => {
    closeCart({ restoreFocus: false });
    setView("shop", { scrollTargetId: "catalog" });
  });
  dom.cartItems.addEventListener("click", (event) => {
    const minus = event.target.closest("[data-cart-minus]");
    const plus = event.target.closest("[data-cart-plus]");
    const remove = event.target.closest("[data-cart-remove]");
    if (minus) changeCartQuantity(minus.dataset.cartMinus, -1, minus);
    if (plus) changeCartQuantity(plus.dataset.cartPlus, 1, plus);
    if (remove) removeCartItem(remove.dataset.cartRemove);
  });

  document.querySelectorAll("[data-open-search]").forEach((button) => button.addEventListener("click", openSearch));
  document.querySelector("[data-close-search]").addEventListener("click", closeSearch);
  dom.searchDialog.addEventListener("click", (event) => {
    if (event.target === dom.searchDialog) closeSearch();
  });
  dom.searchDialog.addEventListener("close", () => {
    if (!dom.checkoutDialog.open && !dom.cartDrawer.classList.contains("is-open")) document.body.classList.remove("is-locked");
  });
  dom.searchInput.addEventListener("input", () => filterSearch(dom.searchInput.value));
  dom.searchInput.addEventListener("keydown", (event) => {
    if (event.key !== "Enter") return;
    const firstVisible = dom.searchResults.find((result) => !result.hidden);
    if (firstVisible) selectSearchResult(Number(firstVisible.dataset.searchResult));
  });
  document.querySelectorAll("[data-suggestion]").forEach((button) => button.addEventListener("click", () => {
    dom.searchInput.value = button.dataset.suggestion;
    filterSearch(button.dataset.suggestion);
    dom.searchInput.focus();
  }));
  dom.searchResultsContainer.addEventListener("click", (event) => {
    const result = event.target.closest("[data-search-result]");
    if (result) selectSearchResult(Number(result.dataset.searchResult));
  });

  dom.catalogFilters.forEach((button) => {
    button.addEventListener("click", () => setCatalogFilter(button.dataset.catalogFilter));
  });
  dom.catalogAdds.forEach((button) => {
    button.addEventListener("click", (event) => {
      const id = button.dataset.catalogAdd;
      addToCart(id, state.catalogQuantities.get(id) || 1, event.currentTarget);
    });
  });
  dom.catalogQuantityMinuses.forEach((button) => {
    button.addEventListener("click", () => changeCatalogQuantity(button.dataset.catalogQtyMinus, -1));
  });
  dom.catalogQuantityPluses.forEach((button) => {
    button.addEventListener("click", () => changeCatalogQuantity(button.dataset.catalogQtyPlus, 1));
  });
  dom.catalogDetailButtons.forEach((button) => {
    button.addEventListener("click", () => showProductDetail(button.dataset.catalogDetail));
  });

  dom.language.addEventListener("change", () => applyLanguage(dom.language.value));

  document.querySelectorAll("[data-open-auth]").forEach((button) => button.addEventListener("click", openAuth));
  document.querySelector("[data-close-auth]").addEventListener("click", closeAuth);
  document.querySelectorAll("[data-auth-mode]").forEach((tab) => tab.addEventListener("click", () => setAuthMode(tab.dataset.authMode)));
  dom.authDialog.addEventListener("click", (event) => {
    if (event.target === dom.authDialog) closeAuth();
  });
  dom.authDialog.addEventListener("close", () => {
    if (!dom.checkoutDialog.open && !dom.searchDialog.open) document.body.classList.remove("is-locked");
  });
  dom.authForm.addEventListener("submit", submitAuth);
  dom.authLogout.addEventListener("click", logout);

  document.querySelectorAll("[data-open-legal]").forEach((button) => button.addEventListener("click", openLegal));
  document.querySelector("[data-close-legal]").addEventListener("click", closeLegal);
  dom.legalDialog.addEventListener("click", (event) => {
    if (event.target === dom.legalDialog) closeLegal();
  });
  dom.legalDialog.addEventListener("close", () => {
    if (!dom.checkoutDialog.open && !dom.searchDialog.open) document.body.classList.remove("is-locked");
  });

  dom.checkoutButton.addEventListener("click", openCheckout);
  document.querySelector("[data-close-checkout]").addEventListener("click", closeCheckout);
  document.querySelector("[data-finish-checkout]").addEventListener("click", closeCheckout);
  dom.checkoutDialog.addEventListener("click", (event) => {
    if (event.target === dom.checkoutDialog) closeCheckout();
  });
  dom.checkoutDialog.addEventListener("close", () => document.body.classList.remove("is-locked"));
  dom.checkoutForm.addEventListener("submit", submitCheckout);

  dom.navToggle.addEventListener("click", () => toggleNavigation());
  dom.nav.querySelectorAll("a").forEach((link) => link.addEventListener("click", () => toggleNavigation(false)));

  dom.viewToggles.forEach((toggle) => {
    toggle.addEventListener("click", (event) => {
      const href = toggle.getAttribute("href");
      const rawTargetId = href && href.startsWith("#") ? href.slice(1) : null;
      const targetId = rawTargetId === "top" || rawTargetId === "refrescos" ? null : rawTargetId;
      event.preventDefault();
      if (toggle.dataset.departmentFilter) setCatalogFilter(toggle.dataset.departmentFilter);
      setView(toggle.dataset.viewToggle, { scrollTargetId: targetId });
    });
  });

  document.querySelectorAll("[data-department-filter]:not([data-view-toggle])").forEach((control) => {
    control.addEventListener("click", () => {
      setCatalogFilter(control.dataset.departmentFilter);
      setView("shop", { scrollTargetId: "catalog" });
    });
  });

  window.addEventListener("keydown", (event) => {
    const dialogOpen = dom.searchDialog.open || dom.checkoutDialog.open || dom.legalDialog.open || dom.authDialog.open;
    if (event.key === "Escape" && dom.cartDrawer.classList.contains("is-open")) closeCart();
    if (dialogOpen || ["INPUT", "TEXTAREA"].includes(document.activeElement?.tagName)) return;
    if (event.key === "ArrowRight") {
      if (state.currentView === "refrescos" && stepActiveRefresco) stepActiveRefresco(1);
      else step(1);
    }
    if (event.key === "ArrowLeft") {
      if (state.currentView === "refrescos" && stepActiveRefresco) stepActiveRefresco(-1);
      else step(-1);
    }
  });

  if (drinkProducts.length) {
    const refrescoDom = {
      carousel: document.querySelector("[data-refresco-carousel]"),
      cards: [...document.querySelectorAll("[data-refresco-card]")],
      tabs: [...document.querySelectorAll("[data-refresco-select]")],
      info: document.querySelector(".refrescos-info"),
      sku: document.querySelector("[data-refresco-sku]"),
      category: document.querySelector("[data-refresco-category]"),
      name: document.querySelector("[data-refresco-name]"),
      nameEn: document.querySelector("[data-refresco-name-en]"),
      nameZh: document.querySelector("[data-refresco-name-zh]"),
      description: document.querySelector("[data-refresco-description]"),
      weight: document.querySelector("[data-refresco-weight]"),
      caseSize: document.querySelector("[data-refresco-case]"),
      price: document.querySelector("[data-refresco-price]"),
      unitPrice: document.querySelector("[data-refresco-unit-price]"),
      promo: document.querySelector("[data-refresco-promo]"),
      sweetness: document.querySelector("[data-refresco-sweetness]"),
      kcal: document.querySelector("[data-refresco-kcal]"),
      kcalBasis: document.querySelector("[data-refresco-kcal-basis]"),
      quantity: document.querySelector("[data-refresco-quantity]"),
      addSelected: document.querySelector("[data-refresco-add-selected]"),
      detailButtons: [...document.querySelectorAll("[data-refresco-detail]")],
      detailLabels: [...document.querySelectorAll("[data-refresco-detail-label]")],
      story: document.querySelector("[data-refresco-story]"),
      storyBrand: document.querySelector("[data-refresco-story-brand]"),
      storyCategory: document.querySelector("[data-refresco-story-category]"),
      storySku: document.querySelector("[data-refresco-story-sku]"),
      storyTitle: document.querySelector("[data-refresco-story-title]"),
      storyNameEn: document.querySelector("[data-refresco-story-name-en]"),
      storyNameZh: document.querySelector("[data-refresco-story-name-zh]"),
      storyDescription: document.querySelector("[data-refresco-story-description]"),
      storySweetness: document.querySelector("[data-refresco-story-sweetness]"),
      storyKcal: document.querySelector("[data-refresco-story-kcal]"),
      storyKcalBasis: document.querySelector("[data-refresco-story-kcal-basis]"),
      storyUnit: document.querySelector("[data-refresco-story-unit]"),
      storyCase: document.querySelector("[data-refresco-story-case]"),
      storyPrice: document.querySelector("[data-refresco-story-price]"),
      storySource: document.querySelector("[data-refresco-story-source]"),
      storyImage: document.querySelector("[data-refresco-story-image]"),
      storyNote: document.querySelector("[data-refresco-story-note]"),
    };

    const refrescoState = {
      selected: 0,
      quantity: 1,
      angle: 0,
      target: 0,
      velocity: 0,
      dragging: false,
      dragStartX: 0,
      dragStartAngle: 0,
      lastX: 0,
      moved: 0,
      detailProductId: String(drinkProducts[0].id),
    };

    function refrescoDistance(value) {
      return modulo(value + drinkProducts.length / 2, drinkProducts.length) - drinkProducts.length / 2;
    }

    function refrescoCycleTo(index) {
      const rounded = Math.round(refrescoState.target);
      const current = modulo(rounded, drinkProducts.length);
      return rounded + refrescoDistance(index - current);
    }

    function localizeRefrescoControls() {
      refrescoDom.cards.forEach((card, cardIndex) => {
        const cardProduct = localizedProduct(drinkProducts[cardIndex]);
        card.setAttribute("aria-label", t("refrescos.select", { name: cardProduct.name }));
        const image = card.querySelector("img");
        if (image) image.alt = cardProduct.name;
      });
      refrescoDom.tabs.forEach((tab, tabIndex) => {
        tab.textContent = localizedProduct(drinkProducts[tabIndex]).name;
      });
    }

    const refrescoDetailButtonById = new Map(
      refrescoDom.detailButtons.map((button) => [button.dataset.refrescoDetail, button])
    );
    const refrescoDetailLabelById = new Map(
      refrescoDom.detailLabels.map((label) => [label.dataset.refrescoDetailLabel, label])
    );

    function renderRefrescoStoryById(id, { animate = true } = {}) {
      const index = drinkProducts.findIndex((product) => product.id === String(id));
      if (index < 0 || !refrescoDom.story) return;
      const baseProduct = drinkProducts[index];
      const product = localizedProduct(baseProduct);
      const previousDetailId = refrescoState.detailProductId;

      refrescoDom.story.dataset.detailId = product.id;
      refrescoDom.story.dataset.category = baseProduct.category;
      refrescoDom.story.classList.remove("is-changing");
      if (animate) requestAnimationFrame(() => refrescoDom.story.classList.add("is-changing"));
      if (refrescoDom.storyBrand) refrescoDom.storyBrand.textContent = product.brand;
      if (refrescoDom.storyCategory) refrescoDom.storyCategory.textContent = t(`refrescos.filter.${baseProduct.category}`);
      if (refrescoDom.storySku) refrescoDom.storySku.textContent = product.sku;
      if (refrescoDom.storyTitle) refrescoDom.storyTitle.textContent = product.name;
      if (refrescoDom.storyNameEn) refrescoDom.storyNameEn.textContent = product.name_en || "";
      if (refrescoDom.storyNameZh) refrescoDom.storyNameZh.textContent = product.name_zh || "";
      if (refrescoDom.storyDescription) refrescoDom.storyDescription.textContent = product.description || "";
      if (refrescoDom.storySweetness) refrescoDom.storySweetness.textContent = `${product.sweetness_level}/5`;
      if (refrescoDom.storyKcal) refrescoDom.storyKcal.textContent = product.kcal;
      if (refrescoDom.storyKcalBasis) refrescoDom.storyKcalBasis.textContent = product.kcal_basis;
      if (refrescoDom.storyUnit) refrescoDom.storyUnit.textContent = translateWeight(product.unit_size);
      if (refrescoDom.storyCase) refrescoDom.storyCase.textContent = packLabel(product);
      if (refrescoDom.storyPrice) refrescoDom.storyPrice.textContent = product.price_label;
      if (refrescoDom.storySource) refrescoDom.storySource.href = product.nutrition_source_url || "#";
      if (refrescoDom.storyImage) {
        const image = product.image.replace("/refrescos/", "/refrescos/cutouts/");
        if (refrescoDom.storyImage.getAttribute("src") !== image) refrescoDom.storyImage.src = image;
      }
      if (refrescoDom.storyNote) {
        refrescoDom.storyNote.innerHTML = `${escapeHtml(product.brand)}<br>${escapeHtml(product.unit_size)}`;
      }

      refrescoState.detailProductId = String(product.id);
      updateRefrescoDetailButtons(previousDetailId, refrescoState.detailProductId);
    }

    function setRefrescoTheme(index, { centerTab = true, localizeControls = false } = {}) {
      const baseProduct = drinkProducts[index];
      const product = localizedProduct(baseProduct);
      const previousIndex = refrescoState.selected;
      refrescoState.selected = index;
      preloadCarouselWindow(refrescoDom.cards, index);

      refrescoDom.info?.classList.remove("is-changing");
      requestAnimationFrame(() => refrescoDom.info?.classList.add("is-changing"));

      if (refrescoDom.sku) refrescoDom.sku.textContent = product.sku;
      if (refrescoDom.category) refrescoDom.category.textContent = baseProduct.category
        ? t(`refrescos.filter.${baseProduct.category}`)
        : product.category_label || t("refrescos.type");
      if (refrescoDom.name) refrescoDom.name.textContent = product.name;
      if (refrescoDom.nameEn) refrescoDom.nameEn.textContent = product.name_en || "";
      if (refrescoDom.nameZh) refrescoDom.nameZh.textContent = product.name_zh || "";
      if (refrescoDom.description) refrescoDom.description.textContent = product.description || "";
      if (refrescoDom.weight) refrescoDom.weight.textContent = `${product.unit_size} · ${unitNounSingular(product)}`;
      if (refrescoDom.caseSize) refrescoDom.caseSize.textContent = packLabel(product);
      if (refrescoDom.price) refrescoDom.price.textContent = product.price_label;
      if (refrescoDom.unitPrice) refrescoDom.unitPrice.textContent = product.unit_price_label || "";
      if (refrescoDom.promo) {
        refrescoDom.promo.textContent = product.promo ? t(product.promo) : "";
        refrescoDom.promo.hidden = !product.promo;
      }
      if (refrescoDom.kcal) refrescoDom.kcal.textContent = product.kcal;
      if (refrescoDom.kcalBasis) refrescoDom.kcalBasis.textContent = product.kcal_basis;
      if (refrescoDom.sweetness) {
        refrescoDom.sweetness.hidden = product.sweetness_applicable !== true;
        refrescoDom.sweetness.setAttribute("aria-label", product.sweetness_label || "");
        const fill = refrescoDom.sweetness.querySelector("i");
        const label = refrescoDom.sweetness.querySelector("small");
        if (fill) fill.style.setProperty("--sweetness", `${product.sweetness}%`);
        if (label) label.textContent = product.sweetness_label || "";
      }
      if (refrescoDom.addSelected) {
        refrescoDom.addSelected.disabled = product.is_available === false;
        const label = refrescoDom.addSelected.querySelector("[data-i18n]");
        if (label) label.textContent = t(product.is_available === false ? "catalog.soldOut" : "wholesale.addCase");
      }

      if (localizeControls) localizeRefrescoControls();
      new Set([previousIndex, index]).forEach((cardIndex) => {
        const active = cardIndex === index;
        refrescoDom.cards[cardIndex]?.classList.toggle("is-active", active);
        refrescoDom.cards[cardIndex]?.setAttribute("aria-pressed", String(active));
        refrescoDom.tabs[cardIndex]?.classList.toggle("is-active", active);
        refrescoDom.tabs[cardIndex]?.setAttribute("aria-pressed", String(active));
      });
      const activeTab = refrescoDom.tabs[index];
      if (activeTab && centerTab) centerTabInScroller(activeTab);
    }

    function updateRefrescoDetailButtons(previousId, activeId) {
      new Set([previousId, activeId].filter(Boolean)).forEach((id) => {
        const active = id === activeId;
        const button = refrescoDetailButtonById.get(id);
        const label = refrescoDetailLabelById.get(id);
        button?.setAttribute("aria-pressed", String(active));
        button?.closest("[data-refresco-catalog-card]")?.classList.toggle("is-detail-selected", active);
        if (label) label.textContent = t(active ? "catalog.selected" : "catalog.details");
      });
    }

    function showRefrescoDetail(id) {
      const index = drinkProducts.findIndex((product) => product.id === String(id));
      if (index < 0) return;
      goToRefresco(index);
      renderRefrescoStoryById(id);
      const target = refrescoDom.story;
      if (target) {
        const scrollToStory = (behavior = reducedMotion ? "auto" : "smooth") => {
          const headerOffset = dom.header?.getBoundingClientRect().height || 0;
          const top = documentOffsetTop(target) - headerOffset - 20;
          window.scrollTo({ top: Math.max(0, top), behavior });
        };
        scrollToStory();
        window.setTimeout(() => scrollToStory("auto"), reducedMotion ? 0 : 850);
        window.setTimeout(() => scrollToStory("auto"), reducedMotion ? 0 : 1700);
      }
      window.setTimeout(
        () => refrescoDom.storyTitle?.focus({ preventScroll: true }),
        reducedMotion ? 0 : 1850
      );
    }

    let refrescoFrame = 0;
    let refrescoInView = false;
    let refrescoPrepared = false;
    let lastRefrescoFrameTime = performance.now();
    let lastRefrescoCandidates = new Set();

    function queueRefrescoDraw() {
      if (!refrescoFrame && refrescoInView && !document.hidden) {
        refrescoFrame = requestAnimationFrame(drawRefrescoCarousel);
      }
    }

    function goToRefresco(index) {
      const normalized = modulo(index, drinkProducts.length);
      setCarouselTarget(refrescoState, refrescoCycleTo(normalized));
      setRefrescoTheme(normalized);
      queueRefrescoDraw();
    }

    function stepRefresco(direction) {
      goToRefresco(refrescoState.selected + direction);
    }

    stepActiveRefresco = stepRefresco;

    function drawRefrescoCarousel(frameTime = performance.now()) {
      refrescoFrame = 0;
      if (refrescoDom.carousel) {
        const frameScale = clamp((frameTime - lastRefrescoFrameTime) / 16.667, 0.25, 3);
        lastRefrescoFrameTime = frameTime;
        if (!refrescoState.dragging) advanceCarouselMotion(refrescoState, frameScale);

        if (!refrescoPrepared) {
          refrescoPrepared = true;
        }

        const shellWidth = refrescoDom.carousel.clientWidth || 360;
        const compactCarousel = window.innerWidth <= 820;
        const radius = clamp(shellWidth * (compactCarousel ? 0.58 : 0.52), compactCarousel ? 165 : 260, compactCarousel ? 250 : 450);
        const depth = clamp(shellWidth * 0.42, compactCarousel ? 145 : 220, compactCarousel ? 240 : 370);
        const candidates = new Set([-1, 0, 1].map((offset) => modulo(refrescoState.selected + offset, drinkProducts.length)));
        lastRefrescoCandidates.forEach((index) => {
          if (candidates.has(index)) return;
          const card = refrescoDom.cards[index];
          card.classList.remove("is-rendered");
          card.style.opacity = "0";
          card.style.pointerEvents = "none";
          card.tabIndex = -1;
          card.setAttribute("aria-hidden", "true");
        });
        candidates.forEach((index) => {
          const card = refrescoDom.cards[index];
          if (!lastRefrescoCandidates.has(index)) card.classList.add("is-rendered");
          const distance = refrescoDistance(index - refrescoState.angle);
          const absoluteDistance = Math.abs(distance);
          const selectedDistance = Math.abs(refrescoDistance(index - refrescoState.selected));
          const isVisible = selectedDistance <= 1;
          if (isVisible) activateCarouselImage(card, index === refrescoState.selected ? "high" : "low");
          const theta = clamp(distance, -4, 4) * 0.52;
          const x = Math.sin(theta) * radius;
          const z = (Math.cos(theta) - 1) * depth;
          const proximity = clamp(1 + z / (depth * 2.6), 0, 1);
          const scale = 0.68 + proximity * 0.32;
          const rotationY = distance * -24;
          const float = reducedMotion || mobileMode ? 0 : Math.sin(frameTime / 2100 + index * 2.1) * 3 * proximity;
          card.style.transform = `translate3d(${x.toFixed(1)}px, ${float.toFixed(1)}px, ${z.toFixed(1)}px) rotateY(${rotationY.toFixed(1)}deg) scale(${scale.toFixed(3)})`;
          card.style.opacity = isVisible ? String(0.38 + proximity * 0.62) : "0";
          card.style.zIndex = String(1000 + Math.round(z));
          const pointerEvents = isVisible ? "auto" : "none";
          const tabIndex = absoluteDistance < 0.55 ? 0 : -1;
          const ariaHidden = String(!isVisible);
          if (card.style.pointerEvents !== pointerEvents) card.style.pointerEvents = pointerEvents;
          if (card.tabIndex !== tabIndex) card.tabIndex = tabIndex;
          if (card.getAttribute("aria-hidden") !== ariaHidden) card.setAttribute("aria-hidden", ariaHidden);
        });
        lastRefrescoCandidates = candidates;
      }
      const refrescoMoving = refrescoState.dragging
        || Math.abs(refrescoState.target - refrescoState.angle) > 0.0008
        || Math.abs(refrescoState.velocity) > 0.0008;
      if (refrescoMoving) queueRefrescoDraw();
    }

    function refrescoNearestSelectionFromAngle() {
      const selected = modulo(Math.round(refrescoState.angle), drinkProducts.length);
      if (selected !== refrescoState.selected) setRefrescoTheme(selected);
    }

    function onRefrescoPointerDown(event) {
      if (event.pointerType === "mouse" && event.button !== 0) return;
      refrescoState.dragging = true;
      refrescoState.dragStartX = event.clientX;
      refrescoState.lastX = event.clientX;
      refrescoState.dragStartAngle = refrescoState.angle;
      refrescoState.moved = 0;
      refrescoState.velocity = 0;
      refrescoDom.carousel.classList.add("is-dragging");
      refrescoDom.carousel.setPointerCapture?.(event.pointerId);
      queueRefrescoDraw();
    }

    function onRefrescoPointerMove(event) {
      if (!refrescoState.dragging) return;
      const delta = event.clientX - refrescoState.dragStartX;
      refrescoState.moved = Math.max(refrescoState.moved, Math.abs(delta));
      const shellWidth = refrescoDom.carousel.clientWidth || 360;
      refrescoState.angle = refrescoState.dragStartAngle - delta / clamp(shellWidth * 0.72, 180, 380);
      refrescoState.velocity = -(event.clientX - refrescoState.lastX) / 260;
      refrescoState.lastX = event.clientX;
      refrescoNearestSelectionFromAngle();
      queueRefrescoDraw();
    }

    function onRefrescoPointerUp(event) {
      if (!refrescoState.dragging) return;
      refrescoState.dragging = false;
      refrescoDom.carousel.classList.remove("is-dragging");
      refrescoDom.carousel.releasePointerCapture?.(event.pointerId);
      refrescoState.target = Math.round(refrescoState.angle + refrescoState.velocity * 2.4);
      goToRefresco(modulo(refrescoState.target, drinkProducts.length));
    }

    refrescoDom.carousel.addEventListener("pointerdown", onRefrescoPointerDown);
    window.addEventListener("pointermove", onRefrescoPointerMove, { passive: true });
    window.addEventListener("pointerup", onRefrescoPointerUp);
    window.addEventListener("pointercancel", onRefrescoPointerUp);

    document.querySelector("[data-refresco-previous]")?.addEventListener("click", () => stepRefresco(-1));
    document.querySelector("[data-refresco-next]")?.addEventListener("click", () => stepRefresco(1));
    refrescoDom.tabs.forEach((tab, index) => tab.addEventListener("click", () => goToRefresco(index)));
    refrescoDom.cards.forEach((card, index) => card.addEventListener("click", () => {
      if (refrescoState.moved < 7) goToRefresco(index);
    }));

    document.querySelector("[data-refresco-quantity-minus]")?.addEventListener("click", () => {
      refrescoState.quantity = clamp(refrescoState.quantity - 1, 1, 20);
      if (refrescoDom.quantity) refrescoDom.quantity.textContent = String(refrescoState.quantity);
    });
    document.querySelector("[data-refresco-quantity-plus]")?.addEventListener("click", () => {
      refrescoState.quantity = clamp(refrescoState.quantity + 1, 1, 20);
      if (refrescoDom.quantity) refrescoDom.quantity.textContent = String(refrescoState.quantity);
    });
    refrescoDom.detailButtons.forEach((button) =>
      button.addEventListener("click", () => showRefrescoDetail(button.dataset.refrescoDetail))
    );

    refrescoDom.addSelected?.addEventListener("click", (event) => {
      addToCart(drinkProducts[refrescoState.selected].id, refrescoState.quantity, event.currentTarget);
    });

    let refrescoInitialized = false;
    refreshRefrescos = () => {
      if (!refrescoInitialized) return;
      setRefrescoTheme(refrescoState.selected, { centerTab: false, localizeControls: true });
      renderRefrescoStoryById(refrescoState.detailProductId, { animate: false });
    };
    renderRefrescoStoryById(refrescoState.detailProductId, { animate: false });
    const refrescoVisibility = new IntersectionObserver((entries) => {
      refrescoInView = entries.some((entry) => entry.isIntersecting);
      if (refrescoInView) {
        if (!refrescoInitialized) {
          refrescoInitialized = true;
          setRefrescoTheme(refrescoState.selected, { centerTab: false, localizeControls: true });
        }
        queueRefrescoDraw();
      }
    }, { rootMargin: "160px 0px" });
    refrescoVisibility.observe(refrescoDom.carousel);

    const refrescoCatalogDom = {
      filters: [...document.querySelectorAll("[data-refresco-catalog-filter]")],
      cards: [...document.querySelectorAll("[data-refresco-catalog-card]")],
      adds: [...document.querySelectorAll("[data-refresco-catalog-add]")],
      quantityOutputs: [...document.querySelectorAll("[data-refresco-catalog-quantity]")],
      quantityMinuses: [...document.querySelectorAll("[data-refresco-catalog-qty-minus]")],
      quantityPluses: [...document.querySelectorAll("[data-refresco-catalog-qty-plus]")],
    };
    const refrescoCatalogQuantities = new Map(drinkProducts.map((product) => [product.id, 1]));

    function setRefrescoCatalogFilter(category) {
      refrescoCatalogDom.filters.forEach((button) => {
        const active = button.dataset.refrescoCatalogFilter === category;
        button.classList.toggle("is-active", active);
        button.setAttribute("aria-pressed", String(active));
      });
      refrescoCatalogDom.cards.forEach((card) => {
        card.hidden = category !== "all" && card.dataset.category !== category;
      });
    }

    function changeRefrescoCatalogQuantity(id, delta) {
      const next = clamp((refrescoCatalogQuantities.get(id) || 1) + delta, 1, 20);
      refrescoCatalogQuantities.set(id, next);
      const output = refrescoCatalogDom.quantityOutputs.find((element) => element.dataset.refrescoCatalogQuantity === id);
      if (output) output.textContent = String(next);
    }

    refrescoCatalogDom.filters.forEach((button) => {
      button.addEventListener("click", () => setRefrescoCatalogFilter(button.dataset.refrescoCatalogFilter));
    });
    refrescoCatalogDom.adds.forEach((button) => {
      button.addEventListener("click", (event) => {
        const id = button.dataset.refrescoCatalogAdd;
        addToCart(id, refrescoCatalogQuantities.get(id) || 1, event.currentTarget);
      });
    });
    refrescoCatalogDom.quantityMinuses.forEach((button) => {
      button.addEventListener("click", () => changeRefrescoCatalogQuantity(button.dataset.refrescoCatalogQtyMinus, -1));
    });
    refrescoCatalogDom.quantityPluses.forEach((button) => {
      button.addEventListener("click", () => changeRefrescoCatalogQuantity(button.dataset.refrescoCatalogQtyPlus, 1));
    });

  }

  const revealObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add("is-visible");
      observer.unobserve(entry.target);
    });
  }, { threshold: 0.12 });
  document.querySelectorAll(".reveal").forEach((element) => revealObserver.observe(element));

  const carouselVisibility = new IntersectionObserver((entries) => {
    carouselInView = entries.some((entry) => entry.isIntersecting);
    if (carouselInView) queueCarouselDraw();
    else flushCarouselSideEffects();
  }, { rootMargin: "120px 0px" });
  carouselVisibility.observe(dom.carousel);

  let headerFrame = 0;
  function queueHeaderUpdate() {
    if (headerFrame) return;
    headerFrame = requestAnimationFrame(() => {
      headerFrame = 0;
      updateHeader();
    });
  }

  window.addEventListener("scroll", queueHeaderUpdate, { passive: true });
  function handleViewportChange() {
    const deviceChanged = syncDevicePresentation();
    if (deviceChanged && mobileMode) {
      state.lookX = 0;
      state.lookY = 0;
      state.lookTargetX = 0;
      state.lookTargetY = 0;
    }
    invalidateHeaderMetrics();
    queueHeaderUpdate();
    queueCarouselDraw();
  }
  window.addEventListener("resize", handleViewportChange, { passive: true });
  window.addEventListener("orientationchange", handleViewportChange, { passive: true });
  [phoneViewport, compactViewport, coarsePointer].forEach((query) => {
    query.addEventListener?.("change", handleViewportChange);
  });
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) queueCarouselDraw();
  });

  applyLanguage(state.language, { persist: false, initial: true });
  loadCurrentUser();
  updateHeader();
  queueCarouselDraw();
})();
