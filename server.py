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
import subprocess
import sys
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": os.environ.get("CORS_ORIGIN", "*").split(",")}})

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'flac', 'aiff', 'm4a'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_audio_to_midi(audio_path, settings):
    """Run the external microtonal engine to convert audio to MIDI."""
    midi_path = audio_path + '_converted.mid'
    script_path = os.path.join(os.path.dirname(__file__), 'script.py')
    cmd = [sys.executable, script_path, audio_path, midi_path]
    subprocess.run(cmd, check=True)
    midi = pretty_midi.PrettyMIDI(midi_path)
    return midi, midi_path

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
            # Convert audio to MIDI using external script
            midi, midi_path = convert_audio_to_midi(temp_path, settings)

            print("MIDI conversion completed successfully")
            
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
    app.run(debug=True, host='0.0.0.0', port=port) 