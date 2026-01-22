/**
 * Coffre Mini-Game - Faithful port of roue.dll
 * Original: 4-digit combination lock, NOT a wheel of fortune!
 *
 * Solution: 2002 (year the Euro was introduced as physical currency)
 *
 * Form layout (640x400):
 * - Image1: Background at (-6, -78), 640x480
 * - Label1-4: 4 digit counters at specific positions
 * - Image2-9: +/- button zones for each digit
 * - Image10: Quit button at (8, 336)
 *
 * Font: Century Gothic Bold, Blue color
 */

import React, { useState, useCallback, useEffect } from 'react';
import { useGameStore } from '../../store/gameStore';

interface CoffreGameProps {
  onClose: () => void;
  onSuccess?: () => void;
}

// Solution: 2002 - year of Euro physical introduction
const SOLUTION = [2, 0, 0, 2];

// Asset path
const BACKGROUND_IMAGE = '/assets/minigames/roue/Image_1.png';

// Digit positions from original DFM (adjusted for our container)
// Original form is 640x400, image offset at (-6, -78)
// We'll use a 640x400 container
const DIGIT_POSITIONS = [
  { left: 106, top: 156, fontSize: 24 },  // Label1: digit 1
  { left: 266, top: 102, fontSize: 16 },  // Label2: digit 2
  { left: 358, top: 240, fontSize: 24 },  // Label3: digit 3
  { left: 434, top: 62, fontSize: 21 },   // Label4: digit 4
];

// Button zones from original (Image2-Image9)
// Image2/Image3 control Label1, Image4/Image5 control Label2, etc.
const BUTTON_ZONES = [
  // Digit 1 controls
  { digitIndex: 0, increment: true, left: 49, top: 198, width: 109, height: 58 },   // Image2: +
  { digitIndex: 0, increment: false, left: 52, top: 148, width: 105, height: 45 },  // Image3: -
  // Digit 2 controls
  { digitIndex: 1, increment: true, left: 230, top: 132, width: 69, height: 37 },   // Image4: +
  { digitIndex: 1, increment: false, left: 229, top: 87, width: 71, height: 44 },   // Image5: -
  // Digit 3 controls
  { digitIndex: 2, increment: true, left: 302, top: 284, width: 106, height: 48 },  // Image6: +
  { digitIndex: 2, increment: false, left: 300, top: 219, width: 107, height: 64 }, // Image7: -
  // Digit 4 controls
  { digitIndex: 3, increment: true, left: 391, top: 92, width: 88, height: 43 },    // Image8: +
  { digitIndex: 3, increment: false, left: 390, top: 47, width: 87, height: 44 },   // Image9: -
];

