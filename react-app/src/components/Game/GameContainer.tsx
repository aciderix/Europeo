/**
 * Game Container
 * Main game component that manages scenes and navigation
 */

import React, { useState, useEffect } from 'react';
import { Scene } from './Scene';
import { Toolbar } from '../UI/Toolbar';
import {
  FrancsGame,
  TourEiffelGame,
  ProblemeGame,
  MemoryGame,
  RoueGame,
  type MiniGameType,
} from '../MiniGames';
import { EuroCalculator } from '../EuroCalculator';
import { useGameStore } from '../../store/gameStore';
import { loadCountry, getCountryList } from '../../engine/GameDataLoader';
import type { Country } from '../../types/game';

// Country name mappings
const COUNTRY_NAMES: Record<string, string> = {
  allem: 'Allemagne',
  angl: 'Angleterre',
  autr: 'Autriche',
  belge: 'Belgique',
  danem: 'Danemark',
  ecosse: 'Écosse',
  espa: 'Espagne',
  finlan: 'Finlande',
  france: 'France',
  grece: 'Grèce',
  holl: 'Pays-Bas',
  irland: 'Irlande',
  italie: 'Italie',
  portu: 'Portugal',
  suede: 'Suède',
};

interface GameContainerProps {
  debug?: boolean;
}

