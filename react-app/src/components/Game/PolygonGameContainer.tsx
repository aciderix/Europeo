/**
 * Game Container avec support des polygones
 * Utilise les données extraites avec vnd_polygon_parser.py
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useGameStore } from '../../store/gameStore';
import { getScene, getAssetPath, getCountryList } from '../../engine/PolygonDataLoader';
import { PolygonScene } from './PolygonScene';
import type { PolygonScene as SceneType, PolygonHotspot } from '../../types/polygon';

// Mapping des noms de pays
const COUNTRY_NAMES: Record<string, string> = {
  couleurs1: 'Euroland',
  allem: 'Allemagne',
  angl: 'Angleterre',
  autr: 'Autriche',
  belge: 'Belgique',
  danem: 'Danemark',
  ecosse: 'Écosse',
  espa: 'Espagne',
  finlan: 'Finlande',
  france: 'France',
  grece: 'Grèce',
  holl: 'Pays-Bas',
  irland: 'Irlande',
  italie: 'Italie',
  portu: 'Portugal',
  suede: 'Suède',
  biblio: 'Bibliothèque',
};

interface PolygonGameContainerProps {
  initialCountry?: string;
  initialScene?: number;
  debug?: boolean;
}

export const PolygonGameContainer: React.FC<PolygonGameContainerProps> = ({
  initialCountry = 'couleurs1',
  initialScene = 1,
  debug = false,
}) => {
  const { currentCountry, currentScene, navigateTo, score } = useGameStore();
  const [scene, setSceneData] = useState<SceneType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentVideo, setCurrentVideo] = useState<string | null>(null);
  const [showCountryPicker, setShowCountryPicker] = useState(false);
  const [countries, setCountries] = useState<Array<{ id: string; name: string }>>([]);

  // Calculer l'échelle pour s'adapter à l'écran
  const scale = Math.min(
    (window.innerWidth - 40) / 640,
    (window.innerHeight - 120) / 480,
    1.5
  );

  // Charger la liste des pays
  useEffect(() => {
    getCountryList().then(setCountries).catch(console.error);
  }, []);

  // Initialisation
  useEffect(() => {
    if (currentCountry === 'frontal') {
      navigateTo(initialCountry, initialScene);
    }
  }, [initialCountry, initialScene, navigateTo, currentCountry]);

  // Charger la scène
  useEffect(() => {
    let mounted = true;

    async function loadScene() {
      setLoading(true);
      setError(null);

      try {
        const sceneData = await getScene(currentCountry, currentScene);
        if (!mounted) return;

        if (sceneData) {
          setSceneData(sceneData);
        } else {
          // Si la scène n'existe pas, essayer la première scène
          const firstScene = await getScene(currentCountry, 1);
          if (firstScene) {
            setSceneData(firstScene);
            navigateTo(currentCountry, 1);
          } else {
            setError(`Aucune scène trouvée pour ${currentCountry}`);
          }
        }
      } catch (err) {
        if (!mounted) return;
        setError(err instanceof Error ? err.message : 'Erreur de chargement');
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    loadScene();

    return () => {
      mounted = false;
    };
  }, [currentCountry, currentScene, navigateTo]);

  // Gestion des clics sur hotspot
  const handleHotspotClick = useCallback((hotspot: PolygonHotspot) => {
    console.log('Hotspot clicked:', hotspot.text, hotspot);

    // Si vidéo associée, la jouer
    if (hotspot.video) {
      const videoPath = getAssetPath(currentCountry, hotspot.video, 'video');
      setCurrentVideo(videoPath);
      return;
    }

    // Si navigation vers une autre scène
    if (hotspot.goto_scene) {
      navigateTo(currentCountry, hotspot.goto_scene);
    }
  }, [currentCountry, navigateTo]);

  // Fin de vidéo
  const handleVideoEnded = useCallback(() => {
    setCurrentVideo(null);
  }, []);

  // Sélection de pays
  const handleSelectCountry = useCallback((countryId: string) => {
    setShowCountryPicker(false);
    navigateTo(countryId, 1);
  }, [navigateTo]);

  // Dimensions
  const gameWidth = 640 * scale;
  const gameHeight = 400 * scale;
  const toolbarHeight = 60;

  if (loading) {
    return (
      <div style={{
        width: gameWidth,
        height: gameHeight + toolbarHeight,
        backgroundColor: '#1a1a2e',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#fff',
        margin: '20px auto',
        borderRadius: 8,
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 32, marginBottom: 16 }}>🌍</div>
          <div>Chargement de {COUNTRY_NAMES[currentCountry] || currentCountry}...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        width: gameWidth,
        height: gameHeight + toolbarHeight,
        backgroundColor: '#2d1b1b',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#fff',
        margin: '20px auto',
        borderRadius: 8,
        padding: 20,
        textAlign: 'center',
      }}>
        <div>
          <div style={{ fontSize: 32, marginBottom: 16 }}>⚠️</div>
          <div style={{ marginBottom: 16 }}>{error}</div>
          <button
            onClick={() => setShowCountryPicker(true)}
            style={{
              padding: '10px 20px',
              backgroundColor: '#3498db',
              border: 'none',
              borderRadius: 6,
              color: '#fff',
              cursor: 'pointer',
            }}
          >
            Choisir un pays
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      className="polygon-game-container"
      style={{
        width: gameWidth,
        margin: '20px auto',
        backgroundColor: '#000',
        borderRadius: 8,
        overflow: 'hidden',
        boxShadow: '0 4px 20px rgba(0,0,0,0.5)',
      }}
    >
      {/* Zone de jeu */}
      {scene && (
        <PolygonScene
          scene={scene}
          countryId={currentCountry}
          scale={scale}
          debug={debug}
          onHotspotClick={handleHotspotClick}
        />
      )}

      {/* Barre d'outils simplifiée */}
      <div
        style={{
          height: toolbarHeight,
          backgroundColor: '#1a1a2e',
          display: 'flex',
          alignItems: 'center',
          padding: '0 16px',
          gap: 12,
        }}
      >
        {/* Score */}
        <div style={{
          color: '#f1c40f',
          fontFamily: '"Comic Sans MS", cursive',
          fontSize: 16,
          fontWeight: 'bold',
        }}>
          Score: {score}
        </div>

        {/* Pays actuel */}
        <div style={{ color: '#fff', fontSize: 14, marginLeft: 'auto' }}>
          📍 {COUNTRY_NAMES[currentCountry] || currentCountry}
        </div>

        {/* Scène actuelle */}
        <div style={{ color: '#888', fontSize: 12 }}>
          Scene {currentScene}
        </div>

        {/* Bouton pays */}
        <button
          onClick={() => setShowCountryPicker(true)}
          style={{
            padding: '8px 16px',
            backgroundColor: '#3498db',
            border: 'none',
            borderRadius: 6,
            color: '#fff',
            cursor: 'pointer',
            fontSize: 14,
          }}
        >
          🌍 Pays
        </button>

        {/* Toggle debug */}
        {debug && (
          <div style={{
            padding: '4px 8px',
            backgroundColor: '#27ae60',
            borderRadius: 4,
            color: '#fff',
            fontSize: 11,
          }}>
            DEBUG
          </div>
        )}
      </div>

      {/* Lecteur vidéo (overlay) */}
      {currentVideo && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            backgroundColor: 'rgba(0,0,0,0.95)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
          onClick={handleVideoEnded}
        >
          <div style={{ position: 'relative', maxWidth: '90%', maxHeight: '90%' }}>
            <video
              src={currentVideo}
              autoPlay
              onEnded={handleVideoEnded}
              onError={() => {
                console.error('Erreur vidéo:', currentVideo);
                setCurrentVideo(null);
              }}
              style={{
                maxWidth: '100%',
                maxHeight: '80vh',
                borderRadius: 8,
              }}
            />
            <div style={{
              position: 'absolute',
              bottom: -30,
              left: '50%',
              transform: 'translateX(-50%)',
              color: '#888',
              fontSize: 12,
            }}>
              Cliquez pour fermer
            </div>
          </div>
        </div>
      )}

      {/* Sélecteur de pays */}
      {showCountryPicker && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            backgroundColor: 'rgba(0,0,0,0.9)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
          onClick={() => setShowCountryPicker(false)}
        >
          <div
            style={{
              backgroundColor: '#1a1a2e',
              borderRadius: 12,
              padding: 24,
              maxWidth: 600,
              maxHeight: '80vh',
              overflow: 'auto',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h2 style={{ color: '#f1c40f', marginTop: 0, textAlign: 'center' }}>
              🌍 Choisir un pays
            </h2>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(3, 1fr)',
                gap: 10,
                marginTop: 16,
              }}
            >
              {countries.map(({ id, name }) => (
                <button
                  key={id}
                  onClick={() => handleSelectCountry(id)}
                  style={{
                    padding: '12px 16px',
                    backgroundColor: id === currentCountry ? '#27ae60' : '#34495e',
                    border: id === currentCountry ? '2px solid #2ecc71' : '1px solid #555',
                    borderRadius: 8,
                    color: '#fff',
                    cursor: 'pointer',
                    fontSize: 14,
                    transition: 'all 0.2s',
                  }}
                  onMouseEnter={(e) => {
                    if (id !== currentCountry) {
                      e.currentTarget.style.backgroundColor = '#3498db';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (id !== currentCountry) {
                      e.currentTarget.style.backgroundColor = '#34495e';
                    }
                  }}
                >
                  {COUNTRY_NAMES[id] || name}
                </button>
              ))}
            </div>
            <button
              onClick={() => setShowCountryPicker(false)}
              style={{
                marginTop: 20,
                padding: '10px 24px',
                backgroundColor: '#e74c3c',
                border: 'none',
                borderRadius: 6,
                color: '#fff',
                cursor: 'pointer',
                display: 'block',
                marginLeft: 'auto',
                marginRight: 'auto',
              }}
            >
              Fermer
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default PolygonGameContainer;
