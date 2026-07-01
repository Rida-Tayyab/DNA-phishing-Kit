import React, { useState, useEffect, useRef, useMemo } from 'react';
import Plotly from 'plotly.js-dist-min';
import { motion } from 'framer-motion';
import { Map, Search, Target, Eye, Shield } from 'lucide-react';
import './ThreatLandscapeMap.css';

import threatMapData from '../data/threat_map.json';
import familyStats from '../data/family_stats.json';
import familyColors from '../data/family_colors.json';

interface ThreatPoint {
  hash: string;
  family: string;
  x: number;
  y: number;
  total_files: number;
  useful_files: number;
  php_count: number;
  detected_brand: string;
  sophistication_score: number;
  uses_telegram: boolean;
  steals_card: boolean;
  has_bot_detection: boolean;
}

interface ClassificationResult {
  predicted_family: string;
  confidence: number;
  top_5_neighbours: [string, number][];
}

interface ThreatLandscapeMapProps {
  classificationResult?: ClassificationResult | null;
  newKitCoordinates?: { x: number; y: number } | null;
}

const ThreatLandscapeMap: React.FC<ThreatLandscapeMapProps> = ({
  classificationResult,
  newKitCoordinates
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFamily, setSelectedFamily] = useState<string | null>(null);
  const plotRef = useRef<HTMLDivElement>(null);

  const { plotData, topFamilies } = useMemo(() => {
    const data = threatMapData as ThreatPoint[];
    const familyGroups: { [key: string]: ThreatPoint[] } = {};

    data.forEach(point => {
      if (!familyGroups[point.family]) familyGroups[point.family] = [];
      familyGroups[point.family].push(point);
    });

    const topFams = familyStats.families.slice(0, 15);

    const traces: Record<string, unknown>[] = topFams.map(familyInfo => {
      const points = familyGroups[familyInfo.name] || [];
      const color = (familyColors as Record<string, string>)[familyInfo.name] || '#95a5a6';
      return {
        x: points.map(p => p.x),
        y: points.map(p => p.y),
        mode: 'markers',
        type: 'scatter',
        name: `${familyInfo.name} (${familyInfo.count})`,
        marker: {
          size: 4,
          color,
          opacity: selectedFamily === null || selectedFamily === familyInfo.name ? 0.7 : 0.1
        },
        hovertemplate:
          '<b>%{customdata[0]}</b><br>' +
          'Family: %{customdata[1]}<br>' +
          'Brand: %{customdata[2]}<br>' +
          'Files: %{customdata[3]}<br>' +
          'Sophistication: %{customdata[4]}/10<br>' +
          '<extra></extra>',
        customdata: points.map(p => [
          p.hash.substring(0, 8) + '...',
          p.family,
          p.detected_brand,
          p.total_files,
          p.sophistication_score
        ])
      };
    });

    const otherFamilies = Object.keys(familyGroups).filter(
      family => !topFams.find(f => f.name === family)
    );
    const otherPoints = otherFamilies.flatMap(family => familyGroups[family]);
    if (otherPoints.length > 0) {
      traces.push({
        x: otherPoints.map(p => p.x),
        y: otherPoints.map(p => p.y),
        mode: 'markers',
        type: 'scatter',
        name: `Other families (${otherPoints.length})`,
        marker: { size: 3, color: '#95a5a6', opacity: selectedFamily === null ? 0.3 : 0.05 },
        hovertemplate:
          '<b>%{customdata[0]}</b><br>' +
          'Family: %{customdata[1]}<br>' +
          'Brand: %{customdata[2]}<br>' +
          'Files: %{customdata[3]}<br>' +
          '<extra></extra>',
        customdata: otherPoints.map(p => [
          p.hash.substring(0, 8) + '...',
          p.family,
          p.detected_brand,
          p.total_files
        ])
      });
    }

    if (classificationResult && newKitCoordinates) {
      traces.push({
        x: [newKitCoordinates.x],
        y: [newKitCoordinates.y],
        mode: 'markers',
        type: 'scatter',
        name: '🎯 New Kit',
        marker: { size: 15, color: '#00ff88', opacity: 1, symbol: 'star' },
        hovertemplate:
          '<b>🎯 Uploaded Kit</b><br>' +
          'Predicted: ' + classificationResult.predicted_family + '<br>' +
          'Confidence: ' + (classificationResult.confidence * 100).toFixed(1) + '%<br>' +
          '<extra></extra>',
        showlegend: true
      });
    }

    return { plotData: traces, topFamilies: topFams };
  }, [selectedFamily, classificationResult, newKitCoordinates]);

  useEffect(() => {
    if (!plotRef.current) return;
    const layout: Record<string, unknown> = {
      title: {
        text: selectedFamily
          ? `${selectedFamily} Family Distribution`
          : 'Phishing Kit Families - UMAP Projection',
        font: { color: '#ffffff', size: 16 },
        x: 0.5
      },
      xaxis: { title: { text: 'UMAP Dimension 1' }, showgrid: false, zeroline: false, showticklabels: false, color: '#888' },
      yaxis: { title: { text: 'UMAP Dimension 2' }, showgrid: false, zeroline: false, showticklabels: false, color: '#888' },
      plot_bgcolor: 'rgba(0,0,0,0)',
      paper_bgcolor: 'rgba(0,0,0,0)',
      font: { color: '#ffffff' },
      showlegend: true,
      legend: {
        orientation: 'v', x: 1.02, y: 1,
        bgcolor: 'rgba(0,0,0,0.5)', bordercolor: '#333', borderwidth: 1,
        font: { size: 11 }
      },
      margin: { l: 40, r: 200, t: 60, b: 40 },
      hovermode: 'closest'
    };
    Plotly.react(plotRef.current, plotData, layout, {
      displayModeBar: true,
      displaylogo: false,
      responsive: true
    });
  }, [plotData, selectedFamily]);

  const filteredFamilies = useMemo(
    () => topFamilies.filter(f => f.name.toLowerCase().includes(searchTerm.toLowerCase())),
    [topFamilies, searchTerm]
  );

  return (
    <div className="threat-landscape-container">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="threat-landscape-header"
      >
        <div className="header-content">
          <div className="header-left">
            <Map className="map-icon" size={28} />
            <div>
              <h2>Threat Landscape Map</h2>
              <p>
                Interactive visualization of {familyStats.total_kits.toLocaleString()} phishing kits
                across {familyStats.total_families.toLocaleString()} families
              </p>
            </div>
          </div>
          <div className="accuracy-badge">
            <Shield size={20} />
            <span>88.0% Accuracy</span>
          </div>
        </div>
      </motion.div>

      <div className="threat-landscape-content">
        <div className="map-controls">
          <div className="family-search">
            <Search size={16} />
            <input
              type="text"
              placeholder="Search families..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <div className="family-list">
            <div
              className={`family-item ${selectedFamily === null ? 'active' : ''}`}
              onClick={() => setSelectedFamily(null)}
            >
              <Eye size={14} />
              <span>All Families</span>
              <span className="family-count">{familyStats.total_kits.toLocaleString()}</span>
            </div>
            {filteredFamilies.map(family => (
              <div
                key={family.name}
                className={`family-item ${selectedFamily === family.name ? 'active' : ''}`}
                onClick={() => setSelectedFamily(selectedFamily === family.name ? null : family.name)}
              >
                <div
                  className="family-color-dot"
                  style={{ backgroundColor: (familyColors as Record<string, string>)[family.name] || '#95a5a6' }}
                />
                <span className="family-name">{family.name}</span>
                <span className="family-count">{family.count}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="map-visualization">
          <div ref={plotRef} style={{ width: '100%', height: '600px' }} />
        </div>
      </div>

      {classificationResult && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="classification-overlay"
        >
          <Target className="target-icon" size={20} />
          <div className="overlay-content">
            <h4>New Kit Classified</h4>
            <p>
              Predicted as <strong>{classificationResult.predicted_family}</strong> with{' '}
              <strong>{(classificationResult.confidence * 100).toFixed(1)}%</strong> confidence
            </p>
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default ThreatLandscapeMap;
