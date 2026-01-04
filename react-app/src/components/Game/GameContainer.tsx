/**
 * Game Container
 * Main game component that manages scenes and navigation
 */

import React, { useState } from 'react';
import { Scene } from './Scene';
import { Toolbar } from '../UI/Toolbar';
import { useGameStore } from '../../store/gameStore';
import type { Scene as SceneType } from '../../types/game';

// Demo scene data (will be replaced by loaded JSON)
const DEMO_SCENES: Record<string, SceneType[]> = {
  france: [
    {
      id: 1,
      name: 'Intro France',
      background: 'france_bg.bmp',
      hotspots: [
        {
          id: 1,
          rect: { x1: 100, y1: 100, x2: 200, y2: 200 },
          tooltip: 'Tour Eiffel',
          onClick: [],
        },
        {
          id: 2,
          rect: { x1: 300, y1: 150, x2: 450, y2: 300 },
          tooltip: 'Personnage',
          onClick: [],
        },
      ],
      onEnter: [],
      onExit: [],
    },
  ],
  allem: [
    {
      id: 1,
      name: 'Berlin',
      background: 'berlin.bmp',
      hotspots: [
        {
          id: 1,
          rect: { x1: 150, y1: 100, x2: 300, y2: 250 },
          tooltip: 'Mur de Berlin',
          onClick: [],
        },
      ],
      onEnter: [],
      onExit: [],
    },
  ],
};

interface GameContainerProps {
  debug?: boolean;
}

export const GameContainer: React.FC<GameContainerProps> = ({ debug = false }) => {
  const currentCountry = useGameStore((state) => state.currentCountry);
  const currentScene = useGameStore((state) => state.currentScene);
  const navigateTo = useGameStore((state) => state.navigateTo);
  const addScore = useGameStore((state) => state.addScore);

  const [scenes] = useState<Record<string, SceneType[]>>(DEMO_SCENES);
  const [showInventory, setShowInventory] = useState(false);
  const [showCalculator, setShowCalculator] = useState(false);

  // Get current scene
  const countryScenes = scenes[currentCountry] || [];
  const activeScene = countryScenes.find((s) => s.id === currentScene) || countryScenes[0];

  const handleBack = () => {
    // Return to hub (couleurs1)
    navigateTo('couleurs1', 1);
  };

  const handleInventory = () => {
    setShowInventory(!showInventory);
  };

  const handleCalculator = () => {
    setShowCalculator(!showCalculator);
  };

  const handlePhone = () => {
    // Phone/help reduces score by 1
    addScore(-1);
    alert('Aide: Explore les différentes zones pour trouver des objets et gagner des points!');
  };

  const handleSettings = () => {
    // Toggle debug mode or show settings
    alert('Paramètres: Volume, Langue, Crédits...');
  };

  const containerStyle: React.CSSProperties = {
    width: '100vw',
    height: '100vh',
    backgroundColor: '#000',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
  };

  const gameAreaStyle: React.CSSProperties = {
    flex: 1,
    position: 'relative',
  };

  return (
    <div className="game-container" style={containerStyle}>
      <div style={gameAreaStyle}>
        {activeScene ? (
          <Scene scene={activeScene} countryId={currentCountry} debug={debug} />
        ) : (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              color: '#fff',
              fontSize: 24,
            }}
          >
            <div>
              <h2>Europeo</h2>
              <p>Chargement de {currentCountry}...</p>
              <p>Scène: {currentScene}</p>
            </div>
          </div>
        )}
      </div>

      <Toolbar
        onBack={handleBack}
        onInventory={handleInventory}
        onCalculator={handleCalculator}
        onPhone={handlePhone}
        onSettings={handleSettings}
      />

      {/* Inventory Modal */}
      {showInventory && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
          onClick={() => setShowInventory(false)}
        >
          <div
            style={{
              backgroundColor: '#2c3e50',
              borderRadius: 10,
              padding: 30,
              minWidth: 400,
              maxWidth: 600,
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h2 style={{ color: '#fff', marginTop: 0 }}>🎒 Inventaire</h2>
            <p style={{ color: '#bdc3c7' }}>Objets collectés apparaîtront ici.</p>
            <button
              onClick={() => setShowInventory(false)}
              style={{
                backgroundColor: '#3498db',
                border: 'none',
                borderRadius: 5,
                padding: '10px 20px',
                color: '#fff',
                cursor: 'pointer',
                marginTop: 20,
              }}
            >
              Fermer
            </button>
          </div>
        </div>
      )}

      {/* Calculator Modal */}
      {showCalculator && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
          onClick={() => setShowCalculator(false)}
        >
          <div
            style={{
              backgroundColor: '#2c3e50',
              borderRadius: 10,
              padding: 30,
              minWidth: 300,
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h2 style={{ color: '#fff', marginTop: 0 }}>🧮 Convertisseur Euro</h2>
            <p style={{ color: '#bdc3c7' }}>1 EUR = 6.55957 FRF</p>
            <input
              type="number"
              placeholder="Montant en Euros"
              style={{
                width: '100%',
                padding: 10,
                borderRadius: 5,
                border: 'none',
                marginBottom: 10,
              }}
            />
            <button
              onClick={() => setShowCalculator(false)}
              style={{
                backgroundColor: '#27ae60',
                border: 'none',
                borderRadius: 5,
                padding: '10px 20px',
                color: '#fff',
                cursor: 'pointer',
                width: '100%',
              }}
            >
              Fermer
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default GameContainer;
