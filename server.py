from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import tempfile
import json
import base64
import io
from werkzeug.utils import secure_filename
import librosa
import pretty_midi
import numpy as np

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'flac', 'aiff', 'm4a'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_audio_to_midi(audio_path, settings):
    """
    Convert audio to MIDI using the existing script logic
    """
    # Extract settings
    PITCH_BEND_RANGE = settings.get('pitchBendRange', 2)
    DRIFT_THRESHOLD = settings.get('driftThreshold', 0.5)
    QUANTIZATION_STEP = settings.get('quantizationStep', 0.5)

    # Load audio
    y, sr = librosa.load(audio_path, sr=None)

    # Pitch tracking (monophonic)
    f0, voiced_flag, _ = librosa.pyin(
        y,
        fmin=librosa.note_to_hz('C2'),
        fmax=librosa.note_to_hz('C7'),
        sr=sr,
        frame_length=2048,
        hop_length=256
    )

    times = librosa.times_like(f0, sr=sr, hop_length=256)

    # Init MIDI
    midi = pretty_midi.PrettyMIDI()
    instrument = pretty_midi.Instrument(program=0)

    note_start = None
    note_pitch_ref = None
    note_index_start = None

    def quantize_pitch(pitch):
        return round(pitch / QUANTIZATION_STEP) * QUANTIZATION_STEP

    for i in range(len(f0)):
        if voiced_flag[i] and not np.isnan(f0[i]):
            current_pitch = pretty_midi.hz_to_note_number(f0[i])
            current_pitch = quantize_pitch(current_pitch)

            if note_start is None:
                # First note
                note_start = times[i]
                note_pitch_ref = current_pitch
                note_index_start = i
            else:
                pitch_deviation = current_pitch - note_pitch_ref
                if abs(pitch_deviation) > DRIFT_THRESHOLD:
                    # Finish current note
                    note_end = times[i]
                    base_pitch = int(round(note_pitch_ref))
                    note = pretty_midi.Note(
                        velocity=100,
                        pitch=base_pitch,
                        start=note_start,
                        end=note_end
                    )
                    instrument.notes.append(note)

                    for j in range(note_index_start, i):
                        if voiced_flag[j] and not np.isnan(f0[j]):
                            raw_pitch = pretty_midi.hz_to_note_number(f0[j])
                            quantized_pitch = quantize_pitch(raw_pitch)
                            bend_semitones = quantized_pitch - base_pitch
                            bend_value = int((bend_semitones / PITCH_BEND_RANGE) * 8192)
                            bend_value = np.clip(bend_value, -8192, 8191)
                            instrument.pitch_bends.append(
                                pretty_midi.PitchBend(pitch=bend_value, time=times[j])
                            )

                    # Start new note
                    note_start = times[i]
                    note_pitch_ref = current_pitch
                    note_index_start = i
        else:
            if note_start is not None:
                # Finish last note due to silence
                note_end = times[i]
                base_pitch = int(round(note_pitch_ref))
                note = pretty_midi.Note(
                    velocity=100,
                    pitch=base_pitch,
                    start=note_start,
                    end=note_end
                )
                instrument.notes.append(note)

                for j in range(note_index_start, i):
                    if voiced_flag[j] and not np.isnan(f0[j]):
                        raw_pitch = pretty_midi.hz_to_note_number(f0[j])
                        quantized_pitch = quantize_pitch(raw_pitch)
                        bend_semitones = quantized_pitch - base_pitch
                        bend_value = int((bend_semitones / PITCH_BEND_RANGE) * 8192)
                        bend_value = np.clip(bend_value, -8192, 8191)
                        instrument.pitch_bends.append(
                            pretty_midi.PitchBend(pitch=bend_value, time=times[j])
                        )

            note_start = None
            note_pitch_ref = None
            note_index_start = None

    # Handle last note
    if note_start is not None and note_index_start is not None:
        note_end = times[-1]
        base_pitch = int(round(note_pitch_ref))
        note = pretty_midi.Note(
            velocity=100,
            pitch=base_pitch,
            start=note_start,
            end=note_end
        )
        instrument.notes.append(note)

        for j in range(note_index_start, len(f0)):
            if voiced_flag[j] and not np.isnan(f0[j]):
                raw_pitch = pretty_midi.hz_to_note_number(f0[j])
                quantized_pitch = quantize_pitch(raw_pitch)
                bend_semitones = quantized_pitch - base_pitch
                bend_value = int((bend_semitones / PITCH_BEND_RANGE) * 8192)
                bend_value = np.clip(bend_value, -8192, 8191)
                instrument.pitch_bends.append(
                    pretty_midi.PitchBend(pitch=bend_value, time=times[j])
                )

    # Add instrument to MIDI
    midi.instruments.append(instrument)
    
    return midi

