# Microtonal Audio to MIDI Converter

A first-of-its-kind, robust tool with easy-to-use React front-end to convert Microtonal Audio to MIDI. I made this tool to aid research I was conducting on training generative AI audio models for microtonal, maqam Oud music. It should be highly useful for researchers in similar fields, as many analytical algorithms — such as segmentation through LBDM from MATLAB’s MIDIToolbox or complexity analyses — operate on symbolic MIDI data. While results are not 100% perfect, they are extremely close to accurate and, in my experience, fully sufficient for downstream MIDI analysis workflows.

You can synthesize the resulting MIDI in any DAW that supports pitch bending. The tool processes the audio frame-by-frame, tracking pitch with high temporal resolution and quantizing it to the nearest quarter tone. If a new microtone is detected (say, a shift of roughly ±50 cents from the current note’s pitch), the current note is ended and a new note is started, preserving microtonal fidelity in the MIDI structure. Instead of representing all microtonal inflections as continuous bends, this creates distinct note events for quarter-tone changes while still encoding smaller pitch movements (like vibrato) as pitch bends within the same note. This should ensure that phrasing, ornamentation, expressive microtonal steps, etc are faithfully represented, making the MIDI suitable for both playback and symbolic analysis.


## (Current) Features
-  **Drag & Drop Audio Upload**
-  **Interactive Piano Roll**
-  **Advanced Settings** (pitch bend range, drift threshold, and quantization -- more to come.)
-  **Audio Preview** 
-  **Real-time Conversion**
-  **MIDI Download**

## Screenshots

## Installation
This is a Python script written in 3.9 (was not tested on earlier versions of python). It requires librosa, numpy, pretty_midi, and flask. For the front-end, you will need React/Node.js.

### Frontend Setup
- Install and run the front-end environment
- 
```bash
npm install
npm start
```

The backend API will be available by default at port 3000 (`http://localhost:3000`)

### Backend Setup

- Install Python dependencies
```bash
pip install -r requirements.txt
```

- Start the Flask backend server
```bash
python server.py
```

The backend API will be available by default at port 5000

## Usage

1. Drag and drop an audio file or click to browse
2. Click "Advanced" to customize conversion parameters as you wish (the default suffice for microtonal Arabic music, but I thought making the tool more modular would aid with other styles of music as well.)
3. Click "Convert to MIDI" to start the conversion process
4. Watch the piano roll visualization update in real-time
5. Click "Download MIDI" to save the converted file

## Settings Explained

### Pitch Bend Range
This controls the range of pitch bend message. Must match your synthesizer's pitch bend range if you're planinng to synthesize the midi into audio. Ranges 1-12 semitones

### Drift Threshold
Determines when to split into new notes. Higher values generally mean fewer note splits. Ranges 0.1-2.0

### Quantization Step
Quantizes pitch to specific intervals. 0.5 = half semitone (quarter tones), which is defult. Ranges 0.1-1.0

## API Endpoints

- `POST /api/convert` to convert audio to MIDI
- `GET /api/health` health check

### Audio Processing Pipeline
1. Load audio file with Librosa
2. Extract fundamental frequency (F0) using pYIN algorithm
3. Quantize pitches based on settings
4. Detect note boundaries using drift threshold
5. Generate MIDI notes and pitch bend messages
6. Export as MIDI file


## License

This project is open source and available under the MIT License.


