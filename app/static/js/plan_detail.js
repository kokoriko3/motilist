const initProfileDropdown = () => {
  document.querySelectorAll('[data-dropdown]').forEach((dropdown) => {
    const button = dropdown.querySelector('.icon-user')
    button?.addEventListener('click', (event) => {
      event.stopPropagation()
      dropdown.classList.toggle('open')
    })
  })

  document.addEventListener('click', () => {
    document.querySelectorAll('[data-dropdown].open').forEach((dropdown) => {
      dropdown.classList.remove('open')
    })
  })
}

const initPlanDetail = () => {
  const container = document.querySelector('[data-plan-detail]')
  if (!container) {
    return
  }

  const planId = container.getAttribute('data-plan-id')
  const timelineList = container.querySelector('[data-timeline]')
  const refreshButton = container.querySelector('[data-refresh-timeline]')

  const renderTimeline = (entries) => {
    if (!timelineList) return
    timelineList.innerHTML = ''
    entries.forEach((entry) => {
      const li = document.createElement('li')
      li.className = 'timeline-entry'
      const time = document.createElement('time')
      time.textContent = entry.time
      const description = document.createElement('p')
      description.textContent = entry.description
      li.appendChild(time)
      li.appendChild(description)
      timelineList.appendChild(li)
    })
  }

  refreshButton?.addEventListener('click', () => {
    if (!planId) return
    refreshButton.disabled = true
    refreshButton.textContent = '最新情報を読み込み中...'

    fetch(`/plans/${planId}/progress`)
      .then((response) => response.json())
      .then((payload) => {
        renderTimeline(payload.timeline)
        refreshButton.textContent = '最新情報を取得'
      })
      .catch(() => {
        refreshButton.textContent = '取得に失敗しました'
      })
      .finally(() => {
        setTimeout(() => {
          refreshButton.disabled = false
          refreshButton.textContent = '最新情報を取得'
        }, 800)
      })
  })
}

const initPurposeInput = () => {
  const container = document.querySelector('[data-purpose]')
  if (!container) return

  const input = container.querySelector('[data-purpose-input]')
  const addButton = container.querySelector('[data-purpose-add]')
  const list = container.querySelector('[data-purpose-list]')
  const hidden = container.querySelector('[data-purpose-hidden]')

  const parseValues = () => {
    if (!hidden || !hidden.value) return []
    return hidden.value
      .split(',')
      .map((value) => value.trim())
      .filter((value) => value.length > 0)
  }

  let values = parseValues()

  const render = () => {
    if (!list) return
    list.innerHTML = ''
    values.forEach((value) => {
      const chip = document.createElement('span')
      chip.className = 'chip is-selected'
      chip.dataset.purposeChip = ''
      chip.dataset.value = value

      const label = document.createElement('span')
      label.className = 'chip__label'
      label.textContent = value
      chip.appendChild(label)

      const removeButton = document.createElement('button')
      removeButton.type = 'button'
      removeButton.className = 'chip__remove'
      removeButton.setAttribute('aria-label', '削除')
      removeButton.dataset.purposeRemove = ''
      removeButton.textContent = '×'
      chip.appendChild(removeButton)

      list.appendChild(chip)
    })
    if (hidden) {
      hidden.value = values.join(',')
    }
  }

  const addValue = () => {
    if (!input) return
    const value = input.value.trim()
    if (!value || values.includes(value)) {
      input.value = ''
      return
    }
    values = [...values, value]
    input.value = ''
    render()
  }

  addButton?.addEventListener('click', addValue)
  input?.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
      event.preventDefault()
      addValue()
    }
  })

  list?.addEventListener('click', (event) => {
    const button = event.target.closest('[data-purpose-remove]')
    if (!button) return
    const chip = button.closest('[data-purpose-chip]')
    const value = chip?.dataset.value
    if (!value) return
    values = values.filter((item) => item !== value)
    render()
  })

  render()
}

const initLogoutModal = () => {
  const modal = document.querySelector('[data-logout-modal]')
  const trigger = document.querySelector('[data-logout-trigger]')
  if (!modal || !trigger) {
    return
  }

  const confirmButton = modal.querySelector('[data-logout-confirm]')
  const cancelButton = modal.querySelector('[data-logout-cancel]')
  const backdrop = modal.querySelector('[data-logout-dismiss]')

  const openModal = () => {
    modal.classList.add('is-open')
    modal.removeAttribute('hidden')
  }

  const closeModal = () => {
    modal.classList.remove('is-open')
    modal.setAttribute('hidden', '')
  }

  trigger.addEventListener('click', (event) => {
    event.preventDefault()
    document.querySelectorAll('[data-dropdown].open').forEach((dropdown) => {
      dropdown.classList.remove('open')
    })
    openModal()
  })

  cancelButton?.addEventListener('click', closeModal)
  backdrop?.addEventListener('click', closeModal)

  confirmButton?.addEventListener('click', () => {
    const logoutUrl = confirmButton.getAttribute('data-logout-url') || '/logout'
    window.location.href = logoutUrl
  })

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && modal.classList.contains('is-open')) {
      closeModal()
    }
  })
}

document.addEventListener('DOMContentLoaded', () => {
  initProfileDropdown()
  initPlanDetail()
  initPurposeInput()
  initLogoutModal()
})
