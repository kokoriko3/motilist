document.addEventListener('DOMContentLoaded', () => {
  const errorBox = document.querySelector('[data-checklist-error]')

  const showError = (message) => {
    if (!errorBox) return
    errorBox.textContent = message
    errorBox.hidden = false
  }

  const hideError = () => {
    if (!errorBox) return
    errorBox.hidden = true
  }

  const generateBtn = document.querySelector('[data-checklist-generate]')
  if (generateBtn) {
    generateBtn.addEventListener('click', async () => {
      hideError()
      generateBtn.setAttribute('aria-busy', 'true')
      generateBtn.textContent = '作成中…'
      generateBtn.disabled = true;
      const originalText = generateBtn.textContent;

      try {
        const response = await fetch('/plans/checklists/generate', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          }
        });

        const data = await response.json();

        if (!response.ok) {
          // 既に存在する場合(409)はメッセージを表示してリダイレクト
          if (response.status === 409 && data.redirect_url) {
            alert(data.error || 'チェックリストは既に存在します。');
            window.location.href = data.redirect_url;
            return;
          }
          throw new Error(data.error || '生成に失敗しました');
        }

        // 成功したらサーバーから指定されたURLにリダイレクト
        if (data.redirect_url) {
          window.location.href = data.redirect_url;
        } else {
          // フォールバックとしてリロード
          window.location.reload();
        }

      } catch (error) {
        console.error('Error:', error);
        showError(error.message || '生成に失敗しました。もう一度お試しください。');
        
        // ボタンを元に戻す
        generateBtn.textContent = originalText;
        generateBtn.disabled = false;
        generateBtn.removeAttribute('aria-busy');
      }
    });
  }

  const addRow = (stackEl) => {
    const row = document.createElement('div')
    row.className = 'edit-row'
    row.setAttribute('data-item-row', '')
    row.innerHTML = `
      <input name="item_form" type="text" value="" placeholder="追加..." />
      <div class="row-right">
        <input name="num_from" type="text" value="" placeholder="数量:入力" />
        <button type="button" name="delete" class="icon-button" data-item-delete aria-label="削除">🗑</button>
      </div>
    `
    stackEl.insertBefore(row, stackEl.querySelector('.adder'))
  }

  const bindStackEvents = (stackEl) => {
    stackEl.addEventListener('click', (event) => {
      const target = event.target
      if (target.matches('[data-item-add]')) {
        event.preventDefault()
        addRow(stackEl)
      }
      if (target.matches('[data-item-delete]')) {
        event.preventDefault()
        const row = target.closest('[data-item-row]')
        if (row) row.remove()
      }
    })
  }

  document.querySelectorAll('.item-stack').forEach((stackEl) => bindStackEvents(stackEl))

  const globalAdd = document.querySelector('[data-item-add-global]')
  if (globalAdd) {
    globalAdd.addEventListener('click', () => {
      const firstStack = document.querySelector('.item-stack')
      if (firstStack) addRow(firstStack)
    })
  }

  const submitBtn = document.querySelector('[data-checklist-submit]')
  if (submitBtn) {
    submitBtn.addEventListener('click', (event) => {
      event.preventDefault()
      hideError()

      const hasEmpty = Array.from(document.querySelectorAll("input[name='item_form']")).some(
        (input) => !input.value.trim(),
      )
      if (hasEmpty) {
        showError('アイテム名を入力してください')
        return
      }

      submitBtn.setAttribute('aria-busy', 'true')
      setTimeout(() => {
        window.location.href = '/checklist'
      }, 500)
    })
  }
})