export const CoffreGame: React.FC<CoffreGameProps> = ({ onClose, onSuccess }) => {
  const addScore = useGameStore((state) => state.addScore);
  const setVariable = useGameStore((state) => state.setVariable);

  const [digits, setDigits] = useState([0, 0, 0, 0]);
  const [isCorrect, setIsCorrect] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);

  // Check if current combination matches solution
  useEffect(() => {
    const correct = digits.every((d, i) => d === SOLUTION[i]);
    if (correct && !isCorrect) {
      setIsCorrect(true);
      setShowSuccess(true);
      addScore(50);
      setVariable('COFFRE', 1);
      onSuccess?.();
    }
  }, [digits, isCorrect, addScore, setVariable, onSuccess]);

  // Handle digit change (wrap 0-9)
  const changeDigit = useCallback((index: number, increment: boolean) => {
    if (isCorrect) return;

    setDigits(prev => {
      const newDigits = [...prev];
      if (increment) {
        newDigits[index] = (newDigits[index] + 1) % 10;
      } else {
        newDigits[index] = (newDigits[index] - 1 + 10) % 10;
      }
      return newDigits;
    });
  }, [isCorrect]);

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: '#000',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
    }}>
      <div style={{
        position: 'relative',
        width: 640,
        height: 400,
        overflow: 'hidden',
      }}>
        {/* Background image - positioned at (-6, -78) in original */}
        <img
          src={BACKGROUND_IMAGE}
          alt="Coffre"
          style={{
            position: 'absolute',
            left: -6,
            top: -78,
            width: 640,
            height: 480,
            objectFit: 'cover',
          }}
          onError={(e) => {
            // Fallback if image not found
            (e.target as HTMLImageElement).style.display = 'none';
          }}
        />

        {/* Fallback background if image fails */}
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          background: 'linear-gradient(135deg, #2c1810 0%, #4a2c1a 50%, #2c1810 100%)',
          zIndex: -1,
        }} />

        {/* Digit displays - Century Gothic Bold Blue */}
        {DIGIT_POSITIONS.map((pos, index) => (
          <div
            key={index}
            style={{
              position: 'absolute',
              left: pos.left,
              top: pos.top,
              fontFamily: '"Century Gothic", sans-serif',
              fontSize: pos.fontSize,
              fontWeight: 'bold',
              color: '#0000ff',
              cursor: 'default',
              userSelect: 'none',
              textShadow: '1px 1px 2px rgba(0,0,0,0.3)',
            }}
          >
            {digits[index]}
          </div>
        ))}

        {/* Invisible button zones */}
        {BUTTON_ZONES.map((zone, index) => (
          <div
            key={index}
            onClick={() => changeDigit(zone.digitIndex, zone.increment)}
            style={{
              position: 'absolute',
              left: zone.left,
              top: zone.top,
              width: zone.width,
              height: zone.height,
              cursor: isCorrect ? 'default' : 'pointer',
              // Debug: uncomment to see hitboxes
              // backgroundColor: 'rgba(255, 0, 0, 0.2)',
              // border: '1px solid red',
            }}
            title={zone.increment ? '+' : '-'}
          />
        ))}

        {/* Quit button zone (Image10) */}
        <div
          onClick={onClose}
          style={{
            position: 'absolute',
            left: 8,
            top: 336,
            width: 57,
            height: 49,
            cursor: 'pointer',
            // Debug: uncomment to see hitbox
            // backgroundColor: 'rgba(0, 255, 0, 0.2)',
          }}
          title="Quitter"
        />

        {/* Manual quit button (visible) */}
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            left: 550,
            top: 360,
            padding: '8px 16px',
            fontSize: 14,
            fontFamily: '"Century Gothic", sans-serif',
            fontWeight: 'bold',
            backgroundColor: '#8b4513',
            color: '#fff',
            border: 'none',
            borderRadius: 4,
            cursor: 'pointer',
          }}
        >
          Quitter
        </button>

        {/* Success overlay */}
        {showSuccess && (
          <div style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            backgroundColor: 'rgba(0, 128, 0, 0.95)',
            color: '#fff',
            padding: '30px 50px',
            borderRadius: 15,
            textAlign: 'center',
            fontFamily: '"Century Gothic", sans-serif',
            boxShadow: '0 10px 40px rgba(0,0,0,0.5)',
          }}>
            <div style={{ fontSize: 32, fontWeight: 'bold', marginBottom: 10 }}>
              Bravo !
            </div>
            <div style={{ fontSize: 20 }}>
              Le code est 2002
            </div>
            <div style={{ fontSize: 16, marginTop: 10, opacity: 0.9 }}>
              L'année de l'Euro !
            </div>
          </div>
        )}

        {/* Hint text */}
        {!showSuccess && (
          <div style={{
            position: 'absolute',
            bottom: 20,
            left: '50%',
            transform: 'translateX(-50%)',
            fontFamily: '"Century Gothic", sans-serif',
            fontSize: 14,
            color: '#fff',
            textShadow: '1px 1px 3px #000',
            textAlign: 'center',
          }}>
            Trouvez le code à 4 chiffres...
          </div>
        )}
      </div>
    </div>
  );
};

export default CoffreGame;
