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
 * Original DFM Layout (640x400):
 * - Label1: (272, 24) "Toto est parti en vacances en Italie"
 * - Label2: (280, 56) "avec 2000 francs belges. Sachant"
 * - Label3: (304, 88) "qu'il a dépensé 48000 lires,"
 * - Label4: (304, 120) "combien lui reste-t-il d'euros ?"
 * - Label5: (192, 360) "C'est facile, voyons!"
 * - Label6: (392, 280) "La réponse est"
 * - MaskEdit1: (424, 312) width 33
 * - Label8: (464, 312) "euros..."
 * - Label7: (540, 360) "..." feedback
 * - Image1 (quit): (4, 352) 53x45
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
  const [feedback, setFeedback] = useState('...');
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
      setFeedback('Non...');
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
      setFeedback('...');
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
        {/* Label1: "Toto est parti en vacances en Italie" */}
        <span style={{
          position: 'absolute',
          left: 272,
          top: 24,
          fontSize: 19,
          color: '#000',
        }}>Toto est parti en vacances en Italie</span>

        {/* Label2: "avec 2000 francs belges. Sachant" */}
        <span style={{
          position: 'absolute',
          left: 280,
          top: 56,
          fontSize: 19,
          color: '#000',
        }}>avec 2000 francs belges. Sachant</span>

        {/* Label3: "qu'il a dépensé 48000 lires," */}
        <span style={{
          position: 'absolute',
          left: 304,
          top: 88,
          fontSize: 19,
          color: '#000',
        }}>qu'il a dépensé 48000 lires,</span>

        {/* Label4: "combien lui reste-t-il d'euros ?" */}
        <span style={{
          position: 'absolute',
          left: 304,
          top: 120,
          fontSize: 19,
          color: '#000',
        }}>combien lui reste-t-il d'euros ?</span>

        {/* Label5: "C'est facile, voyons!" */}
        <span style={{
          position: 'absolute',
          left: 192,
          top: 360,
          fontSize: 19,
          color: '#000',
        }}>C'est facile, voyons!</span>

        {/* Label6: "La réponse est" */}
        <span style={{
          position: 'absolute',
          left: 392,
          top: 280,
          fontSize: 19,
          color: '#000',
        }}>La réponse est</span>

        {/* MaskEdit1: Input field at (424, 312) */}
        <input
          ref={inputRef}
          type="text"
          value={answer}
          onChange={handleInputChange}
          onKeyPress={handleKeyPress}
          disabled={showResult}
          style={{
            position: 'absolute',
            left: 424,
            top: 312,
            width: 33,
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

        {/* Label8: "euros..." */}
        <span style={{
          position: 'absolute',
          left: 464,
          top: 312,
          fontSize: 19,
          color: '#000',
        }}>euros...</span>

        {/* Label7: Feedback "..." at (540, 360) */}
        <span style={{
          position: 'absolute',
          left: 540,
          top: 360,
          fontSize: 19,
          color: '#000',
        }}>{feedback}</span>

        {/* Image1: Quit button hitbox at (4, 352) 53x45 */}
        <div
          onClick={onClose}
          style={{
            position: 'absolute',
            left: 4,
            top: 352,
            width: 53,
            height: 45,
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
            top: 180,
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
      </div>
    </div>
  );
};

export default ProblemeGame;
