document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('form[action*="stay_select"]');
  const errorBox = document.querySelector('[data-stay-error]');
  const stayList = document.querySelector('[data-stay-list]');
  const confirmBtn = document.querySelector('[data-stay-confirm]');
  const clearBtn = document.querySelector('[data-stay-clear]');
  const saveBtn = document.querySelector('[data-stay-save]');
  const sortToggle = document.querySelector('[data-sort-toggle]');
  const sortMenu = document.querySelector('[data-sort-menu]');

  const hideError = () => {
    if (errorBox) errorBox.hidden = true;
  };

  const showError = (msg) => {
    if (!errorBox) return;
    errorBox.textContent = msg;
    errorBox.hidden = false;
  };

  // --- カードクリック時 ---
  if (stayList) {
    stayList.addEventListener('click', (event) => {
      const card = event.target.closest('[data-stay-id]');
      if (!card) return;
      hideError();

      // いったん全部リセット
      stayList.querySelectorAll('[data-stay-id]').forEach((c) => {
        c.classList.remove('selected', 'disabled');
        const r = c.querySelector('input[name="hotel_id"]');
        if (r) {
          r.checked = false;
          r.disabled = false;
        }
      });

      // クリックされたカードだけ選択
      card.classList.add('selected');
      const selectedRadio = card.querySelector('input[name="hotel_id"]');
      if (selectedRadio) {
        selectedRadio.checked = true;
      }

      // 他のカードは disabled＋ラジオも無効化
      stayList.querySelectorAll('[data-stay-id]').forEach((c) => {
        if (c === card) return;
        c.classList.add('disabled');
        const r = c.querySelector('input[name="hotel_id"]');
        if (r) r.disabled = true;
      });
    });
  }

  // --- 確定ボタン ---
  if (confirmBtn && form) {
    confirmBtn.addEventListener('click', () => {
      hideError();
      const selected = form.querySelector('input[name="hotel_id"]:checked');
      if (!selected) {
        showError('宿泊先を選択してください');
        return;
      }
      confirmBtn.setAttribute('aria-busy', 'true');
      form.submit();
    });
  }

  // --- 選択しないボタン ---
  if (clearBtn && form && stayList) {
    clearBtn.addEventListener('click', () => {
      console.log('clear clicked'); // 動作確認用

      hideError();

      // radio解除＋有効化
      form.querySelectorAll('input[name="hotel_id"]').forEach((r) => {
        r.checked = false;
        r.disabled = false;
      });

      // 見た目も全部解除
      stayList.querySelectorAll('[data-stay-id]').forEach((c) => {
        c.classList.remove('selected', 'disabled');
      });
    });
  }

  if (sortToggle && sortMenu) {
    sortToggle.addEventListener('click', () => {
      sortMenu.hidden = !sortMenu.hidden;
    });
  }
});