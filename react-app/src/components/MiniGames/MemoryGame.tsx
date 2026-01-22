/**
 * Memory Mini-Game - Faithful port of Memory.dll
 * Original: Card matching game with timer
 *
 * Original DFM Layout (640x400):
 * - Fond (background): Image_1.bmp
 * - Grid 4x4 at positions starting (128, 104)
 * - Card size: 65x45 pixels
 * - Column X: 128, 200, 272, 344 (step 72)
 * - Row Y: 104, 152, 200, 248 (step 48)
 * - Image_2 to Image_17: Card backs (clickable covers)
 * - Image_18 to Image_25: 8 unique symbols for pairs
 * - TimeLbl: (124, 44) "TEMPS" - Font: Village Square, Color: clLime
 * - CommentLbl: (440, 200) - Font: Serpentine, Color: clBlue
 * - Matched pairs shown at bottom row (112-472, 340-348)
 * - CacheTmr: 700ms delay before hiding unmatched cards
 */

import React, { useState, useCallback, useEffect, useRef } from 'react';
import { useGameStore } from '../../store/gameStore';

interface MemoryGameProps {
  onClose: () => void;
  onSuccess?: () => void;
}

// Asset paths
const BACKGROUND_IMAGE = '/assets/minigames/memory/Image_1.png';
const CARD_BACK = '/assets/minigames/memory/Image_2.png'; // All card backs use same image

// The 8 unique symbol images (Image_18 to Image_25)
const SYMBOL_IMAGES = [
  '/assets/minigames/memory/Image_18.png',
  '/assets/minigames/memory/Image_19.png',
  '/assets/minigames/memory/Image_20.png',
  '/assets/minigames/memory/Image_21.png',
  '/assets/minigames/memory/Image_22.png',
  '/assets/minigames/memory/Image_23.png',
  '/assets/minigames/memory/Image_24.png',
  '/assets/minigames/memory/Image_25.png',
];

// Grid positions from DFM (4 columns x 4 rows = 16 cards)
const GRID_POSITIONS: { x: number; y: number }[] = [
  // Row 1 (y=104)
  { x: 128, y: 104 }, { x: 200, y: 104 }, { x: 272, y: 104 }, { x: 344, y: 104 },
  // Row 2 (y=152)
  { x: 128, y: 152 }, { x: 200, y: 152 }, { x: 272, y: 152 }, { x: 344, y: 152 },
  // Row 3 (y=200)
  { x: 128, y: 200 }, { x: 200, y: 200 }, { x: 272, y: 200 }, { x: 344, y: 200 },
  // Row 4 (y=248)
  { x: 128, y: 248 }, { x: 200, y: 248 }, { x: 272, y: 248 }, { x: 344, y: 248 },
];

// Card dimensions from DFM
const CARD_WIDTH = 65;
const CARD_HEIGHT = 45;

// Matched pairs display positions at bottom (from DFM Image33-Image40)
const MATCHED_DISPLAY_POSITIONS = [
  { x: 112, y: 340, w: 50, h: 45 },  // Image_18
  { x: 164, y: 340, w: 51, h: 45 },  // Image_19
  { x: 220, y: 348, w: 36, h: 39 },  // Image_20
  { x: 260, y: 344, w: 52, h: 43 },  // Image_21
  { x: 316, y: 344, w: 41, h: 43 },  // Image_22
  { x: 364, y: 348, w: 50, h: 32 },  // Image_23
  { x: 420, y: 348, w: 50, h: 28 },  // Image_24
  { x: 472, y: 344, w: 39, h: 37 },  // Image_25
];

interface Card {
  uniqueId: number;
  pairId: number;  // 0-7 for the 8 pairs
  symbolImage: string;
  gridIndex: number;
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

  // Create 8 pairs (16 cards total)
  for (let pairId = 0; pairId < 8; pairId++) {
    const symbolImage = SYMBOL_IMAGES[pairId];
    // Each pair has 2 cards
    cards.push({
      uniqueId: uniqueId++,
      pairId,
      symbolImage,
      gridIndex: -1, // Will be set after shuffle
      isFlipped: false,
      isMatched: false,
    });
    cards.push({
      uniqueId: uniqueId++,
      pairId,
      symbolImage,
      gridIndex: -1,
      isFlipped: false,
      isMatched: false,
    });
  }

  // Shuffle and assign grid positions
  const shuffled = shuffleArray(cards);
  shuffled.forEach((card, index) => {
    card.gridIndex = index;
  });

  return shuffled;
}

