/**
 * HTML Viewer Component
 * Displays HTML content from the game in an iframe
 */

import React from 'react';

interface HtmlViewerProps {
  src: string;
  rect?: { x: number; y: number; w: number; h: number };
  onClose?: () => void;
  scale?: number;
}

export const HtmlViewer: React.FC<HtmlViewerProps> = ({
  src,
  rect,
  onClose,
  scale = 1,
}) => {
  const defaultRect = { x: 50, y: 50, w: 540, h: 380 };
  const bounds = rect || defaultRect;

  const overlayStyle: React.CSSProperties = {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    zIndex: 100,
  };

  const containerStyle: React.CSSProperties = {
    position: 'absolute',
    left: bounds.x * scale,
    top: bounds.y * scale,
    width: bounds.w * scale,
    height: bounds.h * scale,
    backgroundColor: '#fff',
    borderRadius: 8,
    boxShadow: '0 4px 20px rgba(0, 0, 0, 0.5)',
    overflow: 'hidden',
    display: 'flex',
    flexDirection: 'column',
  };

  const headerStyle: React.CSSProperties = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '8px 12px',
    backgroundColor: '#2c3e50',
    color: '#fff',
    fontSize: 14 * scale,
  };

  const closeButtonStyle: React.CSSProperties = {
    background: '#e74c3c',
    border: 'none',
    borderRadius: 4,
    padding: '4px 12px',
    color: '#fff',
    cursor: 'pointer',
    fontSize: 12 * scale,
  };

  const iframeStyle: React.CSSProperties = {
    flex: 1,
    border: 'none',
    width: '100%',
  };

  // Extract filename for title
  const filename = src.split('/').pop() || 'Document';

  return (
    <div style={overlayStyle} onClick={onClose}>
      <div style={containerStyle} onClick={(e) => e.stopPropagation()}>
        <div style={headerStyle}>
          <span>📄 {filename}</span>
          {onClose && (
            <button style={closeButtonStyle} onClick={onClose}>
              Fermer ✕
            </button>
          )}
        </div>
        <iframe
          src={src}
          title={filename}
          style={iframeStyle}
          sandbox="allow-same-origin"
        />
      </div>
    </div>
  );
};

export default HtmlViewer;
