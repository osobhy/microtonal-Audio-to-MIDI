# Audio to MIDI Converter

A beautiful and modern React web application for converting audio files to MIDI with real-time piano roll visualization.

## Features

- 🎵 **Drag & Drop Audio Upload** - Support for WAV, MP3, FLAC, AIFF, M4A
- 🎹 **Interactive Piano Roll** - Visualize MIDI notes with zoom and scroll
- 🎚️ **Advanced Settings** - Customize pitch bend range, drift threshold, and quantization
- 🔊 **Audio Preview** - Play uploaded audio with waveform visualization
- 📊 **Real-time Conversion** - Watch the conversion progress
- 💾 **MIDI Download** - Download converted MIDI files
- 🎨 **Modern UI** - Beautiful, responsive design with animations

## Screenshots

The application features a modern, gradient-based design with:
- Left panel: File upload, settings, and conversion controls
- Right panel: Audio player and piano roll visualization
- Real-time progress tracking and error handling

## Installation

### Prerequisites

- Node.js (v16 or higher)
- Python (v3.8 or higher)
- pip (Python package manager)

### Frontend Setup

1. Install Node.js dependencies:
```bash
npm install
```

2. Start the React development server:
```bash
npm start
```

The frontend will be available at `http://localhost:3000`

### Backend Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Start the Flask backend server:
```bash
python server.py
```

The backend API will be available at `http://localhost:5000`

## Usage

1. **Upload Audio**: Drag and drop an audio file or click to browse
2. **Adjust Settings** (optional): Click "Advanced" to customize conversion parameters
3. **Convert**: Click "Convert to MIDI" to start the conversion process
4. **Visualize**: Watch the piano roll visualization update in real-time
5. **Download**: Click "Download MIDI" to save the converted file

## Settings Explained

### Pitch Bend Range
- Controls the range of pitch bend messages
- Must match your synthesizer's pitch bend range
- Range: 1-12 semitones

### Drift Threshold
- Determines when to split into new notes
- Higher values = fewer note splits
- Range: 0.1-2.0

### Quantization Step
- Quantizes pitch to specific intervals
- 0.5 = half semitone (quarter tones)
- 1.0 = full semitone
- Range: 0.1-1.0

## Presets

- **Default**: Balanced settings for most audio
- **Precise**: Higher precision, fewer note splits
- **Microtonal**: Optimized for microtonal music

## API Endpoints

- `POST /api/convert` - Convert audio to MIDI
- `GET /api/health` - Health check

## Technical Details

### Frontend Technologies
- React 18
- Tailwind CSS
- Framer Motion (animations)
- React Dropzone (file upload)
- Canvas API (piano roll visualization)

### Backend Technologies
- Flask (Python web framework)
- Librosa (audio processing)
- Pretty MIDI (MIDI file handling)
- NumPy (numerical computations)

### Audio Processing Pipeline
1. Load audio file with Librosa
2. Extract fundamental frequency (F0) using pYIN algorithm
3. Quantize pitches based on settings
4. Detect note boundaries using drift threshold
5. Generate MIDI notes and pitch bend messages
6. Export as MIDI file

## Development

### Project Structure
```
├── public/                 # Static files
├── src/
│   ├── components/         # React components
│   │   ├── AudioUploader.js
│   │   ├── PianoRoll.js
│   │   ├── AudioPlayer.js
│   │   └── SettingsPanel.js
│   ├── App.js             # Main application
│   ├── index.js           # React entry point
│   └── index.css          # Global styles
├── server.py              # Flask backend
├── script.py              # Original Python script
├── requirements.txt       # Python dependencies
└── package.json           # Node.js dependencies
```

### Running in Development Mode

1. Start the backend:
```bash
python server.py
```

2. In a new terminal, start the frontend:
```bash
npm start
```

3. Open `http://localhost:3000` in your browser

## Troubleshooting

### Common Issues

1. **Audio file not supported**
   - Ensure file is WAV, MP3, FLAC, AIFF, or M4A
   - Check file is not corrupted

2. **Conversion fails**
   - Check Python dependencies are installed
   - Ensure backend server is running
   - Check console for error messages

3. **Piano roll not displaying**
   - Ensure MIDI conversion completed successfully
   - Check browser console for errors

### Performance Tips

- Use shorter audio files for faster conversion
- Lower drift threshold for more precise results
- Higher quantization step for simpler output

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Acknowledgments

- Librosa for audio processing capabilities
- Pretty MIDI for MIDI file handling
- React and Tailwind CSS communities
- Framer Motion for smooth animations 