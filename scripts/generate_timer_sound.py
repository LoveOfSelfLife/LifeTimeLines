#!/usr/bin/env python3
"""
Generate a pleasant timer completion sound file.
Creates a 2-second audio file with a nice bell-like completion sound.
"""

import wave
import math
import struct
import os

def generate_completion_sound(filename="timer-complete.wav", duration=2.0, sample_rate=44100):
    """
    Generate a pleasant completion sound with multiple harmonics for a bell-like effect.
    """
    print(f"Generating timer completion sound: {filename}")
    
    # Calculate total samples
    total_samples = int(duration * sample_rate)
    
    # Create audio data
    audio_data = []
    
    for i in range(total_samples):
        t = i / sample_rate  # Time in seconds
        
        # Create a bell-like sound with multiple harmonic frequencies
        # Base frequency and harmonics
        freq1 = 800   # Primary tone
        freq2 = 1000  # Harmonic
        freq3 = 1200  # Higher harmonic
        freq4 = 600   # Lower harmonic for richness
        
        # Generate composite waveform with envelope
        envelope = math.exp(-t * 2.5)  # Exponential decay like a real bell
        
        # Mix multiple sine waves for rich harmonic content
        wave1 = 0.4 * math.sin(2 * math.pi * freq1 * t) * envelope
        wave2 = 0.2 * math.sin(2 * math.pi * freq2 * t) * envelope
        wave3 = 0.15 * math.sin(2 * math.pi * freq3 * t) * envelope
        wave4 = 0.25 * math.sin(2 * math.pi * freq4 * t) * envelope
        
        # Add subtle tremolo for more natural sound
        tremolo = 1 + 0.1 * math.sin(2 * math.pi * 4 * t)
        
        # Combine all components
        sample = (wave1 + wave2 + wave3 + wave4) * tremolo
        
        # Apply fade out in last 0.3 seconds for smooth ending
        if t > duration - 0.3:
            fade_factor = (duration - t) / 0.3
            sample *= fade_factor
        
        # Convert to 16-bit integer
        sample_int = int(sample * 32767)
        audio_data.append(sample_int)
    
    # Write WAV file
    with wave.open(filename, 'w') as wav_file:
        # Set parameters: 1 channel (mono), 2 bytes per sample, sample rate
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        
        # Write audio data
        for sample in audio_data:
            wav_file.writeframes(struct.pack('<h', sample))
    
    file_size = os.path.getsize(filename)
    print(f"✅ Created {filename}")
    print(f"   Duration: {duration} seconds")
    print(f"   Sample rate: {sample_rate} Hz")
    print(f"   File size: {file_size:,} bytes")
    print(f"   Type: Pleasant bell-like completion sound")

def generate_simple_chime(filename="completion.wav", duration=1.5):
    """
    Generate a simpler chime sound - shorter and more subtle.
    """
    print(f"Generating simple chime sound: {filename}")
    
    sample_rate = 44100
    total_samples = int(duration * sample_rate)
    audio_data = []
    
    for i in range(total_samples):
        t = i / sample_rate
        
        # Simple two-tone chime: high note followed by lower note
        if t < 0.7:
            # High note (C6 - 1047 Hz)
            frequency = 1047
            envelope = math.exp(-t * 3)
        else:
            # Lower note (G5 - 784 Hz)
            frequency = 784
            envelope = math.exp(-(t - 0.7) * 2) * 0.7
        
        # Generate sine wave with envelope
        sample = 0.5 * math.sin(2 * math.pi * frequency * t) * envelope
        
        # Apply final fade
        if t > duration - 0.2:
            fade_factor = (duration - t) / 0.2
            sample *= fade_factor
        
        sample_int = int(sample * 32767)
        audio_data.append(sample_int)
    
    # Write WAV file
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2) 
        wav_file.setframerate(sample_rate)
        
        for sample in audio_data:
            wav_file.writeframes(struct.pack('<h', sample))
    
    file_size = os.path.getsize(filename)
    print(f"✅ Created {filename}")
    print(f"   Duration: {duration} seconds")
    print(f"   File size: {file_size:,} bytes")
    print(f"   Type: Simple two-tone chime")

if __name__ == "__main__":
    # Create sounds directory if it doesn't exist
    sounds_dir = "../services/fitnessclub/static/sounds"
    os.makedirs(sounds_dir, exist_ok=True)
    
    # Generate both sound files in the correct location
    bell_path = os.path.join(sounds_dir, "timer-complete.wav")
    chime_path = os.path.join(sounds_dir, "completion.wav")
    
    print("🎵 Generating timer completion sounds...")
    print("=" * 50)
    
    # Generate the main bell-like sound
    generate_completion_sound(bell_path, duration=2.0)
    print()
    
    # Generate the simpler chime alternative  
    generate_simple_chime(chime_path, duration=1.5)
    print()
    
    print("🎯 Sound files created successfully!")
    print("The timer will now use these custom sounds instead of generated tones.")
    print(f"Files created in: {os.path.abspath(sounds_dir)}")