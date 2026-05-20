
<script>
  // Use global namespace to avoid conflicts with HTMX reloads
  window.ExerciseTimer = window.ExerciseTimer || {
    activeTimers: {},

    start: function (exerciseId, duration) {
      const timerWrapper = document.querySelector(`[data-exercise-id="${exerciseId}"]`);
      const timerDisplay = document.getElementById(`timer-${exerciseId}`);

      // If timer is already running, stop it
      if (this.activeTimers[exerciseId]) {
        this.stop(exerciseId);
        return;
      }

      // Start new timer
      let remainingTime = duration;
      timerWrapper.classList.add('running');
      timerWrapper.classList.remove('completed');
      timerWrapper.setAttribute('title', 'Click to stop timer');

      // Update display immediately
      timerDisplay.textContent = this.formatTime(remainingTime);

      this.activeTimers[exerciseId] = setInterval(() => {
        remainingTime--;
        timerDisplay.textContent = this.formatTime(remainingTime);

        if (remainingTime <= 0) {
          // Timer completed
          clearInterval(this.activeTimers[exerciseId]);
          delete this.activeTimers[exerciseId];

          timerWrapper.classList.remove('running');
          timerWrapper.classList.add('completed');
          timerWrapper.setAttribute('title', 'Timer completed! Click to restart');

          // Flash effect and sound
          timerWrapper.style.animation = 'pulse 1s infinite';

          // Play completion sound with multiple fallbacks
          this.playCompletionSound();

          // Remove animation after 3 seconds and reset display
          setTimeout(() => {
            timerWrapper.style.animation = '';
            timerDisplay.textContent = `${duration}s`;
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

      const timerWrapper = document.querySelector(`[data-exercise-id="${exerciseId}"]`);
      const timerDisplay = document.getElementById(`timer-${exerciseId}`);
      const duration = parseInt(timerWrapper.getAttribute('data-duration'));

      timerWrapper.classList.remove('running', 'completed');
      timerWrapper.setAttribute('title', `Start ${duration} second timer`);
      timerWrapper.style.animation = '';
      timerDisplay.textContent = `${duration}s`;
    },

    formatTime: function (seconds) {
      if (seconds < 0) return '0s';

      if (seconds < 60) {
        return `${seconds}s`;
      } else {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
      }
    },

    cleanup: function () {
      Object.keys(this.activeTimers).forEach(exerciseId => this.stop(exerciseId));
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
  function startExerciseTimer(exerciseId, duration) {
    window.ExerciseTimer.start(exerciseId, duration);
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
