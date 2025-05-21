    JSONEditor.defaults.callbacks.upload = {
        "realUploadHandler": function (jseditor, pointer, fileBlob, callback) {
            // fileBlob: the File object from the <input type="file">
            // pointer: JSON Pointer to the property (e.g. "/avatar")
            // callback: fn(urlString) — call with the URL when done

            // build FormData
            var formData = new FormData();
            formData.append('file', fileBlob);

            // POST to your API
            fetch(jseditor.jsoneditor.options.upload_end_point, 
            {
                method: 'POST',
                body: formData,
                credentials: 'same-origin'
            })
                .then(function (res) {
                    if (!res.ok) callback.failure("failuer on upload: " + res.status);
                    return res.json();
                })
                .then(function (json) {
                    if (!json.url) throw new Error("No URL returned");
                    callback.success(json.url);
                })
                .catch(function (err) {
                    console.error(err);
                    // Pass `null` or empty string on error so editor knows upload failed
                    callback.failure("failuer on upload: " + err.message);
                });
        }
    };
    JSONEditor.defaults.iconlibs.fontawesome5.iconClass = 'fas';
    JSONEditor.defaults.options.theme = 'bootstrap5';        

    document.addEventListener('htmx:load', function (event) {
      console.log('htmx:load event triggered');
      if (true) {
        const links = document.querySelectorAll('.nav-link');
        const dropdownItems = document.querySelectorAll('.dropdown-item');
        const navbarToggler = document.querySelector('.navbar-toggler');
        const navbarCollapse = document.querySelector('.navbar-collapse');

        links.forEach(link => {
          link.addEventListener('click', function () {
            console.log('Link clicked:', this);
            links.forEach(l => l.classList.remove('active'));
            this.classList.add('active');
            if (navbarToggler && navbarCollapse.classList.contains('show') && !this.classList.contains('dropdown-toggle')) {
              navbarToggler.click();
            }
          });
        });

        dropdownItems.forEach(item => {
          item.addEventListener('click', function () {
            console.log('Dropdown item clicked:', this);
            if (navbarToggler && navbarCollapse.classList.contains('show')) {
              navbarToggler.click();
            }
          });
        });
      }
    }); 
    