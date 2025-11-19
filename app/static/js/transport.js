document.addEventListener('DOMContentLoaded', () => {
  const errorBox = document.querySelector('[data-transport-error]')
  const cards = Array.from(document.querySelectorAll('[data-option]'))
  const confirmBtn = document.querySelector('[data-transport-confirm]')
  const saveBtn = document.querySelector('[data-transport-save]')

  const hideError = () => {
    if (errorBox) errorBox.hidden = true
  }

  const showError = (msg) => {
    if (!errorBox) return
    errorBox.textContent = msg
    errorBox.hidden = false
  }

  cards.forEach((card) => {
    card.addEventListener('click', () => {
      hideError()
      cards.forEach((c) => c.classList.remove('selected'))
      card.classList.add('selected')
    })
  })

  if (confirmBtn) {
    confirmBtn.addEventListener('click', () => {
      hideError()
      const selected = cards.find((c) => c.classList.contains('selected'))
      if (!selected) {
        showError('選択してください')
        return
      }
      confirmBtn.setAttribute('aria-busy', 'true')
      const redirect = confirmBtn.getAttribute('data-redirect') || '/transport/confirm'
      setTimeout(() => {
        window.location.href = redirect
      }, 400)
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
})
