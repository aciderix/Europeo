/**
 * Tour Eiffel Mini-Game - Faithful port of pepe.dll
 * Original question: "Combien y a t-il de marches pour monter au dernier étage de la tour Eiffel ?"
 * Answer: 1652 marches (from STRINGTABLE resource)
 *
 * Original messages:
 * - "euh..."
 * - "Tout ça !"
 * - "Non... Essaye encore !"
 * - "Il me semble qu'il y en a moins."
 * - "Je crois qu'il y en a plus."
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { useGameStore } from '../../store/gameStore';

interface TourEiffelGameProps {
  onClose: () => void;
  onSuccess?: () => void;
}

// From STRINGTABLE: 65351 = "1652"
const CORRECT_ANSWER = 1652;

// Asset path
const BACKGROUND_IMAGE = '/assets/minigames/pepe/Image_1.png';

export const TourEiffelGame: React.FC<TourEiffelGameProps> = ({ onClose, onSuccess }) => {
  const addScore = useGameStore((state) => state.addScore);
  const setVariable = useGameStore((state) => state.setVariable);

  const [answer, setAnswer] = useState('');
  const [hint, setHint] = useState('');
  const [isCorrect, setIsCorrect] = useState(false);
  const [showResult, setShowResult] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = useCallback(() => {
    if (!answer.trim()) return;

    const userValue = parseInt(answer, 10);

    if (isNaN(userValue)) {
      setHint('euh...');
      return;
    }

    if (userValue === CORRECT_ANSWER) {
      setIsCorrect(true);
      setShowResult(true);
      setHint('Tout ça !');
      addScore(20);
      setVariable('PEPE', 1);
      onSuccess?.();
    } else if (userValue > CORRECT_ANSWER) {
      // "Il me semble qu'il y en a moins."
      setHint('Il me semble\nqu\'il y en a moins.');
    } else {
      // "Je crois qu'il y en a plus."
      setHint('Je crois\nqu\'il y en a plus.');
    }
  }, [answer, addScore, setVariable, onSuccess]);

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSubmit();
    }
  };

  // Only allow 4 digits - matching original EditMask: 0000;0;*
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    if (/^\d*$/.test(value) && value.length <= 4) {
      setAnswer(value);
      setHint('');
    }
  };

  // Original form: 640x400, positions from DFM
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
        backgroundImage: `url(${BACKGROUND_IMAGE})`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        fontFamily: '"Comic Sans MS", cursive, sans-serif',
      }}>
        {/* Question - positioned at Right side (Left: 400 area) */}
        <div style={{
          position: 'absolute',
          left: 400,
          top: 80,
          width: 200,
          color: '#000',
          fontSize: 19,
          lineHeight: 1.3,
        }}>
          <p style={{ margin: 0 }}>Combien y a t-il de</p>
          <p style={{ margin: 0 }}>marches pour monter</p>
          <p style={{ margin: 0 }}>au dernier étage de la</p>
          <p style={{ margin: 0 }}>tour Eiffel ?</p>
        </div>

        {/* Answer row - "Il y a [input] marches" */}
        <div style={{
          position: 'absolute',
          left: 424,
          top: 224,
          display: 'flex',
          alignItems: 'center',
          gap: 8,
        }}>
          <span style={{ fontSize: 19, color: '#000' }}>Il y a</span>
          <input
            ref={inputRef}
            type="text"
            value={answer}
            onChange={handleInputChange}
            onKeyPress={handleKeyPress}
            placeholder="____"
            disabled={showResult}
            style={{
              width: 60,
              padding: '4px 8px',
              fontSize: 19,
              fontFamily: '"Comic Sans MS", cursive, sans-serif',
              color: '#0000ff',
              backgroundColor: '#fff',
              border: 'none',
              textAlign: 'center',
              outline: 'none',
            }}
          />
        </div>

        {/* "marches" label below */}
        <span style={{
          position: 'absolute',
          left: 456,
          top: 256,
          fontSize: 19,
          color: '#000',
        }}>marches</span>

        {/* Comment/Hint area (lblComment) */}
        <div style={{
          position: 'absolute',
          left: 200,
          top: 320,
          width: 240,
          textAlign: 'center',
          fontSize: 18,
          color: isCorrect ? '#008000' : '#cc0000',
          whiteSpace: 'pre-line',
          fontWeight: 'bold',
        }}>
          {hint}
        </div>

        {/* Validate button */}
        {!showResult && (
          <button
            onClick={handleSubmit}
            style={{
              position: 'absolute',
              left: 500,
              top: 300,
              padding: '8px 20px',
              fontSize: 16,
              fontFamily: '"Comic Sans MS", cursive, sans-serif',
              fontWeight: 'bold',
              backgroundColor: '#4CAF50',
              color: '#fff',
              border: 'none',
              borderRadius: 4,
              cursor: 'pointer',
            }}
          >
            Valider
          </button>
        )}

        {/* Success message */}
        {isCorrect && (
          <div style={{
            position: 'absolute',
            left: 150,
            top: 150,
            padding: '20px 40px',
            backgroundColor: 'rgba(0, 128, 0, 0.9)',
            color: '#fff',
            fontSize: 24,
            fontWeight: 'bold',
            borderRadius: 10,
          }}>
            Bravo ! {CORRECT_ANSWER} marches !
          </div>
        )}

        {/* Quit button (btnQuit area) */}
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            left: 16,
            top: 350,
            padding: '8px 25px',
            fontSize: 16,
            fontFamily: '"Comic Sans MS", cursive, sans-serif',
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
      </div>
    </div>
  );
};

export default TourEiffelGame;
