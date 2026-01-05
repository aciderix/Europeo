/**
 * Frog Mini-Game - Faithful port of frog.dll
 * Original: Simon Says memory game with frogs
 *
 * Gameplay:
 * 1. Computer shows a sequence of frogs lighting up
 * 2. Player must repeat the sequence by clicking frogs
 * 3. Each success adds one more frog to the sequence
 * 4. Golden bonus frog appears randomly for extra points
 *
 * Form layout (640x400):
 * - Image9: Background with frogs at rest
 * - Image1-8: Frog animations (singing frogs)
 * - Image10-17: Hitbox zones for clicks
 * - Image3: Golden bonus frog (hidden by default)
 * - Timer1: 2000ms for golden frog appearance
 *
 * Frogs mapping:
 * - 0: Haut-Gauche (125, 19) - Image_7.png
 * - 1: Haut-Droite (543, 7) - Image_4.png
 * - 2: Milieu-Gauche (127, 96) - Image_3.png
 * - 3: Milieu-Centre (402, 95) - Image_8.png
 * - 4: Centre-Petit (306, 148) - Image_6.png
 * - 5: Bas-Gauche (13, 155) - Image_10.png
 * - 6: Bas-Droite (426, 239) - Image_9.png
 * - Bonus: Golden (585, 157) - Image_5.png
 */

import React, { useState, useCallback, useEffect, useRef } from 'react';
import { useGameStore } from '../../store/gameStore';

interface FrogGameProps {
  onClose: () => void;
  onSuccess?: () => void;
}

// Asset paths
const ASSETS_PATH = '/assets/minigames/frog';
const BACKGROUND = `${ASSETS_PATH}/Image_1.png`;
const BUBBLE = `${ASSETS_PATH}/Image_2.png`;

// Frog definitions from original DFM
const FROGS = [
  {
    id: 0,
    name: 'Haut-Gauche',
    image: `${ASSETS_PATH}/Image_7.png`,
    x: 125, y: 19,
    hitbox: { x: 92, y: 3, w: 84, h: 74 },
  },
  {
    id: 1,
    name: 'Haut-Droite',
    image: `${ASSETS_PATH}/Image_4.png`,
    x: 543, y: 7,
    hitbox: { x: 536, y: 3, w: 93, h: 78 },
  },
  {
    id: 2,
    name: 'Milieu-Gauche',
    image: `${ASSETS_PATH}/Image_3.png`,
    x: 127, y: 96,
    hitbox: { x: 115, y: 89, w: 89, h: 74 },
  },
  {
    id: 3,
    name: 'Milieu-Centre',
    image: `${ASSETS_PATH}/Image_8.png`,
    x: 402, y: 95,
    hitbox: { x: 390, y: 82, w: 78, h: 73 },
  },
  {
    id: 4,
    name: 'Centre-Petit',
    image: `${ASSETS_PATH}/Image_6.png`,
    x: 306, y: 148,
    hitbox: { x: 287, y: 142, w: 79, h: 61 },
  },
  {
    id: 5,
    name: 'Bas-Gauche',
    image: `${ASSETS_PATH}/Image_10.png`,
    x: 13, y: 155,
    hitbox: { x: 2, y: 152, w: 84, h: 78 },
  },
  {
    id: 6,
    name: 'Bas-Droite',
    image: `${ASSETS_PATH}/Image_9.png`,
    x: 426, y: 239,
    hitbox: { x: 428, y: 222, w: 80, h: 77 },
  },
];

// Golden bonus frog
const GOLDEN_FROG = {
  id: 7,
  name: 'Golden',
  image: `${ASSETS_PATH}/Image_5.png`,
  x: 585, y: 157,
  hitbox: { x: 542, y: 115, w: 81, h: 83 },
};

type GamePhase = 'intro' | 'showing' | 'playing' | 'success' | 'fail' | 'win';

