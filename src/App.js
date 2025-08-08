import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Music, 
  Download, 
  Volume2, 
  Settings,
  FileText,
  AlertCircle,
  Loader
} from 'lucide-react';
import AudioUploader from './components/AudioUploader';
import PianoRoll from './components/PianoRoll';
import AudioPlayer from './components/AudioPlayer';
import SettingsPanel from './components/SettingsPanel';
import './App.css';

function App() {
  const [audioFile, setAudioFile] = useState(null);
  const [midiData, setMidiData] = useState(null);
  const [isConverting, setIsConverting] = useState(false);
  const [conversionProgress, setConversionProgress] = useState(0);
  const [error, setError] = useState(null);
  const [showSettings, setShowSettings] = useState(false);
  const [settings, setSettings] = useState({
    pitchBendRange: 2,
    driftThreshold: 0.5,
    quantizationStep: 0.5
  });

  const handleFileUpload = (file) => {
    setAudioFile(file);
    setMidiData(null);
    setError(null);
  };

  const handleConvert = async () => {
    if (!audioFile) return;

    setIsConverting(true);
    setConversionProgress(0);
    setError(null);

    const formData = new FormData();
    formData.append('audio', audioFile);
    formData.append('settings', JSON.stringify(settings));

    try {
      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setConversionProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 500);

      const response = await fetch('/api/convert', {
        method: 'POST',
        body: formData,
      });

      clearInterval(progressInterval);

      if (!response.ok) {
        throw new Error('Conversion failed');
      }

      const result = await response.json();
      setMidiData(result);
      setConversionProgress(100);
      
      setTimeout(() => {
        setIsConverting(false);
        setConversionProgress(0);
      }, 1000);

    } catch (err) {
      setError(err.message);
      setIsConverting(false);
      setConversionProgress(0);
    }
  };

  const handleDownload = () => {
    if (!midiData) return;
    
    // Decode base64 MIDI content
    const binaryString = atob(midiData.midiContent);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    
    const blob = new Blob([bytes], { type: 'audio/midi' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${audioFile.name.replace(/\.[^/.]+$/, '')}_converted.mid`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-dark-900 relative overflow-hidden">
      {/* Subtle green glow/vignette */}
      <div className="pointer-events-none fixed inset-0 z-0" style={{background: 'radial-gradient(ellipse at 70% 10%, #10b98122 0%, #000 80%)'}} />
      <div className="container mx-auto px-4 py-8 relative z-10">
        {/* Header */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <h1 className="text-6xl font-extrabold bg-gradient-to-r from-white via-emerald-200 to-emerald-400 bg-clip-text text-transparent mb-4 tracking-widest" style={{ fontFamily: 'Space Grotesk, sans-serif', letterSpacing: '0.08em' }}>
            Audio to MIDI Converter
          </h1>
          <p className="text-xl text-gray-200 max-w-2xl mx-auto">
            Transform your audio files into MIDI with beautiful piano roll visualization
          </p>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 max-w-7xl mx-auto">
          {/* Left Panel - Upload and Controls */}
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="space-y-6"
          >
            {/* Upload Section */}
            <div className="bg-dark-800 rounded-2xl shadow-xl p-6 border border-dark-700/60">
              <AudioUploader 
                onFileUpload={handleFileUpload}
                audioFile={audioFile}
              />
            </div>

            {/* Settings Panel */}
            <div className="bg-dark-800 rounded-2xl shadow-xl p-6 border border-dark-700/60">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                  <Settings className="w-5 h-5 text-emerald-400" />
                  Conversion Settings
                </h3>
                <button
                  onClick={() => setShowSettings(!showSettings)}
                  className="text-emerald-300 hover:text-emerald-200 text-sm font-medium"
                >
                  {showSettings ? 'Hide' : 'Advanced'}
                </button>
              </div>
              <AnimatePresence>
                {showSettings && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="overflow-hidden"
                  >
                    <SettingsPanel 
                      settings={settings}
                      onSettingsChange={setSettings}
                    />
                  </motion.div>
                )}
              </AnimatePresence>
              <div className="mt-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-300">Pitch Bend Range:</span>
                  <span className="text-sm font-medium text-white">{settings.pitchBendRange} semitones</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-300">Drift Threshold:</span>
                  <span className="text-sm font-medium text-white">{settings.driftThreshold}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-300">Quantization Step:</span>
                  <span className="text-sm font-medium text-white">{settings.quantizationStep}</span>
                </div>
              </div>
            </div>

            {/* Convert Button */}
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleConvert}
              disabled={!audioFile || isConverting}
              className={`w-full py-4 px-6 rounded-xl font-semibold text-lg transition-all duration-200 flex items-center justify-center gap-3 ${
                !audioFile || isConverting
                  ? 'bg-dark-700 text-gray-500 cursor-not-allowed'
                  : 'bg-gradient-to-r from-emerald-500 via-emerald-400 to-emerald-300 text-dark-900 hover:from-emerald-600 hover:to-emerald-400 shadow-lg hover:shadow-xl'
              }`}
            >
              {isConverting ? (
                <>
                  <Loader className="animate-spin w-6 h-6 mr-2" />
                  Converting...
                </>
              ) : (
                <>
                  <Music className="w-6 h-6" />
                  Convert Audio
                </>
              )}
            </motion.button>
            {error && (
              <div className="bg-red-100 text-red-700 rounded-lg p-3 flex items-center gap-2 mt-2">
                <AlertCircle className="w-5 h-5" />
                <span>{error}</span>
              </div>
            )}
            {midiData && (
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleDownload}
                className="w-full py-3 px-6 rounded-xl font-semibold text-lg bg-gradient-to-r from-emerald-400 via-emerald-500 to-emerald-700 text-dark-900 hover:from-emerald-500 hover:to-emerald-800 shadow-lg hover:shadow-xl flex items-center justify-center gap-2 mt-2"
              >
                <Download className="w-5 h-5" />
                Download MIDI
              </motion.button>
            )}
          </motion.div>

          {/* Right Panel - Piano Roll */}
          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-dark-800 rounded-2xl shadow-xl p-6 border border-dark-700/60"
          >
            <PianoRoll midiData={midiData} isConverting={isConverting} />
          </motion.div>
        </div>
      </div>
    </div>
  );
}

export default App; 