/**
 * Probleme Mini-Game - Faithful port of probleme.dll
 * Original question: "Toto est parti en vacances en Italie avec 2000 francs belges.
 * Sachant qu'il a dépensé 48000 lires, combien lui reste-t-il d'euros ?"
 *
 * Calculation (simplified school rates used in original):
 * - 2000 BEF / 40 = 50 EUR (approx: 1€ = 40 BEF)
 * - 48000 ITL / 2000 = 24 EUR (approx: 1€ = 2000 ITL)
 * - Remaining: 50 - 24 = 26 EUR
 *
 * EditMask: '00;0;*' = 2 digits
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { useGameStore } from '../../store/gameStore';

interface ProblemeGameProps {
  onClose: () => void;
  onSuccess?: () => void;
}

// Simplified school calculation: 50 - 24 = 26 (from original game logic)
const CORRECT_ANSWER = 26;

// Asset path
const BACKGROUND_IMAGE = '/assets/minigames/probleme/Image_1.png';

export const ProblemeGame: React.FC<ProblemeGameProps> = ({ onClose, onSuccess }) => {
  const addScore = useGameStore((state) => state.addScore);
  const setVariable = useGameStore((state) => state.setVariable);

  const [answer, setAnswer] = useState('');
  const [feedback, setFeedback] = useState('');
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
      setFeedback('...');
      return;
    }

    // Accept 25 or 26 (both valid depending on rounding method)
    if (userValue === CORRECT_ANSWER || userValue === 25) {
      setIsCorrect(true);
      setShowResult(true);
      setFeedback('Bravo !');
      addScore(20);
      setVariable('PROBLEME', 1);
      onSuccess?.();
    } else {
      setFeedback('Non...\nEssaye encore !');
    }
  }, [answer, addScore, setVariable, onSuccess]);

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSubmit();
    }
  };

  // Only allow 2 digits - matching original EditMask: 00;0;*
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    if (/^\d*$/.test(value) && value.length <= 2) {
      setAnswer(value);
      setFeedback('');
    }
  };

  // Original form: 640x400
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
        {/* Problem text - Labels 1-4 at top */}
        <div style={{
          position: 'absolute',
          left: 40,
          top: 24,
          width: 550,
          color: '#000',
          fontSize: 19,
          lineHeight: 1.5,
        }}>
          <p style={{ margin: '0 0 4px 0' }}>Toto est parti en vacances en Italie</p>
          <p style={{ margin: '0 0 4px 0' }}>avec 2000 francs belges. Sachant</p>
          <p style={{ margin: '0 0 4px 0' }}>qu'il a dépensé 48000 lires,</p>
          <p style={{ margin: 0 }}>combien lui reste-t-il d'euros ?</p>
        </div>

        {/* Hint text - Label5 */}
        <p style={{
          position: 'absolute',
          left: 40,
          top: 140,
          margin: 0,
          fontSize: 18,
          color: '#000',
          fontStyle: 'italic',
        }}>
          C'est facile, voyons!
        </p>

        {/* Answer row - "La réponse est [input] euros..." */}
        <div style={{
          position: 'absolute',
          left: 320,
          top: 200,
          display: 'flex',
          alignItems: 'center',
          gap: 8,
        }}>
          <span style={{ fontSize: 19, color: '#000' }}>La réponse est</span>
          <input
            ref={inputRef}
            type="text"
            value={answer}
            onChange={handleInputChange}
            onKeyPress={handleKeyPress}
            placeholder="__"
            disabled={showResult}
            style={{
              width: 40,
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
          <span style={{ fontSize: 19, color: '#000' }}>euros...</span>
        </div>

        {/* Feedback area (Label7 "...") */}
        <div style={{
          position: 'absolute',
          left: 400,
          top: 260,
          width: 200,
          textAlign: 'center',
          fontSize: 18,
          color: isCorrect ? '#008000' : '#cc0000',
          whiteSpace: 'pre-line',
          fontWeight: 'bold',
        }}>
          {feedback}
        </div>

        {/* Validate button */}
        {!showResult && (
          <button
            onClick={handleSubmit}
            style={{
              position: 'absolute',
              left: 500,
              top: 320,
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

        {/* Success overlay */}
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
            textAlign: 'center',
          }}>
            Bravo !<br/>
            Il reste {CORRECT_ANSWER}€ à Toto !
          </div>
        )}

        {/* Quit button (Image1 area - bottom left) */}
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

export default ProblemeGame;
