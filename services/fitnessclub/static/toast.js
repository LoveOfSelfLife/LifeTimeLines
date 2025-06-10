;(function () {
  const toastElement = document.getElementById("toast")
  const toastBody = document.getElementById("toast-body")
  const toast = new bootstrap.Toast(toastElement, { delay: 3000 })

  htmx.on("showMessage", (e) => {
    console.log("🔔 HTMX showMessage:", e.detail);
    toastBody.innerText = e.detail.value
    toast.show()
  });

  // Function to show the toast with a custom message
  window.showToast = function (message) {
    toastBody.innerText = message;
    console.log("showToast called with message:", message);
    toast.show();
  }  

})();
