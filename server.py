from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import base64
from werkzeug.utils import secure_filename
from script import convert_audio_file
import threading
import uuid
import time

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": os.environ.get("CORS_ORIGIN", "*").split(",")}})

# Simple in-memory job store: {job_id: {status:'pending'|'running'|'done'|'error', result:..., error:...}}
jobs = {}

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'flac', 'aiff', 'm4a'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _process_job(job_id, temp_path, filename, settings):
    try:
        jobs[job_id]['status'] = 'running'
        midi_path = temp_path + '_converted.mid'
        # Run conversion (this is CPU-heavy)
        midi = convert_audio_file(temp_path, midi_path)

        # Read MIDI file
        with open(midi_path, 'rb') as f:
            midi_data = f.read()

        # Prepare notes/pitch bends
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
            pitch_bends_data.append({'pitch': int(bend.pitch), 'time': float(bend.time)})

        response_data = {
            'success': True,
            'notes': notes_data,
            'pitchBends': pitch_bends_data,
            'midiContent': base64.b64encode(midi_data).decode('utf-8'),
            'totalNotes': int(len(notes_data)),
            'totalPitchBends': int(len(pitch_bends_data)),
            'duration': float(midi.get_end_time())
        }

        jobs[job_id]['status'] = 'done'
        jobs[job_id]['result'] = response_data

    except Exception as e:
        jobs[job_id]['status'] = 'error'
        jobs[job_id]['error'] = str(e)
        import traceback
        traceback.print_exc()
    finally:
        # cleanup temp files
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            if 'midi_path' in locals() and os.path.exists(midi_path):
                os.remove(midi_path)
        except Exception as cleanup_error:
            print(f"Warning: Could not clean up temporary files: {cleanup_error}")


def convert_audio_to_midi(audio_path, settings):
    """Legacy wrapper kept for sync usage. Not used by threaded endpoint."""
    midi_path = audio_path + '_converted.mid'
    midi = convert_audio_file(audio_path, midi_path)
    return midi, midi_path


@app.route('/api/convert', methods=['POST'])
def convert_audio():
    try:
        print("=== Starting conversion (received request) ===")

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
                settings = {}
                print("Using default settings")

        # Save uploaded file temporarily
        filename = secure_filename(audio_file.filename)
        temp_path = os.path.join(UPLOAD_FOLDER, filename)
        print(f"Saving file to: {temp_path}")
        audio_file.save(temp_path)

        # Create job and start background thread
        job_id = str(uuid.uuid4())
        jobs[job_id] = {'status': 'pending', 'result': None}
        thread = threading.Thread(target=_process_job, args=(job_id, temp_path, filename, settings))
        thread.daemon = True
        thread.start()

        # Return job id immediately
        return jsonify({'jobId': job_id, 'status': 'pending'}), 202

    except Exception as e:
        print(f"Error in convert_audio: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/status/<job_id>', methods=['GET'])
def job_status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    if job['status'] == 'done':
        return jsonify({'status': 'done', 'result': job['result']})
    if job['status'] == 'error':
        return jsonify({'status': 'error', 'error': job.get('error')}), 500
    return jsonify({'status': job['status']}), 200


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'Audio to MIDI converter is running'})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(debug=True, host='0.0.0.0', port=port)