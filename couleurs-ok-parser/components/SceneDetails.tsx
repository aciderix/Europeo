
import React, { useState } from 'react';
import { ParsedScene, HotspotCommand, Hotspot } from '../types';
import { Image, Box, MousePointer2, Music, Type, Code, MonitorPlay, MousePointerClick, MessageSquare, Video, ScrollText, AlertTriangle, CheckCircle2, FileWarning, FileImage, Trophy, HelpCircle, Ban, Sparkles, Database } from 'lucide-react';

interface SceneDetailsProps {
  scene: ParsedScene;
  gameSlot?: number;
  isExcluded?: boolean;
}

export const SceneDetails: React.FC<SceneDetailsProps> = ({ scene, gameSlot, isExcluded }) => {
  const [activeTab, setActiveTab] = useState<'files' | 'hotspots' | 'config'>('files');

  // --- RENDU SPECIAL POUR SLOT VIDE ---
  if (scene.sceneType === 'empty') {
      return (
          <div className="bg-slate-900/40 rounded-lg border border-slate-800 p-3 mb-2 flex items-center justify-between opacity-60 hover:opacity-100 transition-opacity">
              <div className="flex items-center gap-3">
                  <span className="bg-slate-800 text-slate-500 text-xs px-2 py-1 rounded font-mono">SLOT {gameSlot}</span>
                  <span className="text-sm font-bold text-slate-600 flex items-center gap-2">
                      <Ban size={14} /> EMPLACEMENT VIDE
                  </span>
              </div>
              <span className="text-xs font-mono text-slate-700">@0x{scene.offset.toString(16).toUpperCase()}</span>
          </div>
      );
  }

  // Helper to interpret command IDs
  const getCommandLabel = (cmd: HotspotCommand) => {
    // ID 0 : Affichage / Config
    if (cmd.id === 0) {
        if (cmd.subtype === 39) return { label: "Config Police", icon: <Type size={12} />, color: "text-fuchsia-400", bg: "bg-fuchsia-950/30", border: "border-fuchsia-900" };
        if (cmd.subtype === 38) return { label: "Affichage Texte", icon: <MessageSquare size={12} />, color: "text-blue-300", bg: "bg-blue-950/30", border: "border-blue-900" };
        if (cmd.subtype === 24) return { label: "Zone Image", icon: <Image size={12} />, color: "text-sky-300", bg: "bg-sky-950/30", border: "border-sky-900" };
        if (cmd.subtype === 27) return { label: "Image Overlay", icon: <FileImage size={12} />, color: "text-cyan-300", bg: "bg-cyan-950/30", border: "border-cyan-900" };
        if (cmd.subtype === 41) return { label: "Score / Logic", icon: <Trophy size={12} />, color: "text-orange-400", bg: "bg-orange-950/30", border: "border-orange-900" };
        return { label: `Display (Sub:${cmd.subtype})`, icon: <MonitorPlay size={12} />, color: "text-slate-400", bg: "bg-slate-950/30", border: "border-slate-800" };
    }
    // ID 1 : Média
    if (cmd.id === 1) {
        if (cmd.subtype === 6) return { label: "Son Système", icon: <MousePointerClick size={12} />, color: "text-amber-400", bg: "bg-amber-950/30", border: "border-amber-900" };
        if (cmd.subtype === 9) return { label: "Vidéo AVI", icon: <Video size={12} />, color: "text-red-400", bg: "bg-red-950/30", border: "border-red-900" };
        if (cmd.subtype === 11) return { label: "Audio WAV", icon: <Music size={12} />, color: "text-pink-400", bg: "bg-pink-950/30", border: "border-pink-900" };
        return { label: `Media (Sub:${cmd.subtype})`, icon: <Music size={12} />, color: "text-yellow-600", bg: "bg-yellow-950/30", border: "border-yellow-900" };
    }
    // ID 3 : Script
    if (cmd.id === 3) {
        if (cmd.subtype === 21) return { label: "Script Logic", icon: <Code size={12} />, color: "text-emerald-400", bg: "bg-emerald-950/30", border: "border-emerald-900" };
        if (cmd.subtype === 6) return { label: "Navigation", icon: <MousePointerClick size={12} />, color: "text-emerald-500", bg: "bg-emerald-950/30", border: "border-emerald-900" };
        return { label: `Script (Sub:${cmd.subtype})`, icon: <Code size={12} />, color: "text-emerald-600", bg: "bg-emerald-950/30", border: "border-emerald-900" };
    }
    // ID 9999 : Recovered / Inconnu
    if (cmd.id === 9999) {
        return { label: "Commande", icon: <Sparkles size={12} />, color: "text-indigo-400", bg: "bg-indigo-950/30", border: "border-indigo-900" };
    }
    
    return { label: `Cmd ${cmd.id}:${cmd.subtype}`, icon: <HelpCircle size={12} />, color: "text-slate-500", bg: "bg-slate-900", border: "border-slate-800" };
  };

  const renderRecoveredBadge = (hs: Hotspot) => {
      // Discret, intégré au flux
      return <span className="flex items-center gap-1 text-[10px] font-medium text-indigo-400 bg-indigo-950/30 px-1.5 py-0.5 rounded border border-indigo-900/50"><Sparkles size={10} /> RECOVERED</span>;
  }

  const renderHealthBadge = () => {
      switch (scene.parseMethod) {
          case 'signature':
              return (
                <span className="flex items-center gap-1 text-[10px] uppercase font-bold text-emerald-400 bg-emerald-950/50 px-2 py-1 rounded border border-emerald-900">
                    <CheckCircle2 size={12} /> Structure Saine
                </span>
              );
          case 'heuristic_recovered':
              return (
                <span className="flex items-center gap-1 text-[10px] uppercase font-bold text-indigo-400 bg-indigo-950/50 px-2 py-1 rounded border border-indigo-900">
                    <Sparkles size={12} /> Données Récupérées
                </span>
              );
          default:
              return (
                <span className="flex items-center gap-1 text-[10px] uppercase font-bold text-amber-400 bg-amber-950/50 px-2 py-1 rounded border border-amber-900">
                    <FileWarning size={12} /> Mode Heuristique (Incertain)
                </span>
              );
      }
  };

  // Helper pour calculer la viewBox SVG en fonction des points
  const getSvgViewBox = (points: { x: number; y: number }[]) => {
      if (!points || points.length === 0) return "0 0 640 480";

      const xs = points.map(p => p.x);
      const ys = points.map(p => p.y);
      const minX = Math.min(...xs);
      const maxX = Math.max(...xs);
      const minY = Math.min(...ys);
      const maxY = Math.max(...ys);

      const width = Math.max(10, maxX - minX);
      const height = Math.max(10, maxY - minY);
      const padding = 10;

      // Si les coordonnées sont standard, on garde 640x480, sinon on zoom sur l'objet
      if (minX >= 0 && maxX <= 800 && minY >= 0 && maxY <= 600) {
          return "0 0 800 600";
      }

      return `${minX - padding} ${minY - padding} ${width + padding * 2} ${height + padding * 2}`;
  };

  return (
    <div className={`bg-slate-800 rounded-lg border overflow-hidden mb-6 shadow-xl ${isExcluded ? 'border-red-900/50 opacity-60' : 'border-slate-700'}`}>
      {/* Header avec Statut de Santé */}
      <div className="p-4 bg-slate-900 border-b border-slate-700 flex flex-wrap justify-between items-center gap-4">
        <div>
          <div className="flex items-center gap-3 flex-wrap">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
                {gameSlot !== undefined && (
                  <span className="bg-emerald-600 text-xs px-2 py-1 rounded shadow">SLOT {gameSlot}</span>
                )}
                {scene.sceneName && (
                    <span className="bg-purple-950 text-purple-200 text-xs px-2 py-1 rounded border border-purple-800 font-mono">
                        "{scene.sceneName}"
                    </span>
                )}
                {isExcluded && (
                  <span className="bg-red-950 text-red-400 text-[10px] uppercase px-2 py-1 rounded border border-red-900">
                    EXCLU
                  </span>
                )}
                {scene.files.length > 50 && (
                     <span className="bg-purple-600 text-[10px] uppercase px-2 py-1 rounded shadow flex items-center gap-1">
                        <Database size={12} /> Global Vars
                     </span>
                )}
            </h3>
            {renderHealthBadge()}
          </div>
          <div className="flex gap-4 mt-2 text-xs font-mono text-slate-500">
             <span>Start: <span className="text-slate-300">0x{scene.offset.toString(16).toUpperCase()}</span></span>
             <span>Len: <span className="text-slate-300">{scene.length} bytes</span></span>
          </div>
        </div>
        
        <div className="flex bg-slate-950 rounded-lg p-1 gap-1">
          <button
            onClick={() => setActiveTab('files')}
            className={`px-3 py-1.5 rounded text-sm font-medium transition-colors flex items-center gap-2 ${activeTab === 'files' ? 'bg-slate-700 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'}`}
          >
            <Image size={14} /> Fichiers ({scene.files.length})
          </button>
          <button
            onClick={() => setActiveTab('hotspots')}
            className={`px-3 py-1.5 rounded text-sm font-medium transition-colors flex items-center gap-2 ${activeTab === 'hotspots' ? 'bg-slate-700 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'}`}
          >
            <MousePointer2 size={14} /> Hotspots ({scene.hotspots.length})
          </button>
          <button
            onClick={() => setActiveTab('config')}
            className={`px-3 py-1.5 rounded text-sm font-medium transition-colors flex items-center gap-2 ${activeTab === 'config' ? 'bg-slate-700 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200'}`}
          >
            <Box size={14} /> Logic
          </button>
        </div>
      </div>

      {/* Warnings Area */}
      {scene.warnings.length > 0 && (
          <div className="bg-amber-950/30 border-b border-amber-900/50 p-2 px-4">
              {scene.warnings.map((w, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs text-amber-400 font-mono">
                      <AlertTriangle size={12} /> {w}
                  </div>
              ))}
          </div>
      )}

      <div className="p-4 bg-slate-800/50">
        {activeTab === 'files' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
            {scene.files.map((file) => {
              const isTitle = file.slot === 1;
              return (
                <div key={file.slot} className={`p-3 rounded border relative group ${file.filename ? 'bg-slate-700/50 border-slate-600' : 'bg-slate-900/50 border-slate-800 opacity-50'} ${isTitle ? 'md:col-span-2 lg:col-span-4 bg-gradient-to-r from-slate-800 to-slate-700 !border-blue-900/50' : ''}`}>
                  <div className="flex justify-between items-start mb-2">
                    <span className={`text-xs font-bold uppercase ${isTitle ? 'text-blue-400' : 'text-slate-500'}`}>
                        {isTitle ? 'Background / Titre' : `Slot ${file.slot}`}
                    </span>
                    <span className="text-[10px] text-slate-600 font-mono">@0x{file.offset.toString(16).toUpperCase()}</span>
                  </div>
                  {file.filename ? (
                    <div className={`text-sm font-medium break-all ${isTitle ? 'text-white text-base' : 'text-emerald-300'}`}>{file.filename}</div>
                  ) : (
                    <div className="text-sm italic text-slate-600">Vide</div>
                  )}
                  {file.param !== 0 && (
                      <div className="absolute bottom-2 right-2 text-[10px] bg-slate-950 px-1.5 rounded text-slate-400 border border-slate-800">
                          Param: {file.param}
                      </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {activeTab === 'hotspots' && (
          <div className="space-y-3">
             {scene.hotspots.length === 0 ? (
                <div className="text-center py-8 border-2 border-dashed border-slate-700 rounded-lg">
                    <MousePointer2 className="mx-auto text-slate-600 mb-2" size={32} />
                    <p className="text-slate-500 italic">Aucun hotspot interactif détecté.</p>
                </div>
             ) : (
                scene.hotspots.map((hs, i) => (
                  <div key={i} className={`bg-slate-900/80 border border-slate-700 rounded p-3 transition-colors ${hs.isRecovered ? 'border-indigo-900/30' : ''}`}>
                    <div className="flex justify-between items-center mb-2 pb-2 border-b border-slate-800">
                       <div className="flex items-center gap-2">
                           <span className="font-bold text-slate-300 text-sm">Obj #{hs.index + 1 !== 0 ? hs.index + 1 : '?'}</span>
                           {hs.isRecovered && renderRecoveredBadge(hs)}
                           <span className="text-[10px] bg-slate-950 text-slate-500 px-1.5 py-0.5 rounded font-mono border border-slate-800">@0x{hs.offset.toString(16).toUpperCase()}</span>
                       </div>
                       <span className="text-xs text-slate-500 font-mono flex gap-2">
                         <span className={`px-1 rounded ${hs.geometry.pointCount > 0 ? 'bg-emerald-900 text-emerald-400' : 'bg-slate-800 text-slate-400'}`}>
                             Pts: {hs.geometry.pointCount}
                         </span>
                         <span className={`px-1 rounded ${hs.commands.length > 0 ? 'bg-slate-800 text-slate-400' : 'bg-red-950 text-red-400'}`}>Cmds: {hs.commands.length}</span>
                       </span>
                    </div>
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                        <div>
                            {hs.commands.length > 0 ? (
                                <ul className="space-y-1">
                                    {hs.commands.map((cmd, idx) => {
                                        const info = getCommandLabel(cmd);
                                        return (
                                            <li key={idx} className={`text-xs flex items-center gap-2 ${info.bg} border ${info.border} px-2 py-1.5 rounded`}>
                                                <div className={`${info.color} shrink-0`}>{info.icon}</div>
                                                <div className="flex-1 min-w-0 flex justify-between items-center">
                                                    <span className={`font-semibold ${info.color} mr-2`}>{info.label}</span>
                                                    <div className="text-slate-300 font-mono truncate max-w-[150px] opacity-80" title={cmd.param}>
                                                        {cmd.param}
                                                    </div>
                                                </div>
                                            </li>
                                        );
                                    })}
                                </ul>
                            ) : (
                                <div className="h-full flex flex-col items-center justify-center p-4 border border-dashed border-slate-800 rounded bg-slate-950/30">
                                    <span className="text-slate-600 text-xs italic flex items-center gap-2 mb-1">
                                        <AlertTriangle size={12} /> Script manquant ou non détecté
                                    </span>
                                    {hs.geometry.cursorId > 30 && hs.geometry.cursorId < 128 && (
                                        <div className="text-[10px] text-indigo-400 bg-indigo-950/30 px-2 py-1 rounded border border-indigo-900/50">
                                            Indice: CursorID '{String.fromCharCode(hs.geometry.cursorId)}' ({hs.geometry.cursorId})
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                        <div className="relative h-full min-h-[60px] bg-slate-950 rounded border border-slate-800 p-2 flex items-center justify-center">
                             {hs.geometry.points.length > 0 ? (
                                <div className="w-full text-center">
                                    <div className="text-[10px] text-slate-500 mb-1 uppercase tracking-widest">Hitbox Preview</div>
                                    <svg viewBox={getSvgViewBox(hs.geometry.points)} className="w-full h-24 bg-slate-900 border border-slate-800 rounded">
                                        <polygon 
                                            points={hs.geometry.points.map(p => `${p.x},${p.y}`).join(' ')} 
                                            className="fill-emerald-500/20 stroke-emerald-500 stroke-1"
                                        />
                                    </svg>
                                    <div className="mt-1 text-[9px] text-slate-600 font-mono">
                                        Cursor ID: {hs.geometry.cursorId} | Flags: {hs.geometry.extraFlag}
                                    </div>
                                </div>
                             ) : (
                                 <div className="text-center">
                                     <span className="text-xs text-slate-600">Sans géométrie</span>
                                 </div>
                             )}
                        </div>
                    </div>
                  </div>
                ))
             )}
          </div>
        )}

        {activeTab === 'config' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
             <div className="lg:col-span-2 bg-slate-900/50 p-4 rounded border border-slate-800 flex flex-col h-full">
                <div className="flex items-center justify-between mb-3">
                    <h4 className="text-sm font-bold text-slate-300 flex items-center gap-2">
                        <ScrollText size={16} className="text-emerald-400" />
                        Init Script
                    </h4>
                    <span className="text-[10px] text-slate-500 font-mono">
                        {scene.initScript.commands.length} instructions
                    </span>
                </div>
                
                <div className="bg-slate-950 rounded-lg border border-slate-800 flex-1 overflow-y-auto p-2 min-h-[200px] max-h-[400px]">
                    {scene.initScript.commands.length > 0 ? (
                        <ul className="space-y-1">
                            {scene.initScript.commands.map((cmd: any, idx) => {
                                const info = getCommandLabel(cmd);
                                return (
                                <li 
                                    key={idx} 
                                    className={`text-xs font-mono border-b pb-1 mb-1 last:border-0 ${cmd.isRecovered ? 'text-indigo-300 border-indigo-900/30 bg-indigo-950/10 p-1 rounded border' : 'text-slate-400 border-slate-900'}`}
                                >
                                    {cmd.isRecovered ? (
                                        <div className="flex items-start gap-2">
                                            <Sparkles size={12} className="text-indigo-500 mt-0.5 shrink-0" />
                                            <div className="break-all">
                                                <span className="text-indigo-200">{cmd.param}</span>
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="flex items-start gap-2">
                                            <span className={`${info.color} mt-0.5 shrink-0`}>{info.icon}</span>
                                            <div>
                                                <span className="text-purple-400 mr-2 text-[10px] opacity-70">[{cmd.id}:{cmd.subtype || 0}]</span>
                                                <span className="text-slate-300">{cmd.param}</span>
                                            </div>
                                        </div>
                                    )}
                                </li>
                            )})}
                        </ul>
                    ) : (
                        <div className="h-full flex flex-col items-center justify-center text-slate-700 italic text-xs gap-2">
                            <Code size={24} />
                            Aucun script d'initialisation.
                        </div>
                    )}
                </div>
             </div>

             <div className="bg-slate-900/50 p-4 rounded border border-slate-800 h-full">
                <h4 className="text-sm font-bold text-slate-400 mb-3 uppercase tracking-wider">Configuration</h4>
                
                <div className="mb-4">
                    <label className="text-[10px] uppercase text-slate-600 font-bold block mb-1">Offset</label>
                    <div className="font-mono text-xs text-blue-400 bg-slate-950 p-1.5 rounded border border-slate-800">
                        0x{scene.config.offset !== -1 ? scene.config.offset.toString(16).toUpperCase() : 'N/A'}
                    </div>
                </div>

                <div className="mb-4">
                    <label className="text-[10px] uppercase text-slate-600 font-bold block mb-1">Signature Flag</label>
                    {scene.config.foundSignature ? (
                        <div className="font-mono text-xs text-emerald-400 bg-emerald-950/30 p-1.5 rounded border border-emerald-900 flex items-center gap-2">
                            <CheckCircle2 size={10} /> 0x{scene.config.flag.toString(16).toUpperCase()}
                        </div>
                    ) : (
                        <div className="font-mono text-xs text-red-400 bg-red-950/30 p-1.5 rounded border border-red-900 flex items-center gap-2">
                            <AlertTriangle size={10} /> MISSING
                        </div>
                    )}
                </div>

                <div>
                    <label className="text-[10px] uppercase text-slate-600 font-bold block mb-1">Paramètres Entiers</label>
                    <div className="grid grid-cols-2 gap-2">
                        {scene.config.ints.map((val, i) => (
                            <div key={i} className="bg-slate-950 p-1.5 rounded text-center border border-slate-800">
                                <span className="text-[9px] text-slate-600 block">INT {i}</span>
                                <span className="text-xs font-mono text-slate-300">{val}</span>
                            </div>
                        ))}
                        {scene.config.ints.length === 0 && <span className="text-xs text-slate-600 italic col-span-2 text-center">Aucun paramètre</span>}
                    </div>
                </div>
             </div>
          </div>
        )}
      </div>
    </div>
  );
};
