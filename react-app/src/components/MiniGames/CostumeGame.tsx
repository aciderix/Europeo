/**
 * Costume Mini-Game - Faithful port of costume.dll
 * Original: Dress-up puzzle with 3 mannequins
 *
 * Gameplay:
 * - 3 mannequin columns (Left, Middle, Right)
 * - 9 clothing items: 3 hats, 3 vests, 3 pants
 * - Drag each item to complete the outfits
 * - Each set (_1, _2, _3) must match its column for the win
 *
 * Clothing items:
 * - Pants: Image_2 (bas_3), Image_3 (bas_2), Image_4 (bas_1)
 * - Hats: Image_5 (chap_2), Image_6 (chap_3), Image_7 (chap_1)
 * - Vests: Image_8 (haut_2), Image_9 (haut_1), Image_10 (haut_3)
 *
 * Solution (to win):
 * - Left column: hat_1 + vest_1 + pants_1 (Image_7, Image_9, Image_4)
 * - Middle column: hat_2 + vest_2 + pants_2 (Image_5, Image_8, Image_3)
 * - Right column: hat_3 + vest_3 + pants_3 (Image_6, Image_10, Image_2)
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { useGameStore } from '../../store/gameStore';

interface CostumeGameProps {
  onClose: () => void;
  onSuccess?: () => void;
}

// Asset paths
const ASSETS_PATH = '/assets/minigames/costume';
const BACKGROUND = `${ASSETS_PATH}/Image_1.png`;

// Column definitions (drop zones)
type ColumnId = 'left' | 'middle' | 'right';

interface Column {
  id: ColumnId;
  index: number; // 1, 2, or 3
  x: number;
  width: number;
}

const COLUMNS: Column[] = [
  { id: 'left', index: 1, x: 0, width: 120 },
  { id: 'middle', index: 2, x: 145, width: 120 },
  { id: 'right', index: 3, x: 290, width: 120 },
];

// Clothing types
type ClothingType = 'hat' | 'vest' | 'pants';

// Clothing item definition
interface ClothingItem {
  id: string;
  type: ClothingType;
  setNumber: number; // 1, 2, or 3 - must match column for correct solution
  image: string;
  initialX: number;
  initialY: number;
  width: number;
  height: number;
  // Snap positions for each column
  positions: Record<ColumnId, { x: number; y: number }>;
}

const CLOTHING_ITEMS: ClothingItem[] = [
  // Pants (bas)
  {
    id: 'pants_3',
    type: 'pants',
    setNumber: 3,
    image: `${ASSETS_PATH}/Image_2.png`,
    initialX: 450, initialY: 280,
    width: 80, height: 90,
    positions: {
      left: { x: 32, y: 230 },
      middle: { x: 178, y: 230 },
      right: { x: 326, y: 230 },
    },
  },
  {
    id: 'pants_2',
    type: 'pants',
    setNumber: 2,
    image: `${ASSETS_PATH}/Image_3.png`,
    initialX: 540, initialY: 280,
    width: 80, height: 90,
    positions: {
      left: { x: 26, y: 228 },
      middle: { x: 172, y: 228 },
      right: { x: 318, y: 222 },
    },
  },
  {
    id: 'pants_1',
    type: 'pants',
    setNumber: 1,
    image: `${ASSETS_PATH}/Image_4.png`,
    initialX: 490, initialY: 180,
    width: 80, height: 90,
    positions: {
      left: { x: 34, y: 232 },
      middle: { x: 180, y: 232 },
      right: { x: 327, y: 232 },
    },
  },
  // Hats (chap)
  {
    id: 'hat_2',
    type: 'hat',
    setNumber: 2,
    image: `${ASSETS_PATH}/Image_5.png`,
    initialX: 450, initialY: 20,
    width: 60, height: 50,
    positions: {
      left: { x: 54, y: 20 },
      middle: { x: 200, y: 24 },
      right: { x: 346, y: 22 },
    },
  },
  {
    id: 'hat_3',
    type: 'hat',
    setNumber: 3,
    image: `${ASSETS_PATH}/Image_6.png`,
    initialX: 520, initialY: 30,
    width: 40, height: 35,
    positions: {
      left: { x: 44, y: 50 },
      middle: { x: 190, y: 50 },
      right: { x: 338, y: 50 },
    },
  },
  {
    id: 'hat_1',
    type: 'hat',
    setNumber: 1,
    image: `${ASSETS_PATH}/Image_7.png`,
    initialX: 580, initialY: 20,
    width: 50, height: 45,
    positions: {
      left: { x: 46, y: 48 },
      middle: { x: 192, y: 52 },
      right: { x: 338, y: 52 },
    },
  },
  // Vests (haut)
  {
    id: 'vest_2',
    type: 'vest',
    setNumber: 2,
    image: `${ASSETS_PATH}/Image_8.png`,
    initialX: 450, initialY: 100,
    width: 90, height: 100,
    positions: {
      left: { x: 10, y: 126 },
      middle: { x: 156, y: 126 },
      right: { x: 302, y: 128 },
    },
  },
  {
    id: 'vest_1',
    type: 'vest',
    setNumber: 1,
    image: `${ASSETS_PATH}/Image_9.png`,
    initialX: 550, initialY: 100,
    width: 80, height: 95,
    positions: {
      left: { x: 16, y: 126 },
      middle: { x: 162, y: 126 },
      right: { x: 310, y: 126 },
    },
  },
  {
    id: 'vest_3',
    type: 'vest',
    setNumber: 3,
    image: `${ASSETS_PATH}/Image_10.png`,
    initialX: 500, initialY: 90,
    width: 85, height: 100,
    positions: {
      left: { x: 12, y: 126 },
      middle: { x: 163, y: 126 },
      right: { x: 304, y: 126 },
    },
  },
];

interface PlacedItem {
  itemId: string;
  column: ColumnId;
}

type GameState = 'playing' | 'won';

export const CostumeGame: React.FC<CostumeGameProps> = ({ onClose, onSuccess }) => {
  const addScore = useGameStore((state) => state.addScore);
  const setVariable = useGameStore((state) => state.setVariable);

  const [positions, setPositions] = useState<Record<string, { x: number; y: number }>>(() =>
    Object.fromEntries(CLOTHING_ITEMS.map(item => [item.id, { x: item.initialX, y: item.initialY }]))
  );
  const [placements, setPlacements] = useState<PlacedItem[]>([]);
  const [draggedItem, setDraggedItem] = useState<string | null>(null);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [gameState, setGameState] = useState<GameState>('playing');

  const containerRef = useRef<HTMLDivElement>(null);

  // Check win condition
  useEffect(() => {
    if (gameState !== 'playing') return;

    // All 9 items must be placed
    if (placements.length !== 9) return;

    // Check if all items are in their correct column (setNumber matches column index)
    const allCorrect = placements.every(placement => {
      const item = CLOTHING_ITEMS.find(i => i.id === placement.itemId);
      if (!item) return false;
      const column = COLUMNS.find(c => c.id === placement.column);
      if (!column) return false;
      return item.setNumber === column.index;
    });

    if (allCorrect) {
      setGameState('won');
      addScore(100);
      setVariable('COSTUME', 1);
      onSuccess?.();
    }
  }, [placements, gameState, addScore, setVariable, onSuccess]);

  // Find which column a point is over
  const findColumnAtPoint = useCallback((x: number): ColumnId | null => {
    for (const col of COLUMNS) {
      if (x >= col.x && x <= col.x + col.width) {
        return col.id;
      }
    }
    return null;
  }, []);

  // Check if a slot is available (only one item per type per column)
  const isSlotAvailable = useCallback((column: ColumnId, type: ClothingType, excludeItemId?: string): boolean => {
    return !placements.some(p => {
      if (p.itemId === excludeItemId) return false;
      const item = CLOTHING_ITEMS.find(i => i.id === p.itemId);
      return item?.type === type && p.column === column;
    });
  }, [placements]);

  // Handle drag start
  const handleDragStart = useCallback((itemId: string, clientX: number, clientY: number) => {
    if (gameState !== 'playing') return;

    const container = containerRef.current;
    if (!container) return;

    const rect = container.getBoundingClientRect();
    const pos = positions[itemId];

    // Remove from placements if already placed
    setPlacements(prev => prev.filter(p => p.itemId !== itemId));

    setDraggedItem(itemId);
    setDragOffset({
      x: clientX - rect.left - pos.x,
      y: clientY - rect.top - pos.y,
    });
  }, [positions, gameState]);

  // Handle drag move
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

  // Handle drag end
  const handleDragEnd = useCallback(() => {
    if (draggedItem === null) return;

    const item = CLOTHING_ITEMS.find(i => i.id === draggedItem);
    if (!item) {
      setDraggedItem(null);
      return;
    }

    const pos = positions[draggedItem];
    const centerX = pos.x + item.width / 2;

    const column = findColumnAtPoint(centerX);

    if (column && isSlotAvailable(column, item.type, draggedItem)) {
      // Snap to column position
      const snapPos = item.positions[column];
      setPositions(prev => ({
        ...prev,
        [draggedItem]: snapPos,
      }));
      setPlacements(prev => [...prev, { itemId: draggedItem, column }]);
    } else {
      // Return to initial position
      setPositions(prev => ({
        ...prev,
        [draggedItem]: { x: item.initialX, y: item.initialY },
      }));
    }

    setDraggedItem(null);
  }, [draggedItem, positions, findColumnAtPoint, isSlotAvailable]);

  // Mouse handlers
  const handleMouseDown = (itemId: string) => (e: React.MouseEvent) => {
    e.preventDefault();
    handleDragStart(itemId, e.clientX, e.clientY);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    handleDragMove(e.clientX, e.clientY);
  };

  const handleMouseUp = () => {
    handleDragEnd();
  };

  // Touch handlers
  const handleTouchStart = (itemId: string) => (e: React.TouchEvent) => {
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
        {/* Background with mannequins */}
        <img
          src={BACKGROUND}
          alt="Mannequins"
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

        {/* Column drop zones (invisible) */}
        {COLUMNS.map(col => (
          <div
            key={col.id}
            style={{
              position: 'absolute',
              left: col.x,
              top: 0,
              width: col.width,
              height: 350,
              // Debug: uncomment to see drop zones
              // backgroundColor: 'rgba(0, 255, 0, 0.1)',
              // border: '2px dashed green',
            }}
          />
        ))}

        {/* Draggable clothing items */}
        {CLOTHING_ITEMS.map(item => {
          const pos = positions[item.id];
          const isPlaced = placements.some(p => p.itemId === item.id);

          return (
            <img
              key={item.id}
              src={item.image}
              alt={item.id}
              style={{
                position: 'absolute',
                left: pos.x,
                top: pos.y,
                width: item.width,
                height: item.height,
                cursor: gameState === 'won' ? 'default' : 'grab',
                zIndex: draggedItem === item.id ? 100 : isPlaced ? 10 : 50,
                transition: draggedItem === item.id ? 'none' : 'all 0.2s',
                userSelect: 'none',
              }}
              onMouseDown={handleMouseDown(item.id)}
              onTouchStart={handleTouchStart(item.id)}
              draggable={false}
            />
          );
        })}

        {/* Progress indicator */}
        <div style={{
          position: 'absolute',
          right: 20,
          top: 20,
          fontFamily: '"Comic Sans MS", cursive',
          fontSize: 16,
          color: '#fff',
          textShadow: '2px 2px 4px #000',
          backgroundColor: 'rgba(0,0,0,0.5)',
          padding: '8px 12px',
          borderRadius: 8,
        }}>
          {placements.length} / 9
        </div>

        {/* Win overlay */}
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
              fontSize: 48,
              fontWeight: 'bold',
              color: '#fff',
              marginBottom: 20,
            }}>
              BRAVO !
            </div>
            <p style={{
              color: '#fff',
              fontFamily: '"Comic Sans MS", cursive',
              marginBottom: 20,
            }}>
              Les mannequins sont bien habillés !
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

        {/* Instructions */}
        <div style={{
          position: 'absolute',
          left: 430,
          bottom: 20,
          fontFamily: '"Comic Sans MS", cursive',
          fontSize: 12,
          color: '#fff',
          textShadow: '1px 1px 2px #000',
          textAlign: 'center',
          width: 180,
        }}>
          Habillez les 3 mannequins<br/>
          avec les bons vêtements !
        </div>
      </div>
    </div>
  );
};

export default CostumeGame;
