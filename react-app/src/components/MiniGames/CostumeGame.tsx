/**
 * Costume Mini-Game - Faithful port of costume.dll
 * Original: Dress-up puzzle with 3 mannequins
 *
 * Original DFM Layout (640x400):
 * Initial positions (all stacked on right side):
 * - Im_bas_3: (504, 142) 100x138 - pants_3
 * - Im_bas_2: (496, 167) 116x89 - pants_2
 * - Im_bas_1: (505, 140) 99x142 - pants_1
 * - im_chap_2: (520, 179) 69x64 - hat_2
 * - im_chap_3: (514, 193) 80x37 - hat_3
 * - im_chap_1: (505, 187) 98x48 - hat_1
 * - Im_haut_2: (479, 149) 151x125 - vest_2
 * - Im_haut_1: (487, 151) 134x120 - vest_1
 * - Im_haut_3: (471, 130) 167x163 - vest_3
 *
 * Drop zones (TShape):
 * - Sh_chap_ga: (40, 14) 111x107 - left hat
 * - Sh_chap_mi: (182, 14) 109x107 - middle hat
 * - Sh_chap_dr: (332, 14) 123x107 - right hat
 * - Sh_haut_ga: (2, 120) 167x131 - left vest
 * - Sh_haut_mi: (168, 120) 135x131 - middle vest
 * - Sh_haut_dr: (302, 120) 185x131 - right vest
 * - Sh_bas_ga: (2, 250) 167x145 - left pants
 * - Sh_bas_mi: (168, 250) 135x143 - middle pants
 * - Sh_bas_dr: (302, 250) 185x141 - right pants
 *
 * Solution: Match _1 items to left, _2 to middle, _3 to right
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

// Drop zone types
type ZoneType = 'hat' | 'vest' | 'pants';
type ColumnId = 'left' | 'middle' | 'right';

interface DropZone {
  type: ZoneType;
  column: ColumnId;
  columnIndex: number; // 1, 2, or 3
  x: number;
  y: number;
  w: number;
  h: number;
}

// Drop zones from DFM TShape objects
const DROP_ZONES: DropZone[] = [
  // Hat zones
  { type: 'hat', column: 'left', columnIndex: 1, x: 40, y: 14, w: 111, h: 107 },
  { type: 'hat', column: 'middle', columnIndex: 2, x: 182, y: 14, w: 109, h: 107 },
  { type: 'hat', column: 'right', columnIndex: 3, x: 332, y: 14, w: 123, h: 107 },
  // Vest zones
  { type: 'vest', column: 'left', columnIndex: 1, x: 2, y: 120, w: 167, h: 131 },
  { type: 'vest', column: 'middle', columnIndex: 2, x: 168, y: 120, w: 135, h: 131 },
  { type: 'vest', column: 'right', columnIndex: 3, x: 302, y: 120, w: 185, h: 131 },
  // Pants zones
  { type: 'pants', column: 'left', columnIndex: 1, x: 2, y: 250, w: 167, h: 145 },
  { type: 'pants', column: 'middle', columnIndex: 2, x: 168, y: 250, w: 135, h: 143 },
  { type: 'pants', column: 'right', columnIndex: 3, x: 302, y: 250, w: 185, h: 141 },
];

// Clothing item definition
interface ClothingItem {
  id: string;
  type: ZoneType;
  setNumber: number; // 1, 2, or 3 - must match column for correct solution
  image: string;
  initialX: number;
  initialY: number;
  width: number;
  height: number;
  // Snap positions for each column (from DFM top_1/left_1, top_2/left_2, top_3/left_3)
  snapPositions: Record<ColumnId, { x: number; y: number }>;
}

// Items from DFM with exact initial positions
const CLOTHING_ITEMS: ClothingItem[] = [
  // Pants (bas)
  {
    id: 'pants_3',
    type: 'pants',
    setNumber: 3,
    image: `${ASSETS_PATH}/Image_2.png`,
    initialX: 504, initialY: 142,
    width: 100, height: 138,
    snapPositions: {
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
    initialX: 496, initialY: 167,
    width: 116, height: 89,
    snapPositions: {
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
    initialX: 505, initialY: 140,
    width: 99, height: 142,
    snapPositions: {
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
    initialX: 520, initialY: 179,
    width: 69, height: 64,
    snapPositions: {
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
    initialX: 514, initialY: 193,
    width: 80, height: 37,
    snapPositions: {
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
    initialX: 505, initialY: 187,
    width: 98, height: 48,
    snapPositions: {
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
    initialX: 479, initialY: 149,
    width: 151, height: 125,
    snapPositions: {
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
    initialX: 487, initialY: 151,
    width: 134, height: 120,
    snapPositions: {
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
    initialX: 471, initialY: 130,
    width: 167, height: 163,
    snapPositions: {
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
      const zone = DROP_ZONES.find(z => z.column === placement.column && z.type === item.type);
      if (!zone) return false;
      return item.setNumber === zone.columnIndex;
    });

    if (allCorrect) {
      setGameState('won');
      addScore(100);
      setVariable('COSTUME', 1);
      onSuccess?.();
    }
  }, [placements, gameState, addScore, setVariable, onSuccess]);

  // Find which zone a point is over
  const findZoneAtPoint = useCallback((x: number, y: number, type: ZoneType): DropZone | null => {
    for (const zone of DROP_ZONES) {
      if (zone.type !== type) continue;
      if (x >= zone.x && x <= zone.x + zone.w && y >= zone.y && y <= zone.y + zone.h) {
        return zone;
      }
    }
    return null;
  }, []);

  // Check if a slot is available (only one item per type per column)
  const isSlotAvailable = useCallback((column: ColumnId, type: ZoneType, excludeItemId?: string): boolean => {
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
    const centerY = pos.y + item.height / 2;

    const zone = findZoneAtPoint(centerX, centerY, item.type);

    if (zone && isSlotAvailable(zone.column, item.type, draggedItem)) {
      // Snap to column position
      const snapPos = item.snapPositions[zone.column];
      setPositions(prev => ({
        ...prev,
        [draggedItem]: snapPos,
      }));
      setPlacements(prev => [...prev, { itemId: draggedItem, column: zone.column }]);
    } else {
      // Return to initial position
      setPositions(prev => ({
        ...prev,
        [draggedItem]: { x: item.initialX, y: item.initialY },
      }));
    }

    setDraggedItem(null);
  }, [draggedItem, positions, findZoneAtPoint, isSlotAvailable]);

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

        {/* Drop zones (invisible) */}
        {DROP_ZONES.map((zone, idx) => (
          <div
            key={idx}
            style={{
              position: 'absolute',
              left: zone.x,
              top: zone.y,
              width: zone.w,
              height: zone.h,
              // Debug: uncomment to see drop zones
              // backgroundColor: 'rgba(0, 255, 0, 0.1)',
              // border: '1px dashed green',
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
          top: 10,
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

        {/* Win overlay - Gagne label at (216, 150) red 64px */}
        {gameState === 'won' && (
          <div style={{
            position: 'absolute',
            left: 216,
            top: 150,
            fontFamily: '"MS Sans Serif", sans-serif',
            fontSize: 64,
            fontWeight: 'bold',
            color: '#ff0000',
          }}>
            GAGNE
          </div>
        )}

        {/* Close button after win */}
        {gameState === 'won' && (
          <button
            onClick={onClose}
            style={{
              position: 'absolute',
              left: 270,
              top: 250,
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
        )}
      </div>
    </div>
  );
};

export default CostumeGame;
