// Toggle checklist items from plan detail view

document.addEventListener('DOMContentLoaded', () => {
  const errorLabel = document.querySelector('[data-checklist-toggle-error]')

  const hideError = () => {
    if (errorLabel) errorLabel.hidden = true
  }

  const showError = () => {
    if (!errorLabel) return
    errorLabel.textContent = '保存に失敗しました'
    errorLabel.hidden = false
  }

  document.addEventListener('change', async (event) => {
    const checkbox = event.target.closest('[data-checklist-toggle]')
    if (!checkbox) return
    const itemId = checkbox.getAttribute('data-checklist-item-id')
    if (!itemId) return

    hideError()
    const nextState = checkbox.checked
    checkbox.disabled = true

    try {
      const response = await fetch(`/plans/checklists/items/${itemId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          is_checked: nextState,
        }),
      })
      const result = await response.json().catch(() => ({}))
      if (!response.ok || result.status !== 'success') {
        checkbox.checked = !nextState
        showError()
      }
    } catch (error) {
      console.error(error)
      checkbox.checked = !nextState
      showError()
    } finally {
      checkbox.disabled = false
    }
  })

})
