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
  console.log('initSortables called');
  if (window.controlDragActive === undefined) {
    window.controlDragActive = false;
  }
  function getAlternativeDropTarget(originalEvent) {
    if (!originalEvent || originalEvent.clientX == null || originalEvent.clientY == null) {
      return null;
    }
    return [...document.querySelectorAll('.workout-alt-drop-list')].find(dropTarget => {
      const bounds = dropTarget.getBoundingClientRect();
      return originalEvent.clientX >= bounds.left
        && originalEvent.clientX <= bounds.right
        && originalEvent.clientY >= bounds.top
        && originalEvent.clientY <= bounds.bottom;
    }) || null;
  }

  function updateAlternativeDropHighlight(originalEvent, sourceElement) {
    document.querySelectorAll('.workout-alt-drop-list.ctrl-drag-over').forEach(dropTarget => {
      dropTarget.classList.remove('ctrl-drag-over');
    });

    const isControlDrag = (originalEvent && originalEvent.ctrlKey) || window.controlDragActive;
    const dropTarget = isControlDrag ? getAlternativeDropTarget(originalEvent) : null;
    if (dropTarget && dropTarget.dataset.primaryExerciseId !== sourceElement.dataset.parentExerciseId
      && dropTarget.dataset.primaryExerciseId !== sourceElement.dataset.exerciseId) {
      dropTarget.classList.add('ctrl-drag-over');
    }
    return dropTarget;
  }

  if (!window.workoutControlDragListenersInstalled) {
    document.addEventListener('keydown', event => {
      if (event.key === 'Control') {
        window.controlDragActive = true;
      }
    });
    document.addEventListener('keyup', event => {
      if (event.key === 'Control') {
        window.controlDragActive = false;
        document.querySelectorAll('.workout-alt-drop-list.ctrl-drag-over').forEach(dropTarget => {
          dropTarget.classList.remove('ctrl-drag-over');
        });
      }
    });
    window.workoutControlDragListenersInstalled = true;
  }

  document.querySelectorAll('.section-list').forEach(listEl => {
    if (Sortable.get(listEl)) {
      return;
    }
    Sortable.create(listEl, {
      group: 'sections',
      handle: '.drag-handle',
      animation: 150,
      onMove(evt) {
        updateAlternativeDropHighlight(evt.originalEvent, evt.dragged);
        return !(evt.originalEvent.ctrlKey || window.controlDragActive);
      },
      onEnd(evt) {
        const exId = evt.item.dataset.exerciseId;
        const workoutId = evt.item.dataset.workoutId;
        const alternativeDropTarget = updateAlternativeDropHighlight(evt.originalEvent, evt.item);
        const isControlDrag = evt.originalEvent.ctrlKey || window.controlDragActive;
        if (isControlDrag && alternativeDropTarget) {
          htmx.ajax('POST', '/workouts/builder/' + workoutId + '/add-as-alternative', {
            values: {
              exercise_id: exId,
              target_exercise_id: alternativeDropTarget.dataset.primaryExerciseId
            },
            target: '#canvas',
            swap: 'innerHTML'
          });
          return;
        }
        if (isControlDrag) {
          return;
        }

        const from = evt.from.dataset.section;
        const to = evt.to.dataset.section;
        const order = [...evt.to.children].map(li => li.dataset.exerciseId);

        if (from !== to) {
          htmx.ajax('POST', '/workouts/builder/' + workoutId + '/move', {
            values: { exercise_id: exId, to_section: to },
            target: '#canvas',
            swap: 'innerHTML'
          });
        }

        htmx.ajax('POST', '/workouts/builder/' + workoutId + '/reorder', {
          values: {
            section: to,
            'order[]': order
          },
          target: '#canvas',
          swap: 'innerHTML'
        });
      }
    });
  });

  document.querySelectorAll('.workout-alt-drop-list').forEach(listEl => {
    if (Sortable.get(listEl)) {
      return;
    }
    Sortable.create(listEl, {
      group: 'sections',
      handle: '.alternative-drag-handle',
      draggable: '.workout-alt-item',
      animation: 150,
      onMove(evt) {
        updateAlternativeDropHighlight(evt.originalEvent, evt.dragged);
        return evt.to.classList.contains('section-list')
          && !(evt.originalEvent.ctrlKey || window.controlDragActive);
      },
      onEnd(evt) {
        const alternativeId = evt.item.dataset.exerciseId;
        const sourceParentId = evt.item.dataset.parentExerciseId;
        const workoutId = evt.item.dataset.workoutId;
        const alternativeDropTarget = updateAlternativeDropHighlight(evt.originalEvent, evt.item);
        const isControlDrag = evt.originalEvent.ctrlKey || window.controlDragActive;

        if (isControlDrag && alternativeDropTarget) {
          htmx.ajax('POST', '/workouts/builder/' + workoutId + '/add-as-alternative', {
            values: {
              exercise_id: alternativeId,
              source_parent_exercise_id: sourceParentId,
              target_exercise_id: alternativeDropTarget.dataset.primaryExerciseId
            },
            target: '#canvas',
            swap: 'innerHTML'
          });
          return;
        }
        if (isControlDrag || !evt.to.classList.contains('section-list')) {
          return;
        }

        htmx.ajax('POST', '/workouts/builder/' + workoutId + '/promote-alternative', {
          values: {
            exercise_id: alternativeId,
            source_parent_exercise_id: sourceParentId,
            target_section: evt.to.dataset.section,
            target_index: evt.newIndex
          },
          target: '#canvas',
          swap: 'innerHTML'
        });
      }
    });
  });
};
function initProgramSortables() {
  console.log('initProgramSortables called');
  document.querySelectorAll('.workout-list').forEach(listEl => {
    Sortable.create(listEl, {
      group: 'sections',         // ← allow cross‐list dragging
      handle: '.drag-handle',
      animation: 150,
      onEnd(evt) {
        const progId = evt.item.dataset.programId;
        const workoutId = evt.item.dataset.workoutId;
        // const from   = evt.from.dataset.section;
        // const to     = evt.to.dataset.section;
        const order = [...evt.to.children].map(li => li.dataset.workoutId);

        htmx.ajax('POST',
          '/program/builder/' + progId + '/reorder',
          {
            values: { 'order[]': order },
            target: '#program-canvas',
            swap: 'innerHTML'
          }
        );
      }
    });
  });
}

