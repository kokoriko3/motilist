// Share link copy on plan detail page

document.addEventListener('DOMContentLoaded', () => {
  const shareBox = document.querySelector('[data-share-box]')
  if (!shareBox) return

  const urlInput = shareBox.querySelector('[data-share-url-input]')
  const actionButton = shareBox.querySelector('[data-share-action]')
  const errorLabel = shareBox.querySelector('[data-share-error]')

  const hideError = () => {
    if (errorLabel) errorLabel.hidden = true
  }

  const showError = (message) => {
    if (!errorLabel) return
    errorLabel.textContent = message
    errorLabel.hidden = false
  }

  const setButtonText = (text) => {
    if (actionButton) actionButton.textContent = text
  }

  const copyText = async (text) => {
    if (!text) return false
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text)
      return true
    }
    if (!urlInput) return false
    urlInput.removeAttribute('readonly')
    urlInput.select()
    urlInput.setSelectionRange(0, text.length)
    const success = document.execCommand('copy')
    urlInput.setAttribute('readonly', '')
    return success
  }

  const fetchShareUrl = async () => {
    try {
      const response = await fetch('/plans/share', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      const result = await response.json().catch(() => ({}))
      if (response.ok && result.status === 'success' && result.url) {
        return result.url
      }
      showError(result.message || '共有リンクの発行に失敗しました')
      return ''
    } catch (error) {
      console.error(error)
      showError('通信エラーが発生しました')
      return ''
    }
  }

  actionButton?.addEventListener('click', async () => {
    hideError()
    if (!actionButton) return

    const originalText = actionButton.textContent
    actionButton.disabled = true
    actionButton.setAttribute('aria-busy', 'true')

    try {
      let shareUrl = urlInput?.value?.trim() || ''
      if (!shareUrl) {
        setButtonText('発行中...')
        shareUrl = await fetchShareUrl()
        if (!shareUrl) {
          setButtonText(originalText || 'リンクを発行')
          return
        }
        if (urlInput) urlInput.value = shareUrl
        setButtonText('コピー')
      }

      const copied = await copyText(shareUrl)
      if (!copied) {
        showError('コピーに失敗しました')
        setButtonText('コピー')
        return
      }

      setButtonText('コピーしました')
      setTimeout(() => {
        setButtonText('コピー')
      }, 1400)
    } catch (error) {
      console.error(error)
      showError('コピーに失敗しました')
      setButtonText('リンクを発行')
    } finally {
      actionButton.disabled = false
      actionButton.removeAttribute('aria-busy')
    }
  })
})
