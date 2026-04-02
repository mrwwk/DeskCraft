# Audacity Audio Assets Manifest

Generated for OSWorld Audacity task testing

## Directory Structure
```
assets/audacity/
├── audio/           # WAV audio files (20 files)
└── projects/        # Placeholder for future .aup3 project files
```

## Audio Asset Inventory

### Basic Test Files
| File Name | Duration | Content | Purpose |
|-----------|----------|---------|---------|
| `sample.wav` | 8s | 440Hz sine wave | General testing |
| `test.wav` | 5s | 440Hz sine wave | Basic operations |

### Speech-Like Audio
| File Name | Duration | Content | Purpose |
|-----------|----------|---------|---------|
| `speech.wav` | 12s | Frequency-varying pattern | Speech operations testing |

### Effect Test Files
| File Name | Duration | Content | Purpose |
|-----------|----------|---------|---------|
| `noisy_recording.wav` | 14s | Sine wave + 15% noise | Noise reduction workflow |
| `fade_test.wav` | 18s | 523Hz sine wave | Fade in/out effects |
| `eq_test.wav` | 20s | Multi-frequency (100Hz, 1kHz, 5kHz) | Equalization testing |
| `clipping_test.wav` | 15s | Overdriven sine wave | Find Clipping feature |
| `volume_test.wav` | 10s | 392Hz sine wave | Amplify/volume adjustment |

### Multi-Track Audio (for mixing)
| File Name | Duration | Content | Purpose |
|-----------|----------|---------|---------|
| `vocals.wav` | 30s | Melodic pattern (440-587Hz) | Vocal track mixing |
| `drums.wav` | 30s | Percussive low-frequency pattern | Drum track mixing |
| `bass.wav` | 30s | Low-frequency variation (80-100Hz) | Bass track mixing |

### Editing Test Files
| File Name | Duration | Content | Purpose |
|-----------|----------|---------|---------|
| `edit_test.wav` | 12s | 440Hz sine wave | Cut/paste operations |
| `duplicate_test.wav` | 8s | 494Hz sine wave | Copy/duplicate operations |
| `delete_test.wav` | 10s | 392Hz sine wave | Delete operations |

### Advanced Test Files
| File Name | Duration | Content | Purpose |
|-----------|----------|---------|---------|
| `crossfade_test.wav` | 15s | Combined 440Hz + 660Hz | Cross-fade between tracks |
| `analysis_test.wav` | 15s | 5-frequency harmonic series | Plot Spectrum analysis |
| `undo_test.wav` | 18s | 392Hz sine wave | Undo/redo history testing |
| `label_test.wav` | 32s | 440Hz sine wave | Label track management |
| `mute_solo_test.wav` | 25s | Dual-frequency pattern | Track mute/solo operations |
| `mix_test.wav` | 20s | 4-frequency chord | Track volume mixing |

## Technical Specifications

- **Sample Rate**: 44100 Hz (44.1 kHz)
- **Bit Depth**: 16-bit PCM
- **Channels**: Mono
- **File Format**: WAV (Waveform Audio File Format)

## Audio Characteristics

### Frequency Range
- **Minimum**: 80 Hz (bass.wav)
- **Maximum**: 3200 Hz (analysis_test harmonics)
- **Most Common**: 390-530 Hz range (speech-like frequencies)

### Dynamic Range
- **Normal Amplitude**: 0.4-0.6 (pre-clip)
- **Clipping Level**: >1.0 (clipping_test.wav intentionally overdriven)
- **Noise Level**: 15% added noise (noisy_recording.wav)

### Duration Range
- **Shortest**: 5 seconds (test.wav)
- **Longest**: 32 seconds (label_test.wav)
- **Most Common**: 12-20 seconds

## Usage Guidelines

### For Basic Tasks (L1)
Use: `sample.wav`, `test.wav`, `speech.wav`, `edit_test.wav`, `duplicate_test.wav`, `delete_test.wav`

### For Effect Tasks (L1/L2)
Use: `noisy_recording.wav`, `fade_test.wav`, `eq_test.wav`, `clipping_test.wav`, `volume_test.wav`

### For Multi-Track Tasks (L2)
Use: `vocals.wav`, `drums.wav`, `bass.wav` (together)

### For Advanced Tasks (L2/L3)
Use: `crossfade_test.wav`, `analysis_test.wav`, `undo_test.wav`, `label_test.wav`, `mute_solo_test.wav`, `mix_test.wav`

## Generation Information

- **Generated with**: Python + NumPy + SciPy
- **Generation Date**: 2026-03-14
- **Total Files**: 20
- **Total Size**: ~30 MB
- **License**: Generated assets are suitable for open-source use (public domain)

## Future Additions

- Audacity project files (.aup3) for pre-configured scenarios
- Stereo versions of mono files
- Different sample rates (48kHz, 96kHz) for advanced testing
- Real vocal/instrument recordings if needed

## Notes

All audio files are synthesized, not recorded. They provide consistent, repeatable test scenarios without licensing concerns. For more realistic testing scenarios, consider adding actual recordings from open-source audio libraries.
