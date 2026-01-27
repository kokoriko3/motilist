console.log('stay.js loaded');

document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('form');
  const errorBox = document.querySelector('[data-stay-error]');
  const stayList = document.querySelector('[data-stay-list]');
  const confirmBtn = document.querySelector('[data-stay-confirm]');
  const clearBtn = document.querySelector('[data-stay-clear]');
  const sortToggle = document.querySelector('[data-sort-toggle]');
  const sortMenu = document.querySelector('[data-sort-menu]');
  const pager = document.querySelector('[data-stay-pager]');

  const hideError = () => {
    if (errorBox) errorBox.hidden = true;
  };

  const showError = (msg) => {
    if (!errorBox) return;
    errorBox.textContent = msg;
    errorBox.hidden = false;
  };

  // ??????????
  if (stayList) {
    stayList.addEventListener('click', (event) => {
      const card = event.target.closest('[data-stay-id]');
      if (!card) return;
      hideError();

      const selectedId = card.dataset.stayId;
      stayList.querySelectorAll('[data-stay-id]').forEach((c) => {
        c.classList.remove('selected', 'disabled');
        const r = c.querySelector('input[name="hotel_id"]');
        if (r) {
          r.checked = false;
          r.disabled = false;
        }
        const cb = c.querySelector('input[data-stay-checkbox]');
        if (cb) cb.checked = false;
      });

      card.classList.add('selected');
      const selectedRadio = card.querySelector('input[name="hotel_id"]');
      if (selectedRadio) {
        selectedRadio.checked = true;
      }
      const selectedCheckbox = card.querySelector('input[data-stay-checkbox]');
      if (selectedCheckbox) {
        selectedCheckbox.checked = true;
      }

      stayList.querySelectorAll('[data-stay-id]').forEach((c) => {
        if (c === card) return;
        c.classList.add('disabled');
        const r = c.querySelector('input[name="hotel_id"]');
        if (r) r.disabled = true;
      });
    });
  }

  // ?????
  if (confirmBtn && form) {
    confirmBtn.addEventListener('click', () => {
      hideError();
      const selected = form.querySelector('input[name="hotel_id"]:checked');
      if (!selected) {
        showError('????????????');
        return;
      }
      confirmBtn.setAttribute('aria-busy', 'true');
      form.submit();
    });
  }

  // ?????
  if (clearBtn && form && stayList) {
    clearBtn.addEventListener('click', () => {
      hideError();

      form.querySelectorAll('input[name="hotel_id"]').forEach((r) => {
        r.checked = false;
        r.disabled = false;
      });
      form.querySelectorAll('input[data-stay-checkbox]').forEach((cb) => {
        cb.checked = false;
      });

      stayList.querySelectorAll('[data-stay-id]').forEach((c) => {
        c.classList.remove('selected', 'disabled');
      });
    });
  }

  // ????????????
  const updateQuery = (patch) => {
    const params = new URLSearchParams(window.location.search);
    Object.entries(patch).forEach(([key, value]) => {
      if (value === null || value === undefined || value === '') {
        params.delete(key);
      } else {
        params.set(key, value);
      }
    });
    window.location.search = params.toString();
  };

  if (sortToggle && sortMenu) {
    sortToggle.addEventListener('click', () => {
      sortMenu.hidden = !sortMenu.hidden;
    });

    sortMenu.querySelectorAll('button[data-sort]').forEach((btn) => {
      btn.addEventListener('click', () => {
        updateQuery({ sort: btn.dataset.sort, page: 1 });
      });
    });
  }

  // ????????
  if (pager) {
    pager.querySelectorAll('button[data-page]').forEach((btn) => {
      btn.addEventListener('click', () => {
        updateQuery({ page: btn.dataset.page });
      });
    });
  }
});
