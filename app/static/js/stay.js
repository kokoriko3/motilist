document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('form[action*="stay_select"]');
  const errorBox = document.querySelector('[data-stay-error]')
  const stayList = document.querySelector('[data-stay-list]')
  const confirmBtn = document.querySelector('[data-stay-confirm]')
  const clearBtn = document.querySelector('[data-stay-clear]')
  const saveBtn = document.querySelector('[data-stay-save]')
  const sortToggle = document.querySelector('[data-sort-toggle]')
  const sortMenu = document.querySelector('[data-sort-menu]')

  const hideError = () => {
    if (errorBox) errorBox.hidden = true
  }

  const showError = (msg) => {
    if (!errorBox) return
    errorBox.textContent = msg
    errorBox.hidden = false
  }

  if (stayList) {
    stayList.addEventListener('click', (event) => {
      const card = event.target.closest('[data-stay-id]');
      if (!card) return
      hideError();
      stayList.querySelectorAll('[data-stay-id]').forEach((c) => c.classList.remove('selected'));
      card.classList.add('selected');

      const radio = card.querySelector('input[name="hotel_id"]');
      if (radio) {
        radio.checked = true;
      }
    })
  }

  if (confirmBtn && form) {
    confirmBtn.addEventListener('click', () => {
      hideError()
      const selected = form.querySelector('input[name="hotel_id"]:checked');
      if (!selected) {
        showError('選択してください')
        return
      }
      confirmBtn.setAttribute('aria-busy', 'true')
      // ★ URL直叩きではなくサーバに POST
      form.submit();
    })
  }

  if (clearBtn && form && stayList) {
    clearBtn.addEventListener('click', () => {
      hideError();

      // radio解除
      form.querySelectorAll('input[name="hotel_id"]').forEach((r) => {
        r.checked = false;
      });

      // 見た目解除
      stayList.querySelectorAll('[data-stay-id]').forEach((c) => {
        c.classList.remove('selected');
      });
    })
  }

  // if (saveBtn) {
  //   saveBtn.addEventListener('click', () => {
  //     hideError()
  //     saveBtn.setAttribute('aria-busy', 'true')
  //     setTimeout(() => {
  //       window.location.href = '/schedule'
  //     }, 400)
  //   })
  // }

  if (sortToggle && sortMenu) {
    sortToggle.addEventListener('click', () => {
      sortMenu.hidden = !sortMenu.hidden
    })
  }
})
