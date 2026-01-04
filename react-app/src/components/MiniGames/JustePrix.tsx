/**
 * Juste Prix Mini-Game
 * A "Price is Right" style guessing game for Euro conversion
 */

import React, { useState, useCallback } from 'react';
import { useGameStore } from '../../store/gameStore';

interface JustePrixProps {
  countryId: string;
  onClose: () => void;
  onWin?: (points: number) => void;
}

// Sample products with prices in Euros
const PRODUCTS = [
  { name: 'Baguette', price: 1.2, image: 'baguette' },
  { name: 'Café', price: 2.5, image: 'cafe' },
  { name: 'Journal', price: 1.8, image: 'journal' },
  { name: 'Croissant', price: 1.5, image: 'croissant' },
  { name: 'Pizza', price: 12, image: 'pizza' },
  { name: 'Bière', price: 4.5, image: 'biere' },
  { name: 'Glace', price: 3, image: 'glace' },
  { name: 'Sandwich', price: 6, image: 'sandwich' },
  { name: 'Chocolat', price: 2, image: 'chocolat' },
  { name: 'Fromage', price: 8, image: 'fromage' },
];

// Conversion rates (historical rates around Euro introduction)
const CONVERSION_RATES: Record<string, { currency: string; rate: number; symbol: string }> = {
  allem: { currency: 'Deutsche Mark', rate: 1.95583, symbol: 'DM' },
  angl: { currency: 'Livre Sterling', rate: 0.70, symbol: '£' },
  autr: { currency: 'Schilling', rate: 13.7603, symbol: 'ATS' },
  belge: { currency: 'Franc Belge', rate: 40.3399, symbol: 'BEF' },
  danem: { currency: 'Couronne Danoise', rate: 7.46, symbol: 'DKK' },
  ecosse: { currency: 'Livre Sterling', rate: 0.70, symbol: '£' },
  espa: { currency: 'Peseta', rate: 166.386, symbol: 'ESP' },
  finlan: { currency: 'Markka', rate: 5.94573, symbol: 'FIM' },
  france: { currency: 'Franc Français', rate: 6.55957, symbol: 'FF' },
  grece: { currency: 'Drachme', rate: 340.75, symbol: 'GRD' },
  holl: { currency: 'Florin', rate: 2.20371, symbol: 'NLG' },
  irland: { currency: 'Livre Irlandaise', rate: 0.787564, symbol: 'IEP' },
  italie: { currency: 'Lire', rate: 1936.27, symbol: 'ITL' },
  portu: { currency: 'Escudo', rate: 200.482, symbol: 'PTE' },
  suede: { currency: 'Couronne Suédoise', rate: 9.50, symbol: 'SEK' },
};

