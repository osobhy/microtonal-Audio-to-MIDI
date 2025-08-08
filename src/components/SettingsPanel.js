import React from 'react';
import { motion } from 'framer-motion';
import { Sliders } from 'lucide-react';

const SettingsPanel = ({ settings, onSettingsChange }) => {
  const handleSettingChange = (key, value) => {
    onSettingsChange({
      ...settings,
      [key]: value
    });
  };

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: 'auto' }}
      exit={{ opacity: 0, height: 0 }}
      className="space-y-4 pt-4 border-t border-gray-200"
    >
      <div className="flex items-center gap-2 mb-4">
        <Sliders className="w-4 h-4 text-gray-600" />
        <span className="text-sm font-medium text-gray-700">Advanced Settings</span>
      </div>

      {/* Pitch Bend Range */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <label className="text-sm font-medium text-gray-700">
            Pitch Bend Range
          </label>
          <span className="text-sm text-gray-500">
            {settings.pitchBendRange} semitones
          </span>
        </div>
        <input
          type="range"
          min="1"
          max="12"
          step="0.5"
          value={settings.pitchBendRange}
          onChange={(e) => handleSettingChange('pitchBendRange', parseFloat(e.target.value))}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
        />
        <p className="text-xs text-gray-500">
          Controls the range of pitch bend messages (must match your synth)
        </p>
      </div>

      {/* Drift Threshold */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <label className="text-sm font-medium text-gray-700">
            Drift Threshold
          </label>
          <span className="text-sm text-gray-500">
            {settings.driftThreshold}
          </span>
        </div>
        <input
          type="range"
          min="0.1"
          max="2.0"
          step="0.1"
          value={settings.driftThreshold}
          onChange={(e) => handleSettingChange('driftThreshold', parseFloat(e.target.value))}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
        />
        <p className="text-xs text-gray-500">
          When to split into new notes (higher = fewer note splits)
        </p>
      </div>

      {/* Quantization Step */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <label className="text-sm font-medium text-gray-700">
            Quantization Step
          </label>
          <span className="text-sm text-gray-500">
            {settings.quantizationStep}
          </span>
        </div>
        <input
          type="range"
          min="0.1"
          max="1.0"
          step="0.1"
          value={settings.quantizationStep}
          onChange={(e) => handleSettingChange('quantizationStep', parseFloat(e.target.value))}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
        />
        <p className="text-xs text-gray-500">
          Quantize to quarter tones (0.5 = half semitone, 1.0 = full semitone)
        </p>
      </div>

      {/* Preset Buttons */}
      <div className="pt-2">
        <p className="text-xs font-medium text-gray-700 mb-2">Quick Presets:</p>
        <div className="flex gap-2">
          <button
            onClick={() => onSettingsChange({
              pitchBendRange: 2,
              driftThreshold: 0.5,
              quantizationStep: 0.5
            })}
            className="px-3 py-1 text-xs bg-blue-100 hover:bg-blue-200 text-blue-700 rounded-md transition-colors"
          >
            Default
          </button>
          <button
            onClick={() => onSettingsChange({
              pitchBendRange: 1,
              driftThreshold: 0.3,
              quantizationStep: 1.0
            })}
            className="px-3 py-1 text-xs bg-green-100 hover:bg-green-200 text-green-700 rounded-md transition-colors"
          >
            Precise
          </button>
          <button
            onClick={() => onSettingsChange({
              pitchBendRange: 4,
              driftThreshold: 1.0,
              quantizationStep: 0.25
            })}
            className="px-3 py-1 text-xs bg-purple-100 hover:bg-purple-200 text-purple-700 rounded-md transition-colors"
          >
            Microtonal
          </button>
        </div>
      </div>
    </motion.div>
  );
};

export default SettingsPanel; 