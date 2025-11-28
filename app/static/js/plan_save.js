document.addEventListener('DOMContentLoaded', () => {
  const planSaveTrigger = document.querySelector('[data-plan-save-trigger]')
  const planSaveModal = document.querySelector('[data-plan-save-modal]')

  if (!planSaveTrigger || !planSaveModal) return

  const titleInput = planSaveModal.querySelector('input[name="template_title"]')
  const noteInput = planSaveModal.querySelector('textarea[name="template_note"]')
  const visibilityInputs = planSaveModal.querySelectorAll('input[name="template_visibility"]')
  const submitButton = planSaveModal.querySelector('[data-plan-save-submit]')
  const errorLabel = planSaveModal.querySelector('[data-plan-save-error]')
  const defaultTitle = document.querySelector('[data-plan-title]')?.textContent?.trim()

  const hidePlanSaveError = () => {
    if (errorLabel) errorLabel.hidden = true
  }

  const showPlanSaveError = (msg) => {
    if (!errorLabel) return
    errorLabel.textContent = msg
    errorLabel.hidden = false
  }

  const syncRadioPills = () => {
    visibilityInputs.forEach((input) => {
      const pill = input.closest('.radio-pill')
      if (pill) {
        pill.classList.toggle('is-active', input.checked)
      }
    })
  }

  const openModal = () => {
    if (titleInput && defaultTitle && !titleInput.value) {
      titleInput.value = defaultTitle
    }
    planSaveModal.hidden = false
    planSaveModal.classList.add('is-open')
    hidePlanSaveError()
    titleInput?.focus()
  }

  const closeModal = () => {
    planSaveModal.classList.remove('is-open')
    planSaveModal.hidden = true
    hidePlanSaveError()
    submitButton?.removeAttribute('aria-busy')
    if (submitButton) submitButton.disabled = false
  }

  syncRadioPills()
  visibilityInputs.forEach((input) => {
    input.addEventListener('change', syncRadioPills)
  })

  planSaveTrigger.addEventListener('click', openModal)

  planSaveModal.addEventListener('click', (event) => {
    if (event.target === planSaveModal || event.target.closest('[data-plan-save-close]')) {
      closeModal()
    }
  })

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && planSaveModal.classList.contains('is-open')) {
      closeModal()
    }
  })

  submitButton?.addEventListener('click', async () => {
    hidePlanSaveError()

    const title = titleInput?.value.trim() || ''
    const description = noteInput?.value.trim() || ''
    const visibility = planSaveModal.querySelector('input[name="template_visibility"]:checked')?.value || 'private'

    if (!title) {
      showPlanSaveError('タイトルを入力してください')
      return
    }

    submitButton.disabled = true
    submitButton.setAttribute('aria-busy', 'true')

    try {
      const response = await fetch('/plans/save', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ title, description, visibility }),
      })
      const result = await response.json().catch(() => ({}))

      if (response.ok && result.status === 'success') {
        window.location.href = result.redirect || window.location.href
        return
      }

      showPlanSaveError(result.message || '保存に失敗しました')
    } catch (error) {
      console.error(error)
      showPlanSaveError('通信エラーが発生しました')
    } finally {
      submitButton.disabled = false
      submitButton.removeAttribute('aria-busy')
    }
  })
})
