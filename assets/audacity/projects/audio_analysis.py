#!/usr/bin/env python3
"""
Simple audio analysis utility for Audacity project validation
"""

import numpy as np
from scipy.io import wavfile
import librosa
import soundfile as sf

def analyze_audio(file_path):
    """Basic audio analysis for testing"""
    try:
        # Load audio
        y, sr = librosa.load(file_path, sr=None)
        
        # Basic properties
        duration = librosa.get_duration(y=y, sr=sr)
        max_amplitude = np.max(np.abs(y))
        
        # Frequency analysis
        fft = np.fft.fft(y)
        freqs = np.fft.fftfreq(len(y), 1/sr)
        magnitude = np.abs(fft)
        peak_freq = freqs[np.argmax(magnitude[1:len(magnitude)//2]) + 1]
        
        return {
            "duration": duration,
            "sample_rate": sr,
            "max_amplitude": float(max_amplitude),
            "peak_frequency": abs(float(peak_freq)),
            "channels": 1 if len(y.shape) == 1 else y.shape[0],
            "samples": len(y)
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = analyze_audio(sys.argv[1])
        print(result)
    else:
        print("Usage: python audio_analysis.py <audio_file>")
