# Microtonal Audio to MIDI Converter
# **Try now! Netlify link: https://microtonal.netlify.app/**


A first-of-its-kind, robust tool with easy-to-use React front-end to convert Microtonal Audio to MIDI. I made this tool to aid research I was conducting on training generative AI audio models for microtonal, maqam Oud music. It should be highly useful for researchers in similar fields, as many analytical algorithms — such as segmentation through LBDM from MATLAB’s MIDIToolbox or complexity analyses — operate on symbolic MIDI data. While results are not 100% perfect, they are extremely close to accurate and, in my experience, fully sufficient for downstream MIDI analysis workflows.

You can synthesize the resulting MIDI in any DAW that supports pitch bending. The tool processes the audio frame-by-frame, tracking pitch with high temporal resolution and quantizing it to the nearest quarter tone. If a new microtone is detected (say, a shift of roughly ±50 cents from the current note’s pitch), the current note is ended and a new note is started, preserving microtonal fidelity in the MIDI structure. Instead of representing all microtonal inflections as continuous bends, this creates distinct note events for quarter-tone changes while still encoding smaller pitch movements (like vibrato) as pitch bends within the same note. This should ensure that phrasing, ornamentation, expressive microtonal steps, etc are faithfully represented, making the MIDI suitable for both playback and symbolic analysis.

## Screenshots
<img width="1067" height="623" alt="image" src="https://github.com/user-attachments/assets/86122d63-dbfb-4231-a421-83b87de1254a" />

## Installation
This is a Python script written in 3.9 (was not tested on earlier versions of python). It requires librosa, numpy, pretty_midi, and flask. For the front-end, you will need React/Node.js.

### Frontend Setup
- Install and run the front-end environment
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

## Use without React
To use without setting up a fancy front-end, simply call script.py with the input file and output file. First, clone the project, cd into the project directory, install the dependencies
```bash
pip install librosa numpy pretty_midi
```
Then call
```bash
python script.py 30.wav 30.mid
```
where 30.wav is an audio file in the samme directory. You are going to get an output of 30.mid in the same directory. 

## Settings

- Pitch bend range controls the range of pitch bend message. Must match your synthesizer's pitch bend range if you're planinng to synthesize the midi into audio. Ranges 1-12 semitones

- Drift threshold determines when to split into new notes. Higher values generally mean fewer note splits. Ranges 0.1-2.0

- Quantization step quantizes pitch to specific intervals. 0.5 = half semitone (quarter tones), which is defult. Ranges 0.1-1.0

## API Endpoints

- `POST /api/convert` to convert audio to MIDI
- `GET /api/health` health check