document.addEventListener('htmx:afterSwap', e => {
  if (e.detail.target.id === 'canvas') {
    initSortables();
  };
  if (e.detail.target.id === 'program-canvas') {
    initProgramSortables();
  };
});

// document.addEventListener('DOMContentLoaded', function () {
//   var imageModal = document.getElementById('imageModal');
//   imageModal.addEventListener('show.bs.modal', function (event) {
//     // `event.relatedTarget` is the <img> that triggered the modal
//     var thumb = event.relatedTarget;
//     var fullUrl = thumb.getAttribute('data-full-url');
//     var description = thumb.getAttribute('alt') || '';
//     // Update modal contents
//     var modalImg = document.getElementById('modalImage');
//     var modalTitle = document.getElementById('imageModalLabel');
//     modalImg.src = fullUrl;
//     modalImg.alt = description;
//     modalTitle.textContent = description;
//   });
// });

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
function toggleExerciseDetails(id, allow_popups = 'false') {
  console.log('toggleExerciseDetails called for id:', id, 'allow_popups: <', allow_popups, '>');
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
    '/workouts/viewer/exercise/' + id + '/details?allow_popups=' + allow_popups,
    { target: '#details-' + id, swap: 'innerHTML' }
  );
}
// Call this to open/close the details panel
function toggleWorkoutDetails(id, key, programId) {

  const container = document.getElementById('workout-details-' + id);
  // If it already has content, just clear it (close)
  if (container.innerHTML.trim()) {
    container.innerHTML = '';
    return;
  }
  // Otherwise, close any other open panels
  document.querySelectorAll('.workout-details')
    .forEach(el => {
      if (el.id !== 'workout-details-' + id) el.innerHTML = '';
    });
  // And fire an HTMX request to load this one
  htmx.ajax('GET',
    '/program/viewer/workout2/' + id + '?workout_key_str=' + key + '&program_id=' + programId,
    { target: '#workout-details-' + id, swap: 'innerHTML' }
  );
}

/* facebook login support */

window.fbAsyncInit = function () {
  FB.init({
    appId: '1151061913225629',
    cookie: true,
    xfbml: true,
    version: 'v23.0'
  });

  FB.AppEvents.logPageView();

};

(function (d, s, id) {
  var js, fjs = d.getElementsByTagName(s)[0];
  if (d.getElementById(id)) { return; }
  js = d.createElement(s); js.id = id;
  js.src = "https://connect.facebook.net/en_US/sdk.js";
  fjs.parentNode.insertBefore(js, fjs);
}(document, 'script', 'facebook-jssdk'));
