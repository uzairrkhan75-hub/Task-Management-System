(function () {
  function stripPrefixVariants(el, prefix) {
    if (!prefix || typeof prefix !== 'string') {
      return;
    }
    Array.from(el.classList).forEach(function (c) {
      if (c.indexOf(prefix + '--') === 0) {
        el.classList.remove(c);
      }
    });
  }

  function syncMechanic(sel) {
    stripPrefixVariants(sel, 'mechanic-status-select');
    var map = { free: 'free', busy: 'busy', on_leave: 'on-leave' };
    sel.classList.add(
      'mechanic-status-select--' + (map[sel.value] || 'free'),
    );
  }

  function syncEnum(sel, prefix) {
    if (!prefix || typeof prefix !== 'string') {
      return;
    }
    stripPrefixVariants(sel, prefix);
    var v = (sel.value || '').replace(/_/g, '-');
    if (v) {
      sel.classList.add(prefix + '--' + v);
    }
  }

  function init() {
    document.querySelectorAll('.mechanic-status-select').forEach(function (sel) {
      if (sel.dataset.enumThemeBound === '1') {
        return;
      }
      sel.dataset.enumThemeBound = '1';
      syncMechanic(sel);
      sel.addEventListener('change', function () {
        syncMechanic(sel);
      });
    });

    document.querySelectorAll('select.enum-task-status').forEach(function (sel) {
      if (sel.dataset.enumThemeBound === '1') {
        return;
      }
      sel.dataset.enumThemeBound = '1';
      syncEnum(sel, 'enum-task-status');
      sel.addEventListener('change', function () {
        syncEnum(sel, 'enum-task-status');
      });
    });

    document.querySelectorAll('select.enum-task-priority').forEach(function (sel) {
      if (sel.dataset.enumThemeBound === '1') {
        return;
      }
      sel.dataset.enumThemeBound = '1';
      syncEnum(sel, 'enum-task-priority');
      sel.addEventListener('change', function () {
        syncEnum(sel, 'enum-task-priority');
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
