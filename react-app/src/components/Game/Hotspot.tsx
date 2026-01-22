/**
 * Hotspot Component
 * Represents a clickable area in the scene
 */

import React, { useState, useCallback } from 'react';
import type { Hotspot as HotspotType } from '../../types/game';
import { commandExecutor } from '../../engine/CommandInterpreter';

interface HotspotProps {
  hotspot: HotspotType;
  scale: number;
  onHover?: (hotspot: HotspotType | null) => void;
}

export const Hotspot: React.FC<HotspotProps> = ({ hotspot, scale, onHover }) => {
  const [, setIsHovered] = useState(false);

  const handleClick = useCallback(() => {
    if (hotspot.onClick) {
      hotspot.onClick.forEach((cmd) => commandExecutor.execute(cmd));
    }
  }, [hotspot.onClick]);

  const handleMouseEnter = useCallback(() => {
    setIsHovered(true);
    onHover?.(hotspot);
    if (hotspot.onEnter) {
      hotspot.onEnter.forEach((cmd) => commandExecutor.execute(cmd));
    }
  }, [hotspot, onHover]);

  const handleMouseLeave = useCallback(() => {
    setIsHovered(false);
    onHover?.(null);
    if (hotspot.onLeave) {
      hotspot.onLeave.forEach((cmd) => commandExecutor.execute(cmd));
    }
  }, [hotspot, onHover]);

  const { rect } = hotspot;
  const width = rect.x2 - rect.x1;
  const height = rect.y2 - rect.y1;

  const style: React.CSSProperties = {
    position: 'absolute',
    left: rect.x1 * scale,
    top: rect.y1 * scale,
    width: width * scale,
    height: height * scale,
    cursor: hotspot.cursor ? `url(${hotspot.cursor}), pointer` : 'pointer',
    // Debug mode: show hotspot boundaries
    // border: isHovered ? '2px solid rgba(255, 255, 0, 0.8)' : '1px solid rgba(255, 255, 255, 0.2)',
    // backgroundColor: isHovered ? 'rgba(255, 255, 0, 0.2)' : 'transparent',
    backgroundColor: 'transparent',
    border: 'none',
    zIndex: 10,
  };

  return (
    <div
      className="hotspot"
      style={style}
      onClick={handleClick}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      role="button"
      tabIndex={0}
      aria-label={hotspot.tooltip || `Hotspot ${hotspot.id}`}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          handleClick();
        }
      }}
    />
  );
};

// Debug version that shows hotspot boundaries
export const HotspotDebug: React.FC<HotspotProps> = ({ hotspot, scale, onHover }) => {
  const [isHovered, setIsHovered] = useState(false);

  const handleClick = useCallback(() => {
    console.log('Hotspot clicked:', hotspot.id, hotspot);
    if (hotspot.onClick) {
      hotspot.onClick.forEach((cmd) => commandExecutor.execute(cmd));
    }
  }, [hotspot]);

  const handleMouseEnter = useCallback(() => {
    setIsHovered(true);
    onHover?.(hotspot);
  }, [hotspot, onHover]);

  const handleMouseLeave = useCallback(() => {
    setIsHovered(false);
    onHover?.(null);
  }, [onHover]);

  const { rect } = hotspot;
  const width = rect.x2 - rect.x1;
  const height = rect.y2 - rect.y1;

  const style: React.CSSProperties = {
    position: 'absolute',
    left: rect.x1 * scale,
    top: rect.y1 * scale,
    width: width * scale,
    height: height * scale,
    cursor: 'pointer',
    border: isHovered ? '2px solid #ffff00' : '1px solid rgba(255, 255, 255, 0.5)',
    backgroundColor: isHovered ? 'rgba(255, 255, 0, 0.3)' : 'rgba(255, 255, 255, 0.1)',
    zIndex: 10,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: 10 * scale,
    color: '#fff',
    textShadow: '1px 1px 2px #000',
  };

  return (
    <div
      className="hotspot-debug"
      style={style}
      onClick={handleClick}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {hotspot.id}
    </div>
  );
};

export default Hotspot;
