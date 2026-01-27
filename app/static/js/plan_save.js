document.addEventListener('DOMContentLoaded', () => {
  const planSaveTrigger = document.querySelectorAll('[data-plan-save-trigger]')
  const planSaveModal = document.querySelector('[data-plan-save-modal]')

  const titleInput = planSaveModal?.querySelector('input[name="template_title"]')
  const noteInput = planSaveModal?.querySelector('textarea[name="template_note"]')
  const tagsInput = planSaveModal?.querySelector('input[name="template_tags"]')
  const pillInputs = planSaveModal?.querySelectorAll('.radio-pill input')
  const submitButton = planSaveModal?.querySelector('[data-plan-save-submit]')
  const errorLabel = planSaveModal?.querySelector('[data-plan-save-error]')
  const planTitleElement = document.querySelector('[data-plan-title]')
  const defaultTitle =
    titleInput?.defaultValue?.trim() ||
    planTitleElement?.dataset?.planTitle?.trim() ||
    planTitleElement?.textContent?.trim()
  const defaultNote = noteInput?.defaultValue?.trim()

  const hideError = (el) => {
    if (el) el.hidden = true
  }
  const showError = (el, msg) => {
    if (!el) return
    el.textContent = msg
    el.hidden = false
  }

  const syncRadioPills = () => {
    pillInputs?.forEach((input) => {
      const pill = input.closest('.radio-pill')
      if (pill) {
        pill.classList.toggle('is-active', input.checked)
      }
    })
  }

  const openSaveModal = () => {
    if (titleInput && defaultTitle && !titleInput.value) {
      titleInput.value = defaultTitle
    }
    if (noteInput && defaultNote && !noteInput.value) {
      noteInput.value = defaultNote
    }
    planSaveModal.hidden = false
    planSaveModal.classList.add('is-open')
    hideError(errorLabel)
    titleInput?.focus()
    syncRadioPills()
  }

  const closeSaveModal = () => {
    planSaveModal?.classList.remove('is-open')
    if (planSaveModal) planSaveModal.hidden = true
    hideError(errorLabel)
    submitButton?.removeAttribute('aria-busy')
    if (submitButton) submitButton.disabled = false
  }

  pillInputs?.forEach((input) => {
    input.addEventListener('change', syncRadioPills)
  })

  planSaveTrigger.forEach((btn) => {
    btn.addEventListener('click', openSaveModal)
  })

  planSaveModal?.addEventListener('click', (event) => {
    if (event.target === planSaveModal || event.target.closest('[data-plan-save-close]')) {
      closeSaveModal()
    }
  })

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && planSaveModal?.classList.contains('is-open')) {
      closeSaveModal()
    }
  })

  submitButton?.addEventListener('click', async () => {
    hideError(errorLabel)

    const title = titleInput?.value.trim() || ''
    const description = noteInput?.value.trim() || ''
    const tags = tagsInput?.value.trim() || ''
    const visibility = planSaveModal.querySelector('input[name="template_visibility"]:checked')?.value || 'private'

    if (!title) {
      showError(errorLabel, 'タイトルを入力してください')
      return
    }
    if (title.length > 50) {
      showError(errorLabel, 'タイトルは50文字以内で入力してください')
      return
    }
    if (description.length > 500) {
      showError(errorLabel, '説明は500文字以内で入力してください')
      return
    }
    if (tags.length > 100) {
      showError(errorLabel, 'タグは100文字以内で入力してください')
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
        body: JSON.stringify({
          title,
          description,
          tags,
          visibility,
        }),
      })
      const result = await response.json().catch(() => ({}))

      if (response.ok && result.status === 'success') {
        window.location.href = result.redirect || window.location.href
        return
      }

      showError(errorLabel, result.message || '保存に失敗しました')
    } catch (error) {
      console.error(error)
      showError(errorLabel, '通信エラーが発生しました')
    } finally {
      submitButton.disabled = false
      submitButton.removeAttribute('aria-busy')
    }
  })

})
