/**
 * Exercise Editor with Camera Integration
 * Handles camera access, photo/video capture, and media management
 */

// Global state - use window properties to avoid redeclaration issues with HTMX
window.cameraStreams = window.cameraStreams || {};
window.mediaRecorder = window.mediaRecorder || {};
window.recordingChunks = window.recordingChunks || {};

/**
 * Initialize camera for images or videos
 */
async function initCamera(type) {
    try {
        // const constraints = {
        //     video: true,
        //     audio: type === 'videos' // Only need audio for video recording
        // };
        const constraints = {
            video: {
                facingMode: { ideal: 'environment' }, // Prefer rear camera but fallback if not available
                width: { ideal: 1920 },
                height: { ideal: 1080 }
            },
            audio: type === 'videos'
        };        
        
        const stream = await navigator.mediaDevices.getUserMedia(constraints);
        const videoElement = document.getElementById(`camera-video-${type}`);
        
        videoElement.srcObject = stream;
        videoElement.play();
        
        window.cameraStreams[type] = stream;
        return true;
    } catch (err) {
        console.error('Error accessing camera:', err);
        showEditorToast('Camera access denied or not available');
        return false;
    }
}

/**
 * Toggle camera display
 */
async function toggleCamera(type) {
    const cameraSection = document.getElementById(`camera-section-${type}`);
    
    if (cameraSection.style.display === 'none') {
        // Show camera
        const success = await initCamera(type);
        if (success) {
            cameraSection.style.display = 'block';
        }
    } else {
        // Hide camera
        stopCamera(type);
    }
}

/**
 * Stop camera stream
 */
function stopCamera(type) {
    const cameraSection = document.getElementById(`camera-section-${type}`);
    const videoElement = document.getElementById(`camera-video-${type}`);
    
    if (window.cameraStreams[type]) {
        window.cameraStreams[type].getTracks().forEach(track => track.stop());
        window.cameraStreams[type] = null;
    }
    
    videoElement.srcObject = null;
    cameraSection.style.display = 'none';
    
    // Reset recording state if applicable
    if (type === 'videos' && window.mediaRecorder[type]) {
        window.mediaRecorder[type] = null;
        const recordBtn = document.getElementById(`record-btn-${type}`);
        recordBtn.innerHTML = '<i class="bi bi-record-circle me-1"></i>Start Recording';
        recordBtn.className = 'btn btn-danger me-2';
    }
}

/**
 * Capture photo from camera
 */
function capturePhoto(type) {
    const videoElement = document.getElementById(`camera-video-${type}`);
    const canvas = document.getElementById(`camera-canvas-${type}`);
    const ctx = canvas.getContext('2d');
    
    // Set canvas dimensions to match video
    canvas.width = videoElement.videoWidth;
    canvas.height = videoElement.videoHeight;
    
    // Draw video frame to canvas
    ctx.drawImage(videoElement, 0, 0);
    
    // Convert canvas to blob
    canvas.toBlob(async (blob) => {
        if (blob) {
            const filename = `exercise-${Date.now()}.jpg`;
            await uploadMediaFile(blob, filename, type, 'start-of-movement', 'Captured photo');
            showEditorToast('Photo captured successfully!');
        }
    }, 'image/jpeg', 0.8);
}

/**
 * Toggle video recording
 */
function toggleRecording(type) {
    const recordBtn = document.getElementById(`record-btn-${type}`);
    
    if (!window.mediaRecorder[type] || window.mediaRecorder[type].state === 'inactive') {
        startRecording(type);
    } else if (window.mediaRecorder[type].state === 'recording') {
        stopRecording(type);
    }
}

/**
 * Start video recording
 */
function startRecording(type) {
    const stream = window.cameraStreams[type];
    if (!stream) {
        showEditorToast('Camera not available');
        return;
    }
    
    window.recordingChunks[type] = [];
    
    try {
        window.mediaRecorder[type] = new MediaRecorder(stream);
        
        window.mediaRecorder[type].addEventListener('dataavailable', (event) => {
            if (event.data.size > 0) {
                window.recordingChunks[type].push(event.data);
            }
        });
        
        window.mediaRecorder[type].addEventListener('stop', async () => {
            const blob = new Blob(window.recordingChunks[type], { type: 'video/webm' });
            const filename = `exercise-${Date.now()}.webm`;
            await uploadMediaFile(blob, filename, type, 'movement', 'Recorded video');
            showEditorToast('Video recorded successfully!');
            window.recordingChunks[type] = [];
        });
        
        window.mediaRecorder[type].start();
        
        // Update button state
        const recordBtn = document.getElementById(`record-btn-${type}`);
        recordBtn.innerHTML = '<i class="bi bi-stop-circle me-1"></i>Stop Recording';
        recordBtn.className = 'btn btn-success me-2';
        
    } catch (err) {
        console.error('Error starting recording:', err);
        showEditorToast('Recording failed to start');
    }
}

