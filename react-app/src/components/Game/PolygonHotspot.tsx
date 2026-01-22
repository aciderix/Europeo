/**
 * Composant Hotspot avec support des polygones
 * Utilise SVG pour le rendu des zones cliquables polygonales
 */

import React, { useState, useCallback, useMemo } from 'react';
import type { PolygonHotspot as HotspotType, Point } from '../../types/polygon';
import { polygonToSvgPath, tuplesToPoints } from '../../utils/geometry';

interface PolygonHotspotProps {
  hotspot: HotspotType;
  scale: number;
  onHover: (hotspot: HotspotType | null) => void;
  onClick: (hotspot: HotspotType) => void;
  debug?: boolean;
}

export const PolygonHotspot: React.FC<PolygonHotspotProps> = ({
  hotspot,
  scale,
  onHover,
  onClick,
  debug = false,
}) => {
  const [isHovered, setIsHovered] = useState(false);

  const handleMouseEnter = useCallback(() => {
    setIsHovered(true);
    onHover(hotspot);
  }, [hotspot, onHover]);

  const handleMouseLeave = useCallback(() => {
    setIsHovered(false);
    onHover(null);
  }, [onHover]);

  const handleClick = useCallback(() => {
    onClick(hotspot);
  }, [hotspot, onClick]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onClick(hotspot);
    }
  }, [hotspot, onClick]);

  // Pas de zone cliquable = pas de rendu
  if (!hotspot.clickable_area) {
    return null;
  }

  const area = hotspot.clickable_area;
  const { bbox } = area;

  // Calcul des dimensions
  const width = (bbox.x2 - bbox.x1) * scale;
  const height = (bbox.y2 - bbox.y1) * scale;
  const left = bbox.x1 * scale;
  const top = bbox.y1 * scale;

  // Convertir les points du polygone
  const points: Point[] = useMemo(() => {
    if (area.type === 'polygon' && area.points && area.points.length >= 3) {
      return tuplesToPoints(area.points);
    }
    return [];
  }, [area]);

  // Générer le path SVG pour le polygone (relatif à la bbox)
  const svgPath = useMemo(() => {
    if (points.length < 3) return '';

    // Décaler les points pour qu'ils soient relatifs à la bbox
    const relativePoints = points.map(p => ({
      x: (p.x - bbox.x1) * scale,
      y: (p.y - bbox.y1) * scale,
    }));

    return polygonToSvgPath(relativePoints);
  }, [points, bbox, scale]);

  // Style du conteneur
  const containerStyle: React.CSSProperties = {
    position: 'absolute',
    left,
    top,
    width,
    height,
    cursor: 'pointer',
    pointerEvents: 'none',
  };

  // Si pas de polygone valide, utiliser un rectangle simple
  if (area.type !== 'polygon' || points.length < 3) {
    return (
      <div
        style={{
          ...containerStyle,
          pointerEvents: 'auto',
          backgroundColor: debug
            ? (isHovered ? 'rgba(255, 255, 0, 0.3)' : 'rgba(255, 255, 255, 0.1)')
            : 'transparent',
          border: debug ? '1px solid rgba(255, 255, 255, 0.5)' : 'none',
        }}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        role="button"
        tabIndex={0}
        aria-label={hotspot.text}
      />
    );
  }

  // Rendu avec SVG pour le polygone
  return (
    <div style={containerStyle}>
      <svg
        width={width}
        height={height}
        style={{ position: 'absolute', top: 0, left: 0 }}
        role="button"
        tabIndex={0}
        aria-label={hotspot.text}
        onKeyDown={handleKeyDown}
      >
        <path
          d={svgPath}
          fill={debug
            ? (isHovered ? 'rgba(255, 255, 0, 0.3)' : 'rgba(0, 255, 0, 0.15)')
            : 'transparent'
          }
          stroke={debug ? (isHovered ? '#ffff00' : '#00ff00') : 'transparent'}
          strokeWidth={debug ? 2 : 0}
          style={{ cursor: 'pointer', pointerEvents: 'auto' }}
          onMouseEnter={handleMouseEnter}
          onMouseLeave={handleMouseLeave}
          onClick={handleClick}
        />
      </svg>

      {/* Label en mode debug */}
      {debug && isHovered && (
        <div
          style={{
            position: 'absolute',
            left: '50%',
            top: '50%',
            transform: 'translate(-50%, -50%)',
            backgroundColor: 'rgba(0, 0, 0, 0.85)',
            color: '#fff',
            padding: '4px 8px',
            borderRadius: 4,
            fontSize: 11,
            whiteSpace: 'nowrap',
            pointerEvents: 'none',
            zIndex: 10,
          }}
        >
          {hotspot.text}
        </div>
      )}
    </div>
  );
};

export default PolygonHotspot;
