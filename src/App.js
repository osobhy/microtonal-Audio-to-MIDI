import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Music, 
  Download, 
  Settings,
  AlertCircle,
  Loader
} from 'lucide-react';
import AudioUploader from './components/AudioUploader';
import PianoRoll from './components/PianoRoll';
import SettingsPanel from './components/SettingsPanel';
import './App.css';

function App() {
  const [audioFiles, setAudioFiles] = useState([]);
  const [midiData, setMidiData] = useState([]);
  const [isConverting, setIsConverting] = useState(false);
  const [, setConversionProgress] = useState(0);
  const [error, setError] = useState(null);
  const [showSettings, setShowSettings] = useState(false);
  const [settings, setSettings] = useState({
    pitchBendRange: 2,
    driftThreshold: 0.5,
    quantizationStep: 0.5
  });

  const handleFilesUpload = (files) => {
    setAudioFiles(files);
    setMidiData([]);
    setError(null);
  };

  const handleRemoveFile = (index) => {
    setAudioFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleConvert = async () => {
    if (audioFiles.length === 0) return;

    setIsConverting(true);
    setConversionProgress(0);
    setError(null);

    try {
      const results = [];
      for (let i = 0; i < audioFiles.length; i++) {
        const file = audioFiles[i];
        const formData = new FormData();
        formData.append('audio', file);
        formData.append('settings', JSON.stringify(settings));

        const response = await fetch('/api/convert', {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          throw new Error('Conversion failed');
        }

        const result = await response.json();
        results.push({ file, data: result });
        setConversionProgress(Math.round(((i + 1) / audioFiles.length) * 100));
      }
      setMidiData(results);
      setIsConverting(false);
      setConversionProgress(0);

    } catch (err) {
      setError(err.message);
      setIsConverting(false);
      setConversionProgress(0);
    }
  };

  const handleDownload = (index) => {
    const item = midiData[index];
    if (!item) return;

    const { file, data } = item;
    const binaryString = atob(data.midiContent);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }

    const blob = new Blob([bytes], { type: 'audio/midi' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${file.name.replace(/\.[^/.]+$/, '')}_converted.mid`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-dark-900 relative overflow-hidden">
        {/* Subtle accent glow/vignette */}
      <div className="pointer-events-none fixed inset-0 z-0" style={{background: 'radial-gradient(ellipse at 70% 10%, #6366F122 0%, #000 80%)'}} />
      <div className="container mx-auto px-4 py-8 relative z-10">
        {/* Header */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
            <h1 className="text-6xl font-extrabold bg-gradient-to-r from-white via-indigo-200 to-indigo-400 bg-clip-text text-transparent mb-4 tracking-widest" style={{ fontFamily: 'Space Grotesk, sans-serif', letterSpacing: '0.08em' }}>
              Microtonal Audio to MIDI Converter
            </h1>
            <p className="text-xl text-gray-200 max-w-2xl mx-auto">
              A first-of-its-kind tool to convert Microtonal Audio to MIDI. Enjoy :)
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
                onFilesUpload={handleFilesUpload}
                audioFiles={audioFiles}
                onRemoveFile={handleRemoveFile}
              />
            </div>

            {/* Settings Panel */}
            <div className="bg-dark-800 rounded-2xl shadow-xl p-6 border border-dark-700/60">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                  <Settings className="w-5 h-5 text-indigo-400" />
                  Conversion Settings
                </h3>
                <button
                  onClick={() => setShowSettings(!showSettings)}
                  className="text-indigo-300 hover:text-indigo-200 text-sm font-medium"
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
              disabled={audioFiles.length === 0 || isConverting}
                className={`w-full py-4 px-6 rounded-xl font-semibold text-lg transition-all duration-200 flex items-center justify-center gap-3 ${
                audioFiles.length === 0 || isConverting
                  ? 'bg-dark-700 text-gray-500 cursor-not-allowed'
                  : 'bg-gradient-to-r from-indigo-500 via-purple-500 to-indigo-400 text-white hover:from-indigo-600 hover:to-purple-500 shadow-lg hover:shadow-xl'
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
            {midiData.length > 0 && midiData.map((item, idx) => (
              <motion.button
                key={idx}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => handleDownload(idx)}
                className="w-full py-3 px-6 rounded-xl font-semibold text-lg bg-gradient-to-r from-indigo-400 via-purple-500 to-indigo-700 text-white hover:from-indigo-500 hover:to-indigo-800 shadow-lg hover:shadow-xl flex items-center justify-center gap-2 mt-2"
              >
                <Download className="w-5 h-5" />
                {`Download ${item.file.name.replace(/\.[^/.]+$/, '')}.mid`}
              </motion.button>
            ))}
          </motion.div>

          {/* Right Panel - Piano Roll */}
          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="bg-dark-800 rounded-2xl shadow-xl p-6 border border-dark-700/60"
          >
            <PianoRoll midiData={midiData[0]?.data} isConverting={isConverting} />
          </motion.div>
        </div>
      </div>
    </div>
  );
}

export default App; 