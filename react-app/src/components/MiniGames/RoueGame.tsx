/**
 * Roue Mini-Game - Faithful port of roue.dll
 * Original: 9 sector wheel with click interaction
 * Prize: inc_var score 1000 on win
 * Font: Century Gothic
 */

import React, { useState, useCallback, useRef } from 'react';
import { useGameStore } from '../../store/gameStore';

interface RoueGameProps {
  onClose: () => void;
  onSuccess?: () => void;
}

// 9 sectors matching Image2-Image10 in original DLL
const SECTORS = [
  { id: 2, label: '100', value: 100, color: '#e74c3c' },
  { id: 3, label: '200', value: 200, color: '#3498db' },
  { id: 4, label: '500', value: 500, color: '#2ecc71' },
  { id: 5, label: '💀', value: 0, color: '#2c3e50', isLose: true },
  { id: 6, label: '1000', value: 1000, color: '#f1c40f', isJackpot: true },
  { id: 7, label: '50', value: 50, color: '#9b59b6' },
  { id: 8, label: '💀', value: 0, color: '#2c3e50', isLose: true },
  { id: 9, label: '300', value: 300, color: '#1abc9c' },
  { id: 10, label: '150', value: 150, color: '#e67e22' },
];

export const RoueGame: React.FC<RoueGameProps> = ({ onClose, onSuccess }) => {
  const addScore = useGameStore((state) => state.addScore);
  const setVariable = useGameStore((state) => state.setVariable);

  const [isSpinning, setIsSpinning] = useState(false);
  const [rotation, setRotation] = useState(0);
  const [result, setResult] = useState<typeof SECTORS[0] | null>(null);
  const [gameOver, setGameOver] = useState(false);
  const wheelRef = useRef<HTMLDivElement>(null);

  const spinWheel = useCallback(() => {
    if (isSpinning || gameOver) return;

    setIsSpinning(true);
    setResult(null);

    // Random number of full rotations (5-10) plus random position
    const fullRotations = 5 + Math.floor(Math.random() * 5);
    const randomAngle = Math.random() * 360;
    const totalRotation = rotation + fullRotations * 360 + randomAngle;

    setRotation(totalRotation);

    // Calculate which sector we land on after spin
    setTimeout(() => {
      const normalizedAngle = totalRotation % 360;
      const sectorAngle = 360 / SECTORS.length;
      // Adjust for wheel starting position and rotation direction
      const adjustedAngle = (360 - normalizedAngle + sectorAngle / 2) % 360;
      const sectorIndex = Math.floor(adjustedAngle / sectorAngle);
      const landedSector = SECTORS[sectorIndex % SECTORS.length];

      setResult(landedSector);
      setIsSpinning(false);

      if (landedSector.isLose) {
        setGameOver(true);
        setVariable('ROUEDENT', 0);
      } else {
        addScore(landedSector.value);
        if (landedSector.isJackpot) {
          setVariable('ROUEDENT', 1);
          setGameOver(true);
          onSuccess?.();
        }
      }
    }, 4000);
  }, [isSpinning, gameOver, rotation, addScore, setVariable, onSuccess]);

  const sectorAngle = 360 / SECTORS.length;

  const overlayStyle: React.CSSProperties = {
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
  };

  const containerStyle: React.CSSProperties = {
    backgroundColor: '#1a1a2e',
    borderRadius: 20,
    padding: 40,
    maxWidth: 500,
    width: '95%',
    textAlign: 'center',
    boxShadow: '0 10px 50px rgba(0, 0, 0, 0.5)',
    fontFamily: '"Century Gothic", sans-serif',
  };

  const wheelContainerStyle: React.CSSProperties = {
    position: 'relative',
    width: 300,
    height: 300,
    margin: '20px auto',
  };

  const wheelStyle: React.CSSProperties = {
    position: 'absolute',
    width: '100%',
    height: '100%',
    borderRadius: '50%',
    overflow: 'hidden',
    transform: `rotate(${rotation}deg)`,
    transition: isSpinning ? 'transform 4s cubic-bezier(0.17, 0.67, 0.12, 0.99)' : 'none',
    boxShadow: '0 0 20px rgba(0, 0, 0, 0.5), inset 0 0 30px rgba(0, 0, 0, 0.2)',
  };

  const pointerStyle: React.CSSProperties = {
    position: 'absolute',
    top: -15,
    left: '50%',
    transform: 'translateX(-50%)',
    width: 0,
    height: 0,
    borderLeft: '15px solid transparent',
    borderRight: '15px solid transparent',
    borderTop: '30px solid #f1c40f',
    zIndex: 10,
    filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.5))',
  };

  const buttonStyle: React.CSSProperties = {
    padding: '15px 40px',
    fontSize: 20,
    fontWeight: 'bold',
    backgroundColor: isSpinning || gameOver ? '#7f8c8d' : '#e74c3c',
    color: '#fff',
    border: 'none',
    borderRadius: 10,
    cursor: isSpinning || gameOver ? 'not-allowed' : 'pointer',
    marginTop: 20,
    fontFamily: '"Century Gothic", sans-serif',
  };

  const resultStyle: React.CSSProperties = {
    marginTop: 20,
    padding: 20,
    borderRadius: 10,
    fontSize: 24,
    fontWeight: 'bold',
    backgroundColor: result?.isLose ? '#e74c3c' : result?.isJackpot ? '#f1c40f' : '#27ae60',
    color: result?.isJackpot ? '#000' : '#fff',
  };

  return (
    <div style={overlayStyle}>
      <div style={containerStyle}>
        <h2 style={{ color: '#f1c40f', fontSize: 28, marginTop: 0, marginBottom: 10 }}>
          La Roue de la Fortune
        </h2>

        <div style={wheelContainerStyle}>
          <div style={pointerStyle} />
          <div ref={wheelRef} style={wheelStyle}>
            <svg viewBox="0 0 100 100" width="100%" height="100%">
              {SECTORS.map((sector, index) => {
                const startAngle = index * sectorAngle;
                const endAngle = (index + 1) * sectorAngle;
                const startRad = (startAngle - 90) * (Math.PI / 180);
                const endRad = (endAngle - 90) * (Math.PI / 180);

                const x1 = 50 + 50 * Math.cos(startRad);
                const y1 = 50 + 50 * Math.sin(startRad);
                const x2 = 50 + 50 * Math.cos(endRad);
                const y2 = 50 + 50 * Math.sin(endRad);

                const largeArc = sectorAngle > 180 ? 1 : 0;

                const textAngle = startAngle + sectorAngle / 2;
                const textRad = (textAngle - 90) * (Math.PI / 180);
                const textX = 50 + 32 * Math.cos(textRad);
                const textY = 50 + 32 * Math.sin(textRad);

                return (
                  <g key={sector.id}>
                    <path
                      d={`M 50 50 L ${x1} ${y1} A 50 50 0 ${largeArc} 1 ${x2} ${y2} Z`}
                      fill={sector.color}
                      stroke="#fff"
                      strokeWidth="0.5"
                    />
                    <text
                      x={textX}
                      y={textY}
                      fill="#fff"
                      fontSize={sector.isLose ? "12" : "8"}
                      fontWeight="bold"
                      textAnchor="middle"
                      dominantBaseline="middle"
                      transform={`rotate(${textAngle}, ${textX}, ${textY})`}
                    >
                      {sector.label}
                    </text>
                  </g>
                );
              })}
              <circle cx="50" cy="50" r="8" fill="#2c3e50" stroke="#f1c40f" strokeWidth="2" />
            </svg>
          </div>
        </div>

        {result && (
          <div style={resultStyle}>
            {result.isLose ? (
              <>Perdu ! 💀</>
            ) : result.isJackpot ? (
              <>JACKPOT ! +1000 points ! 🎉</>
            ) : (
              <>+{result.value} points !</>
            )}
          </div>
        )}

        <button
          onClick={spinWheel}
          style={buttonStyle}
          disabled={isSpinning || gameOver}
        >
          {isSpinning ? 'La roue tourne...' : gameOver ? 'Partie terminée' : 'Tourner la roue !'}
        </button>

        <br />

        <button
          onClick={onClose}
          style={{
            ...buttonStyle,
            backgroundColor: '#7f8c8d',
            fontSize: 16,
            padding: '10px 30px',
          }}
        >
          Quitter
        </button>
      </div>
    </div>
  );
};

export default RoueGame;