/**
 * Stop video recording
 */
function stopRecording(type) {
    if (window.mediaRecorder[type] && window.mediaRecorder[type].state === 'recording') {
        window.mediaRecorder[type].stop();
        
        // Update button state
        const recordBtn = document.getElementById(`record-btn-${type}`);
        recordBtn.innerHTML = '<i class="bi bi-record-circle me-1"></i>Start Recording';
        recordBtn.className = 'btn btn-danger me-2';
    }
}

/**
 * Handle GIF file upload from input
 */
function handleGifUpload(input) {
    const file = input.files[0];
    if (!file) {
        return;
    }
    if (!file.type.includes('gif') && !file.name.toLowerCase().endsWith('.gif')) {
        showEditorToast('Please select a GIF file');
        input.value = '';
        return;
    }
    uploadGifFile(file);
    input.value = '';
}

/**
 * Upload GIF file to cloud storage and store its URL
 */
async function uploadGifFile(file) {
    const formData = new FormData();
    formData.append('file', file, file.name);

    try {
        const response = await fetch('/api/upload/fitness-media', {
            method: 'POST',
            body: formData,
            credentials: 'same-origin'
        });

        if (!response.ok) {
            throw new Error(`Upload failed: ${response.statusText}`);
        }

        const result = await response.json();

        if (result.url) {
            window.gifUrl = result.url;
            const gifField = document.getElementById('gif');
            if (gifField) {
                gifField.value = window.gifUrl;
            }
            renderGif();
            showEditorToast('GIF uploaded successfully!');
        }
    } catch (err) {
        console.error('GIF upload error:', err);
        showEditorToast(`Upload failed: ${err.message}`);
    }
}

/**
 * Remove the current GIF
 */
function removeGif() {
    if (confirm('Are you sure you want to remove this GIF?')) {
        window.gifUrl = '';
        const gifField = document.getElementById('gif');
        if (gifField) {
            gifField.value = '';
        }
        renderGif();
        showEditorToast('GIF removed');
    }
}

/**
 * Render GIF preview
 */
