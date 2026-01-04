/**
 * Tour Eiffel Mini-Game - Faithful port of pepe.dll
 * Original question: "Combien y a t-il de marches pour monter au dernier étage de la tour Eiffel ?"
 * Answer: 1665 marches
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { useGameStore } from '../../store/gameStore';

interface TourEiffelGameProps {
  onClose: () => void;
  onSuccess?: () => void;
}

// The Eiffel Tower has 1665 steps to the top (fact from original game)
const CORRECT_ANSWER = 1665;

export const TourEiffelGame: React.FC<TourEiffelGameProps> = ({ onClose, onSuccess }) => {
  const addScore = useGameStore((state) => state.addScore);
  const setVariable = useGameStore((state) => state.setVariable);

  const [answer, setAnswer] = useState('');
  const [feedback, setFeedback] = useState<'none' | 'correct' | 'wrong'>('none');
  const [attempts, setAttempts] = useState(0);
  const [showResult, setShowResult] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = useCallback(() => {
    if (!answer.trim()) return;

    const userValue = parseInt(answer, 10);

    if (isNaN(userValue)) {
      setFeedback('wrong');
      return;
    }

    setAttempts((prev) => prev + 1);

    if (userValue === CORRECT_ANSWER) {
      setFeedback('correct');
      setShowResult(true);
      addScore(15);
      setVariable('TOUREIFFEL', 1);
      onSuccess?.();
    } else {
      setFeedback('wrong');
      if (attempts >= 4) {
        setShowResult(true);
      }
    }
  }, [answer, attempts, addScore, setVariable, onSuccess]);

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
    }
  };

  // Styles matching the original Comic Sans MS design
  const overlayStyle: React.CSSProperties = {
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
  };

  const containerStyle: React.CSSProperties = {
    backgroundColor: '#e8dcc8',
    borderRadius: 8,
    padding: 40,
    maxWidth: 520,
    width: '90%',
    textAlign: 'center',
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
    border: '3px solid #8b7355',
    fontFamily: '"Comic Sans MS", cursive, sans-serif',
  };

  const questionLineStyle: React.CSSProperties = {
    fontSize: 20,
    color: '#000',
    marginBottom: 5,
    lineHeight: 1.4,
  };

  const answerRowStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    marginTop: 25,
    marginBottom: 20,
  };

  const labelStyle: React.CSSProperties = {
    fontSize: 18,
    color: '#000',
  };

  const inputStyle: React.CSSProperties = {
    width: '70px',
    padding: '8px 12px',
    fontSize: 18,
    fontFamily: '"Comic Sans MS", cursive, sans-serif',
    color: '#0000ff',
    backgroundColor: '#fff',
    border: 'none',
    textAlign: 'center',
    outline: 'none',
  };

  const quitButtonStyle: React.CSSProperties = {
    marginTop: 20,
    padding: '8px 25px',
    fontSize: 16,
    fontFamily: '"Comic Sans MS", cursive, sans-serif',
    fontWeight: 'bold',
    backgroundColor: '#8b4513',
    color: '#fff',
    border: 'none',
    borderRadius: 4,
    cursor: 'pointer',
  };

  const feedbackStyle: React.CSSProperties = {
    marginTop: 20,
    padding: 15,
    borderRadius: 8,
    fontSize: 16,
    backgroundColor: feedback === 'correct' ? '#4CAF50' : '#f44336',
    color: '#fff',
  };

  return (
    <div style={overlayStyle}>
      <div style={containerStyle}>
        {/* Original multi-line question from pepe.dll DFM */}
        <p style={questionLineStyle}>Combien y a t-il de</p>
        <p style={questionLineStyle}>marches pour monter</p>
        <p style={questionLineStyle}>au dernier étage de la</p>
        <p style={questionLineStyle}>tour Eiffel ?</p>

        {/* Answer input matching original layout */}
        <div style={answerRowStyle}>
          <span style={labelStyle}>Il y a</span>
          <input
            ref={inputRef}
            type="text"
            value={answer}
            onChange={handleInputChange}
            onKeyPress={handleKeyPress}
            placeholder="0000"
            style={inputStyle}
            disabled={showResult}
          />
          <span style={labelStyle}>marches</span>
        </div>

        {/* Submit button */}
        {!showResult && (
          <button
            onClick={handleSubmit}
            style={{
              ...quitButtonStyle,
              backgroundColor: '#2196F3',
              marginBottom: 10,
            }}
          >
            Valider
          </button>
        )}

        {/* Feedback */}
        {feedback !== 'none' && (
          <div style={feedbackStyle}>
            {feedback === 'correct' ? (
              <>Bravo ! La tour Eiffel a bien {CORRECT_ANSWER} marches !</>
            ) : showResult ? (
              <>La bonne réponse était {CORRECT_ANSWER} marches.</>
            ) : (
              <>Ce n'est pas ça ! Essaie encore ! (Essai {attempts}/5)</>
            )}
          </div>
        )}

        {/* Quit button */}
        <button onClick={onClose} style={quitButtonStyle}>
          Quitter
        </button>
      </div>
    </div>
  );
};

export default TourEiffelGame;
