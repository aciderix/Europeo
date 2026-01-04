/**
 * Europeo - Visual Novel Game
 * React Port by Claude
 */

import { useState } from 'react';
import { GameContainer } from './components/Game/GameContainer';
import { useGameStore } from './store/gameStore';

// Minimal global styles
const globalStyles = `
  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  html, body, #root {
    width: 100%;
    height: 100%;
    overflow: hidden;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  }

  body {
    background-color: #000;
  }
`;

function StartScreen({ onStart }: { onStart: () => void }) {
  const resetGame = useGameStore((state) => state.resetGame);

  const handleNewGame = () => {
    resetGame();
    onStart();
  };

  return (
    <div
      style={{
        width: '100vw',
        height: '100vh',
        background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#fff',
      }}
    >
      <h1
        style={{
          fontSize: 72,
          fontWeight: 'bold',
          marginBottom: 20,
          textShadow: '4px 4px 8px rgba(0, 0, 0, 0.5)',
          color: '#f1c40f',
        }}
      >
        🇪🇺 Europeo
      </h1>

      <p
        style={{
          fontSize: 24,
          marginBottom: 40,
          color: '#bdc3c7',
          textAlign: 'center',
          maxWidth: 600,
        }}
      >
        Découvre l'Europe à travers un voyage interactif !
        <br />
        Visite 15 pays, collecte des objets et apprends plein de choses.
      </p>

      <div style={{ display: 'flex', gap: 20 }}>
        <button
          onClick={handleNewGame}
          style={{
            padding: '20px 50px',
            fontSize: 24,
            backgroundColor: '#27ae60',
            border: 'none',
            borderRadius: 10,
            color: '#fff',
            cursor: 'pointer',
            transition: 'transform 0.2s, box-shadow 0.2s',
            boxShadow: '0 4px 15px rgba(39, 174, 96, 0.4)',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'scale(1.05)';
            e.currentTarget.style.boxShadow = '0 6px 20px rgba(39, 174, 96, 0.6)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'scale(1)';
            e.currentTarget.style.boxShadow = '0 4px 15px rgba(39, 174, 96, 0.4)';
          }}
        >
          Nouvelle Partie
        </button>

        <button
          onClick={onStart}
          style={{
            padding: '20px 50px',
            fontSize: 24,
            backgroundColor: '#3498db',
            border: 'none',
            borderRadius: 10,
            color: '#fff',
            cursor: 'pointer',
            transition: 'transform 0.2s, box-shadow 0.2s',
            boxShadow: '0 4px 15px rgba(52, 152, 219, 0.4)',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'scale(1.05)';
            e.currentTarget.style.boxShadow = '0 6px 20px rgba(52, 152, 219, 0.6)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'scale(1)';
            e.currentTarget.style.boxShadow = '0 4px 15px rgba(52, 152, 219, 0.4)';
          }}
        >
          Continuer
        </button>
      </div>

      <div
        style={{
          position: 'absolute',
          bottom: 30,
          color: '#7f8c8d',
          fontSize: 14,
        }}
      >
        Développé par Sopra Multimedia • Porté en React
      </div>
    </div>
  );
}

function App() {
  const [gameStarted, setGameStarted] = useState(false);
  const [debugMode, setDebugMode] = useState(false);

  // Toggle debug mode with keyboard shortcut
  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'F12' || (e.ctrlKey && e.shiftKey && e.key === 'D')) {
      e.preventDefault();
      setDebugMode((prev) => !prev);
    }
  };

  // Set up keyboard listener
  useState(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  });

  return (
    <>
      <style>{globalStyles}</style>
      {gameStarted ? (
        <GameContainer debug={debugMode} />
      ) : (
        <StartScreen onStart={() => setGameStarted(true)} />
      )}
    </>
  );
}

export default App;
