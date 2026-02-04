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

  // Save checklist for non-owners
  const saveButton = document.querySelector('[data-save-checklist]')
  if (saveButton) {
    saveButton.addEventListener('click', async () => {
      const planId = document.querySelector('[data-plan-detail]').getAttribute('data-plan-id')
      if (!planId) return

      const essentialItems = Array.from(document.querySelectorAll('[data-checklist-column="essential"] [data-checklist-toggle]'))
        .map(cb => ({
          name: cb.nextElementSibling.textContent.split('（')[0].trim(),
          quantity: cb.nextElementSibling.textContent.includes('（') ? parseInt(cb.nextElementSibling.textContent.split('（')[1].split('）')[0].split(/[^\d]/)[0]) || 1 : 1,
          unit: cb.nextElementSibling.textContent.includes('）') ? cb.nextElementSibling.textContent.split('）')[0].split('（')[1].replace(/\d/g, '').trim() : '',
          is_required: true,
          is_checked: cb.checked
        }))

      const extraItems = Array.from(document.querySelectorAll('[data-checklist-column="extra"] [data-checklist-toggle]'))
        .map(cb => ({
          name: cb.nextElementSibling.textContent.split('（')[0].trim(),
          quantity: cb.nextElementSibling.textContent.includes('（') ? parseInt(cb.nextElementSibling.textContent.split('（')[1].split('）')[0].split(/[^\d]/)[0]) || 1 : 1,
          unit: cb.nextElementSibling.textContent.includes('）') ? cb.nextElementSibling.textContent.split('）')[0].split('（')[1].replace(/\d/g, '').trim() : '',
          is_required: false,
          is_checked: cb.checked
        }))

      const categories = [
        { category: '必需品', items: essentialItems },
        { category: '補足品', items: extraItems }
      ]

      try {
        const response = await fetch(`/plans/${planId}/checklists/save_guest`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ categories }),
        })
        const result = await response.json().catch(() => ({}))
        if (response.ok && result.status === 'success') {
          alert('チェックリストを保存しました！')
          window.location.href = result.redirect_url
        } else if (response.status === 401) {
          // ログインが必要
          alert('チェックリストを保存するにはログインが必要です。')
          window.location.href = '/auth/login'
        } else {
          showError()
        }
      } catch (error) {
        console.error(error)
        showError()
      }
    })
  }

  document.addEventListener('change', async (event) => {
    const checkbox = event.target.closest('[data-checklist-toggle]')
    if (!checkbox) return
    const itemId = checkbox.getAttribute('data-checklist-item-id')
    if (!itemId || itemId.startsWith('guest_')) return

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
