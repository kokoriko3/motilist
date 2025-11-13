document.addEventListener('DOMContentLoaded', () => {
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
})
