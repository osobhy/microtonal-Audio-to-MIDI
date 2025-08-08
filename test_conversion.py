import librosa
import pretty_midi
import numpy as np
import os

def test_conversion():
    # Test with a simple sine wave or check if librosa.pyin works
    print("Testing librosa.pyin function...")
    
    # Create a simple test audio (sine wave)
    sr = 22050
    duration = 1.0
    t = np.linspace(0, duration, int(sr * duration))
    y = np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave
    
    try:
        # Test pitch tracking
        f0, voiced_flag, _ = librosa.pyin(
            y,
            fmin=librosa.note_to_hz('C2'),
            fmax=librosa.note_to_hz('C7'),
            sr=sr,
            frame_length=2048,
            hop_length=256
        )
        print("✅ librosa.pyin works")
        print(f"F0 shape: {f0.shape}")
        print(f"Voiced flag shape: {voiced_flag.shape}")
        
        # Test MIDI conversion
        times = librosa.times_like(f0, sr=sr, hop_length=256)
        midi = pretty_midi.PrettyMIDI()
        instrument = pretty_midi.Instrument(program=0)
        
        # Simple conversion
        for i in range(len(f0)):
            if voiced_flag[i] and not np.isnan(f0[i]):
                pitch = pretty_midi.hz_to_note_number(f0[i])
                note = pretty_midi.Note(
                    velocity=100,
                    pitch=int(pitch),
                    start=times[i],
                    end=times[i] + 0.1
                )
                instrument.notes.append(note)
        
        midi.instruments.append(instrument)
        print("✅ MIDI creation works")
        print(f"Created {len(instrument.notes)} notes")
        
        # Test file writing
        test_midi_path = "test_output.mid"
        midi.write(test_midi_path)
        print(f"✅ MIDI file written to {test_midi_path}")
        
        # Clean up
        if os.path.exists(test_midi_path):
            os.remove(test_midi_path)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_conversion() 