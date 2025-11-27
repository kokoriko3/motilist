document.addEventListener('DOMContentLoaded', () => {
  const errorBox = document.querySelector('[data-schedule-error]')
  const dayNav = document.querySelector('[data-day-nav]')
  const dayContainer = document.querySelector('[data-day-container]')

  const hideError = () => {
    if (errorBox) errorBox.hidden = true
  }

  const showError = (msg) => {
    if (!errorBox) return
    errorBox.textContent = msg
    errorBox.hidden = false
  }

  const switchDay = (dayId) => {
    if (!dayContainer || !dayNav) return
    dayContainer.querySelectorAll('[data-day]').forEach((el) => {
      el.classList.toggle('hidden', el.getAttribute('data-day') !== dayId)
    })
    dayNav.querySelectorAll('[data-day-target]').forEach((btn) => {
      btn.classList.toggle('active', btn.getAttribute('data-day-target') === dayId)
    })
  }

  if (dayNav) {
    dayNav.addEventListener('click', (event) => {
      const target = event.target.closest('[data-day-target]')
      if (!target) return
      switchDay(target.getAttribute('data-day-target'))
    })
  }

  const generateBtn = document.querySelector('[data-schedule-generate]')
  if (generateBtn) {
    generateBtn.addEventListener('click', () => {
      hideError()
      generateBtn.setAttribute('aria-busy', 'true')
      generateBtn.textContent = '生成中…'
      setTimeout(() => {
        window.location.href = '/schedule'
      }, 700)
    })
  }

  const addEntryRow = (container) => {
    const row = document.createElement('div')
    row.className = 'schedule-row editable'
    row.setAttribute('data-entry', '')
    // 4列分のHTML (時間, 場所, 補足, 削除ボタン)
    row.innerHTML = `
      <div class="col-time"><input name="time" type="time" value="" placeholder="10:00" /></div>
      <div class="col-place"><input name="place" type="text" value="" placeholder="場所を入力" /></div>
      <div class="col-note"><input name="note" type="text" value="" placeholder="補足" /></div>
      <button type="button" class="icon-button" data-entry-delete aria-label="削除">🗑</button>
    `

    // ボタンそのものを探す
    const adderBtn = container.querySelector('[data-entry-add]')
    
    // 変更点: ボタンが div.schedule-add-row で囲まれている場合、その「親のdiv」の前に挿入する
    const insertTarget = adderBtn ? (adderBtn.closest('.schedule-add-row') || adderBtn) : null
    
    container.insertBefore(row, insertTarget)
  }

  if (dayContainer) {
    dayContainer.addEventListener('click', (event) => {
      const target = event.target
      
      // ★ 修正2: matches ではなく closest を使う (クリック判定を確実にするため)
      // 追加ボタンが押されたとき
      if (target.closest('[data-entry-add]')) {
        const parent = target.closest('[data-day]')
        if (parent) addEntryRow(parent)
      }
      
      // 削除ボタンが押されたとき
      if (target.closest('[data-entry-delete]')) {
        const row = target.closest('[data-entry]')
        if (row) row.remove()
      }
    })
  }
  const saveBtn = document.querySelector('[data-schedule-save]')
  if (saveBtn) {
    saveBtn.addEventListener('click', async (event) => {
      event.preventDefault()
      hideError()

      // 1. バリデーション (場所が空欄のものは許さない例)
      const invalid = Array.from(document.querySelectorAll('[data-entry] input[name="place"]')).some(
        (input) => !input.value.trim(),
      )
      if (invalid) {
        showError('場所・内容は必須入力です')
        return
      }

      saveBtn.setAttribute('aria-busy', 'true')
      saveBtn.textContent = '保存中...'

      // 2. 画面のDOMからデータを収集してJSON構造を作る
      const payload = []
      
      // 各「日」のコンテナをループ
      const dayContainers = document.querySelectorAll('[data-day]')
      dayContainers.forEach(container => {
        const dayNum = parseInt(container.getAttribute('data-day'))
        const details = []

        // その日の中にある「行(entry)」をループ
        const rows = container.querySelectorAll('[data-entry]')
        rows.forEach(row => {
          const time = row.querySelector('input[name="time"]').value
          const place = row.querySelector('input[name="place"]').value
          const note = row.querySelector('input[name="note"]').value

          details.push({
            "time": time,
            "activity": place,       // DBのカラム名に合わせる(title -> activity)
            "transport_notes": note  // DBのカラム名に合わせる(note -> transport_notes)
          })
        })

        payload.push({
          "day": dayNum,
          "details": details
        })
      })

      // 3. Fetch APIでバックエンドへ送信
      try {
        const response = await fetch('/plans/schedule/update', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(payload)
        })

        const result = await response.json()

        if (response.ok && result.status === 'success') {
          // 成功したら一覧画面へ遷移
          window.location.href = result.redirect
        } else {
          showError(result.error || '保存に失敗しました')
          saveBtn.removeAttribute('aria-busy')
          saveBtn.textContent = '保存して完了'
        }
      } catch (err) {
        console.error(err)
        showError('通信エラーが発生しました')
        saveBtn.removeAttribute('aria-busy')
        saveBtn.textContent = '保存して完了'
      }
    })
  }
});