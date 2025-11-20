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
    row.innerHTML = `
      <div class="col-time"><input name="time" type="text" value="" placeholder="10:00~12:00" /></div>
      <div class="col-place"><input name="place" type="text" value="" placeholder="入力してください" /></div>
      <div class="col-note"><input name="note" type="text" value="" placeholder="補足" /></div>
      <button type="button" class="icon-button" data-entry-delete aria-label="削除">🗑</button>
    `
    const adder = container.querySelector('[data-entry-add]')
    container.insertBefore(row, adder || null)
  }

  if (dayContainer) {
    dayContainer.addEventListener('click', (event) => {
      const target = event.target
      if (target.matches('[data-entry-add]')) {
        const parent = target.closest('[data-day]')
        if (parent) addEntryRow(parent)
      }
      if (target.matches('[data-entry-delete]')) {
        const row = target.closest('[data-entry]')
        if (row) row.remove()
      }
    })
  }

  const saveBtn = document.querySelector('[data-schedule-save]')
  if (saveBtn) {
    saveBtn.addEventListener('click', (event) => {
      event.preventDefault()
      hideError()
      const invalid = Array.from(document.querySelectorAll('[data-entry] input[name=\"place\"]')).some(
        (input) => !input.value.trim(),
      )
      if (invalid) {
        showError('入力してください')
        return
      }
      saveBtn.setAttribute('aria-busy', 'true')
      setTimeout(() => {
        window.location.href = '/schedule'
      }, 500)
    })
  }
})
