document.addEventListener('DOMContentLoaded', () => {
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
      const card = event.target.closest('[data-stay-id]')
      if (!card) return
      hideError()
      stayList.querySelectorAll('[data-stay-id]').forEach((c) => c.classList.remove('selected'))
      card.classList.add('selected')
    })
  }

  if (confirmBtn) {
    confirmBtn.addEventListener('click', () => {
      hideError()
      const selected = stayList?.querySelector('.selected')
      if (!selected) {
        showError('選択してください')
        return
      }
      confirmBtn.setAttribute('aria-busy', 'true')
      setTimeout(() => {
        window.location.href = '/stay/confirm'
      }, 400)
    })
  }

  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      hideError()
      stayList?.querySelectorAll('[data-stay-id]').forEach((c) => c.classList.remove('selected'))
    })
  }

  if (saveBtn) {
    saveBtn.addEventListener('click', () => {
      hideError()
      saveBtn.setAttribute('aria-busy', 'true')
      setTimeout(() => {
        window.location.href = '/schedule'
      }, 400)
    })
  }

  if (sortToggle && sortMenu) {
    sortToggle.addEventListener('click', () => {
      sortMenu.hidden = !sortMenu.hidden
    })
  }
})
