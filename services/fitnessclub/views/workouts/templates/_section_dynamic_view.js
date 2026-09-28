
<script>
  // Rebuild the timer object on every render so template/JS fixes always take effect,
  // even in a long-lived tab, while preserving any timers still counting down across HTMX swaps.
  window.ExerciseTimer = {
    activeTimers: (window.ExerciseTimer && window.ExerciseTimer.activeTimers) || {},
    completionResetTimers: (window.ExerciseTimer && window.ExerciseTimer.completionResetTimers) || {},
    RING_RADIUS: 19,

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
      const totalSeconds = this.toSeconds(duration, timeUnit);
      const progressCircle = timerWrapper.querySelector('.timer-ring-progress');
      const circumference = 2 * Math.PI * this.RING_RADIUS;

      if (progressCircle) {
        progressCircle.style.strokeDasharray = `${circumference}`;
        progressCircle.style.strokeDashoffset = '0';
      }

      // Start new timer
      let remainingTime = totalSeconds;
      timerWrapper.classList.add('running');
      timerWrapper.classList.remove('completed');
      timerWrapper.setAttribute('title', 'Click to stop timer');

      // Update display immediately
      timerDisplay.textContent = this.formatTime(remainingTime);

      this.activeTimers[exerciseId] = setInterval(() => {
        remainingTime--;
        timerDisplay.textContent = this.formatTime(remainingTime);

        if (progressCircle && totalSeconds > 0) {
          const elapsedFraction = Math.min(1, 1 - (remainingTime / totalSeconds));
          progressCircle.style.strokeDashoffset = `${circumference * elapsedFraction}`;
        }

        if (remainingTime <= 0) {
          // Timer completed
          clearInterval(this.activeTimers[exerciseId]);
          delete this.activeTimers[exerciseId];

          timerWrapper.classList.remove('running');
          timerWrapper.classList.add('completed');
          timerWrapper.setAttribute('title', 'Timer completed! Click to restart');

          // Play completion sound with multiple fallbacks
          this.playCompletionSound();

          // Reset the ring and label back to idle after a brief celebration
          this.completionResetTimers[exerciseId] = setTimeout(() => {
            delete this.completionResetTimers[exerciseId];
            timerWrapper.classList.remove('completed');
            if (progressCircle) {
              progressCircle.style.strokeDashoffset = '0';
            }
            timerDisplay.textContent = this.formatDuration(duration, timeUnit);
            timerWrapper.setAttribute('title', `Start ${duration} ${timeUnit} timer`);
          }, 3000);

          return;
        }
      }, 1000);
    },

    stop: function (exerciseId) {
      if (this.activeTimers[exerciseId]) {
        clearInterval(this.activeTimers[exerciseId]);
        delete this.activeTimers[exerciseId];
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
      const progressCircle = timerWrapper.querySelector('.timer-ring-progress');

      timerWrapper.classList.remove('running', 'completed');
      timerWrapper.setAttribute('title', `Start ${duration} ${timeUnit} timer`);
      if (progressCircle) {
        progressCircle.style.strokeDashoffset = '0';
      }
      timerDisplay.textContent = this.formatDuration(duration, timeUnit);
    },

    formatTime: function (seconds) {
      if (seconds < 0) return '0s';

      if (seconds < 60) {
        return `${seconds}s`;
      } else if (seconds < 3600) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
      } else {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return `${hours}:${minutes.toString().padStart(2, '0')}:${(seconds % 60).toString().padStart(2, '0')}`;
      }
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

  // Clean up timers when page unloads or when HTMX loads new content
  window.addEventListener('beforeunload', () => {
    window.ExerciseTimer.cleanup();
  });

  // Clean up timers when HTMX replaces content
  document.addEventListener('htmx:beforeSwap', () => {
    window.ExerciseTimer.cleanup();
  });
</script>