export const GameContainer: React.FC<GameContainerProps> = ({ debug = false }) => {
  const currentCountry = useGameStore((state) => state.currentCountry);
  const currentScene = useGameStore((state) => state.currentScene);
  const navigateTo = useGameStore((state) => state.navigateTo);
  const addScore = useGameStore((state) => state.addScore);
  const inventory = useGameStore((state) => state.inventory);

  const [countryData, setCountryData] = useState<Country | null>(null);
  const [, setCountryList] = useState<{ id: string; name: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [showInventory, setShowInventory] = useState(false);
  const [showCalculator, setShowCalculator] = useState(false);
  const [showCountrySelector, setShowCountrySelector] = useState(false);
  const [showMiniGameSelector, setShowMiniGameSelector] = useState(false);
  const [activeMiniGame, setActiveMiniGame] = useState<MiniGameType | null>(null);

  // Load country list on mount
  useEffect(() => {
    getCountryList()
      .then(setCountryList)
      .catch((err) => console.error('Error loading country list:', err));
  }, []);

  // Load country data when country changes
  useEffect(() => {
    setLoading(true);
    loadCountry(currentCountry)
      .then((data) => {
        setCountryData(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Error loading country:', err);
        setLoading(false);
      });
  }, [currentCountry]);

  // Get current scene
  const scenes = countryData?.scenes || [];
  const activeScene = scenes.find((s) => s.id === currentScene) || scenes[0];

  const handleBack = () => {
    setShowCountrySelector(true);
  };

  const handleSelectCountry = (countryId: string) => {
    navigateTo(countryId, 1);
    setShowCountrySelector(false);
  };

  const handleInventory = () => {
    setShowInventory(!showInventory);
  };

  const handleCalculator = () => {
    setShowCalculator(!showCalculator);
  };

  const handlePhone = () => {
    addScore(-1);
    alert('Aide: Explore les différentes zones pour trouver des objets et gagner des points!');
  };

  const handleSettings = () => {
    alert('Paramètres: Volume, Langue, Crédits...');
  };

  const handleMiniGame = () => {
    setShowMiniGameSelector(true);
  };

  const launchMiniGame = (gameType: MiniGameType) => {
    setShowMiniGameSelector(false);
    setActiveMiniGame(gameType);
  };

  const closeMiniGame = () => {
    setActiveMiniGame(null);
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
        {loading ? (
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
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 48, marginBottom: 20 }}>🌍</div>
              <p>Chargement de {COUNTRY_NAMES[currentCountry] || currentCountry}...</p>
            </div>
          </div>
        ) : activeScene ? (
          <Scene scene={activeScene} countryId={currentCountry} debug={debug} />
        ) : (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              color: '#fff',
            }}
          >
            <div style={{ textAlign: 'center' }}>
              <h2 style={{ fontSize: 32 }}>🗺️ {COUNTRY_NAMES[currentCountry] || currentCountry}</h2>
              <p style={{ color: '#bdc3c7' }}>
                {countryData?.assets.images.length || 0} images disponibles
              </p>
              <button
                onClick={() => setShowCountrySelector(true)}
                style={{
                  marginTop: 20,
                  padding: '15px 30px',
                  fontSize: 18,
                  backgroundColor: '#3498db',
                  border: 'none',
                  borderRadius: 8,
                  color: '#fff',
                  cursor: 'pointer',
                }}
              >
                Choisir un pays
              </button>
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
        onMiniGame={handleMiniGame}
      />

      {/* Country Selector Modal */}
      {showCountrySelector && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.9)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
          onClick={() => setShowCountrySelector(false)}
        >
          <div
            style={{
              backgroundColor: '#1a1a2e',
              borderRadius: 15,
              padding: 30,
              maxWidth: 800,
              maxHeight: '80vh',
              overflow: 'auto',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h2 style={{ color: '#f1c40f', marginTop: 0, textAlign: 'center' }}>
              🌍 Choisis ton pays
            </h2>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(3, 1fr)',
                gap: 15,
                marginTop: 20,
              }}
            >
              {Object.entries(COUNTRY_NAMES).map(([id, name]) => (
                <button
                  key={id}
                  onClick={() => handleSelectCountry(id)}
                  style={{
                    padding: '15px 20px',
                    fontSize: 16,
                    backgroundColor: currentCountry === id ? '#27ae60' : '#34495e',
                    border: '2px solid',
                    borderColor: currentCountry === id ? '#2ecc71' : '#3498db',
                    borderRadius: 10,
                    color: '#fff',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                  }}
                  onMouseEnter={(e) => {
                    if (currentCountry !== id) {
                      e.currentTarget.style.backgroundColor = '#3498db';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (currentCountry !== id) {
                      e.currentTarget.style.backgroundColor = '#34495e';
                    }
                  }}
                >
                  {name}
                </button>
              ))}
            </div>
            <button
              onClick={() => setShowCountrySelector(false)}
              style={{
                marginTop: 20,
                padding: '10px 30px',
                fontSize: 16,
                backgroundColor: '#e74c3c',
                border: 'none',
                borderRadius: 8,
                color: '#fff',
                cursor: 'pointer',
                display: 'block',
                marginLeft: 'auto',
                marginRight: 'auto',
              }}
            >
              Fermer
            </button>
          </div>
        </div>
      )}

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
            {inventory.length > 0 ? (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
                {inventory.map((item) => (
                  <div
                    key={item}
                    style={{
                      backgroundColor: '#34495e',
                      padding: '8px 15px',
                      borderRadius: 5,
                      color: '#fff',
                    }}
                  >
                    {item}
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ color: '#bdc3c7' }}>Aucun objet collecté pour le moment.</p>
            )}
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

      {/* Euro Calculator - faithful port of euro32 calculette.dll */}
      {showCalculator && (
        <EuroCalculator onClose={() => setShowCalculator(false)} />
      )}

      {/* Mini-Game Selector */}
      {showMiniGameSelector && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.9)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
          onClick={() => setShowMiniGameSelector(false)}
        >
          <div
            style={{
              backgroundColor: '#1a1a2e',
              borderRadius: 15,
              padding: 30,
              maxWidth: 600,
              width: '90%',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h2 style={{ color: '#f1c40f', marginTop: 0, textAlign: 'center' }}>
              🎮 Mini-Jeux
            </h2>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(2, 1fr)',
                gap: 15,
                marginTop: 20,
              }}
            >
              <button
                onClick={() => launchMiniGame('francs')}
                style={{
                  padding: '20px',
                  fontSize: 16,
                  backgroundColor: '#27ae60',
                  border: 'none',
                  borderRadius: 10,
                  color: '#fff',
                  cursor: 'pointer',
                }}
              >
                💶 Conversion Francs
                <br />
                <small style={{ opacity: 0.8 }}>100 FF = ? EUR</small>
              </button>
              <button
                onClick={() => launchMiniGame('pepe')}
                style={{
                  padding: '20px',
                  fontSize: 16,
                  backgroundColor: '#3498db',
                  border: 'none',
                  borderRadius: 10,
                  color: '#fff',
                  cursor: 'pointer',
                }}
              >
                🗼 Tour Eiffel
                <br />
                <small style={{ opacity: 0.8 }}>Combien de marches ?</small>
              </button>
              <button
                onClick={() => launchMiniGame('probleme')}
                style={{
                  padding: '20px',
                  fontSize: 16,
                  backgroundColor: '#9b59b6',
                  border: 'none',
                  borderRadius: 10,
                  color: '#fff',
                  cursor: 'pointer',
                }}
              >
                🧮 Problème Math
                <br />
                <small style={{ opacity: 0.8 }}>BEF + ITL = EUR</small>
              </button>
              <button
                onClick={() => launchMiniGame('memory')}
                style={{
                  padding: '20px',
                  fontSize: 16,
                  backgroundColor: '#e67e22',
                  border: 'none',
                  borderRadius: 10,
                  color: '#fff',
                  cursor: 'pointer',
                }}
              >
                🃏 Memory
                <br />
                <small style={{ opacity: 0.8 }}>8 paires de drapeaux</small>
              </button>
              <button
                onClick={() => launchMiniGame('roue')}
                style={{
                  padding: '20px',
                  fontSize: 16,
                  backgroundColor: '#e74c3c',
                  border: 'none',
                  borderRadius: 10,
                  color: '#fff',
                  cursor: 'pointer',
                  gridColumn: 'span 2',
                }}
              >
                🎡 Roue de la Fortune
                <br />
                <small style={{ opacity: 0.8 }}>Jackpot: 1000 points !</small>
              </button>
            </div>
            <button
              onClick={() => setShowMiniGameSelector(false)}
              style={{
                marginTop: 20,
                padding: '10px 30px',
                fontSize: 16,
                backgroundColor: '#7f8c8d',
                border: 'none',
                borderRadius: 8,
                color: '#fff',
                cursor: 'pointer',
                display: 'block',
                marginLeft: 'auto',
                marginRight: 'auto',
              }}
            >
              Fermer
            </button>
          </div>
        </div>
      )}

      {/* Active Mini-Games */}
      {activeMiniGame === 'francs' && <FrancsGame onClose={closeMiniGame} />}
      {activeMiniGame === 'pepe' && <TourEiffelGame onClose={closeMiniGame} />}
      {activeMiniGame === 'probleme' && <ProblemeGame onClose={closeMiniGame} />}
      {activeMiniGame === 'memory' && <MemoryGame onClose={closeMiniGame} />}
      {activeMiniGame === 'roue' && <RoueGame onClose={closeMiniGame} />}
    </div>
  );
};

export default GameContainer;
