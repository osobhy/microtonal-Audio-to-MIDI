import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { motion } from 'framer-motion';
import { Upload, FileAudio, X, CheckCircle } from 'lucide-react';

const AudioUploader = ({ onFilesUpload, audioFiles, onRemoveFile }) => {
  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0) {
      onFilesUpload([...audioFiles, ...acceptedFiles]);
    }
  }, [onFilesUpload, audioFiles]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'audio/*': ['.wav', '.mp3', '.flac', '.aiff', '.m4a']
    },
    multiple: true
  });

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-100 flex items-center gap-2">
        <FileAudio className="w-5 h-5" />
        Upload Audio Files
      </h3>

      {audioFiles.length === 0 ? (
        <motion.div
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          {...getRootProps()}
            className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200 ${
            isDragActive
              ? 'border-indigo-500 bg-dark-700'
              : 'border-dark-600 hover:border-indigo-400 hover:bg-dark-700'
          }`}
        >
          <input {...getInputProps()} />
          <motion.div
            animate={isDragActive ? { scale: 1.1 } : { scale: 1 }}
            className="flex flex-col items-center gap-4"
          >
            <div className={`p-4 rounded-full ${
              isDragActive ? 'bg-dark-600' : 'bg-dark-700'
            }`}>
              <Upload className={`w-8 h-8 ${
                isDragActive ? 'text-indigo-400' : 'text-gray-400'
              }`} />
            </div>
            <div>
              <p className="text-lg font-medium text-gray-200 mb-2">
                {isDragActive ? 'Drop your audio files here' : 'Drag & drop your audio files'}
              </p>
              <p className="text-sm text-gray-400">
                or click to browse files
              </p>
              <p className="text-xs text-gray-400 mt-2">
                Supports: WAV, MP3, FLAC, AIFF, M4A
              </p>
            </div>
          </motion.div>
        </motion.div>
      ) : (
        <div className="space-y-2">
          {audioFiles.map((file, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-dark-700 border border-dark-600 rounded-xl p-4 flex items-center justify-between"
            >
              <div className="flex items-center gap-3">
                <div className="p-2 bg-dark-600 rounded-full">
                  <CheckCircle className="w-5 h-5 text-indigo-400" />
                </div>
                <div>
                  <p className="font-medium text-gray-100">{file.name}</p>
                  <p className="text-sm text-gray-400">
                    {formatFileSize(file.size)}
                  </p>
                </div>
              </div>
              <button
                onClick={() => onRemoveFile(idx)}
                className="p-2 text-gray-400 hover:text-red-400 hover:bg-red-900/30 rounded-full transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AudioUploader;