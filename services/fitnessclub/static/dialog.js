;(function () {
  const modalHost = document.getElementById("modals-here")
  if (!modalHost) {
    return
  }
  const defaultHostMarkup = modalHost.innerHTML

  const modal = bootstrap.Modal.getOrCreateInstance(modalHost)

  const isModalSwapTarget = (target) => {
    if (!target || !target.id) {
      return false
    }
    return target.id === "modals-here" || target.id === "dialog"
  }

  htmx.on("htmx:afterSwap", (e) => {
    // Support both legacy #dialog targets and current #modals-here targets.
    if (isModalSwapTarget(e.detail.target)) {
      modal.show()
    }
  })

  htmx.on("htmx:beforeSwap", (e) => {
    // Empty response targeting modal host => hide the modal.
    if (isModalSwapTarget(e.detail.target) && !e.detail.xhr.response) {
      modal.hide()
      e.detail.shouldSwap = false
    }
  })

  // Restore the default shell after hiding to keep legacy selectors stable.
  modalHost.addEventListener("hidden.bs.modal", () => {
    modalHost.innerHTML = defaultHostMarkup
  })
})()
