/**
 * Composant Scène avec hotspots polygones
 * Affiche le fond de scène et les zones cliquables
 */

import React, { useState, useCallback, useEffect } from 'react';
import type { PolygonScene as SceneType, PolygonHotspot as HotspotType } from '../../types/polygon';
import { PolygonHotspot } from './PolygonHotspot';
import { getAssetPath } from '../../engine/PolygonDataLoader';

interface PolygonSceneProps {
  scene: SceneType;
  countryId: string;
  scale: number;
  debug?: boolean;
  onHotspotClick: (hotspot: HotspotType) => void;
}

export const PolygonScene: React.FC<PolygonSceneProps> = ({
  scene,
  countryId,
  scale,
  debug = false,
  onHotspotClick,
}) => {
  const [hoveredHotspot, setHoveredHotspot] = useState<HotspotType | null>(null);
  const [backgroundLoaded, setBackgroundLoaded] = useState(false);
  const [backgroundError, setBackgroundError] = useState(false);

  // Chemin de l'image de fond
  const backgroundPath = getAssetPath(countryId, scene.background, 'image');

  // Reset état au changement de scène
  useEffect(() => {
    setBackgroundLoaded(false);
    setBackgroundError(false);
    setHoveredHotspot(null);
  }, [scene.id, countryId]);

  const handleBackgroundLoad = useCallback(() => {
    setBackgroundLoaded(true);
  }, []);

  const handleBackgroundError = useCallback(() => {
    setBackgroundError(true);
    console.error(`Erreur chargement image: ${backgroundPath}`);
  }, [backgroundPath]);

  const handleHover = useCallback((hotspot: HotspotType | null) => {
    setHoveredHotspot(hotspot);
  }, []);

  // Dimensions du jeu (zone de jeu = 400px, toolbar = 80px)
  const gameWidth = 640 * scale;
  const gameHeight = 400 * scale; // Sans la toolbar

  // Filtrer les hotspots avec zones cliquables
  const clickableHotspots = scene.hotspots.filter(h => h.clickable_area);

  return (
    <div
      className="polygon-scene"
      style={{
        position: 'relative',
        width: gameWidth,
        height: gameHeight,
        backgroundColor: '#000',
        overflow: 'hidden',
      }}
    >
      {/* Image de fond */}
      {!backgroundError ? (
        <img
          src={backgroundPath}
          alt={`Scene ${scene.id}`}
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: gameWidth,
            height: gameHeight,
            objectFit: 'cover',
            opacity: backgroundLoaded ? 1 : 0,
            transition: 'opacity 0.2s ease',
          }}
          onLoad={handleBackgroundLoad}
          onError={handleBackgroundError}
          draggable={false}
        />
      ) : (
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: gameWidth,
            height: gameHeight,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#666',
            fontSize: 14,
            flexDirection: 'column',
            gap: 8,
          }}
        >
          <div>Image non trouvée:</div>
          <div style={{ fontSize: 12, color: '#999' }}>{scene.background}</div>
        </div>
      )}

      {/* Hotspots avec polygones */}
      {clickableHotspots.map((hotspot) => (
        <PolygonHotspot
          key={hotspot.id}
          hotspot={hotspot}
          scale={scale}
          onHover={handleHover}
          onClick={onHotspotClick}
          debug={debug}
        />
      ))}

      {/* Tooltip du hotspot survolé */}
      {hoveredHotspot && (
        <div
          style={{
            position: 'absolute',
            left: Math.min(hoveredHotspot.text_position.x * scale, gameWidth - 200),
            top: Math.min(hoveredHotspot.text_position.y * scale, gameHeight - 40),
            backgroundColor: 'rgba(0, 0, 0, 0.9)',
            color: '#fff',
            padding: '6px 12px',
            borderRadius: 4,
            fontSize: Math.max(14 * scale, 12),
            fontFamily: '"Comic Sans MS", cursive, sans-serif',
            pointerEvents: 'none',
            zIndex: 100,
            maxWidth: 220 * scale,
            textAlign: 'center',
            boxShadow: '2px 2px 8px rgba(0,0,0,0.5)',
            border: '1px solid rgba(255,255,255,0.2)',
          }}
        >
          {hoveredHotspot.text}
        </div>
      )}

      {/* Infos debug */}
      {debug && (
        <div
          style={{
            position: 'absolute',
            bottom: 8,
            left: 8,
            backgroundColor: 'rgba(0, 0, 0, 0.85)',
            color: '#0f0',
            padding: '4px 8px',
            fontSize: 11,
            fontFamily: 'monospace',
            borderRadius: 4,
            zIndex: 100,
          }}
        >
          Scene {scene.id} | {scene.background} | {clickableHotspots.length} hotspots
        </div>
      )}
    </div>
  );
};

export default PolygonScene;
