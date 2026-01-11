/**
 * Barre d'outils du jeu avec les images originales
 * Hauteur: 80px (résolution 640x480, zone de jeu 640x400)
 */

import React, { useState } from 'react';
import { useGameStore } from '../../store/gameStore';

interface GameToolbarProps {
  scale: number;
  onBackClick?: () => void;
  onInventoryClick?: () => void;
  onCalculatorClick?: () => void;
  onPhoneClick?: () => void;
  onCountryClick?: () => void;
}

// Mapping des pays vers leurs images de drapeau
const COUNTRY_FLAGS: Record<string, string> = {
  couleurs1: 'p_euroland.png',
  allem: 'p_all.png',
  angl: 'p_angl.png',
  autr: 'p_autriche.png',
  belge: 'p_belgique.png',
  danem: 'p_danemark.png',
  ecosse: 'p_ecosse.png',
  espa: 'p_espagne.png',
  finlan: 'p_finland.png',
  france: 'p_france.png',
  grece: 'p_grece.png',
  holl: 'p_pays.png',
  irland: 'p_irlande.png',
  italie: 'p_italie.png',
  portu: 'p_port.png',
  suede: 'p_suede.png',
};

// Composant bouton de la toolbar
interface ToolbarButtonProps {
  normalImage: string;
  hoverImage: string;
  alt: string;
  onClick?: () => void;
  scale: number;
  width?: number;
  height?: number;
}

const ToolbarButton: React.FC<ToolbarButtonProps> = ({
  normalImage,
  hoverImage,
  alt,
  onClick,
  scale,
  width = 50,
  height = 50,
}) => {
  const [isHovered, setIsHovered] = useState(false);
  const basePath = '/assets/barre/images';

  return (
    <button
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={{
        width: width * scale,
        height: height * scale,
        padding: 0,
        border: 'none',
        backgroundColor: 'transparent',
        cursor: 'pointer',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
      title={alt}
    >
      <img
        src={`${basePath}/${isHovered ? hoverImage : normalImage}`}
        alt={alt}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'contain',
        }}
        onError={(e) => {
          // Fallback si l'image n'existe pas
          (e.target as HTMLImageElement).style.display = 'none';
        }}
      />
    </button>
  );
};

// Affichage du score avec les images de chiffres
const ScoreDisplay: React.FC<{ score: number; scale: number }> = ({ score, scale }) => {
  const digits = String(Math.min(score, 99999)).padStart(5, '0').split('');
  const basePath = '/assets/barre/images';

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      {digits.map((digit, index) => (
        <img
          key={index}
          src={`${basePath}/f${parseInt(digit) + 1}.png`}
          alt={digit}
          style={{
            width: 16 * scale,
            height: 24 * scale,
            objectFit: 'contain',
          }}
          onError={(e) => {
            // Fallback: afficher le chiffre en texte
            const span = document.createElement('span');
            span.textContent = digit;
            span.style.color = '#f1c40f';
            span.style.fontFamily = 'monospace';
            span.style.fontSize = `${18 * scale}px`;
            span.style.fontWeight = 'bold';
            (e.target as HTMLElement).replaceWith(span);
          }}
        />
      ))}
    </div>
  );
};

export const GameToolbar: React.FC<GameToolbarProps> = ({
  scale,
  onBackClick,
  onInventoryClick,
  onCalculatorClick,
  onPhoneClick,
  onCountryClick,
}) => {
  const { score, currentCountry, inventory, variables } = useGameStore();

  const toolbarHeight = 80 * scale;
  const flagImage = COUNTRY_FLAGS[currentCountry] || 'p_euroland.png';

  // Vérifier si certains items sont actifs dans l'inventaire ou variables
  const hasCalculator = variables['CALC'] === 1 || inventory.includes('calc');
  const hasBag = variables['SACADOS'] === 1 || inventory.includes('sac');
  const hasPhone = variables['TELEPHONE'] === 1 || inventory.includes('telep');

  return (
    <div
      className="game-toolbar"
      style={{
        width: 640 * scale,
        height: toolbarHeight,
        backgroundImage: 'url(/assets/barre/images/barre.png)',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundColor: '#2c3e50',
        display: 'flex',
        alignItems: 'center',
        padding: `0 ${16 * scale}px`,
        gap: 8 * scale,
        boxSizing: 'border-box',
      }}
    >
      {/* Bouton retour */}
      <ToolbarButton
        normalImage="fleche.png"
        hoverImage="fleche2.png"
        alt="Retour"
        onClick={onBackClick}
        scale={scale}
        width={40}
        height={40}
      />

      {/* Bouton transport/active */}
      <ToolbarButton
        normalImage="trans.png"
        hoverImage="trans2.png"
        alt="Transport"
        onClick={onCountryClick}
        scale={scale}
      />

      {/* Calculatrice Euro */}
      <ToolbarButton
        normalImage={hasCalculator ? 'calc2.png' : 'calc1.png'}
        hoverImage="calc2.png"
        alt="Calculatrice Euro"
        onClick={onCalculatorClick}
        scale={scale}
      />

      {/* Téléphone aide */}
      <ToolbarButton
        normalImage={hasPhone ? 'telep2.png' : 'telep.png'}
        hoverImage="telep2.png"
        alt="Aide téléphonique"
        onClick={onPhoneClick}
        scale={scale}
      />

      {/* Sac à dos / Inventaire */}
      <ToolbarButton
        normalImage={hasBag ? 'sac2.png' : 'sac.png'}
        hoverImage="sac2.png"
        alt="Inventaire"
        onClick={onInventoryClick}
        scale={scale}
      />

      {/* Espace flexible */}
      <div style={{ flex: 1 }} />

      {/* Score */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8 * scale,
          backgroundColor: 'rgba(0,0,0,0.3)',
          padding: `${4 * scale}px ${12 * scale}px`,
          borderRadius: 4 * scale,
        }}
      >
        <span
          style={{
            color: '#f1c40f',
            fontSize: 12 * scale,
            fontFamily: '"Comic Sans MS", cursive',
          }}
        >
          Score:
        </span>
        <ScoreDisplay score={score} scale={scale} />
      </div>

      {/* Drapeau du pays actuel */}
      <button
        onClick={onCountryClick}
        style={{
          width: 60 * scale,
          height: 45 * scale,
          padding: 0,
          border: `2px solid rgba(255,255,255,0.3)`,
          borderRadius: 4 * scale,
          backgroundColor: 'transparent',
          cursor: 'pointer',
          overflow: 'hidden',
        }}
        title="Changer de pays"
      >
        <img
          src={`/assets/barre/images/${flagImage}`}
          alt={currentCountry}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
          onError={(e) => {
            (e.target as HTMLImageElement).src = '/assets/barre/images/p_euroland.png';
          }}
        />
      </button>
    </div>
  );
};

export default GameToolbar;
