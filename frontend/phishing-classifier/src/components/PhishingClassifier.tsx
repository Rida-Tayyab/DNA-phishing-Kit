import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, Shield, AlertCircle, Check, Target } from 'lucide-react';
import axios from 'axios';
import './PhishingClassifier.css';
import ThreatLandscapeMap from './ThreatLandscapeMap';

const API_BASE = process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000';

interface ClassificationResult {
  predicted_family: string;
  confidence: number;
  top_5_neighbours: [string, number][];
}

type UploadState = 'idle' | 'uploading' | 'success' | 'error';

const PhishingClassifier: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [uploadState, setUploadState] = useState<UploadState>('idle');
  const [result, setResult] = useState<ClassificationResult | null>(null);
  const [error, setError] = useState<string>('');
  const [dragActive, setDragActive] = useState(false);
  const [newKitCoordinates, setNewKitCoordinates] = useState<{ x: number; y: number } | null>(null);

  // Generate approximate coordinates for new kit based on classification
  const generateKitCoordinates = (result: ClassificationResult) => {
    // Simple approach: place new kit near the center of its predicted family cluster
    // In a real implementation, you'd use the same UMAP model to transform the new kit's features
    const familyOffsets: { [key: string]: { x: number; y: number } } = {
      'paypal': { x: 2.5, y: 1.2 },
      'chase': { x: -1.8, y: 2.1 },
      'microsoft': { x: 0.5, y: -2.3 },
      'apple': { x: -2.1, y: -0.8 },
      'amazon': { x: 1.9, y: 0.7 },
      'default': { x: 0, y: 0 }
    };
    
    const offset = familyOffsets[result.predicted_family] || familyOffsets.default;
    // Add some randomness to avoid exact overlap
    return {
      x: offset.x + (Math.random() - 0.5) * 0.5,
      y: offset.y + (Math.random() - 0.5) * 0.5
    };
  };

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    const files = e.dataTransfer.files;
    if (files && files[0]) {
      const droppedFile = files[0];
      if (droppedFile.name.endsWith('.zip')) {
        setFile(droppedFile);
        setError('');
      } else {
        setError('Please upload a ZIP file containing a phishing kit');
      }
    }
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      if (selectedFile.name.endsWith('.zip')) {
        setFile(selectedFile);
        setError('');
      } else {
        setError('Please upload a ZIP file containing a phishing kit');
      }
    }
  };

  const classifyKit = async () => {
    if (!file) return;

    setUploadState('uploading');
    setError('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post<ClassificationResult>(
        `${API_BASE}/classify`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      if (!response.data || !response.data.predicted_family) {
        throw new Error(`Unexpected response: ${JSON.stringify(response.data)}`);
      }

      setResult(response.data);
      setNewKitCoordinates(generateKitCoordinates(response.data));
      setUploadState('success');
    } catch (err: any) {
      console.error('Classification error:', err);
      setError(
        err.response?.data?.detail ||
        err.message ||
        'Failed to classify the phishing kit. Please try again.'
      );
      setUploadState('error');
    }
  };

  const reset = () => {
    setFile(null);
    setResult(null);
    setError('');
    setUploadState('idle');
    setNewKitCoordinates(null);
  };

  return (
    <div className="classifier-container">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="classifier-header"
      >
        <Shield className="header-icon" size={32} />
        <h1>Phishing Kit Classifier</h1>
        <p>Upload a phishing kit ZIP file for ML-powered analysis</p>
      </motion.div>

      <AnimatePresence mode="wait">
        {uploadState === 'idle' && (
          <motion.div
            key="upload"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="upload-section"
          >
            <div
              className={`upload-zone ${dragActive ? 'drag-active' : ''} ${file ? 'file-selected' : ''}`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              {file ? (
                <div className="file-info">
                  <Check className="file-icon" size={48} />
                  <h3>{file.name}</h3>
                  <p>{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
              ) : (
                <div className="upload-prompt">
                  <Upload className="upload-icon" size={48} />
                  <h3>Drop phishing kit here</h3>
                  <p>or click to select ZIP file</p>
                </div>
              )}
              
              <input
                type="file"
                accept=".zip"
                onChange={handleFileSelect}
                className="file-input"
              />
            </div>

            {error && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="error-message"
              >
                <AlertCircle size={20} />
                <span>{error}</span>
              </motion.div>
            )}

            {file && (
              <motion.button
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="classify-button"
                onClick={classifyKit}
              >
                <Target size={20} />
                Classify Phishing Kit
              </motion.button>
            )}

            <div className="sample-kits-section">
              <p className="sample-kits-label">📦 Try sample kits:</p>
              <div className="sample-kits">
                <a href="/sample-kits/paypal_sample.zip" download className="sample-kit-link">
                  PayPal Sample
                </a>
                <a href="/sample-kits/microsoft_sample.zip" download className="sample-kit-link">
                  Microsoft Sample
                </a>
                <a href="/sample-kits/banking_sample.zip" download className="sample-kit-link">
                  Banking Sample
                </a>
              </div>
            </div>
          </motion.div>
        )}

        {uploadState === 'uploading' && (
          <motion.div
            key="loading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="loading-section"
          >
            <div className="loading-spinner"></div>
            <h3>Analyzing phishing kit...</h3>
            <p>Extracting features and running ML classification</p>
          </motion.div>
        )}

        {uploadState === 'success' && result && (
          <motion.div
            key="results"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="results-section"
          >
            <div className="result-header">
              <Check className="success-icon" size={32} />
              <h3>Classification Complete</h3>
            </div>

            <div className="result-main">
              <div className="predicted-family">
                <h4>Predicted Family</h4>
                <div className="family-name">{result.predicted_family}</div>
              </div>

              <div className="confidence-section">
                <h4>Confidence Score</h4>
                <div className="confidence-bar">
                  <motion.div
                    className="confidence-fill"
                    initial={{ width: 0 }}
                    animate={{ width: `${result.confidence * 100}%` }}
                    transition={{ duration: 1, delay: 0.3 }}
                  />
                  <span className="confidence-text">
                    {(result.confidence * 100).toFixed(1)}%
                  </span>
                </div>
              </div>

              <div className="neighbors-section">
                <h4>Similar Kits</h4>
                <div className="neighbors-list">
                  {result.top_5_neighbours.map(([family, distance], index) => (
                    <motion.div
                      key={index}
                      className="neighbor-item"
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.5 + index * 0.1 }}
                    >
                      <span className="neighbor-rank">#{index + 1}</span>
                      <span className="neighbor-family">{family}</span>
                      <span className="neighbor-distance">
                        {distance.toFixed(3)}
                      </span>
                    </motion.div>
                  ))}
                </div>
              </div>
            </div>

            <button className="reset-button" onClick={reset}>
              Analyze Another Kit
            </button>
          </motion.div>
        )}

        {uploadState === 'error' && (
          <motion.div
            key="error"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="error-section"
          >
            <AlertCircle className="error-icon" size={48} />
            <h3>Classification Failed</h3>
            <p>{error}</p>
            <button className="retry-button" onClick={reset}>
              Try Again
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Always show the threat landscape map */}
      <ThreatLandscapeMap 
        classificationResult={result}
        newKitCoordinates={newKitCoordinates}
      />
    </div>
  );
};

export default PhishingClassifier;