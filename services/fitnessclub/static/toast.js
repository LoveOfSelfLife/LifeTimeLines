;(function () {
  const toastElement = document.getElementById("toast")
  const toastBody = document.getElementById("toast-body")
  const toast = new bootstrap.Toast(toastElement, { delay: 3000 })

  htmx.on("showMessage", (e) => {
    console.log("🔔 HTMX showMessage:", e.detail);
    toastBody.innerText = e.detail.value
    toast.show()
  });

  // Hides the shared #modals-here modal, used after HTMX actions that finish inside it (e.g. exercise swap)
  htmx.on("closeModal", () => {
    const modalEl = document.getElementById("modals-here")
    if (modalEl) {
      const modalInstance = bootstrap.Modal.getInstance(modalEl)
      if (modalInstance) {
        modalInstance.hide()
      }
    }
  });

  // Function to show the toast with a custom message
  window.showToast = function (message) {
    toastBody.innerText = message;
    console.log("showToast called with message:", message);
    toast.show();
  }  

})();
