/**
 * Tour Eiffel Mini-Game - Faithful port of pepe.dll
 * Original question: "Combien y a t-il de marches pour monter au dernier étage de la tour Eiffel ?"
 * Answer: 1652 marches (from STRINGTABLE resource)
 *
 * Original DFM Layout (640x400):
 * - Label3: (400, 88) "Combien y a t-il de"
 * - Label4: (376, 120) "marches pour monter"
 * - Label5: (376, 152) "au dernier étage de la"
 * - Label6: (416, 184) "tour Eiffel ?"
 * - Label1: (424, 224) "Il y a"
 * - maskEdit: (488, 224) width 49
 * - Label2: (456, 256) "marches"
 * - lblComment: (376, 344) 169x57 - hint area
 * - btnQuit: (8, 296) 73x97 - quit hitbox
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
      setHint('Il me semble\nqu\'il y en a moins.');
    } else {
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
        {/* Label3: "Combien y a t-il de" */}
        <span style={{
          position: 'absolute',
          left: 400,
          top: 88,
          fontSize: 19,
          color: '#000',
        }}>Combien y a t-il de</span>

        {/* Label4: "marches pour monter" */}
        <span style={{
          position: 'absolute',
          left: 376,
          top: 120,
          fontSize: 19,
          color: '#000',
        }}>marches pour monter</span>

        {/* Label5: "au dernier étage de la" */}
        <span style={{
          position: 'absolute',
          left: 376,
          top: 152,
          fontSize: 19,
          color: '#000',
        }}>au dernier étage de la</span>

        {/* Label6: "tour Eiffel ?" */}
        <span style={{
          position: 'absolute',
          left: 416,
          top: 184,
          fontSize: 19,
          color: '#000',
        }}>tour Eiffel ?</span>

        {/* Label1: "Il y a" */}
        <span style={{
          position: 'absolute',
          left: 424,
          top: 224,
          fontSize: 19,
          color: '#000',
        }}>Il y a</span>

        {/* maskEdit: Input field at (488, 224) */}
        <input
          ref={inputRef}
          type="text"
          value={answer}
          onChange={handleInputChange}
          onKeyPress={handleKeyPress}
          disabled={showResult}
          style={{
            position: 'absolute',
            left: 488,
            top: 224,
            width: 49,
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

        {/* Label2: "marches" */}
        <span style={{
          position: 'absolute',
          left: 456,
          top: 256,
          fontSize: 19,
          color: '#000',
        }}>marches</span>

        {/* lblComment: Hint area at (376, 344) 169x57 */}
        <div style={{
          position: 'absolute',
          left: 376,
          top: 344,
          width: 169,
          height: 57,
          textAlign: 'center',
          fontSize: 19,
          color: '#000',
          whiteSpace: 'pre-line',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
          {hint}
        </div>

        {/* btnQuit: Quit button hitbox at (8, 296) 73x97 */}
        <div
          onClick={onClose}
          style={{
            position: 'absolute',
            left: 8,
            top: 296,
            width: 73,
            height: 97,
            cursor: 'pointer',
            // Debug: uncomment to see hitbox
            // backgroundColor: 'rgba(255, 0, 0, 0.2)',
          }}
        />

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
          }}>
            Bravo ! {CORRECT_ANSWER} marches !
          </div>
        )}
      </div>
    </div>
  );
};

export default TourEiffelGame;
