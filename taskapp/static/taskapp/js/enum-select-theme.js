(function () {
  function stripPrefixVariants(el, prefix) {
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
    stripPrefixVariants(sel, prefix);
    var v = (sel.value || '').replace(/_/g, '-');
    if (v) {
      sel.classList.add(prefix + '--' + v);
    }
  }

  function init() {
    document.querySelectorAll('.mechanic-status-select').forEach(function (sel) {
      syncMechanic(sel);
      sel.addEventListener('change', function () {
        syncMechanic(sel);
      });
    });

    document.querySelectorAll('select.enum-task-status').forEach(function (sel) {
      syncEnum(sel, 'enum-task-status');
      sel.addEventListener('change', function () {
        syncEnum(sel, 'enum-task-status');
      });
    });

    document.querySelectorAll('select.enum-task-priority').forEach(function (sel) {
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