export const FrogGame: React.FC<FrogGameProps> = ({ onClose, onSuccess }) => {
  const addScore = useGameStore((state) => state.addScore);
  const setVariable = useGameStore((state) => state.setVariable);

  const [phase, setPhase] = useState<GamePhase>('intro');
  const [sequence, setSequence] = useState<number[]>([]);
  const [playerIndex, setPlayerIndex] = useState(0);
  const [activeFrog, setActiveFrog] = useState<number | null>(null);
  const [score, setScore] = useState(0);
  const [level, setLevel] = useState(1);
  const [showGolden, setShowGolden] = useState(false);
  const [message, setMessage] = useState('Écoute bien');
  const [subMessage, setSubMessage] = useState('et répète !');

  const goldenTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const sequenceTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const MAX_LEVEL = 7; // Win after completing 7 levels

  // Clear all timeouts on unmount
  useEffect(() => {
    return () => {
      if (goldenTimeoutRef.current) clearTimeout(goldenTimeoutRef.current);
      if (sequenceTimeoutRef.current) clearTimeout(sequenceTimeoutRef.current);
    };
  }, []);

  // Generate a new random sequence
  const generateSequence = useCallback(() => {
    const newSequence: number[] = [];
    for (let i = 0; i < level; i++) {
      newSequence.push(Math.floor(Math.random() * FROGS.length));
    }
    return newSequence;
  }, [level]);

  // Show the sequence to the player
  const showSequence = useCallback((seq: number[]) => {
    setPhase('showing');
    setMessage('Regarde...');
    setSubMessage('');

    let index = 0;
    const showNext = () => {
      if (index < seq.length) {
        setActiveFrog(seq[index]);
        sequenceTimeoutRef.current = setTimeout(() => {
          setActiveFrog(null);
          index++;
          sequenceTimeoutRef.current = setTimeout(showNext, 300);
        }, 600);
      } else {
        setPhase('playing');
        setMessage('À toi !');
        setSubMessage('');

        // Randomly show golden frog during play
        if (Math.random() > 0.6) {
          goldenTimeoutRef.current = setTimeout(() => {
            setShowGolden(true);
            goldenTimeoutRef.current = setTimeout(() => {
              setShowGolden(false);
            }, 2000);
          }, 500 + Math.random() * 2000);
        }
      }
    };

    sequenceTimeoutRef.current = setTimeout(showNext, 500);
  }, []);

  // Start a new round
  const startRound = useCallback(() => {
    const newSeq = generateSequence();
    setSequence(newSeq);
    setPlayerIndex(0);
    showSequence(newSeq);
  }, [generateSequence, showSequence]);

  // Handle frog click
  const handleFrogClick = useCallback((frogId: number) => {
    if (phase !== 'playing') return;

    // Check if golden frog clicked
    if (frogId === GOLDEN_FROG.id && showGolden) {
      setShowGolden(false);
      setScore(prev => prev + 10);
      addScore(10);
      if (goldenTimeoutRef.current) clearTimeout(goldenTimeoutRef.current);
      return;
    }

    // Flash the clicked frog
    setActiveFrog(frogId);
    setTimeout(() => setActiveFrog(null), 200);

    // Check if correct
    if (frogId === sequence[playerIndex]) {
      setScore(prev => prev + 1);
      const nextIndex = playerIndex + 1;

      if (nextIndex >= sequence.length) {
        // Completed sequence!
        addScore(level * 5);

        if (level >= MAX_LEVEL) {
          // Won the game!
          setPhase('win');
          setMessage('BRAVO !');
          setSubMessage('Tu as gagné !');
          setVariable('FROG', 1);
          onSuccess?.();
        } else {
          // Next level
          setPhase('success');
          setMessage('Bien joué !');
          setSubMessage(`Niveau ${level + 1}...`);
          setLevel(prev => prev + 1);
          setTimeout(() => {
            startRound();
          }, 1500);
        }
      } else {
        setPlayerIndex(nextIndex);
      }
    } else {
      // Wrong frog
      setPhase('fail');
      setMessage('Raté !');
      setSubMessage(`Score: ${score}`);
      setVariable('FROG', 0);
    }
  }, [phase, showGolden, sequence, playerIndex, score, level, addScore, setVariable, onSuccess, startRound]);

  // Start game
  const handleStart = () => {
    setLevel(1);
    setScore(0);
    startRound();
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
        overflow: 'hidden',
      }}>
        {/* Background with resting frogs */}
        <img
          src={BACKGROUND}
          alt="Marais"
          style={{
            position: 'absolute',
            left: 0,
            top: 0,
            width: 640,
            height: 400,
          }}
        />

        {/* Active frog images (when singing) */}
        {FROGS.map(frog => (
          <img
            key={frog.id}
            src={frog.image}
            alt={frog.name}
            style={{
              position: 'absolute',
              left: frog.x,
              top: frog.y,
              opacity: activeFrog === frog.id ? 1 : 0,
              transition: 'opacity 0.1s',
              pointerEvents: 'none',
            }}
          />
        ))}

        {/* Golden bonus frog */}
        {showGolden && (
          <img
            src={GOLDEN_FROG.image}
            alt="Golden Frog"
            style={{
              position: 'absolute',
              left: GOLDEN_FROG.x,
              top: GOLDEN_FROG.y,
              cursor: 'pointer',
              animation: 'pulse 0.5s infinite alternate',
            }}
            onClick={() => handleFrogClick(GOLDEN_FROG.id)}
          />
        )}

        {/* Clickable hitbox zones */}
        {phase === 'playing' && FROGS.map(frog => (
          <div
            key={`hitbox-${frog.id}`}
            onClick={() => handleFrogClick(frog.id)}
            style={{
              position: 'absolute',
              left: frog.hitbox.x,
              top: frog.hitbox.y,
              width: frog.hitbox.w,
              height: frog.hitbox.h,
              cursor: 'pointer',
              // Debug: uncomment to see hitboxes
              // backgroundColor: 'rgba(255, 0, 0, 0.2)',
              // border: '1px solid red',
            }}
          />
        ))}

        {/* Speech bubble with message */}
        <div style={{
          position: 'absolute',
          left: 132,
          top: 203,
          width: 146,
          height: 133,
          backgroundImage: `url(${BUBBLE})`,
          backgroundSize: 'contain',
          backgroundRepeat: 'no-repeat',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          paddingBottom: 20,
        }}>
          <div style={{
            fontFamily: '"Comic Sans MS", cursive',
            fontSize: 16,
            fontWeight: 'bold',
            color: '#000',
            textAlign: 'center',
          }}>
            {message}
          </div>
          <div style={{
            fontFamily: '"Comic Sans MS", cursive',
            fontSize: 14,
            color: '#000',
            textAlign: 'center',
          }}>
            {subMessage}
          </div>
        </div>

        {/* Score display (Label4 from original) */}
        <div style={{
          position: 'absolute',
          left: 226,
          top: 345,
          fontFamily: '"Comic Sans MS", cursive',
          fontSize: 37,
          color: '#0000ff',
        }}>
          {score}
        </div>

        {/* Intro overlay */}
        {phase === 'intro' && (
          <div style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            backgroundColor: 'rgba(0, 100, 0, 0.9)',
            padding: '30px 50px',
            borderRadius: 15,
            textAlign: 'center',
          }}>
            <h2 style={{
              color: '#fff',
              fontFamily: '"Comic Sans MS", cursive',
              margin: '0 0 20px 0',
            }}>
              Le Marais Musical
            </h2>
            <p style={{
              color: '#fff',
              fontFamily: '"Comic Sans MS", cursive',
              marginBottom: 20,
            }}>
              Écoute les grenouilles chanter<br/>
              puis répète la séquence !
            </p>
            <button
              onClick={handleStart}
              style={{
                padding: '12px 30px',
                fontSize: 18,
                fontFamily: '"Comic Sans MS", cursive',
                fontWeight: 'bold',
                backgroundColor: '#4CAF50',
                color: '#fff',
                border: 'none',
                borderRadius: 8,
                cursor: 'pointer',
              }}
            >
              Jouer !
            </button>
          </div>
        )}

        {/* Fail overlay */}
        {phase === 'fail' && (
          <div style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            backgroundColor: 'rgba(150, 0, 0, 0.9)',
            padding: '30px 50px',
            borderRadius: 15,
            textAlign: 'center',
          }}>
            <h2 style={{
              color: '#fff',
              fontFamily: '"Comic Sans MS", cursive',
              margin: '0 0 10px 0',
            }}>
              Perdu !
            </h2>
            <p style={{
              color: '#fff',
              fontFamily: '"Comic Sans MS", cursive',
              marginBottom: 20,
            }}>
              Score final: {score}
            </p>
            <button
              onClick={handleStart}
              style={{
                padding: '10px 25px',
                fontSize: 16,
                fontFamily: '"Comic Sans MS", cursive',
                fontWeight: 'bold',
                backgroundColor: '#ff6b6b',
                color: '#fff',
                border: 'none',
                borderRadius: 8,
                cursor: 'pointer',
                marginRight: 10,
              }}
            >
              Rejouer
            </button>
            <button
              onClick={onClose}
              style={{
                padding: '10px 25px',
                fontSize: 16,
                fontFamily: '"Comic Sans MS", cursive',
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

        {/* Win overlay */}
        {phase === 'win' && (
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
            <h2 style={{
              color: '#fff',
              fontFamily: '"Comic Sans MS", cursive',
              margin: '0 0 10px 0',
              fontSize: 28,
            }}>
              BRAVO !
            </h2>
            <p style={{
              color: '#fff',
              fontFamily: '"Comic Sans MS", cursive',
              marginBottom: 20,
            }}>
              Tu as maîtrisé le marais !<br/>
              Score: {score}
            </p>
            <button
              onClick={onClose}
              style={{
                padding: '12px 30px',
                fontSize: 16,
                fontFamily: '"Comic Sans MS", cursive',
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
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            left: 566,
            top: 339,
            width: 62,
            height: 58,
            backgroundColor: 'transparent',
            border: 'none',
            cursor: 'pointer',
            // Debug: uncomment to see button
            // backgroundColor: 'rgba(255,0,0,0.3)',
          }}
          title="Quitter"
        />
      </div>

      {/* CSS for golden frog pulse animation */}
      <style>{`
        @keyframes pulse {
          from { transform: scale(1); filter: brightness(1); }
          to { transform: scale(1.1); filter: brightness(1.3); }
        }
      `}</style>
    </div>
  );
};

export default FrogGame;
