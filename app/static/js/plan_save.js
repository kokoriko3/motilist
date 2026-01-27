document.addEventListener('DOMContentLoaded', () => {
  const planSaveTrigger = document.querySelectorAll('[data-plan-save-trigger]')
  const planSaveModal = document.querySelector('[data-plan-save-modal]')
  const planShareTriggerButtons = document.querySelectorAll('[data-plan-share-trigger]')
  const planShareModal = document.querySelector('[data-plan-share-modal]')

  const titleInput = planSaveModal?.querySelector('input[name="template_title"]')
  const noteInput = planSaveModal?.querySelector('textarea[name="template_note"]')
  const publicTitleInput = planSaveModal?.querySelector('input[name="template_public_title"]')
  const tagsInput = planSaveModal?.querySelector('input[name="template_tags"]')
  const flagAInput = planSaveModal?.querySelector('input[name="template_flag_a"]')
  const flagBInput = planSaveModal?.querySelector('input[name="template_flag_b"]')
  const dateInput = planSaveModal?.querySelector('input[name="template_date"]')
  const pillInputs = planSaveModal?.querySelectorAll('.radio-pill input')
  const submitButton = planSaveModal?.querySelector('[data-plan-save-submit]')
  const errorLabel = planSaveModal?.querySelector('[data-plan-save-error]')
  const planTitleElement = document.querySelector('[data-plan-title]')
  const defaultTitle =
    titleInput?.defaultValue?.trim() ||
    planTitleElement?.dataset?.planTitle?.trim() ||
    planTitleElement?.textContent?.trim()
  const defaultNote = noteInput?.defaultValue?.trim()

  const shareUrlInput = planShareModal?.querySelector('[data-share-url-input]')
  const shareCopyBtn = planShareModal?.querySelector('[data-share-copy]')
  const shareError = planShareModal?.querySelector('[data-plan-share-error]')

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
    if (publicTitleInput && titleInput?.value && !publicTitleInput.value) {
      publicTitleInput.value = titleInput.value
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

  const openShareModal = () => {
    if (!planShareModal) return
    planShareModal.hidden = false
    planShareModal.classList.add('is-open')
    hideError(shareError)
  }

  const closeShareModal = () => {
    planShareModal?.classList.remove('is-open')
    if (planShareModal) planShareModal.hidden = true
    hideError(shareError)
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

  planShareModal?.addEventListener('click', (event) => {
    if (event.target === planShareModal || event.target.closest('[data-plan-share-close]')) {
      closeShareModal()
    }
  })

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && planSaveModal?.classList.contains('is-open')) {
      closeSaveModal()
    }
    if (event.key === 'Escape' && planShareModal?.classList.contains('is-open')) {
      closeShareModal()
    }
  })

  submitButton?.addEventListener('click', async () => {
    hideError(errorLabel)

    const title = titleInput?.value.trim() || ''
    const publicTitle = publicTitleInput?.value.trim() || ''
    const description = noteInput?.value.trim() || ''
    const tags = tagsInput?.value.trim() || ''
    const visibility = planSaveModal.querySelector('input[name="template_visibility"]:checked')?.value || 'link'
    const storage = planSaveModal.querySelector('input[name="template_storage"]:checked')?.value || 'server'
    const flagA = Boolean(flagAInput?.checked)
    const flagB = Boolean(flagBInput?.checked)
    const date = dateInput?.value || ''

    if (!title) {
      showError(errorLabel, 'タイトルを入力してください')
      return
    }
    if (title.length > 50) {
      showError(errorLabel, 'タイトルは50文字以内で入力してください')
      return
    }
    if (publicTitle && publicTitle.length > 60) {
      showError(errorLabel, '公開タイトルは60文字以内で入力してください')
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
          public_title: publicTitle,
          description,
          tags,
          visibility,
          storage,
          flag_a: flagA,
          flag_b: flagB,
          date,
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

  const fetchShareUrl = async () => {
    hideError(shareError)
    if (shareUrlInput) shareUrlInput.value = '発行中…'
    try {
      const response = await fetch('/plans/share', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      const result = await response.json().catch(() => ({}))

      if (response.ok && result.status === 'success') {
        if (shareUrlInput) shareUrlInput.value = result.url
        return
      }
      showError(shareError, result.message || '共有URLの発行に失敗しました')
    } catch (error) {
      console.error(error)
      showError(shareError, '通信エラーが発生しました')
    }
  }

  const openShareAndFetch = () => {
    openShareModal()
    fetchShareUrl()
  }

  planShareTriggerButtons.forEach((btn) => {
    btn.addEventListener('click', openShareAndFetch)
  })

  shareCopyBtn?.addEventListener('click', async () => {
    if (!shareUrlInput || !shareUrlInput.value) return
    try {
      await navigator.clipboard.writeText(shareUrlInput.value)
      shareCopyBtn.textContent = 'コピーしました'
      setTimeout(() => {
        shareCopyBtn.textContent = 'コピー'
      }, 1200)
    } catch (e) {
      console.error(e)
      showError(shareError, 'コピーに失敗しました')
    }
  })
})
