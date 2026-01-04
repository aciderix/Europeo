/**
 * Toolbar Component
 * Navigation bar at the bottom of the screen
 */

import React from 'react';
import { useGameStore } from '../../store/gameStore';

interface ToolbarProps {
  onBack?: () => void;
  onInventory?: () => void;
  onCalculator?: () => void;
  onPhone?: () => void;
  onSettings?: () => void;
}

export const Toolbar: React.FC<ToolbarProps> = ({
  onBack,
  onInventory,
  onCalculator,
  onPhone,
  onSettings,
}) => {
  const score = useGameStore((state) => state.score);
  const currentCountry = useGameStore((state) => state.currentCountry);
  const showToolbar = useGameStore((state) => state.showToolbar);

  if (!showToolbar) return null;

  const toolbarStyle: React.CSSProperties = {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    height: 80,
    background: 'linear-gradient(to bottom, #2c3e50, #1a252f)',
    borderTop: '2px solid #3498db',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '0 20px',
    zIndex: 100,
  };

  const buttonStyle: React.CSSProperties = {
    backgroundColor: '#34495e',
    border: '2px solid #3498db',
    borderRadius: 8,
    padding: '10px 20px',
    color: '#fff',
    fontSize: 14,
    cursor: 'pointer',
    transition: 'all 0.2s',
    display: 'flex',
    alignItems: 'center',
    gap: 8,
  };

  const scoreStyle: React.CSSProperties = {
    backgroundColor: '#27ae60',
    border: '2px solid #2ecc71',
    borderRadius: 8,
    padding: '10px 20px',
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
    fontFamily: 'monospace',
  };

  const countryBadgeStyle: React.CSSProperties = {
    backgroundColor: '#e74c3c',
    border: '2px solid #c0392b',
    borderRadius: 8,
    padding: '10px 15px',
    color: '#fff',
    fontSize: 14,
    textTransform: 'uppercase',
  };

  return (
    <div className="toolbar" style={toolbarStyle}>
      {/* Left section: Navigation */}
      <div style={{ display: 'flex', gap: 10 }}>
        <button
          style={buttonStyle}
          onClick={onBack}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = '#3498db';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = '#34495e';
          }}
        >
          ← Retour
        </button>

        <button
          style={buttonStyle}
          onClick={onInventory}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = '#3498db';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = '#34495e';
          }}
        >
          🎒 Sac
        </button>
      </div>

      {/* Center section: Country and Score */}
      <div style={{ display: 'flex', gap: 20, alignItems: 'center' }}>
        <div style={countryBadgeStyle}>{currentCountry}</div>
        <div style={scoreStyle}>Score: {score}</div>
      </div>

      {/* Right section: Tools */}
      <div style={{ display: 'flex', gap: 10 }}>
        <button
          style={buttonStyle}
          onClick={onCalculator}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = '#3498db';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = '#34495e';
          }}
        >
          🧮 Euro
        </button>

        <button
          style={buttonStyle}
          onClick={onPhone}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = '#3498db';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = '#34495e';
          }}
        >
          📞 Aide
        </button>

        <button
          style={buttonStyle}
          onClick={onSettings}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = '#3498db';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = '#34495e';
          }}
        >
          ⚙️
        </button>
      </div>
    </div>
  );
};

export default Toolbar;
