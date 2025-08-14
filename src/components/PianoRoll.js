import React, { useRef, useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Music, Play, Pause, Volume2 } from 'lucide-react';

const PianoRoll = ({ midiData, isConverting }) => {
  const canvasRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  const [zoom, setZoom] = useState(2.5); // Start more zoomed in
  const [scrollX, setScrollX] = useState(0);
  
  // MIDI playback state
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [volume, setVolume] = useState(0.7);
  const audioContextRef = useRef(null);
  const playbackStartTimeRef = useRef(0);
  const animationFrameRef = useRef(null);

  // Piano key names - reduced range for less cramped view
  const noteNames = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
  const octaves = [6, 5, 4, 3]; // Reduced octave range
  const pianoKeys = [];
  
  octaves.forEach(octave => {
    noteNames.forEach(note => {
      pianoKeys.push(`${note}${octave}`);
    });
  });

  useEffect(() => {
    const updateDimensions = () => {
      if (canvasRef.current) {
        const rect = canvasRef.current.getBoundingClientRect();
        setDimensions({ width: rect.width, height: rect.height });
      }
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  useEffect(() => {
    if (!canvasRef.current || !midiData || !dimensions.width) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    // Set canvas size
    canvas.width = dimensions.width;
    canvas.height = dimensions.height;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw grid
    drawGrid(ctx, canvas.width, canvas.height);
    
    // Draw notes if available
    if (midiData.notes) {
      drawNotes(ctx, midiData.notes, canvas.width, canvas.height);
    }

  }, [midiData, dimensions, zoom, scrollX, isPlaying, currentTime]);

  // MIDI Synthesizer
  const createSynth = () => {
    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
    }
    return audioContextRef.current;
  };

  const playNote = (frequency, startTime, duration, velocity = 100) => {
    const audioContext = createSynth();
    const gainNode = audioContext.createGain();
    const oscillator = audioContext.createOscillator();
    
    // Connect nodes
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    // Set oscillator properties
    oscillator.frequency.setValueAtTime(frequency, audioContext.currentTime);
    oscillator.type = 'triangle'; // Warm, musical sound
    
    // Set envelope
    const velocityGain = (velocity / 127) * volume;
    gainNode.gain.setValueAtTime(0, audioContext.currentTime);
    gainNode.gain.linearRampToValueAtTime(velocityGain, audioContext.currentTime + 0.01);
    gainNode.gain.exponentialRampToValueAtTime(velocityGain * 0.3, audioContext.currentTime + duration);
    gainNode.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + duration + 0.1);
    
    // Start and stop
    oscillator.start(audioContext.currentTime + startTime);
    oscillator.stop(audioContext.currentTime + startTime + duration + 0.1);
  };

  const midiNoteToFrequency = (note) => {
    return 440 * Math.pow(2, (note - 69) / 12);
  };

  const startPlayback = () => {
    if (!midiData || !midiData.notes) return;
    
    setIsPlaying(true);
    setCurrentTime(0);
    const audioContext = createSynth();
    playbackStartTimeRef.current = audioContext.currentTime;
    
    // Schedule all notes
    midiData.notes.forEach(note => {
      const frequency = midiNoteToFrequency(note.pitch);
      const duration = note.end - note.start;
      playNote(frequency, note.start, duration, note.velocity);
    });
    
    // Update playback position
    const updatePlayback = () => {
      if (!isPlaying) return;
      
      const elapsed = audioContext.currentTime - playbackStartTimeRef.current;
      setCurrentTime(elapsed);
      
      if (elapsed < midiData.duration) {
        animationFrameRef.current = requestAnimationFrame(updatePlayback);
      } else {
        setIsPlaying(false);
        setCurrentTime(0);
      }
    };
    
    updatePlayback();
  };

  const stopPlayback = () => {
    setIsPlaying(false);
    setCurrentTime(0);
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, []);

  const drawGrid = (ctx, width, height) => {
    const gridSize = 30 * zoom; // Larger grid spacing
    const keyHeight = height / pianoKeys.length;

    // Draw horizontal lines (piano keys) - more subtle
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
    ctx.lineWidth = 0.5;
    
    for (let i = 0; i <= pianoKeys.length; i++) {
      const y = i * keyHeight;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }

    // Draw vertical lines (time grid) - more subtle
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
    for (let x = 0; x <= width; x += gridSize) {
      ctx.beginPath();
      ctx.moveTo(x - scrollX, 0);
      ctx.lineTo(x - scrollX, height);
      ctx.stroke();
    }

    // Removed note labels for cleaner look
  };

  const drawNotes = (ctx, notes, width, height) => {
    const keyHeight = height / pianoKeys.length;
    const timeScale = 150 * zoom; // Increased time scale for better visibility

    notes.forEach(note => {
      const noteIndex = note.pitch - 21; // MIDI note 21 is A0
      if (noteIndex >= 0 && noteIndex < pianoKeys.length) {
        const y = noteIndex * keyHeight;
        const x = note.start * timeScale - scrollX;
        const noteWidth = (note.end - note.start) * timeScale;
        const noteHeight = keyHeight * 0.9; // Slightly larger notes

        // Check if note is currently playing
        const isCurrentlyPlaying = isPlaying && 
          currentTime >= note.start && 
          currentTime <= note.end;

        // Draw note rectangle with better colors
        const gradient = ctx.createLinearGradient(x, y, x + noteWidth, y);
        if (isCurrentlyPlaying) {
          // Highlight currently playing notes
          gradient.addColorStop(0, '#fbbf24'); // Yellow
          gradient.addColorStop(0.5, '#f59e0b'); // Orange
          gradient.addColorStop(1, '#d97706'); // Dark orange
        } else {
            gradient.addColorStop(0, '#6366F1'); // Indigo
            gradient.addColorStop(0.5, '#8b5cf6'); // Purple
            gradient.addColorStop(1, '#a855f7'); // Lighter purple
        }
        
        ctx.fillStyle = gradient;
        ctx.fillRect(x, y + keyHeight * 0.05, noteWidth, noteHeight);
        
        // Draw note border with glow effect
        ctx.strokeStyle = isCurrentlyPlaying ? 'rgba(255, 255, 255, 0.8)' : 'rgba(255, 255, 255, 0.4)';
        ctx.lineWidth = isCurrentlyPlaying ? 2 : 1.5;
        ctx.strokeRect(x, y + keyHeight * 0.05, noteWidth, noteHeight);
      }
    });
  };

  const formatTime = (time) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const handleWheel = (e) => {
    e.preventDefault();
    if (e.ctrlKey || e.metaKey) {
      // Zoom
      const newZoom = Math.max(1, Math.min(5, zoom - e.deltaY * 0.001));
      setZoom(newZoom);
    } else {
      // Scroll horizontally
      setScrollX(prev => Math.max(0, prev - e.deltaX));
    }
  };

  const resetView = () => {
    setZoom(2.5); // Reset to default zoom
    setScrollX(0);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Music className="w-5 h-5 text-gray-300" />
          <span className="text-sm font-medium text-gray-300">Piano Roll</span>
        </div>
        <div className="flex items-center gap-2">
          {/* Playback Controls */}
          {midiData && midiData.notes && (
            <div className="flex items-center gap-2">
              <button
                onClick={isPlaying ? stopPlayback : startPlayback}
                  className="flex items-center gap-1 px-3 py-1 text-xs bg-indigo-500 hover:bg-indigo-600 text-white rounded-md transition-colors"
              >
                {isPlaying ? <Pause className="w-3 h-3" /> : <Play className="w-3 h-3" />}
                {isPlaying ? 'Stop' : 'Play'}
              </button>
              <div className="flex items-center gap-1">
                <Volume2 className="w-3 h-3 text-gray-400" />
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={volume}
                  onChange={(e) => setVolume(parseFloat(e.target.value))}
                  className="w-16 h-1 bg-dark-600 rounded-lg appearance-none cursor-pointer"
                />
              </div>
            </div>
          )}
          <button
            onClick={resetView}
            className="px-3 py-1 text-xs bg-dark-700 hover:bg-dark-600 text-gray-300 rounded-md transition-colors"
          >
            Reset View
          </button>
          <span className="text-xs text-gray-400">
            Zoom: {Math.round(zoom * 100)}%
          </span>
        </div>
      </div>

      <div className="relative">
        {!midiData && !isConverting && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="absolute inset-0 flex items-center justify-center bg-dark-800 rounded-lg border-2 border-dashed border-dark-600"
          >
            <div className="text-center">
              <Music className="w-12 h-12 text-gray-500 mx-auto mb-3" />
              <p className="text-gray-400 text-sm">
                Convert audio to see piano roll visualization
              </p>
            </div>
          </motion.div>
        )}

        {isConverting && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="absolute inset-0 flex items-center justify-center bg-dark-800 rounded-lg"
          >
            <div className="text-center">
                <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
              <p className="text-gray-400 text-sm">
                Converting audio...
              </p>
            </div>
          </motion.div>
        )}

        <div 
          className="piano-roll rounded-lg overflow-hidden custom-scrollbar"
          style={{ height: '500px' }} // Increased height for better visibility
        >
          <canvas
            ref={canvasRef}
            onWheel={handleWheel}
            className="piano-roll-grid w-full h-full cursor-grab active:cursor-grabbing"
            style={{ 
              background: '#1a1a1a',
              touchAction: 'none'
            }}
          />
        </div>

        {/* Playback Progress */}
        {midiData && midiData.notes && (
          <div className="mt-2 space-y-1">
            <div className="flex items-center justify-between text-xs text-gray-400">
              <span>{formatTime(currentTime)}</span>
              <span>{formatTime(midiData.duration)}</span>
            </div>
            <div className="w-full bg-dark-600 rounded-full h-1">
              <div
                  className="bg-indigo-500 h-1 rounded-full transition-all duration-100"
                style={{ width: `${(currentTime / midiData.duration) * 100}%` }}
              />
            </div>
          </div>
        )}

        <div className="mt-2 text-xs text-gray-400">
          <p>Scroll to navigate • Ctrl+Scroll to zoom • {midiData?.notes?.length || 0} notes</p>
        </div>
      </div>
    </div>
  );
};

export default PianoRoll; 