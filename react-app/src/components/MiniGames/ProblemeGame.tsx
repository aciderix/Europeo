/**
 * Probleme Mini-Game - Faithful port of probleme.dll
 * Original question: "Toto est parti en vacances en Italie avec 2000 francs belges.
 * Sachant qu'il a dépensé 48000 lires, combien lui reste-t-il d'euros ?"
 *
 * Calculation:
 * - 2000 BEF = 2000 / 40.3399 = 49.58 EUR
 * - 48000 ITL = 48000 / 1936.27 = 24.79 EUR
 * - Remaining: 49.58 - 24.79 = 24.79 ≈ 25 EUR
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { useGameStore } from '../../store/gameStore';

interface ProblemeGameProps {
  onClose: () => void;
  onSuccess?: () => void;
}

// Historical conversion rates (fixed January 1, 1999)
const BEF_TO_EUR = 40.3399; // Belgian Franc
const ITL_TO_EUR = 1936.27; // Italian Lira

// Problem values from original DFM
const INITIAL_BEF = 2000;
const SPENT_ITL = 48000;

// Calculate correct answer
const initialEur = INITIAL_BEF / BEF_TO_EUR; // 49.58 EUR
const spentEur = SPENT_ITL / ITL_TO_EUR; // 24.79 EUR
const CORRECT_ANSWER = Math.round(initialEur - spentEur); // 25 EUR

export const ProblemeGame: React.FC<ProblemeGameProps> = ({ onClose, onSuccess }) => {
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

    // Accept answer within +/- 1 for rounding tolerance
    if (Math.abs(userValue - CORRECT_ANSWER) <= 1) {
      setFeedback('correct');
      setShowResult(true);
      addScore(20);
      setVariable('PROBLEME', 1);
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

  // Only allow 2 digits - matching original EditMask: 00;0;*
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    if (/^\d*$/.test(value) && value.length <= 2) {
      setAnswer(value);
    }
  };

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
    maxWidth: 550,
    width: '90%',
    textAlign: 'center',
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
    border: '3px solid #8b7355',
    fontFamily: '"Comic Sans MS", cursive, sans-serif',
  };

  const questionLineStyle: React.CSSProperties = {
    fontSize: 18,
    color: '#000',
    marginBottom: 5,
    lineHeight: 1.4,
  };

  const hintStyle: React.CSSProperties = {
    fontSize: 16,
    color: '#666',
    marginTop: 15,
    fontStyle: 'italic',
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
    width: '50px',
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
        {/* Original multi-line question from probleme.dll DFM */}
        <p style={questionLineStyle}>Toto est parti en vacances en Italie</p>
        <p style={questionLineStyle}>avec 2000 francs belges. Sachant</p>
        <p style={questionLineStyle}>qu'il a dépensé 48000 lires,</p>
        <p style={questionLineStyle}>combien lui reste-t-il d'euros ?</p>

        <p style={hintStyle}>C'est facile, voyons!</p>

        {/* Answer input matching original layout */}
        <div style={answerRowStyle}>
          <span style={labelStyle}>La réponse est</span>
          <input
            ref={inputRef}
            type="text"
            value={answer}
            onChange={handleInputChange}
            onKeyPress={handleKeyPress}
            placeholder="00"
            style={inputStyle}
            disabled={showResult}
          />
          <span style={labelStyle}>euros...</span>
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
              <>
                Bravo ! Il reste bien environ {CORRECT_ANSWER} euros à Toto !
                <br />
                <small style={{ fontSize: 12, opacity: 0.8 }}>
                  ({INITIAL_BEF} BEF = {initialEur.toFixed(2)}€ - {SPENT_ITL} ITL = {spentEur.toFixed(2)}€)
                </small>
              </>
            ) : showResult ? (
              <>
                La bonne réponse était {CORRECT_ANSWER} euros.
                <br />
                <small style={{ fontSize: 12, opacity: 0.8 }}>
                  {INITIAL_BEF} BEF ÷ {BEF_TO_EUR} = {initialEur.toFixed(2)}€
                  <br />
                  {SPENT_ITL} ITL ÷ {ITL_TO_EUR} = {spentEur.toFixed(2)}€
                </small>
              </>
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

export default ProblemeGame;
