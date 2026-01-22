/**
 * Scene Component
 * Renders a game scene with background, hotspots, and overlays
 */

import React, { useEffect, useState, useCallback, useRef } from 'react';
import type { Scene as SceneType, Hotspot as HotspotType } from '../../types/game';
import { Hotspot, HotspotDebug } from './Hotspot';
import { commandExecutor } from '../../engine/CommandInterpreter';
import { useGameStore } from '../../store/gameStore';
import { useAudio } from '../../hooks/useAudio';
import { HtmlViewer } from '../UI/HtmlViewer';

// Original game resolution
const ORIGINAL_WIDTH = 640;
const ORIGINAL_HEIGHT = 480;

interface SceneProps {
  scene: SceneType;
  countryId: string;
  debug?: boolean;
}

interface DynamicImage {
  id: string;
  src: string;
  x: number;
  y: number;
}

export const Scene: React.FC<SceneProps> = ({ scene, countryId, debug = false }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(1);
  const [dynamicImages, setDynamicImages] = useState<Map<string, DynamicImage>>(new Map());
  const [currentText, setCurrentText] = useState<{ text: string; x: number; y: number } | null>(null);
  const [hoveredHotspot, setHoveredHotspot] = useState<HotspotType | null>(null);
  const [htmlContent, setHtmlContent] = useState<{
    src: string;
    rect?: { x: number; y: number; w: number; h: number };
  } | null>(null);

  // Scene ID from store (for reference)
  useGameStore((state) => state.currentScene);

  // Audio hook
  const { playSound, stopAll: stopAudio } = useAudio(countryId);

  // Calculate scale based on container size
  useEffect(() => {
    const updateScale = () => {
      if (containerRef.current) {
        const containerWidth = containerRef.current.clientWidth;
        const containerHeight = containerRef.current.clientHeight;
        const scaleX = containerWidth / ORIGINAL_WIDTH;
        const scaleY = containerHeight / ORIGINAL_HEIGHT;
        setScale(Math.min(scaleX, scaleY));
      }
    };

    updateScale();
    window.addEventListener('resize', updateScale);
    return () => window.removeEventListener('resize', updateScale);
  }, []);

  // Build asset path (convert BMP to PNG for images)
  const getAssetPath = useCallback(
    (filename: string, type: 'img' | 'audio' | 'video' | 'html' = 'img') => {
      const basePath = `/assets/${countryId}`;
      // Convert BMP to PNG for images
      const finalFilename = type === 'img' && filename.toLowerCase().endsWith('.bmp')
        ? filename.slice(0, -4) + '.png'
        : filename;
      switch (type) {
        case 'img':
          return `${basePath}/img24/${finalFilename}`;
        case 'audio':
          return `${basePath}/digit/${finalFilename}`;
        case 'video':
          return `${basePath}/movie/${finalFilename}`;
        case 'html':
          return `${basePath}/html/${finalFilename}`;
        default:
          return `${basePath}/${finalFilename}`;
      }
    },
    [countryId]
  );

  // Set up media callbacks
  useEffect(() => {
    commandExecutor.setMediaCallbacks({
      addImage: (id, src, x, y) => {
        setDynamicImages((prev) => {
          const next = new Map(prev);
          next.set(id, { id, src, x, y });
          return next;
        });
      },
      removeImage: (id) => {
        setDynamicImages((prev) => {
          const next = new Map(prev);
          next.delete(id);
          return next;
        });
      },
      showText: (text, x, y) => {
        setCurrentText({ text, x, y });
        // Auto-hide after 3 seconds
        setTimeout(() => setCurrentText(null), 3000);
      },
      playAudio: (src, loop) => {
        playSound(src, loop);
      },
      playVideo: (src, rect) => {
        console.log('Play video:', src, 'rect:', rect);
        // TODO: Implement video player
      },
      showHtml: (src, rect) => {
        const htmlPath = getAssetPath(src, 'html');
        setHtmlContent({ src: htmlPath, rect });
      },
      setCursor: (cursor) => {
        console.log('Set cursor:', cursor);
        // TODO: Implement custom cursors
      },
    });
  }, [playSound, getAssetPath]);

  // Execute scene enter commands
  useEffect(() => {
    if (scene.onEnter) {
      scene.onEnter.forEach((cmd) => commandExecutor.execute(cmd));
    }

    // Cleanup: execute exit commands and stop audio
    return () => {
      stopAudio();
      if (scene.onExit) {
        scene.onExit.forEach((cmd) => commandExecutor.execute(cmd));
      }
    };
  }, [scene, stopAudio]);

  const HotspotComponent = debug ? HotspotDebug : Hotspot;

  const containerStyle: React.CSSProperties = {
    position: 'relative',
    width: '100%',
    height: '100%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#000',
    overflow: 'hidden',
  };

  const gameAreaStyle: React.CSSProperties = {
    position: 'relative',
    width: ORIGINAL_WIDTH * scale,
    height: ORIGINAL_HEIGHT * scale,
    backgroundColor: '#1a1a2e',
  };

  const backgroundStyle: React.CSSProperties = {
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    objectFit: 'cover',
  };

  return (
    <div ref={containerRef} className="scene-container" style={containerStyle}>
      <div className="game-area" style={gameAreaStyle}>
        {/* Background */}
        {scene.background && (
          <img
            src={getAssetPath(scene.background)}
            alt="Scene background"
            style={backgroundStyle}
            onError={(e) => {
              // Fallback if image not found
              (e.target as HTMLImageElement).style.display = 'none';
            }}
          />
        )}

        {/* Dynamic images */}
        {Array.from(dynamicImages.values()).map((img) => (
          <img
            key={img.id}
            src={getAssetPath(img.src)}
            alt={img.id}
            style={{
              position: 'absolute',
              left: img.x * scale,
              top: img.y * scale,
              pointerEvents: 'none',
            }}
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = 'none';
            }}
          />
        ))}

        {/* Hotspots */}
        {scene.hotspots.map((hotspot) => (
          <HotspotComponent
            key={hotspot.id}
            hotspot={hotspot}
            scale={scale}
            onHover={setHoveredHotspot}
          />
        ))}

        {/* Text overlay */}
        {currentText && (
          <div
            className="text-overlay"
            style={{
              position: 'absolute',
              left: currentText.x * scale,
              top: currentText.y * scale,
              color: '#fff',
              fontSize: 18 * scale,
              fontFamily: 'Comic Sans MS, cursive',
              textShadow: '2px 2px 4px #000',
              pointerEvents: 'none',
              maxWidth: 400 * scale,
            }}
          >
            {currentText.text}
          </div>
        )}

        {/* Debug info */}
        {debug && (
          <div
            className="debug-info"
            style={{
              position: 'absolute',
              bottom: 10,
              left: 10,
              color: '#0f0',
              fontSize: 12,
              fontFamily: 'monospace',
              backgroundColor: 'rgba(0, 0, 0, 0.7)',
              padding: 8,
              borderRadius: 4,
            }}
          >
            <div>Scene: {scene.id}</div>
            <div>Country: {countryId}</div>
            <div>Hotspots: {scene.hotspots.length}</div>
            {hoveredHotspot && <div>Hovered: #{hoveredHotspot.id}</div>}
          </div>
        )}

        {/* HTML Viewer */}
        {htmlContent && (
          <HtmlViewer
            src={htmlContent.src}
            rect={htmlContent.rect}
            scale={scale}
            onClose={() => setHtmlContent(null)}
          />
        )}
      </div>
    </div>
  );
};

export default Scene;
