(function () {
  const STORAGE_KEY = "taskapp-admin-theme";
  const DARK_THEME = "/static/vendor/bootswatch/cyborg/bootstrap.min.css";
  const LIGHT_THEME = "/static/vendor/bootswatch/flatly/bootstrap.min.css";

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
    const preferredTheme = getStoredTheme();
    applyTheme(preferredTheme === "light" ? "light" : "dark");
    createToggle();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