export const MemoryGame: React.FC<MemoryGameProps> = ({ onClose, onSuccess }) => {
  const addScore = useGameStore((state) => state.addScore);
  const setVariable = useGameStore((state) => state.setVariable);

  const [cards, setCards] = useState<Card[]>(() => createCards());
  const [flippedCards, setFlippedCards] = useState<number[]>([]);
  const [matchedPairIds, setMatchedPairIds] = useState<number[]>([]);
  const [time, setTime] = useState(0);
  const [gameOver, setGameOver] = useState(false);
  const [isChecking, setIsChecking] = useState(false);
  const [comment, setComment] = useState('');

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

      const [first, second] = flippedCards;
      const firstCard = cards.find((c) => c.uniqueId === first);
      const secondCard = cards.find((c) => c.uniqueId === second);

      if (firstCard && secondCard && firstCard.pairId === secondCard.pairId) {
        // Match found!
        setComment('Bravo !');
        setTimeout(() => {
          setCards((prev) =>
            prev.map((c) =>
              c.uniqueId === first || c.uniqueId === second
                ? { ...c, isMatched: true }
                : c
            )
          );
          setMatchedPairIds((prev) => [...prev, firstCard.pairId]);
          setFlippedCards([]);
          setIsChecking(false);
          setComment('');
        }, 500);
      } else {
        // No match - CacheTmr interval is 700ms in original
        setComment('Non...');
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
          setComment('');
        }, 700);
      }
    }
  }, [flippedCards, cards]);

  // Check for game completion
  useEffect(() => {
    if (matchedPairIds.length === 8 && matchedPairIds.length > 0) {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      setGameOver(true);
      setComment('Gagné !');

      // Calculate score based on time
      const baseScore = 50;
      const timeBonus = Math.max(0, 30 - Math.floor(time / 10));
      const totalScore = baseScore + timeBonus;

      addScore(totalScore);
      setVariable('MEMORY', 1);
      onSuccess?.();
    }
  }, [matchedPairIds, time, addScore, setVariable, onSuccess]);

  const handleCardClick = useCallback(
    (uniqueId: number) => {
      if (isChecking || gameOver) return;

      const card = cards.find((c) => c.uniqueId === uniqueId);
      if (!card || card.isFlipped || card.isMatched) return;
      if (flippedCards.length >= 2) return;

      setCards((prev) =>
        prev.map((c) => (c.uniqueId === uniqueId ? { ...c, isFlipped: true } : c))
      );
      setFlippedCards((prev) => [...prev, uniqueId]);
    },
    [cards, flippedCards, isChecking, gameOver]
  );

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
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
      }}>
        {/* TimeLbl: (124, 44) "TEMPS" - Village Square font, lime color */}
        <div style={{
          position: 'absolute',
          left: 124,
          top: 44,
          fontSize: 19,
          fontFamily: '"Century Gothic", "Arial", sans-serif', // Village Square fallback
          color: '#00FF00', // clLime
          fontWeight: 'bold',
        }}>
          TEMPS {formatTime(time)}
        </div>

        {/* CommentLbl: (440, 200) - Serpentine font, blue color */}
        <div style={{
          position: 'absolute',
          left: 440,
          top: 200,
          width: 145,
          height: 21,
          fontSize: 19,
          fontFamily: '"Century Gothic", "Arial", sans-serif', // Serpentine fallback
          color: '#0000FF', // clBlue
          textAlign: 'center',
        }}>
          {comment}
        </div>

        {/* Card grid - 16 cards at exact DFM positions */}
        {cards.map((card) => {
          const pos = GRID_POSITIONS[card.gridIndex];
          return (
            <div
              key={card.uniqueId}
              onClick={() => handleCardClick(card.uniqueId)}
              style={{
                position: 'absolute',
                left: pos.x,
                top: pos.y,
                width: CARD_WIDTH,
                height: CARD_HEIGHT,
                cursor: card.isMatched ? 'default' : 'pointer',
                opacity: card.isMatched ? 0 : 1, // Matched cards disappear
              }}
            >
              {/* Show card back or symbol */}
              <img
                src={card.isFlipped || card.isMatched ? card.symbolImage : CARD_BACK}
                alt=""
                style={{
                  width: '100%',
                  height: '100%',
                  objectFit: 'contain',
                }}
                draggable={false}
              />
            </div>
          );
        })}

        {/* Matched pairs display at bottom - exact DFM positions */}
        {matchedPairIds.map((pairId) => {
          const displayPos = MATCHED_DISPLAY_POSITIONS[pairId];
          return (
            <img
              key={`matched-${pairId}`}
              src={SYMBOL_IMAGES[pairId]}
              alt=""
              style={{
                position: 'absolute',
                left: displayPos.x,
                top: displayPos.y,
                width: displayPos.w,
                height: displayPos.h,
                objectFit: 'contain',
              }}
              draggable={false}
            />
          );
        })}

        {/* Quit button - bottom left area */}
        <div
          onClick={onClose}
          style={{
            position: 'absolute',
            left: 8,
            top: 340,
            width: 80,
            height: 50,
            cursor: 'pointer',
            // backgroundColor: 'rgba(255, 0, 0, 0.2)', // Debug
          }}
        />

        {/* Game over overlay */}
        {gameOver && (
          <div style={{
            position: 'absolute',
            left: 150,
            top: 120,
            width: 340,
            padding: '30px',
            backgroundColor: 'rgba(0, 100, 0, 0.95)',
            color: '#fff',
            fontSize: 24,
            fontWeight: 'bold',
            borderRadius: 10,
            textAlign: 'center',
            border: '3px solid #00FF00',
          }}>
            <div style={{ marginBottom: 15 }}>Félicitations !</div>
            <div style={{ fontSize: 18, marginBottom: 10 }}>
              Tu as trouvé toutes les paires !
            </div>
            <div style={{ fontSize: 16, color: '#00FF00' }}>
              TEMPS: {formatTime(time)}
            </div>
            <button
              onClick={onClose}
              style={{
                marginTop: 20,
                padding: '10px 30px',
                fontSize: 16,
                fontWeight: 'bold',
                backgroundColor: '#c0392b',
                color: '#fff',
                border: 'none',
                borderRadius: 6,
                cursor: 'pointer',
              }}
            >
              Fermer
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default MemoryGame;