@app.route('/api/convert', methods=['POST'])
def convert_audio():
    try:
        print("=== Starting conversion ===")
        
        # Check if audio file is present
        if 'audio' not in request.files:
            print("Error: No audio file in request")
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        print(f"Received file: {audio_file.filename}")
        
        if audio_file.filename == '':
            print("Error: Empty filename")
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(audio_file.filename):
            print(f"Error: Invalid file type: {audio_file.filename}")
            return jsonify({'error': 'Invalid file type'}), 400

        # Get settings
        settings = {}
        if 'settings' in request.form:
            try:
                settings = json.loads(request.form['settings'])
                print(f"Settings: {settings}")
            except json.JSONDecodeError:
                settings = {
                    'pitchBendRange': 2,
                    'driftThreshold': 0.5,
                    'quantizationStep': 0.5
                }
                print("Using default settings")
        else:
            settings = {
                'pitchBendRange': 2,
                'driftThreshold': 0.5,
                'quantizationStep': 0.5
            }
            print("Using default settings")

        # Save uploaded file temporarily
        filename = secure_filename(audio_file.filename)
        temp_path = os.path.join(UPLOAD_FOLDER, filename)
        print(f"Saving file to: {temp_path}")
        audio_file.save(temp_path)

        try:
            print("Starting MIDI conversion...")
            # Convert audio to MIDI
            midi = convert_audio_to_midi(temp_path, settings)
            
            print("MIDI conversion completed successfully")
            
            # Save MIDI to temporary file
            midi_path = temp_path + '_converted.mid'
            print(f"Saving MIDI to: {midi_path}")
            midi.write(midi_path)
            
            # Read MIDI file and convert to base64
            with open(midi_path, 'rb') as f:
                midi_data = f.read()
            
            print(f"MIDI file size: {len(midi_data)} bytes")
            
            # Prepare response data
            notes_data = []
            for note in midi.instruments[0].notes:
                notes_data.append({
                    'pitch': int(note.pitch),
                    'start': float(note.start),
                    'end': float(note.end),
                    'velocity': int(note.velocity)
                })
            
            pitch_bends_data = []
            for bend in midi.instruments[0].pitch_bends:
                pitch_bends_data.append({
                    'pitch': int(bend.pitch),
                    'time': float(bend.time)
                })
            
            print(f"Created {len(notes_data)} notes and {len(pitch_bends_data)} pitch bends")
            
            response_data = {
                'success': True,
                'notes': notes_data,
                'pitchBends': pitch_bends_data,
                'midiContent': base64.b64encode(midi_data).decode('utf-8'),
                'totalNotes': int(len(notes_data)),
                'totalPitchBends': int(len(pitch_bends_data)),
                'duration': float(midi.get_end_time())
            }
            
            # Clean up temporary files
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                if os.path.exists(midi_path):
                    os.remove(midi_path)
            except Exception as cleanup_error:
                print(f"Warning: Could not clean up temporary files: {cleanup_error}")
            
            print("=== Conversion completed successfully ===")
            return jsonify(response_data)
            
        except Exception as e:
            print(f"Error during conversion: {e}")
            import traceback
            traceback.print_exc()
            # Clean up on error
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                if 'midi_path' in locals() and os.path.exists(midi_path):
                    os.remove(midi_path)
            except Exception as cleanup_error:
                print(f"Warning: Could not clean up temporary files on error: {cleanup_error}")
            raise e
            
    except Exception as e:
        print(f"Error in convert_audio: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'Audio to MIDI converter is running'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000) 