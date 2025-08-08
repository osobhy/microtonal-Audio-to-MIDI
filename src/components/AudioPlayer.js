import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Play, Pause, Volume2, VolumeX } from 'lucide-react';

const AudioPlayer = ({ audioFile }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const [waveform, setWaveform] = useState([]);
  
  const audioRef = useRef(null);
  const canvasRef = useRef(null);

  useEffect(() => {
    if (!audioFile) return;

    const audio = new Audio(URL.createObjectURL(audioFile));
    audioRef.current = audio;

    audio.addEventListener('loadedmetadata', () => {
      setDuration(audio.duration);
    });

    audio.addEventListener('timeupdate', () => {
      setCurrentTime(audio.currentTime);
    });

    audio.addEventListener('ended', () => {
      setIsPlaying(false);
      setCurrentTime(0);
    });

    // Generate waveform data
    generateWaveform(audioFile);

    return () => {
      audio.pause();
      audio.src = '';
    };
  }, [audioFile]);

  const generateWaveform = async (file) => {
    try {
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const arrayBuffer = await file.arrayBuffer();
      const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
      
      const channelData = audioBuffer.getChannelData(0);
      const samples = 100; // Number of waveform bars
      const blockSize = Math.floor(channelData.length / samples);
      const waveformData = [];

      for (let i = 0; i < samples; i++) {
        const start = blockSize * i;
        let sum = 0;
        for (let j = 0; j < blockSize; j++) {
          sum += Math.abs(channelData[start + j]);
        }
        waveformData.push(sum / blockSize);
      }

      setWaveform(waveformData);
    } catch (error) {
      console.error('Error generating waveform:', error);
    }
  };

  const togglePlay = () => {
    if (!audioRef.current) return;

    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
    setIsPlaying(!isPlaying);
  };

  const handleSeek = (e) => {
    if (!audioRef.current) return;
    
    const rect = e.currentTarget.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const percentage = clickX / rect.width;
    const newTime = percentage * duration;
    
    audioRef.current.currentTime = newTime;
    setCurrentTime(newTime);
  };

  const handleVolumeChange = (e) => {
    const newVolume = parseFloat(e.target.value);
    setVolume(newVolume);
    if (audioRef.current) {
      audioRef.current.volume = newVolume;
    }
  };

  const toggleMute = () => {
    if (!audioRef.current) return;
    
    if (isMuted) {
      audioRef.current.volume = volume;
      setIsMuted(false);
    } else {
      audioRef.current.volume = 0;
      setIsMuted(true);
    }
  };

  const formatTime = (time) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  const maxWaveformHeight = 60;

  return (
    <div className="space-y-4">
      {/* Waveform Visualization */}
      <div className="relative">
        <div
          className="h-16 bg-dark-700 rounded-lg cursor-pointer relative overflow-hidden"
          onClick={handleSeek}
        >
          {waveform.length > 0 ? (
            <div className="flex items-end justify-between h-full px-2 py-2">
              {waveform.map((amplitude, index) => {
                const height = (amplitude / Math.max(...waveform)) * maxWaveformHeight;
                const isActive = (index / waveform.length) * duration <= currentTime;
                
                return (
                  <motion.div
                    key={index}
                    className={`waveform flex-1 mx-px rounded-sm transition-all duration-200 ${
                      isActive ? 'opacity-100' : 'opacity-40'
                    }`}
                    style={{ height: `${Math.max(2, height)}px` }}
                    initial={{ height: 0 }}
                    animate={{ height: `${Math.max(2, height)}px` }}
                    transition={{ duration: 0.3, delay: index * 0.001 }}
                  />
                );
              })}
            </div>
          ) : (
            <div className="flex items-center justify-center h-full">
              <div className="w-8 h-8 border-2 border-dark-600 border-t-transparent rounded-full animate-spin"></div>
            </div>
          )}
          
          {/* Progress overlay */}
          <div 
            className="absolute top-0 left-0 h-full bg-blue-500 bg-opacity-20 pointer-events-none"
            style={{ width: `${(currentTime / duration) * 100}%` }}
          />
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-4">
        {/* Play/Pause Button */}
        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={togglePlay}
          className="w-12 h-12 bg-blue-600 hover:bg-blue-700 text-white rounded-full flex items-center justify-center transition-colors"
        >
          {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5 ml-1" />}
        </motion.button>

        {/* Time Display */}
        <div className="flex-1 text-center">
          <div className="text-sm font-mono text-gray-300">
            {formatTime(currentTime)} / {formatTime(duration)}
          </div>
        </div>

        {/* Volume Control */}
        <div className="flex items-center gap-2">
          <button
            onClick={toggleMute}
            className="p-2 text-gray-300 hover:text-white transition-colors"
          >
            {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
          </button>
          <input
            type="range"
            min="0"
            max="1"
            step="0.01"
            value={isMuted ? 0 : volume}
            onChange={handleVolumeChange}
            className="w-20 h-2 bg-dark-600 rounded-lg appearance-none cursor-pointer slider"
          />
        </div>
      </div>

      {/* File Info */}
      <div className="text-xs text-gray-400">
        <p>Duration: {formatTime(duration)} • Format: {audioFile?.type || 'Unknown'}</p>
      </div>
    </div>
  );
};

export default AudioPlayer; 