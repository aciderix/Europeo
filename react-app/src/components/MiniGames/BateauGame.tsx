/**
 * Bateau Mini-Game - Faithful port of bateau.dll
 * Original: Drag & Drop cultural objects to their countries
 *
 * Gameplay:
 * - 8 draggable cultural objects at bottom of screen
 * - 6 European country drop zones on map
 * - Drag each object to its correct country
 * - Timer counts down, must complete before time runs out
 *
 * Objects (from DFM):
 * - Image_2: Manneken Pis (sculpture) → Belgium
 * - Image_3: Violin → Austria
 * - Image_4: Chianti bottle → Italy
 * - Image_5: Tyrolean hat → Austria
 * - Image_6: Trojan horse → Greece
 * - Image_7: Bowler hat → England
 * - Image_8: Dutch painting → Netherlands
 * - Image_9: Red bus → England
 *
 * Drop zones (TShape from DFM):
 * - Belgium: (124, 188) + (40, 144)
 * - Austria: (120, 272) + (48, 272)
 * - England: (356, 60)
 * - Greece: (488, 160)
 * - Netherlands: (360, 168)
 * - Italy: (184, 240)
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { useGameStore } from '../../store/gameStore';

interface BateauGameProps {
  onClose: () => void;
  onSuccess?: () => void;
}

// Asset paths
const ASSETS_PATH = '/assets/minigames/bateau';
const BACKGROUND = `${ASSETS_PATH}/Image_1.png`;
const BUBBLE = `${ASSETS_PATH}/Image_10.png`;

// Countries (drop zones)
type CountryId = 'belgium' | 'austria' | 'england' | 'greece' | 'netherlands' | 'italy';

interface Country {
  id: CountryId;
  name: string;
  zones: Array<{ x: number; y: number; w: number; h: number }>;
}

const COUNTRIES: Country[] = [
  {
    id: 'belgium',
    name: 'Belgique',
    zones: [
      { x: 124, y: 188, w: 69, h: 77 },
      { x: 40, y: 144, w: 145, h: 121 },
    ],
  },
  {
    id: 'austria',
    name: 'Autriche',
    zones: [
      { x: 120, y: 272, w: 49, h: 125 },
      { x: 48, y: 272, w: 121, h: 121 },
    ],
  },
  {
    id: 'england',
    name: 'Angleterre',
    zones: [{ x: 356, y: 60, w: 133, h: 101 }],
  },
  {
    id: 'greece',
    name: 'Grèce',
    zones: [{ x: 488, y: 160, w: 73, h: 105 }],
  },
  {
    id: 'netherlands',
    name: 'Pays-Bas',
    zones: [{ x: 360, y: 168, w: 121, h: 113 }],
  },
  {
    id: 'italy',
    name: 'Italie',
    zones: [{ x: 184, y: 240, w: 119, h: 113 }],
  },
];

// Draggable objects
interface DraggableItem {
  id: number;
  name: string;
  image: string;
  x: number;
  y: number;
  width: number;
  height: number;
  correctCountry: CountryId;
}

const ITEMS: DraggableItem[] = [
  {
    id: 5,
    name: 'Manneken Pis',
    image: `${ASSETS_PATH}/Image_2.png`,
    x: 0, y: 302,
    width: 43, height: 85,
    correctCountry: 'belgium',
  },
  {
    id: 2,
    name: 'Violon',
    image: `${ASSETS_PATH}/Image_3.png`,
    x: 192, y: 342,
    width: 118, height: 46,
    correctCountry: 'austria',
  },
  {
    id: 7,
    name: 'Chianti',
    image: `${ASSETS_PATH}/Image_4.png`,
    x: 335, y: 309,
    width: 59, height: 82,
    correctCountry: 'italy',
  },
  {
    id: 4,
    name: 'Chapeau tyrolien',
    image: `${ASSETS_PATH}/Image_5.png`,
    x: 425, y: 284,
    width: 88, height: 71,
    correctCountry: 'austria',
  },
  {
    id: 8,
    name: 'Cheval de Troie',
    image: `${ASSETS_PATH}/Image_6.png`,
    x: 568, y: 111,
    width: 71, height: 78,
    correctCountry: 'greece',
  },
  {
    id: 3,
    name: 'Chapeau melon',
    image: `${ASSETS_PATH}/Image_7.png`,
    x: 296, y: 80,
    width: 51, height: 68,
    correctCountry: 'england',
  },
  {
    id: 6,
    name: 'Tableau',
    image: `${ASSETS_PATH}/Image_8.png`,
    x: 223, y: 44,
    width: 68, height: 77,
    correctCountry: 'netherlands',
  },
  {
    id: 1,
    name: 'Bus rouge',
    image: `${ASSETS_PATH}/Image_9.png`,
    x: 306, y: 240,
    width: 100, height: 61,
    correctCountry: 'england',
  },
];

type GameState = 'playing' | 'won' | 'lost';

export const BateauGame: React.FC<BateauGameProps> = ({ onClose, onSuccess }) => {
  const addScore = useGameStore((state) => state.addScore);
  const setVariable = useGameStore((state) => state.setVariable);

  const [items, setItems] = useState(() =>
    ITEMS.map(item => ({ ...item, placed: false }))
  );
  const [draggedItem, setDraggedItem] = useState<number | null>(null);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [positions, setPositions] = useState<Record<number, { x: number; y: number }>>(() =>
    Object.fromEntries(ITEMS.map(item => [item.id, { x: item.x, y: item.y }]))
  );
  const [gameState, setGameState] = useState<GameState>('playing');
  const [timer, setTimer] = useState(60);
  const [score, setScore] = useState(0);

  const containerRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Timer countdown
  useEffect(() => {
    if (gameState !== 'playing') return;

    timerRef.current = setInterval(() => {
      setTimer(prev => {
        if (prev <= 1) {
          setGameState('lost');
          setVariable('BATEAU', 0);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [gameState, setVariable]);

  // Check win condition
  useEffect(() => {
    const allPlaced = items.every(item => item.placed);
    if (allPlaced && gameState === 'playing') {
      setGameState('won');
      addScore(50 + timer);
      setVariable('BATEAU', 1);
      onSuccess?.();
      if (timerRef.current) clearInterval(timerRef.current);
    }
  }, [items, gameState, timer, addScore, setVariable, onSuccess]);

  // Find which country a point is over
  const findCountryAtPoint = useCallback((x: number, y: number): CountryId | null => {
    for (const country of COUNTRIES) {
      for (const zone of country.zones) {
        if (
          x >= zone.x && x <= zone.x + zone.w &&
          y >= zone.y && y <= zone.y + zone.h
        ) {
          return country.id;
        }
      }
    }
    return null;
  }, []);

  // Handle mouse/touch events
  const handleDragStart = useCallback((itemId: number, clientX: number, clientY: number) => {
    if (gameState !== 'playing') return;

    const item = items.find(i => i.id === itemId);
    if (!item || item.placed) return;

    const container = containerRef.current;
    if (!container) return;

    const rect = container.getBoundingClientRect();
    const pos = positions[itemId];

    setDraggedItem(itemId);
    setDragOffset({
      x: clientX - rect.left - pos.x,
      y: clientY - rect.top - pos.y,
    });
  }, [items, positions, gameState]);

  const handleDragMove = useCallback((clientX: number, clientY: number) => {
    if (draggedItem === null) return;

    const container = containerRef.current;
    if (!container) return;

    const rect = container.getBoundingClientRect();
    const newX = Math.max(0, Math.min(640 - 50, clientX - rect.left - dragOffset.x));
    const newY = Math.max(0, Math.min(400 - 50, clientY - rect.top - dragOffset.y));

    setPositions(prev => ({
      ...prev,
      [draggedItem]: { x: newX, y: newY },
    }));
  }, [draggedItem, dragOffset]);

  const handleDragEnd = useCallback(() => {
    if (draggedItem === null) return;

    const item = items.find(i => i.id === draggedItem);
    if (!item) {
      setDraggedItem(null);
      return;
    }

    const pos = positions[draggedItem];
    const centerX = pos.x + item.width / 2;
    const centerY = pos.y + item.height / 2;

    const country = findCountryAtPoint(centerX, centerY);

    if (country === item.correctCountry) {
      // Correct placement!
      setItems(prev =>
        prev.map(i => i.id === draggedItem ? { ...i, placed: true } : i)
      );
      setScore(prev => prev + 10);
      addScore(10);
    } else if (country !== null) {
      // Wrong country - reset position
      setPositions(prev => ({
        ...prev,
        [draggedItem]: { x: item.x, y: item.y },
      }));
    }

    setDraggedItem(null);
  }, [draggedItem, items, positions, findCountryAtPoint, addScore]);

  // Mouse event handlers
  const handleMouseDown = (itemId: number) => (e: React.MouseEvent) => {
    e.preventDefault();
    handleDragStart(itemId, e.clientX, e.clientY);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    handleDragMove(e.clientX, e.clientY);
  };

  const handleMouseUp = () => {
    handleDragEnd();
  };

  // Touch event handlers
  const handleTouchStart = (itemId: number) => (e: React.TouchEvent) => {
    const touch = e.touches[0];
    handleDragStart(itemId, touch.clientX, touch.clientY);
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    const touch = e.touches[0];
    handleDragMove(touch.clientX, touch.clientY);
  };

  const handleTouchEnd = () => {
    handleDragEnd();
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
      <div
        ref={containerRef}
        style={{
          position: 'relative',
          width: 640,
          height: 400,
          overflow: 'hidden',
          cursor: draggedItem !== null ? 'grabbing' : 'default',
        }}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
      >
        {/* Background map */}
        <img
          src={BACKGROUND}
          alt="Carte Europe"
          style={{
            position: 'absolute',
            left: 0,
            top: 0,
            width: 640,
            height: 400,
            userSelect: 'none',
            pointerEvents: 'none',
          }}
          draggable={false}
        />

        {/* Country drop zones (invisible but for debug) */}
        {COUNTRIES.map(country =>
          country.zones.map((zone, idx) => (
            <div
              key={`${country.id}-${idx}`}
              style={{
                position: 'absolute',
                left: zone.x,
                top: zone.y,
                width: zone.w,
                height: zone.h,
                // Debug: uncomment to see drop zones
                // backgroundColor: 'rgba(0, 255, 0, 0.2)',
                // border: '2px dashed green',
              }}
            />
          ))
        )}

        {/* Draggable items */}
        {items.map(item => {
          const pos = positions[item.id];
          return (
            <img
              key={item.id}
              src={item.image}
              alt={item.name}
              style={{
                position: 'absolute',
                left: pos.x,
                top: pos.y,
                width: item.width,
                height: item.height,
                cursor: item.placed ? 'default' : 'grab',
                opacity: item.placed ? 0.7 : 1,
                filter: item.placed ? 'grayscale(50%)' : 'none',
                transition: draggedItem === item.id ? 'none' : 'opacity 0.3s',
                zIndex: draggedItem === item.id ? 100 : item.placed ? 1 : 10,
                userSelect: 'none',
                pointerEvents: item.placed ? 'none' : 'auto',
              }}
              onMouseDown={handleMouseDown(item.id)}
              onTouchStart={handleTouchStart(item.id)}
              draggable={false}
            />
          );
        })}

        {/* Timer bubble */}
        <div style={{
          position: 'absolute',
          left: 28,
          top: 28,
          width: 149,
          height: 70,
          backgroundImage: `url(${BUBBLE})`,
          backgroundSize: 'contain',
          backgroundRepeat: 'no-repeat',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
          <span style={{
            fontFamily: '"Comic Sans MS", cursive',
            fontSize: 24,
            fontWeight: 'bold',
            color: timer > 10 ? '#ff0000' : '#ff0000',
            animation: timer <= 10 ? 'blink 0.5s infinite' : 'none',
          }}>
            {timer}
          </span>
        </div>

        {/* Score display */}
        <div style={{
          position: 'absolute',
          right: 20,
          top: 20,
          fontFamily: '"Comic Sans MS", cursive',
          fontSize: 20,
          color: '#fff',
          textShadow: '2px 2px 4px #000',
        }}>
          Score: {score}
        </div>

        {/* Win/Lose overlays */}
        {gameState === 'won' && (
          <div style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            backgroundColor: 'rgba(0, 128, 0, 0.95)',
            padding: '30px 50px',
            borderRadius: 15,
            textAlign: 'center',
          }}>
            <div style={{
              fontFamily: '"MS Sans Serif", sans-serif',
              fontSize: 64,
              fontWeight: 'bold',
              color: '#ff0000',
              marginBottom: 20,
            }}>
              GAGNE
            </div>
            <p style={{
              color: '#fff',
              fontFamily: '"Comic Sans MS", cursive',
              marginBottom: 20,
            }}>
              Score: {score}
            </p>
            <button
              onClick={onClose}
              style={{
                padding: '12px 30px',
                fontSize: 16,
                fontWeight: 'bold',
                backgroundColor: '#4CAF50',
                color: '#fff',
                border: 'none',
                borderRadius: 8,
                cursor: 'pointer',
              }}
            >
              Continuer
            </button>
          </div>
        )}

        {gameState === 'lost' && (
          <div style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            backgroundColor: 'rgba(0, 0, 128, 0.95)',
            padding: '30px 50px',
            borderRadius: 15,
            textAlign: 'center',
          }}>
            <div style={{
              fontFamily: '"MS Sans Serif", sans-serif',
              fontSize: 64,
              fontWeight: 'bold',
              color: '#0000ff',
              marginBottom: 20,
              textShadow: '2px 2px 0 #000',
            }}>
              PERDU
            </div>
            <button
              onClick={onClose}
              style={{
                padding: '12px 30px',
                fontSize: 16,
                fontWeight: 'bold',
                backgroundColor: '#666',
                color: '#fff',
                border: 'none',
                borderRadius: 8,
                cursor: 'pointer',
              }}
            >
              Quitter
            </button>
          </div>
        )}

        {/* Quit button */}
        {gameState === 'playing' && (
          <button
            onClick={onClose}
            style={{
              position: 'absolute',
              left: 560,
              top: 360,
              padding: '6px 16px',
              fontSize: 14,
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
        )}
      </div>

      {/* Blink animation for low timer */}
      <style>{`
        @keyframes blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }
      `}</style>
    </div>
  );
};

export default BateauGame;
