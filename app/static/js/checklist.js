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
    if (!stackEl) return
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
    const adder = stackEl.querySelector('.adder')
    if (adder) {
      stackEl.insertBefore(row, adder)
    } else {
      stackEl.appendChild(row)
    }
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

  const getCategoryTitle = (card) => {
    if (!card) return ''
    const titleInput = card.querySelector('.category-title-input')
    if (titleInput) return titleInput.value.trim()
    const titleEl = card.querySelector('.category-title')
    return titleEl ? titleEl.innerText.trim() : ''
  }

  const createCategoryCard = () => {
    const card = document.createElement('article')
    card.className = 'category-card'

    const header = document.createElement('header')
    header.className = 'category-title'
    const titleInput = document.createElement('input')
    titleInput.type = 'text'
    titleInput.className = 'category-title-input'
    titleInput.placeholder = 'カテゴリ名'
    titleInput.value = '新しいカテゴリ'
    header.appendChild(titleInput)

    const stack = document.createElement('div')
    stack.className = 'item-stack'
    const adder = document.createElement('button')
    adder.type = 'button'
    adder.name = 'item_append'
    adder.className = 'adder'
    adder.setAttribute('data-item-add', '')
    adder.textContent = '追加...'
    stack.appendChild(adder)

    card.appendChild(header)
    card.appendChild(stack)

    bindStackEvents(stack)
    return { card, stack, titleInput }
  }

  const globalAdd = document.querySelector('[data-item-add-global]')
  if (globalAdd) {
    globalAdd.addEventListener('click', () => {
      const categoryGrid =
        document.querySelector('[data-checklist-list]') || document.querySelector('.category-grid')
      if (!categoryGrid) return
      const { card, stack, titleInput } = createCategoryCard()
      categoryGrid.appendChild(card)
      addRow(stack)
      if (titleInput) {
        titleInput.focus()
        titleInput.select()
      }
    })
  }

  // --- 保存（確定）ボタンの処理 ---
  const submitBtn = document.querySelector('[data-checklist-submit]')
  if (submitBtn) {
    submitBtn.addEventListener('click', async (event) => {
      event.preventDefault()
      hideError()

      // 1. 入力チェック（空欄があるか）
      // ※すべて空欄でなければ許可するなど、要件に合わせて調整してください
      // ここでは「名前が入力されているものだけ」を送信対象とするため、空欄チェックは必須としません。
      
      // 2. データの収集
      const categoriesData = []
      const categoryCards = document.querySelectorAll('.category-card')

      categoryCards.forEach(card => {
        const categoryTitle = getCategoryTitle(card) || '新しいカテゴリ'
        const items = []
        
        const rows = card.querySelectorAll('[data-item-row]')
        rows.forEach(row => {
          const nameInput = row.querySelector('input[name="item_form"]')
          const qtyInput = row.querySelector('input[name="num_from"]')
          
          const name = nameInput ? nameInput.value.trim() : ''
          const quantity = qtyInput ? qtyInput.value.trim() : ''

          if (name) {
            items.push({
              name: name,
              quantity: quantity
            })
          }
        })

        // アイテムがある、もしくはカテゴリを残したい場合はリストに追加
        if (items.length > 0) {
          categoriesData.push({
            category: categoryTitle,
            items: items
          })
        }
      })

      // 3. 送信処理
      submitBtn.setAttribute('aria-busy', 'true')
      submitBtn.textContent = '保存中...'
      submitBtn.disabled = true

      try {
        const response = await fetch('/plans/checklists/update', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ categories: categoriesData })
        })

        const result = await response.json()

        if (!response.ok) {
          throw new Error(result.error || '保存に失敗しました')
        }

        // 成功したら一覧へリダイレクト
        window.location.href = result.redirect_url || '/plans/checklists'

      } catch (error) {
        console.error(error)
        showError(error.message)
        submitBtn.removeAttribute('aria-busy')
        submitBtn.textContent = '確定'
        submitBtn.disabled = false
      }
    })
  }
})
