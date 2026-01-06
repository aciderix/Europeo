/**
 * Francs Mini-Game - Faithful port of francs.dll
 * Original: Currency converter - "Combien font 100 francs français en euros ?"
 * Answer: 100 / 6.55957 = 15,24 EUR
 *
 * Original DFM Layout (640x400):
 * - lblQuestion: (64, 88) 160x78 "Combien font 100 francs français en euros ?"
 * - lblAnswer1: (428, 52) "100 francs font"
 * - maskEdit: (428, 90) width 65, EditMask: '00,00;0;*'
 * - lblAnswer2: (500, 88) "euros."
 * - lblComment: (508, 288) 97x89 "Entre les chiffres au clavier."
 * - btnQuit: (16, 284) 81x101 - hitbox
 * - lblQuit: (100, 336) "Quitter" white bold
 *
 * STRINGTABLE:
 * - 65345: "Oui\rC'est ça !!!"
 * - 65346: "Non...\rEssaye encore"
 * - 65347: "1524" (answer without comma)
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { useGameStore } from '../../store/gameStore';

interface FrancsGameProps {
  onClose: () => void;
  onSuccess?: () => void;
}

// Original question: 100 FRF = ? EUR (rate: 6.55957)
const CORRECT_ANSWER = "15,24"; // 100 / 6.55957 ≈ 15.24 EUR

// Asset path
const BACKGROUND_IMAGE = '/assets/minigames/francs/Image_1.png';

export const FrancsGame: React.FC<FrancsGameProps> = ({ onClose, onSuccess }) => {
  const addScore = useGameStore((state) => state.addScore);
  const setVariable = useGameStore((state) => state.setVariable);

  const [answer, setAnswer] = useState('');
  const [feedback, setFeedback] = useState('');
  const [isCorrect, setIsCorrect] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Check answer on each change (like original OnChange behavior)
  const checkAnswer = useCallback((value: string) => {
    // Format: XX,XX - check if complete (5 chars with comma)
    const normalized = value.replace('.', ',');

    if (normalized === CORRECT_ANSWER || normalized === "15.24") {
      setIsCorrect(true);
      setFeedback("Oui\nC'est ça !!!");
      addScore(20);
      setVariable('FRANCS', 1);
      onSuccess?.();
    } else if (value.length >= 4) {
      // Only show error when they've entered enough digits
      setFeedback("Non...\nEssaye encore");
    }
  }, [addScore, setVariable, onSuccess]);

  // Handle input - EditMask: '00,00;0;*' means XX,XX format
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let value = e.target.value;

    // Remove non-digits except comma/dot
    value = value.replace(/[^\d,\.]/g, '');

    // Auto-insert comma after 2 digits
    if (value.length === 2 && !value.includes(',') && !value.includes('.')) {
      value = value + ',';
    }

    // Limit to 5 chars (XX,XX)
    if (value.length <= 5) {
      setAnswer(value);
      setFeedback('');

      // Check if answer is complete
      if (value.replace(',', '').replace('.', '').length >= 4) {
        checkAnswer(value);
      }
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      checkAnswer(answer);
    }
  };

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
        {/* lblQuestion: (64, 88) 160x78 */}
        <div style={{
          position: 'absolute',
          left: 64,
          top: 88,
          width: 160,
          height: 78,
          fontSize: 19,
          color: '#000',
          textAlign: 'center',
          wordWrap: 'break-word',
        }}>
          Combien font 100 francs français en euros ?
        </div>

        {/* lblAnswer1: (428, 52) "100 francs font" */}
        <span style={{
          position: 'absolute',
          left: 428,
          top: 52,
          fontSize: 19,
          color: '#000',
        }}>100 francs font</span>

        {/* maskEdit: (428, 90) width 65 */}
        <input
          ref={inputRef}
          type="text"
          value={answer}
          onChange={handleInputChange}
          onKeyPress={handleKeyPress}
          placeholder="00,00"
          disabled={isCorrect}
          style={{
            position: 'absolute',
            left: 428,
            top: 90,
            width: 65,
            height: 23,
            padding: 0,
            fontSize: 19,
            fontFamily: '"Comic Sans MS", cursive, sans-serif',
            color: '#0000ff',
            backgroundColor: '#fff',
            border: 'none',
            textAlign: 'left',
            outline: 'none',
          }}
        />

        {/* lblAnswer2: (500, 88) "euros." */}
        <span style={{
          position: 'absolute',
          left: 500,
          top: 88,
          fontSize: 19,
          color: '#000',
        }}>euros.</span>

        {/* lblComment: (508, 288) 97x89 - Instruction text */}
        <div style={{
          position: 'absolute',
          left: 508,
          top: 288,
          width: 97,
          height: 89,
          fontSize: 19,
          color: '#000',
          textAlign: 'center',
          wordWrap: 'break-word',
        }}>
          Entre les chiffres au clavier.
        </div>

        {/* Feedback area - centered */}
        {feedback && (
          <div style={{
            position: 'absolute',
            left: 250,
            top: 200,
            width: 200,
            textAlign: 'center',
            fontSize: 22,
            color: isCorrect ? '#008000' : '#cc0000',
            fontWeight: 'bold',
            whiteSpace: 'pre-line',
            backgroundColor: 'rgba(255,255,255,0.9)',
            padding: '15px 20px',
            borderRadius: 8,
          }}>
            {feedback}
          </div>
        )}

        {/* btnQuit: (16, 284) 81x101 - Invisible hitbox */}
        <div
          onClick={onClose}
          style={{
            position: 'absolute',
            left: 16,
            top: 284,
            width: 81,
            height: 101,
            cursor: 'pointer',
            // Debug: uncomment to see hitbox
            // backgroundColor: 'rgba(255, 0, 0, 0.2)',
          }}
        />

        {/* lblQuit: (100, 336) "Quitter" - Note: This might be visible on the background */}
        {/* The quit text is likely part of the background image or appears on hover */}
      </div>
    </div>
  );
};

export default FrancsGame;
