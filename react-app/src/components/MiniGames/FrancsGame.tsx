/**
 * Francs Mini-Game - Faithful port of francs.dll
 * Original: "Combien font 100 francs français en euros ?"
 * Answer: 100 / 6.55957 = 15,24 EUR
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { useGameStore } from '../../store/gameStore';

interface FrancsGameProps {
  onClose: () => void;
  onSuccess?: () => void;
}

// Exact conversion rate from French Franc to Euro (fixed January 1, 1999)
const FRF_TO_EUR = 6.55957;

// The original question from francs.dll DFM
const QUESTION_AMOUNT = 100;
const CORRECT_ANSWER = (QUESTION_AMOUNT / FRF_TO_EUR).toFixed(2); // "15.24"

export const FrancsGame: React.FC<FrancsGameProps> = ({ onClose, onSuccess }) => {
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

    // Normalize input: replace comma with dot for parsing
    const normalizedAnswer = answer.replace(',', '.');
    const userValue = parseFloat(normalizedAnswer);
    const correctValue = parseFloat(CORRECT_ANSWER);

    if (isNaN(userValue)) {
      setFeedback('wrong');
      return;
    }

    setAttempts((prev) => prev + 1);

    // Check if answer is within 0.01 tolerance (for rounding)
    if (Math.abs(userValue - correctValue) <= 0.01) {
      setFeedback('correct');
      setShowResult(true);
      addScore(10);
      setVariable('JUSTEPRIXOK', 1);
      onSuccess?.();
    } else {
      setFeedback('wrong');
      if (attempts >= 4) {
        // After 5 attempts, show the correct answer
        setShowResult(true);
      }
    }
  }, [answer, attempts, addScore, setVariable, onSuccess]);

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSubmit();
    }
  };

  // Prevent non-numeric input except comma and dot
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    // Only allow digits, comma, and dot - matching original EditMask: 00,00;0;*
    if (/^[\d,\.]*$/.test(value) && value.length <= 5) {
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
    backgroundColor: '#e8dcc8', // Parchment-like background
    borderRadius: 8,
    padding: 40,
    maxWidth: 500,
    width: '90%',
    textAlign: 'center',
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
    border: '3px solid #8b7355',
    fontFamily: '"Comic Sans MS", cursive, sans-serif',
  };

  const questionStyle: React.CSSProperties = {
    fontSize: 22,
    color: '#000',
    marginBottom: 30,
    lineHeight: 1.4,
  };

  const answerRowStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    marginBottom: 20,
  };

  const labelStyle: React.CSSProperties = {
    fontSize: 18,
    color: '#000',
  };

  const inputStyle: React.CSSProperties = {
    width: '80px',
    padding: '8px 12px',
    fontSize: 18,
    fontFamily: '"Comic Sans MS", cursive, sans-serif',
    color: '#0000ff', // Blue text like original
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

  const commentStyle: React.CSSProperties = {
    fontSize: 14,
    color: '#666',
    marginBottom: 20,
    fontStyle: 'italic',
  };

  return (
    <div style={overlayStyle}>
      <div style={containerStyle}>
        {/* Original instruction */}
        <p style={commentStyle}>Entre les chiffres au clavier.</p>

        {/* Original question from DFM */}
        <p style={questionStyle}>
          Combien font {QUESTION_AMOUNT} francs français en euros ?
        </p>

        {/* Answer input matching original layout */}
        <div style={answerRowStyle}>
          <span style={labelStyle}>{QUESTION_AMOUNT} francs font</span>
          <input
            ref={inputRef}
            type="text"
            value={answer}
            onChange={handleInputChange}
            onKeyPress={handleKeyPress}
            placeholder="00,00"
            style={inputStyle}
            disabled={showResult}
          />
          <span style={labelStyle}>euros.</span>
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
              <>Bravo ! La bonne réponse est bien {CORRECT_ANSWER.replace('.', ',')} euros !</>
            ) : showResult ? (
              <>La bonne réponse était {CORRECT_ANSWER.replace('.', ',')} euros.</>
            ) : (
              <>Ce n'est pas la bonne réponse. Essaie encore ! (Essai {attempts}/5)</>
            )}
          </div>
        )}

        {/* Quit button - always visible like original */}
        <button onClick={onClose} style={quitButtonStyle}>
          Quitter
        </button>
      </div>
    </div>
  );
};

export default FrancsGame;