function renderGif() {
    const container = document.getElementById('gif-container');
    if (!container) {
        return;
    }

    if (!window.gifUrl) {
        container.innerHTML = `
            <div class="text-center text-muted py-4">
                <i class="bi bi-file-earmark-play display-4"></i>
                <p class="mt-2">No GIF added yet. Upload a file.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = `
        <div class="media-item card mb-3">
            <div class="row g-0">
                <div class="col-md-4">
                    <img src="${window.gifUrl}" class="img-fluid rounded-start" alt="Exercise GIF"
                         style="height: 150px; object-fit: cover; width: 100%;">
                </div>
                <div class="col-md-8">
                    <div class="card-body text-end">
                        <button type="button" class="btn btn-outline-danger btn-sm" onclick="removeGif()">
                            <i class="bi bi-trash"></i> Remove
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Handle file upload from input
 */
function handleFileUpload(input, type) {
    const files = Array.from(input.files);
    
    files.forEach(async (file) => {
        const mediaType = type === 'images' ? 'start-of-movement' : 'movement';
        await uploadMediaFile(file, file.name, type, mediaType, file.name);
    });
    
    // Clear input
    input.value = '';
}

/**
 * Upload media file to server
 */
async function uploadMediaFile(blob, filename, mediaType, subType, description) {
    const formData = new FormData();
    formData.append('file', blob, filename);
    
    try {
        // Use existing upload handler
        const response = await fetch('/api/upload/fitness-media', {
            method: 'POST',
            body: formData,
            credentials: 'same-origin'
        });
        
        if (!response.ok) {
            throw new Error(`Upload failed: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        if (result.url) {
            // Add to media data
            const mediaItem = {
                url: result.url,
                description: description,
                type: subType
            };
            
            if (mediaType === 'images') {
                // Ensure imagesData is an array
                if (!Array.isArray(window.imagesData)) {
                    window.imagesData = [];
                }
                window.imagesData.push(mediaItem);
                console.log('Added new image, total images:', window.imagesData.length);
            } else {
                // Ensure videosData is an array
                if (!Array.isArray(window.videosData)) {
                    window.videosData = [];
                }
                window.videosData.push(mediaItem);
                console.log('Added new video, total videos:', window.videosData.length);
            }
            
            // Update hidden form fields immediately
            updateHiddenMediaFields();
            
            renderMedia();
        }
        
    } catch (err) {
        console.error('Upload error:', err);
        showEditorToast(`Upload failed: ${err.message}`);
    }
}

/**
 * Update hidden form fields with current media data
 */
function updateHiddenMediaFields() {
    const imagesField = document.getElementById('images_data');
    const videosField = document.getElementById('videos_data');
    
    if (imagesField) {
        const imagesData = Array.isArray(window.imagesData) ? window.imagesData : [];
        imagesField.value = JSON.stringify(imagesData);
        console.log('Updated images hidden field:', imagesData.length, 'items');
    }
    
    if (videosField) {
        const videosData = Array.isArray(window.videosData) ? window.videosData : [];
        videosField.value = JSON.stringify(videosData);
        console.log('Updated videos hidden field:', videosData.length, 'items');
    }
}

/**
 * Remove media item
 */
function removeMedia(index, type) {
    if (confirm('Are you sure you want to remove this media item?')) {
        if (type === 'images' && Array.isArray(window.imagesData)) {
            window.imagesData.splice(index, 1);
            console.log('Removed image, total images:', window.imagesData.length);
        } else if (type === 'videos' && Array.isArray(window.videosData)) {
            window.videosData.splice(index, 1);
            console.log('Removed video, total videos:', window.videosData.length);
        }
        
        // Update hidden form fields immediately
        updateHiddenMediaFields();
        
        renderMedia();
        showEditorToast('Media removed');
    }
}

/**
 * Update media description
 */
function updateMediaDescription(index, type, description) {
    if (type === 'images' && Array.isArray(window.imagesData) && window.imagesData[index]) {
        window.imagesData[index].description = description;
        console.log('Updated image description at index', index, 'to:', description);
    } else if (type === 'videos' && Array.isArray(window.videosData) && window.videosData[index]) {
        window.videosData[index].description = description;
        console.log('Updated video description at index', index, 'to:', description);
    }
    
    // Update hidden form fields immediately
    updateHiddenMediaFields();
}

/**
 * Update media type
 */
function updateMediaType(index, mediaType, newType) {
    if (mediaType === 'images' && Array.isArray(window.imagesData) && window.imagesData[index]) {
        window.imagesData[index].type = newType;
        console.log('Updated image type at index', index, 'to:', newType);
    } else if (mediaType === 'videos' && Array.isArray(window.videosData) && window.videosData[index]) {
        window.videosData[index].type = newType;
        console.log('Updated video type at index', index, 'to:', newType);
    }
    
    // Update hidden form fields immediately
    updateHiddenMediaFields();
}

/**
 * Render media items
 */
function renderMedia() {
    console.log('renderMedia called - Images:', window.imagesData, 'Videos:', window.videosData);
    renderImages();
    renderVideos();
    renderGif();
}

/**
 * Render images
 */
function renderImages() {
    const container = document.getElementById('images-container');
    if (!container) {
        console.error('Images container not found');
        return;
    }
    
    // Ensure imagesData is an array
    if (!Array.isArray(window.imagesData)) {
        console.warn('window.imagesData is not an array:', window.imagesData);
        window.imagesData = [];
    }
    
    console.log('Rendering images - count:', window.imagesData.length, 'data:', window.imagesData);
    
    if (window.imagesData.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted py-4">
                <i class="bi bi-camera display-4"></i>
                <p class="mt-2">No images added yet. Use the camera or upload files.</p>
            </div>
        `;
        return;
    }
    
    const html = window.imagesData.map((image, index) => `
        <div class="media-item card mb-3">
            <div class="row g-0">
                <div class="col-md-4">
                    <img src="${image.url}" class="img-fluid rounded-start" alt="Exercise image" 
                         style="height: 150px; object-fit: cover; width: 100%;">
                </div>
                <div class="col-md-8">
                    <div class="card-body">
                        <div class="row mb-2">
                            <div class="col-sm-6">
                                <label class="form-label small fw-bold">Type</label>
                                <select class="form-select form-select-sm" 
                                        onchange="updateMediaType(${index}, 'images', this.value)">
                                    <option value="start-of-movement" ${image.type === 'start-of-movement' ? 'selected' : ''}>
                                        Start of Movement
                                    </option>
                                    <option value="end-of-movement" ${image.type === 'end-of-movement' ? 'selected' : ''}>
                                        End of Movement
                                    </option>
                                </select>
                            </div>
                            <div class="col-sm-6 text-end">
                                <button type="button" class="btn btn-outline-danger btn-sm" 
                                        onclick="removeMedia(${index}, 'images')">
                                    <i class="bi bi-trash"></i> Remove
                                </button>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col">
                                <label class="form-label small fw-bold">Description</label>
                                <input type="text" class="form-control form-control-sm" 
                                       value="${image.description || ''}"
                                       placeholder="Image description..."
                                       onchange="updateMediaDescription(${index}, 'images', this.value)">
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = html;
}

/**
 * Render videos
 */
function renderVideos() {
    const container = document.getElementById('videos-container');
    if (!container) {
        console.error('Videos container not found');
        return;
    }
    
    // Ensure videosData is an array
    if (!Array.isArray(window.videosData)) {
        console.warn('window.videosData is not an array:', window.videosData);
        window.videosData = [];
    }
    
    console.log('Rendering videos - count:', window.videosData.length, 'data:', window.videosData);
    
    if (window.videosData.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted py-4">
                <i class="bi bi-camera-video display-4"></i>
                <p class="mt-2">No videos added yet. Use the camera or upload files.</p>
            </div>
        `;
        return;
    }
    
    const html = window.videosData.map((video, index) => `
        <div class="media-item card mb-3">
            <div class="row g-0">
                <div class="col-md-4">
                    <video controls class="w-100 rounded-start" style="height: 150px; object-fit: cover;">
                        <source src="${video.url}" type="video/webm">
                        <source src="${video.url}" type="video/mp4">
                        Your browser does not support the video tag.
                    </video>
                </div>
                <div class="col-md-8">
                    <div class="card-body">
                        <div class="row mb-2">
                            <div class="col-sm-6">
                                <label class="form-label small fw-bold">Description</label>
                                <input type="text" class="form-control form-control-sm" 
                                       value="${video.description || ''}"
                                       placeholder="Video description..."
                                       onchange="updateMediaDescription(${index}, 'videos', this.value)">
                            </div>
                            <div class="col-sm-6 text-end">
                                <button type="button" class="btn btn-outline-danger btn-sm" 
                                        onclick="removeMedia(${index}, 'videos')">
                                    <i class="bi bi-trash"></i> Remove
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = html;
}

/**
 * Show toast notification - wrapper for the global toast function
 */
function showEditorToast(message, type = 'info') {
    // Use the global showToast function from toast.js
    if (typeof window.showToast === 'function') {
        window.showToast(message);
    } else {
        // Fallback alert
        console.warn('Toast function not available, using alert');
        alert(message);
    }
}

/**
 * Form validation
 */
function validateForm() {
    const form = document.getElementById('exercise-form');
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
        }
    });
    
    // Check if at least one primary muscle is selected
    const primaryMuscles = form.querySelectorAll('input[name="primaryMuscles"]:checked');
    if (primaryMuscles.length === 0) {
        showEditorToast('Please select at least one primary muscle group');
        isValid = false;
    }
    
    return isValid;
}

// Clean up camera streams when page unloads
window.addEventListener('beforeunload', () => {
    Object.keys(window.cameraStreams).forEach(type => {
        if (window.cameraStreams[type]) {
            window.cameraStreams[type].getTracks().forEach(track => track.stop());
        }
    });
});

// Initialize sortable for media containers if Sortable is available
document.addEventListener('DOMContentLoaded', function() {
    if (typeof Sortable !== 'undefined') {
        // Make media containers sortable
        const imagesContainer = document.getElementById('images-container');
        const videosContainer = document.getElementById('videos-container');
        
        if (imagesContainer) {
            new Sortable(imagesContainer, {
                animation: 150,
                onEnd: function(evt) {
                    // Reorder imagesData array
                    const item = window.imagesData.splice(evt.oldIndex, 1)[0];
                    window.imagesData.splice(evt.newIndex, 0, item);
                }
            });
        }
        
        if (videosContainer) {
            new Sortable(videosContainer, {
                animation: 150,
                onEnd: function(evt) {
                    // Reorder videosData array
                    const item = window.videosData.splice(evt.oldIndex, 1)[0];
                    window.videosData.splice(evt.newIndex, 0, item);
                }
            });
        }
    }
});