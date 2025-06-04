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

    function initSortables() {
    document.querySelectorAll('.section-list').forEach(listEl => {
      Sortable.create(listEl, {
        group: 'sections',         // ← allow cross‐list dragging
        handle: '.drag-handle',
        animation: 150,
        onEnd(evt) {
          const exId   = evt.item.dataset.exerciseId;
          const workoutId   = evt.item.dataset.workoutId;
          const from   = evt.from.dataset.section;
          const to     = evt.to.dataset.section;
          const order  = [...evt.to.children].map(li=>li.dataset.exerciseId);

          if (from !== to) {
            // 1) Tell the server “move” first
            htmx.ajax('POST',
                '/workouts/builder/'+ workoutId + '/move',
              {
                values: { exercise_id: exId, to_section: to },
                target: '#canvas',
                swap:   'innerHTML'
              }
            );
          }

          // 2) Then reorder the destination section to match the drop order
          htmx.ajax('POST',
            '/workouts/builder/' + workoutId + '/reorder',
            {
              values: { section: to, 'order[]': order },
              target: '#canvas',
              swap:   'innerHTML'
            }
          );
        }
      });
    });
  }

  document.addEventListener('htmx:afterSwap', e => {
    if (e.detail.target.id === 'canvas') {
      initSortables();
    }
  });

  document.addEventListener('DOMContentLoaded', function(){
    var imageModal = document.getElementById('imageModal');
    imageModal.addEventListener('show.bs.modal', function (event) {
      // `event.relatedTarget` is the <img> that triggered the modal
      var thumb     = event.relatedTarget;
      var fullUrl   = thumb.getAttribute('data-full-url');
      var description = thumb.getAttribute('alt') || '';
      // Update modal contents
      var modalImg   = document.getElementById('modalImage');
      var modalTitle = document.getElementById('imageModalLabel');
      modalImg.src   = fullUrl;
      modalImg.alt   = description;
      modalTitle.textContent = description;
    });
  });


  // Call this to open/close the details panel
  function toggleExerciseDetails(id) {
    const container = document.getElementById('details-' + id);
    // If it already has content, just clear it (close)
    if (container.innerHTML.trim()) {
      container.innerHTML = '';
      return;
    }
    // Otherwise, close any other open panels
    document.querySelectorAll('.exercise-details')
      .forEach(el => {
        if (el.id !== 'details-' + id) el.innerHTML = '';
      });
    // And fire an HTMX request to load this one
    htmx.ajax('GET',
      '/workouts/viewer/exercise/' + id + '/details',
      { target: '#details-' + id, swap: 'innerHTML' }
    );
  }

  /* facebook login support */
  
  window.fbAsyncInit = function() {
    FB.init({
      appId      : '1151061913225629',
      cookie     : true,
      xfbml      : true,
      version    : 'v23.0'
    });
      
    FB.AppEvents.logPageView();   
      
  };

  (function(d, s, id){
     var js, fjs = d.getElementsByTagName(s)[0];
     if (d.getElementById(id)) {return;}
     js = d.createElement(s); js.id = id;
     js.src = "https://connect.facebook.net/en_US/sdk.js";
     fjs.parentNode.insertBefore(js, fjs);
   }(document, 'script', 'facebook-jssdk'));
