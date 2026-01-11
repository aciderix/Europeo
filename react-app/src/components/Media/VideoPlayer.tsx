/**
 * Lecteur vidéo pour les animations du jeu
 * Gère la lecture des fichiers MP4 (convertis depuis AVI)
 */

import React, { useRef, useEffect, useCallback } from 'react';

interface VideoPlayerProps {
  src: string;
  onEnded: () => void;
  onError?: (error: string) => void;
  autoPlay?: boolean;
  controls?: boolean;
  style?: React.CSSProperties;
}

export const VideoPlayer: React.FC<VideoPlayerProps> = ({
  src,
  onEnded,
  onError,
  autoPlay = true,
  controls = false,
  style,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video || !autoPlay) return;

    // Reset la vidéo quand la source change
    video.load();
    video.play().catch((err) => {
      console.error('Erreur lecture vidéo:', err);
      onError?.(err.message || 'Erreur de lecture');
    });
  }, [src, autoPlay, onError]);

  const handleEnded = useCallback(() => {
    onEnded();
  }, [onEnded]);

  const handleError = useCallback(() => {
    const video = videoRef.current;
    const errorMessage = video?.error?.message || `Impossible de lire: ${src}`;
    console.error('VideoPlayer error:', errorMessage);
    onError?.(errorMessage);
  }, [src, onError]);

  return (
    <video
      ref={videoRef}
      src={src}
      style={{
        width: '100%',
        height: '100%',
        objectFit: 'contain',
        backgroundColor: '#000',
        ...style,
      }}
      onEnded={handleEnded}
      onError={handleError}
      controls={controls}
      playsInline
    />
  );
};

export default VideoPlayer;
