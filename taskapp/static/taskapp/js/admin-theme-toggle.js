(function () {
  const STORAGE_KEY = "taskapp-admin-theme";
  const DARK_THEME = "/static/vendor/bootswatch/cyborg/bootstrap.min.css";
  const LIGHT_THEME = "/static/vendor/bootswatch/flatly/bootstrap.min.css";

  function injectToggleStyles() {
    if (document.getElementById("task-theme-toggle-styles")) return;
    const style = document.createElement("style");
    style.id = "task-theme-toggle-styles";
    style.textContent = `
      .theme-toggle-group {
        display: inline-flex !important;
        align-items: center !important;
        gap: 0.45rem !important;
        padding: 0.3rem 0.55rem 0.3rem 0.3rem !important;
        margin: 0.15rem 0.75rem 0 0 !important;
        border: 1px solid rgba(148,163,184,0.25) !important;
        border-radius: 999px !important;
        background: rgba(255,255,255,0.05) !important;
      }
      .theme-toggle-group .theme-toggle-label {
        color: #e5eefb !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.02em !important;
        padding-left: 0.25rem !important;
      }
      .theme-toggle-mode {
        color: #97a3b6 !important;
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        min-width: 2.6rem !important;
      }
      .theme-switch {
        position: relative !important;
        display: inline-block !important;
        width: 3.6rem !important;
        height: 1.9rem !important;
        margin: 0 !important;
        cursor: pointer !important;
        flex-shrink: 0 !important;
      }
      .theme-switch input[type="checkbox"] {
        position: absolute !important;
        inset: 0 !important;
        opacity: 0 !important;
        width: 100% !important;
        height: 100% !important;
        margin: 0 !important;
        cursor: pointer !important;
        z-index: 2 !important;
        appearance: none !important;
        -webkit-appearance: none !important;
      }
      .theme-switch-track {
        position: absolute !important;
        inset: 0 !important;
        border-radius: 999px !important;
        background: rgba(15,23,42,0.75) !important;
        border: 1.5px solid rgba(148,163,184,0.3) !important;
        transition: background 0.25s ease, border-color 0.25s ease !important;
        display: block !important;
        overflow: visible !important;
      }
      .theme-switch-thumb {
        position: absolute !important;
        top: 0.14rem !important;
        left: 0.14rem !important;
        width: 1.58rem !important;
        height: 1.58rem !important;
        border-radius: 50% !important;
        background: linear-gradient(135deg,#1e3a5f,#1e293b) !important;
        color: #93c5fd !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-size: 0.75rem !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.5) !important;
        transition: transform 0.28s cubic-bezier(0.34,1.56,0.64,1), background 0.25s ease !important;
        pointer-events: none !important;
        z-index: 1 !important;
      }
      .theme-switch-icon-light { display: none !important; }
      .theme-switch input[type="checkbox"]:checked ~ .theme-switch-track {
        background: rgba(37,99,235,0.28) !important;
        border-color: rgba(59,130,246,0.55) !important;
      }
      .theme-switch input[type="checkbox"]:checked ~ .theme-switch-track .theme-switch-thumb {
        transform: translateX(1.66rem) !important;
        background: linear-gradient(135deg,#3b82f6,#22d3ee) !important;
        color: #fff !important;
      }
      .theme-switch input[type="checkbox"]:checked ~ .theme-switch-track .theme-switch-icon-dark { display: none !important; }
      .theme-switch input[type="checkbox"]:checked ~ .theme-switch-track .theme-switch-icon-light { display: inline-block !important; }
    `;
    document.head.appendChild(style);
  }

  function getThemeLink() {
    return document.getElementById("jazzmin-theme");
  }

  function getStoredTheme() {
    try {
      return window.localStorage.getItem(STORAGE_KEY) || "dark";
    } catch (error) {
      return "dark";
    }
  }

  function storeTheme(theme) {
    try {
      window.localStorage.setItem(STORAGE_KEY, theme);
    } catch (error) {
      // localStorage can be unavailable in hardened browsers.
    }
  }

  function setActiveButton(theme) {
    const checkbox = document.getElementById("task-theme-checkbox");
    const label = document.getElementById("task-theme-label");

    if (checkbox) {
      checkbox.checked = theme === "light";
    }

    if (label) {
      label.textContent = theme === "light" ? "Light" : "Dark";
    }
  }

  function ensureThemeStylesheet() {
    let styleTag = document.getElementById("task-theme-runtime-styles");
    if (!styleTag) {
      styleTag = document.createElement("style");
      styleTag.id = "task-theme-runtime-styles";
      document.head.appendChild(styleTag);
    }
    return styleTag;
  }

  function applyThemeStyles(theme) {
    const styleTag = ensureThemeStylesheet();
    const isDark = theme === "dark";
    if (!isDark) {
      styleTag.textContent = "";
      return;
    }

    styleTag.textContent = `
      body[data-dashboard-theme="dark"] {
        color-scheme: dark;
      }

      body[data-dashboard-theme="dark"] .select2-container--default .select2-selection--single,
      body[data-dashboard-theme="dark"] .select2-container--default .select2-selection--multiple,
      body[data-dashboard-theme="dark"] .select2-container--default .select2-selection {
        background: #0d1320 !important;
        background-color: #0d1320 !important;
        color: #e5eefb !important;
        border: 1px solid rgba(148, 163, 184, 0.14) !important;
        box-shadow: none !important;
      }

      body[data-dashboard-theme="dark"] .select2-container--default .select2-selection--single .select2-selection__rendered,
      body[data-dashboard-theme="dark"] .select2-container--default .select2-selection--multiple .select2-selection__rendered,
      body[data-dashboard-theme="dark"] .select2-container--default .select2-selection__placeholder,
      body[data-dashboard-theme="dark"] .select2-container--default .select2-selection__choice,
      body[data-dashboard-theme="dark"] .select2-container--default .select2-selection__clear,
      body[data-dashboard-theme="dark"] .select2-container--default .select2-selection__arrow b {
        color: #e5eefb !important;
      }

      body[data-dashboard-theme="dark"] .select2-container--default .select2-search__field,
      body[data-dashboard-theme="dark"] .select2-container--default .select2-search--dropdown .select2-search__field,
      body[data-dashboard-theme="dark"] .select2-container--default .select2-dropdown,
      body[data-dashboard-theme="dark"] .select2-dropdown,
      body[data-dashboard-theme="dark"] .select2-results,
      body[data-dashboard-theme="dark"] .select2-results__options,
      body[data-dashboard-theme="dark"] .select2-results__option {
        background: #0d1320 !important;
        background-color: #0d1320 !important;
        color: #e5eefb !important;
        border-color: rgba(148, 163, 184, 0.14) !important;
      }

      body[data-dashboard-theme="dark"] .select2-container--default .select2-results__option--highlighted[aria-selected],
      body[data-dashboard-theme="dark"] .select2-container--default .select2-results__option[aria-selected='true'] {
        background: rgba(59, 130, 246, 0.18) !important;
        color: #ffffff !important;
      }
    `;
  }

  function applyTheme(theme) {
    const themeLink = getThemeLink();
    if (!themeLink) {
      return;
    }

    const isDark = theme === "dark";
    themeLink.href = isDark ? DARK_THEME : LIGHT_THEME;

    document.body.dataset.dashboardTheme = isDark ? "dark" : "light";
    document.documentElement.dataset.dashboardTheme = isDark ? "dark" : "light";

    document.body.classList.toggle("theme-dark", isDark);
    document.body.classList.toggle("theme-light", !isDark);

    setActiveButton(theme);
    storeTheme(theme);
    applyThemeStyles(theme);
  }

  function createToggle() {
    const target = document.querySelector("#jazzy-navbar .navbar-nav.ml-auto");
    if (!target || document.getElementById("task-theme-toggle")) {
      return;
    }

    const wrapper = document.createElement("li");
    wrapper.className =
      "nav-item dropdown d-none d-sm-inline-flex align-items-center";
    wrapper.id = "task-theme-toggle";

    wrapper.innerHTML = `
      <div class="theme-toggle-group">
        <span class="theme-toggle-label">Theme</span>
        <label class="theme-switch" title="Toggle light theme">
          <input id="task-theme-checkbox" type="checkbox" aria-label="Toggle admin theme">
          <span class="theme-switch-track">
            <span class="theme-switch-thumb">
              <i class="fas fa-moon theme-switch-icon-dark"></i>
              <i class="fas fa-sun theme-switch-icon-light"></i>
            </span>
          </span>
        </label>
        <span id="task-theme-label" class="theme-toggle-mode">Dark</span>
      </div>
    `;

    target.prepend(wrapper);

    const checkbox = wrapper.querySelector("#task-theme-checkbox");
    if (checkbox) {
      checkbox.addEventListener("change", () => {
        applyTheme(checkbox.checked ? "light" : "dark");
      });
    }
  }

  function init() {
    injectToggleStyles();
    const preferredTheme = getStoredTheme();
    applyTheme(preferredTheme === "light" ? "light" : "dark");
    createToggle();

    const observer = new MutationObserver(() => {
      if (document.body.dataset.dashboardTheme === "dark") {
        applyThemeStyles("dark");
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true,
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
