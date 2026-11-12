
<script>
  // Rebuild the timer object on every render so template/JS fixes always take effect,
  // even in a long-lived tab, while preserving any timers still counting down across HTMX swaps.
  window.ExerciseTimer = {
    activeTimers: (window.ExerciseTimer && window.ExerciseTimer.activeTimers) || {},
    completionResetTimers: (window.ExerciseTimer && window.ExerciseTimer.completionResetTimers) || {},
    RING_RADIUS: 19,
    overlayState: (window.ExerciseTimer && window.ExerciseTimer.overlayState) || null,

    // Converts a duration value expressed in the exercise's configured time unit (Tu) into seconds.
    toSeconds: function (value, unit) {
      const numericValue = Number(value) || 0;
      const normalizedUnit = (unit || 'sec').toString().trim().toLowerCase();
      if (normalizedUnit.startsWith('hour')) {
        return numericValue * 3600;
      }
      if (normalizedUnit.startsWith('min')) {
        return numericValue * 60;
      }
      return numericValue;
    },

    // Renders the initial/idle label for a timer, e.g. "3m" or "60s", matching the configured unit.
    formatDuration: function (value, unit) {
      const normalizedUnit = (unit || 'sec').toString().trim().toLowerCase();
      const suffix = normalizedUnit.charAt(0) || 's';
      return `${value}${suffix}`;
    },

    start: function (exerciseId, duration, unit) {
      const timerWrapper = document.querySelector(`[data-exercise-id="${exerciseId}"]`);
      const timerDisplay = document.getElementById(`timer-${exerciseId}`);
      if (!timerWrapper || !timerDisplay) {
        return;
      }

      // If timer is already running, stop it
      if (this.activeTimers[exerciseId]) {
        this.stop(exerciseId);
        return;
      }

      if (this.completionResetTimers[exerciseId]) {
        clearTimeout(this.completionResetTimers[exerciseId]);
        delete this.completionResetTimers[exerciseId];
      }

      const timeUnit = unit || timerWrapper.getAttribute('data-unit') || 'sec';
      duration = duration !== undefined ? duration : timerWrapper.getAttribute('data-duration');
      const totalSeconds = this.toSeconds(duration, timeUnit);
      if (totalSeconds <= 0) {
        return;
      }

      this.removeOverlay();
      const overlay = this.buildOverlay(exerciseId, totalSeconds);
      const state = {
        exerciseId: exerciseId,
        remaining: totalSeconds,
        total: totalSeconds,
        paused: false,
        overlay: overlay,
        interval: null
      };
      this.overlayState = state;
      this.renderOverlay(state);

      // Pressing the timer card pauses/resumes; pressing anywhere else dismisses.
      overlay.addEventListener('click', (event) => {
        event.stopPropagation();
        if (event.target.closest('.exercise-timer-card')) {
          this.togglePause(state);
        } else {
          this.stop(exerciseId);
        }
      });

      timerWrapper.classList.add('running');
      state.interval = setInterval(() => {
        if (state.paused) {
          return;
        }
        state.remaining--;
        this.renderOverlay(state);
        if (state.remaining <= 0) {
          this.playCompletionSound();
          this.stop(exerciseId);
        }
      }, 1000);
      this.activeTimers[exerciseId] = state.interval;
    },

    togglePause: function (state) {
      state.paused = !state.paused;
      this.renderOverlay(state);
    },

    buildOverlay: function (exerciseId, totalSeconds) {
      if (!document.getElementById('exercise-timer-styles')) {
        const style = document.createElement('style');
        style.id = 'exercise-timer-styles';
        style.textContent = `
          .exercise-timer-overlay { position: fixed; inset: 0; z-index: 2000; display: flex;
            align-items: center; justify-content: center; background: rgba(0,0,0,0.75); }
          .exercise-timer-card { position: relative; width: min(80vw, 380px); aspect-ratio: 1;
            border-radius: 50%; background: #fff; display: flex; flex-direction: column;
            align-items: center; justify-content: center; cursor: pointer; user-select: none;
            -webkit-tap-highlight-color: transparent; box-shadow: 0 0 40px rgba(0,0,0,0.5); }
          .exercise-timer-card svg { position: absolute; inset: 0; width: 100%; height: 100%; transform: rotate(-90deg); }
          .exercise-timer-card .et-bg { fill: none; stroke: #e9ecef; stroke-width: 4; }
          .exercise-timer-card .et-progress { fill: none; stroke: #0d6efd; stroke-width: 4; stroke-linecap: round;
            transition: stroke-dashoffset 1s linear; }
          .exercise-timer-card.paused .et-progress { stroke: #fd7e14; }
          .exercise-timer-time { position: relative; font-size: clamp(3.5rem, 20vw, 6rem); font-weight: 700;
            font-variant-numeric: tabular-nums; line-height: 1; color: #212529; }
          .exercise-timer-hint { position: relative; margin-top: .5rem; font-size: 1rem; color: #6c757d; }
        `;
        document.head.appendChild(style);
      }
      const circumference = 2 * Math.PI * 46;
      const overlay = document.createElement('div');
      overlay.className = 'exercise-timer-overlay';
      overlay.innerHTML = `
        <div class="exercise-timer-card">
          <svg viewBox="0 0 100 100">
            <circle class="et-bg" cx="50" cy="50" r="46"></circle>
            <circle class="et-progress" cx="50" cy="50" r="46"
              stroke-dasharray="${circumference}" stroke-dashoffset="0"></circle>
          </svg>
          <div class="exercise-timer-time"></div>
          <div class="exercise-timer-hint"></div>
        </div>`;
      document.body.appendChild(overlay);
      return overlay;
    },

    renderOverlay: function (state) {
      const remaining = Math.max(0, state.remaining);
      const card = state.overlay.querySelector('.exercise-timer-card');
      const progress = state.overlay.querySelector('.et-progress');
      const circumference = 2 * Math.PI * 46;
      state.overlay.querySelector('.exercise-timer-time').textContent = this.formatTime(remaining);
      state.overlay.querySelector('.exercise-timer-hint').textContent =
        state.paused ? 'Paused – tap to resume' : 'Tap to pause';
      card.classList.toggle('paused', state.paused);
      progress.style.strokeDashoffset = `${circumference * (1 - remaining / state.total)}`;
    },

    removeOverlay: function () {
      if (this.overlayState) {
        clearInterval(this.overlayState.interval);
        this.overlayState.overlay.remove();
        this.overlayState = null;
      }
    },

    stop: function (exerciseId) {
      if (this.activeTimers[exerciseId]) {
        clearInterval(this.activeTimers[exerciseId]);
        delete this.activeTimers[exerciseId];
      }
      if (this.overlayState && this.overlayState.exerciseId === exerciseId) {
        this.removeOverlay();
      }
      if (this.completionResetTimers[exerciseId]) {
        clearTimeout(this.completionResetTimers[exerciseId]);
        delete this.completionResetTimers[exerciseId];
      }

      const timerWrapper = document.querySelector(`[data-exercise-id="${exerciseId}"]`);
      const timerDisplay = document.getElementById(`timer-${exerciseId}`);
      if (!timerWrapper || !timerDisplay) {
        return;
      }
      const duration = timerWrapper.getAttribute('data-duration');
      const timeUnit = timerWrapper.getAttribute('data-unit') || 'sec';

      timerWrapper.classList.remove('running', 'completed');
      timerWrapper.setAttribute('title', `Start ${duration} ${timeUnit} timer`);
      timerDisplay.textContent = this.formatDuration(duration, timeUnit);
    },

    // Always minutes:seconds (e.g. 0:45, 1:30, 65:00 for long durations).
    formatTime: function (seconds) {
      const total = Math.max(0, Math.floor(seconds));
      const minutes = Math.floor(total / 60);
      return `${minutes}:${(total % 60).toString().padStart(2, '0')}`;
    },

    cleanup: function () {
      Object.keys(this.activeTimers).forEach(exerciseId => this.stop(exerciseId));
      Object.keys(this.completionResetTimers).forEach(exerciseId => {
        clearTimeout(this.completionResetTimers[exerciseId]);
        delete this.completionResetTimers[exerciseId];
      });
    },

    playCompletionSound: function () {
      // Try recorded audio file first, then fallback to generated tone
      this.playRecordedAudioSound() || this.playWebAudioSound() || this.playHTMLAudioSound() || this.playFallbackSound();
    },

    playRecordedAudioSound: function () {
      try {
        // Try to play a recorded completion sound file
        // Place your audio file in /static/sounds/ directory
        const audioFiles = [
          '/static/sounds/timer-complete.wav',
          '/static/sounds/timer-complete.mp3',
          '/static/sounds/completion.wav',
          '/static/sounds/completion.mp3'
        ];

        // Try each audio file until one loads successfully
        for (const audioFile of audioFiles) {
          const audio = new Audio(audioFile);
          audio.volume = 0.7; // Good volume for recorded files
          audio.preload = 'auto';

          // Return a promise that resolves when audio plays successfully
          return audio.play().then(() => {
            console.log(`✅ Timer completion sound played: ${audioFile}`);
            return true;
          }).catch(() => {
            console.log(`⚠️ Could not play: ${audioFile}`);
            return false;
          });
        }

        return false; // No audio files found
      } catch (e) {
        console.log('⚠️ Recorded audio not available:', e.message);
        return false;
      }
    },

    playWebAudioSound: function () {
      console.log('playWebAudioSound called');
      try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();

        // Create a long sustained completion sound (2 full seconds)
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();

        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);

        // Use sine wave for smooth, pleasant sound
        oscillator.type = 'sine';
        oscillator.frequency.setValueAtTime(600, audioContext.currentTime); // Pleasant mid-range

        // Keep volume steady for most of the duration, then fade at the very end
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);           // Start loud
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime + 1.7);     // Hold steady for 1.7 seconds
        gainNode.gain.linearRampToValueAtTime(0, audioContext.currentTime + 2.0); // Quick fade in last 0.3s

        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 2.0);

        console.log('✅ Long timer completion sound played (Web Audio API) - 2 seconds sustained');
        return true;
      } catch (e) {
        console.log('⚠️ Web Audio API not available:', e.message);
        return false;
      }
    },

    playHTMLAudioSound: function () {
      console.log('playHTMLAudioSound called - using backup base64 audio');
      try {
        // Fallback: Create audio element with embedded longer beep
        const audio = new Audio('data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmsdBTCG0PHJYB4FJHfH8N2QQAoUXrTp66hVFApGn+DyvmsdBTCG0PHJeCQFJHfH8N2QQAoUXrTp66hVFApGn+DyvmsdBTCGz+7BcygEJ3bH8N2QQAoUXrTp66hVFApGn+DyvmsdBTGG0PHJeCQFJHfH8N2QQAoUXrTp66hVFApGn+DyvmsdBTGG0PHJeCQF');
        audio.volume = 0.3;
        audio.play().then(() => {
          console.log('✅ Timer completion sound played (HTML Audio - Base64)');
        }).catch(() => {
          throw new Error('HTML Audio failed');
        });
        return true;
      } catch (e) {
        console.log('⚠️ HTML Audio not available:', e.message);
        return false;
      }
    },

    playFallbackSound: function () {
      console.log('playFallbackSound called');
      try {
        // Visual notification if sound fails
        console.log('🔔 TIMER COMPLETED! (Sound not available)');

        // Try system notification if available
        if ('Notification' in window && Notification.permission === 'granted') {
          new Notification('Exercise Timer Complete!', {
            body: 'Your exercise timer has finished.',
            icon: '/static/icon-timer.png',
            silent: false
          });
          console.log('✅ Timer completion notification sent');
          return true;
        } else if ('Notification' in window && Notification.permission !== 'denied') {
          Notification.requestPermission().then(permission => {
            if (permission === 'granted') {
              new Notification('Exercise Timer Complete!', {
                body: 'Your exercise timer has finished.',
                silent: false
              });
            }
          });
        }

        return true; // Always return true for fallback
      } catch (e) {
        console.log('⚠️ All sound methods failed:', e.message);
        return false;
      }
    }
  };

  // Global timer functions for backward compatibility
  function startExerciseTimer(exerciseId, duration, unit) {
    window.ExerciseTimer.start(exerciseId, duration, unit);
  }

  function stopExerciseTimer(exerciseId) {
    window.ExerciseTimer.stop(exerciseId);
  }

  function formatTime(seconds) {
    return window.ExerciseTimer.formatTime(seconds);
  }

  // Applies an edited T/Tu parameter to the timer button (HX-Trigger from the server).
  if (window.exerciseTimerParamHandler) {
    document.body.removeEventListener('timerParamChanged', window.exerciseTimerParamHandler);
  }
  window.exerciseTimerParamHandler = function (event) {
    const detail = event.detail || {};
    const wrapper = document.querySelector(`.timer-ring-wrapper[data-exercise-id="${detail.exerciseId}"]`);
    if (!wrapper) {
      return;
    }
    window.ExerciseTimer.stop(detail.exerciseId);
    const value = (detail.value || '').toString().trim();
    if (detail.param === 'T' && /^\d+(\.\d+)?$/.test(value)) {
      wrapper.setAttribute('data-duration', value);
    } else if (detail.param === 'Tu' && value) {
      wrapper.setAttribute('data-unit', value);
    } else {
      return;
    }
    window.ExerciseTimer.stop(detail.exerciseId);
  };
  document.body.addEventListener('timerParamChanged', window.exerciseTimerParamHandler);

  // Clean up timers when page unloads or when HTMX loads new content
  window.addEventListener('beforeunload', () => {
    window.ExerciseTimer.cleanup();
  });

  // Clean up timers when HTMX replaces content
  document.addEventListener('htmx:beforeSwap', () => {
    window.ExerciseTimer.cleanup();
  });
</script>
