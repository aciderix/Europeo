/**
 * Memory Mini-Game - Faithful port of Memory.dll
 * Original: Card matching game with timer ("TEMPS")
 * Font: Village Square
 */

import React, { useState, useCallback, useEffect, useRef } from 'react';
import { useGameStore } from '../../store/gameStore';

interface MemoryGameProps {
  onClose: () => void;
  onSuccess?: () => void;
}

// European country flags/symbols for the memory cards
const CARD_PAIRS = [
  { id: 1, symbol: '🇫🇷', name: 'France' },
  { id: 2, symbol: '🇩🇪', name: 'Allemagne' },
  { id: 3, symbol: '🇮🇹', name: 'Italie' },
  { id: 4, symbol: '🇪🇸', name: 'Espagne' },
  { id: 5, symbol: '🇧🇪', name: 'Belgique' },
  { id: 6, symbol: '🇳🇱', name: 'Pays-Bas' },
  { id: 7, symbol: '🇬🇷', name: 'Grèce' },
  { id: 8, symbol: '🇵🇹', name: 'Portugal' },
];

interface Card {
  uniqueId: number;
  pairId: number;
  symbol: string;
  name: string;
  isFlipped: boolean;
  isMatched: boolean;
}

function shuffleArray<T>(array: T[]): T[] {
  const arr = [...array];
  for (let i = arr.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}

function createCards(): Card[] {
  const cards: Card[] = [];
  let uniqueId = 0;

  // Create pairs
  CARD_PAIRS.forEach((pair) => {
    cards.push({
      uniqueId: uniqueId++,
      pairId: pair.id,
      symbol: pair.symbol,
      name: pair.name,
      isFlipped: false,
      isMatched: false,
    });
    cards.push({
      uniqueId: uniqueId++,
      pairId: pair.id,
      symbol: pair.symbol,
      name: pair.name,
      isFlipped: false,
      isMatched: false,
    });
  });

  return shuffleArray(cards);
}

export const MemoryGame: React.FC<MemoryGameProps> = ({ onClose, onSuccess }) => {
  const addScore = useGameStore((state) => state.addScore);
  const setVariable = useGameStore((state) => state.setVariable);

  const [cards, setCards] = useState<Card[]>(() => createCards());
  const [flippedCards, setFlippedCards] = useState<number[]>([]);
  const [matchedPairs, setMatchedPairs] = useState(0);
  const [moves, setMoves] = useState(0);
  const [time, setTime] = useState(0);
  const [gameOver, setGameOver] = useState(false);
  const [isChecking, setIsChecking] = useState(false);

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Start timer
  useEffect(() => {
    timerRef.current = setInterval(() => {
      setTime((prev) => prev + 1);
    }, 1000);

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, []);

  // Check for match when two cards are flipped
  useEffect(() => {
    if (flippedCards.length === 2) {
      setIsChecking(true);
      setMoves((prev) => prev + 1);

      const [first, second] = flippedCards;
      const firstCard = cards.find((c) => c.uniqueId === first);
      const secondCard = cards.find((c) => c.uniqueId === second);

      if (firstCard && secondCard && firstCard.pairId === secondCard.pairId) {
        // Match found!
        setTimeout(() => {
          setCards((prev) =>
            prev.map((c) =>
              c.uniqueId === first || c.uniqueId === second
                ? { ...c, isMatched: true }
                : c
            )
          );
          setMatchedPairs((prev) => prev + 1);
          setFlippedCards([]);
          setIsChecking(false);
        }, 500);
      } else {
        // No match - flip back
        setTimeout(() => {
          setCards((prev) =>
            prev.map((c) =>
              c.uniqueId === first || c.uniqueId === second
                ? { ...c, isFlipped: false }
                : c
            )
          );
          setFlippedCards([]);
          setIsChecking(false);
        }, 1000);
      }
    }
  }, [flippedCards, cards]);

  // Check for game completion
  useEffect(() => {
    if (matchedPairs === CARD_PAIRS.length && matchedPairs > 0) {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      setGameOver(true);

      // Calculate score based on time and moves
      const baseScore = 50;
      const timeBonus = Math.max(0, 30 - Math.floor(time / 10));
      const moveBonus = Math.max(0, 20 - moves);
      const totalScore = baseScore + timeBonus + moveBonus;

      addScore(totalScore);
      setVariable('MEMORY', 1);
      onSuccess?.();
    }
  }, [matchedPairs, time, moves, addScore, setVariable, onSuccess]);

  const handleCardClick = useCallback(
    (uniqueId: number) => {
      if (isChecking) return;

      const card = cards.find((c) => c.uniqueId === uniqueId);
      if (!card || card.isFlipped || card.isMatched) return;
      if (flippedCards.length >= 2) return;

      setCards((prev) =>
        prev.map((c) => (c.uniqueId === uniqueId ? { ...c, isFlipped: true } : c))
      );
      setFlippedCards((prev) => [...prev, uniqueId]);
    },
    [cards, flippedCards, isChecking]
  );

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
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
    backgroundColor: '#1a3a1a',
    borderRadius: 12,
    padding: 30,
    maxWidth: 500,
    width: '95%',
    textAlign: 'center',
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.5)',
    border: '4px solid #2d5a2d',
  };

  const headerStyle: React.CSSProperties = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
    padding: '0 10px',
  };

  const timerStyle: React.CSSProperties = {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#00ff00', // Lime color from original DFM
    fontFamily: 'monospace',
  };

  const gridStyle: React.CSSProperties = {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: 10,
    padding: 10,
  };

  const cardStyle = (card: Card): React.CSSProperties => ({
    aspectRatio: '1',
    backgroundColor: card.isFlipped || card.isMatched ? '#fff' : '#2196F3',
    borderRadius: 8,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: 32,
    cursor: card.isMatched ? 'default' : 'pointer',
    transition: 'transform 0.3s, background-color 0.3s',
    transform: card.isFlipped || card.isMatched ? 'rotateY(180deg)' : 'rotateY(0)',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.3)',
    opacity: card.isMatched ? 0.7 : 1,
    border: card.isMatched ? '2px solid #4CAF50' : '2px solid transparent',
  });

  const quitButtonStyle: React.CSSProperties = {
    marginTop: 20,
    padding: '10px 30px',
    fontSize: 16,
    fontWeight: 'bold',
    backgroundColor: '#c0392b',
    color: '#fff',
    border: 'none',
    borderRadius: 6,
    cursor: 'pointer',
  };

  if (gameOver) {
    return (
      <div style={overlayStyle}>
        <div style={containerStyle}>
          <h2 style={{ color: '#00ff00', fontSize: 28, marginBottom: 20 }}>
            Félicitations !
          </h2>
          <p style={{ color: '#fff', fontSize: 18, marginBottom: 10 }}>
            Tu as trouvé toutes les paires !
          </p>
          <div style={{ color: '#ccc', fontSize: 16, marginBottom: 20 }}>
            <p>TEMPS: {formatTime(time)}</p>
            <p>Coups: {moves}</p>
          </div>
          <button onClick={onClose} style={quitButtonStyle}>
            Fermer
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={overlayStyle}>
      <div style={containerStyle}>
        <div style={headerStyle}>
          <span style={{ color: '#fff', fontSize: 16 }}>Coups: {moves}</span>
          <span style={timerStyle}>TEMPS: {formatTime(time)}</span>
          <span style={{ color: '#fff', fontSize: 16 }}>
            Paires: {matchedPairs}/{CARD_PAIRS.length}
          </span>
        </div>

        <div style={gridStyle}>
          {cards.map((card) => (
            <div
              key={card.uniqueId}
              style={cardStyle(card)}
              onClick={() => handleCardClick(card.uniqueId)}
            >
              {(card.isFlipped || card.isMatched) ? card.symbol : '?'}
            </div>
          ))}
        </div>

        <button onClick={onClose} style={quitButtonStyle}>
          Quitter
        </button>
      </div>
    </div>
  );
};

export default MemoryGame;
