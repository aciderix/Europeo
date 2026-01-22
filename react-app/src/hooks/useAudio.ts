/**
 * Audio Hook
 * Manages audio playback for the game
 */

import { useCallback, useRef, useEffect } from 'react';

interface AudioState {
  currentAudio: HTMLAudioElement | null;
  currentLoop: HTMLAudioElement | null;
}

export function useAudio(countryId: string) {
  const stateRef = useRef<AudioState>({
    currentAudio: null,
    currentLoop: null,
  });

  // Stop all audio on unmount or country change
  useEffect(() => {
    return () => {
      stopAll();
    };
  }, [countryId]);

  const getAudioPath = useCallback(
    (filename: string) => {
      return `/assets/${countryId}/digit/${filename}`;
    },
    [countryId]
  );

  const playSound = useCallback(
    (filename: string, loop: boolean = false) => {
      try {
        const audio = new Audio(getAudioPath(filename));
        audio.loop = loop;

        if (loop) {
          // Stop any existing loop
          if (stateRef.current.currentLoop) {
            stateRef.current.currentLoop.pause();
            stateRef.current.currentLoop = null;
          }
          stateRef.current.currentLoop = audio;
        } else {
          // Stop any existing one-shot
          if (stateRef.current.currentAudio) {
            stateRef.current.currentAudio.pause();
          }
          stateRef.current.currentAudio = audio;
        }

        audio.play().catch((err) => {
          console.warn('Audio playback failed:', err);
        });

        return audio;
      } catch (err) {
        console.error('Error creating audio:', err);
        return null;
      }
    },
    [getAudioPath]
  );

  const stopAll = useCallback(() => {
    if (stateRef.current.currentAudio) {
      stateRef.current.currentAudio.pause();
      stateRef.current.currentAudio = null;
    }
    if (stateRef.current.currentLoop) {
      stateRef.current.currentLoop.pause();
      stateRef.current.currentLoop = null;
    }
  }, []);

  const stopLoop = useCallback(() => {
    if (stateRef.current.currentLoop) {
      stateRef.current.currentLoop.pause();
      stateRef.current.currentLoop = null;
    }
  }, []);

  return {
    playSound,
    stopAll,
    stopLoop,
  };
}