export const JustePrix: React.FC<JustePrixProps> = ({ countryId, onClose, onWin }) => {
  const addScore = useGameStore((state) => state.addScore);
  const setVariable = useGameStore((state) => state.setVariable);

  const [currentProduct, setCurrentProduct] = useState(() =>
    PRODUCTS[Math.floor(Math.random() * PRODUCTS.length)]
  );
  const [guess, setGuess] = useState('');
  const [feedback, setFeedback] = useState<'none' | 'higher' | 'lower' | 'correct'>('none');
  const [attempts, setAttempts] = useState(0);
  const [gameOver, setGameOver] = useState(false);
  const [score, setScore] = useState(0);
  const [questionsAnswered, setQuestionsAnswered] = useState(0);

  const conversionInfo = CONVERSION_RATES[countryId] || CONVERSION_RATES.france;
  const priceInLocalCurrency = currentProduct.price * conversionInfo.rate;

  const handleGuess = useCallback(() => {
    const guessValue = parseFloat(guess);
    if (isNaN(guessValue) || guessValue <= 0) {
      return;
    }

    setAttempts((prev) => prev + 1);

    const tolerance = currentProduct.price * 0.1; // 10% tolerance

    if (Math.abs(guessValue - currentProduct.price) <= tolerance) {
      setFeedback('correct');
      const points = Math.max(10 - attempts * 2, 2);
      setScore((prev) => prev + points);
      addScore(points);
      setVariable('JUSTEPRIXOK', 1);

      setTimeout(() => {
        setQuestionsAnswered((prev) => prev + 1);
        if (questionsAnswered >= 4) {
          setGameOver(true);
          onWin?.(score + points);
        } else {
          // Next product
          setCurrentProduct(PRODUCTS[Math.floor(Math.random() * PRODUCTS.length)]);
          setGuess('');
          setFeedback('none');
          setAttempts(0);
        }
      }, 1500);
    } else if (guessValue < currentProduct.price) {
      setFeedback('higher');
    } else {
      setFeedback('lower');
    }

    // Game over after 5 wrong attempts
    if (attempts >= 4 && feedback !== 'correct') {
      setTimeout(() => {
        setQuestionsAnswered((prev) => prev + 1);
        if (questionsAnswered >= 4) {
          setGameOver(true);
        } else {
          setCurrentProduct(PRODUCTS[Math.floor(Math.random() * PRODUCTS.length)]);
          setGuess('');
          setFeedback('none');
          setAttempts(0);
        }
      }, 1500);
    }
  }, [guess, currentProduct, attempts, feedback, questionsAnswered, score, addScore, setVariable, onWin]);

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleGuess();
    }
  };

  const overlayStyle: React.CSSProperties = {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.85)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
  };

  const containerStyle: React.CSSProperties = {
    backgroundColor: '#1a1a2e',
    borderRadius: 15,
    padding: 30,
    maxWidth: 500,
    width: '90%',
    color: '#fff',
    textAlign: 'center',
    boxShadow: '0 10px 40px rgba(0, 0, 0, 0.5)',
  };

  const inputStyle: React.CSSProperties = {
    width: '150px',
    padding: '12px 20px',
    fontSize: 24,
    borderRadius: 8,
    border: '2px solid #3498db',
    backgroundColor: '#2c3e50',
    color: '#fff',
    textAlign: 'center',
    marginRight: 10,
  };

  const buttonStyle: React.CSSProperties = {
    padding: '12px 30px',
    fontSize: 18,
    backgroundColor: '#27ae60',
    border: 'none',
    borderRadius: 8,
    color: '#fff',
    cursor: 'pointer',
  };

  if (gameOver) {
    return (
      <div style={overlayStyle}>
        <div style={containerStyle}>
          <h2 style={{ color: '#f1c40f', fontSize: 32 }}>Jeu Terminé!</h2>
          <div style={{ fontSize: 64, margin: '20px 0' }}>
            {score >= 30 ? '🏆' : score >= 20 ? '🎉' : '👍'}
          </div>
          <p style={{ fontSize: 24 }}>Score: {score} points</p>
          <button
            onClick={onClose}
            style={{ ...buttonStyle, marginTop: 20, backgroundColor: '#3498db' }}
          >
            Fermer
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={overlayStyle}>
      <div style={containerStyle}>
        <h2 style={{ color: '#f1c40f', marginTop: 0 }}>Le Juste Prix</h2>

        <div style={{
          backgroundColor: '#2c3e50',
          padding: 20,
          borderRadius: 10,
          margin: '20px 0'
        }}>
          <div style={{ fontSize: 48, marginBottom: 10 }}>🛒</div>
          <h3 style={{ color: '#ecf0f1', margin: '10px 0' }}>{currentProduct.name}</h3>
          <p style={{ color: '#bdc3c7', fontSize: 14 }}>
            Prix en {conversionInfo.currency}: <strong>{priceInLocalCurrency.toFixed(2)} {conversionInfo.symbol}</strong>
          </p>
          <p style={{ color: '#f39c12', fontSize: 18, marginTop: 15 }}>
            Quel est le prix en Euros?
          </p>
        </div>

        <div style={{ margin: '20px 0' }}>
          <input
            type="number"
            step="0.1"
            min="0"
            value={guess}
            onChange={(e) => setGuess(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="€"
            style={inputStyle}
            autoFocus
          />
          <button onClick={handleGuess} style={buttonStyle}>
            Valider
          </button>
        </div>

        {feedback !== 'none' && (
          <div style={{
            padding: 15,
            borderRadius: 8,
            backgroundColor: feedback === 'correct' ? '#27ae60' : '#e74c3c',
            marginBottom: 15
          }}>
            {feedback === 'correct' && '✅ Correct! Bien joué!'}
            {feedback === 'higher' && '⬆️ C\'est plus!'}
            {feedback === 'lower' && '⬇️ C\'est moins!'}
          </div>
        )}

        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          color: '#bdc3c7',
          fontSize: 14,
          marginTop: 20
        }}>
          <span>Question {questionsAnswered + 1}/5</span>
          <span>Essais: {attempts}/5</span>
          <span>Score: {score}</span>
        </div>

        <button
          onClick={onClose}
          style={{
            ...buttonStyle,
            marginTop: 20,
            backgroundColor: '#7f8c8d',
            padding: '8px 20px',
            fontSize: 14
          }}
        >
          Quitter
        </button>
      </div>
    </div>
  );
};

export default JustePrix;
