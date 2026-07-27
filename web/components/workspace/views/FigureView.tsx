"use client";

import React, { useState } from "react";
import { useWorkspaceStore } from "@/hooks/useWorkspaceStore";
import { motion, AnimatePresence } from "framer-motion";
import { Image as ImageIcon, Eye, Maximize2, X, Download } from "lucide-react";

export function FigureView() {
  const { fullDocumentData, activePaperId, setActivePageNumber, setSelectedBoundingBox } = useWorkspaceStore();
  const [selectedImage, setSelectedImage] = useState<{ url: string; caption: string } | null>(null);

  const realFigures = fullDocumentData?.figures || [];
  const isDynamic = realFigures.length > 0;

  const getImageUrl = (imagePath?: string, pageNumber?: number) => {
    if (!imagePath) return null;
    const normalized = imagePath.replace(/\\/g, "/");
    const parts = normalized.split("/");
    const filename = parts[parts.length - 1];
    const folder = parts[parts.length - 2];

    if (filename && folder && folder !== "figures") {
      return `http://localhost:8000/figures/${folder}/${filename}`;
    }
    if (filename && activePaperId) {
      return `http://localhost:8000/figures/${activePaperId}/${filename}`;
    }
    return null;
  };

  return (
    <div className="h-full bg-[#070a12] p-8 overflow-y-auto relative">
      <div className="max-w-5xl mx-auto space-y-6">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <ImageIcon className="w-5 h-5 text-purple-400" />
            Extracted Figures & Diagrams {isDynamic && (
              <span className="text-xs font-mono text-emerald-400 font-normal px-2.5 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20">
                LIVE FASTAPI DATA ({realFigures.length} Figures Extracted)
              </span>
            )}
          </h2>
          <p className="text-xs text-slate-400 mt-1 font-mono">
            FigureExtractor • PyMuPDF High-Res Cropping & Image Serving
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {isDynamic ? (
            realFigures.map((fig, idx) => {
              const figId = fig.id || fig.figure_id || `fig-${idx}`;
              const imageUrl = getImageUrl(fig.image_path, fig.page_number);
              const captionText = fig.caption || `Figure on Page ${fig.page_number}`;

              return (
                <motion.div
                  key={figId}
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: Math.min(idx * 0.05, 0.4) }}
                  className="glass-panel rounded-2xl p-6 border-slate-800 space-y-4 flex flex-col justify-between group hover:border-purple-500/40 transition-all"
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-mono text-purple-400 px-2.5 py-1 rounded bg-purple-500/10 border border-purple-500/20 uppercase font-semibold">
                        {fig.figure_type || "Extracted Figure"}
                      </span>
                      <span className="text-[10px] font-mono text-slate-500 font-semibold">
                        Page {fig.page_number}
                      </span>
                    </div>

                    {/* Figure Image Container */}
                    <div className="w-full h-56 rounded-xl bg-slate-950 border border-slate-800/80 flex items-center justify-center p-3 relative overflow-hidden group-hover:border-purple-500/30 transition-colors">
                      {imageUrl ? (
                        <div className="w-full h-full relative flex items-center justify-center cursor-pointer overflow-hidden group/img" onClick={() => setSelectedImage({ url: imageUrl, caption: captionText })}>
                          <img
                            src={imageUrl}
                            alt={captionText}
                            className="max-h-full max-w-full object-contain rounded-lg group-hover/img:scale-105 transition-transform duration-300"
                            onError={(e) => {
                              // Fallback if image fails to load
                              (e.target as HTMLElement).style.display = "none";
                            }}
                          />
                          <div className="absolute inset-0 bg-slate-950/40 opacity-0 group-hover/img:opacity-100 transition-opacity flex items-center justify-center gap-2">
                            <span className="text-xs font-mono text-white bg-slate-900/90 px-3 py-1.5 rounded-lg border border-slate-700 flex items-center gap-1.5">
                              <Maximize2 className="w-3.5 h-3.5 text-purple-400" />
                              Expand View
                            </span>
                          </div>
                        </div>
                      ) : (
                        <div className="flex flex-col items-center justify-center text-slate-500">
                          <ImageIcon className="w-8 h-8 mb-1" />
                          <span className="text-xs font-mono">Figure on Page {fig.page_number}</span>
                        </div>
                      )}
                    </div>

                    {/* Caption */}
                    <p className="text-xs text-slate-200 leading-relaxed font-serif bg-slate-900/40 p-3.5 rounded-xl border border-slate-800/60">
                      {captionText}
                    </p>
                  </div>

                  <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px]">
                    <span className="text-slate-500 font-mono text-[10px]">
                      Page {fig.page_number}
                    </span>
                    <button
                      onClick={() => {
                        setActivePageNumber(fig.page_number);
                        if (fig.bounding_box) {
                          setSelectedBoundingBox(fig.bounding_box, fig.page_number);
                        }
                      }}
                      className="flex items-center gap-1.5 text-blue-400 hover:text-blue-300 font-medium transition-colors"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      View Page Context
                    </button>
                  </div>
                </motion.div>
              );
            })
          ) : (
            <div className="col-span-2 p-12 text-center text-xs font-mono text-slate-400">Loading extracted figures...</div>
          )}
        </div>
      </div>

      {/* Lightbox High-Res Image Preview Modal */}
      <AnimatePresence>
        {selectedImage && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/90 backdrop-blur-md flex items-center justify-center p-6"
            onClick={() => setSelectedImage(null)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="max-w-4xl max-h-[90vh] bg-slate-900 rounded-2xl border border-slate-800 p-6 space-y-4 relative flex flex-col items-center"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="w-full flex items-center justify-between">
                <span className="text-xs font-mono text-purple-400 font-bold uppercase">
                  Extracted Figure High-Res View
                </span>
                <button
                  onClick={() => setSelectedImage(null)}
                  className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="flex-1 overflow-hidden flex items-center justify-center bg-slate-950 p-4 rounded-xl border border-slate-800 max-h-[65vh]">
                <img
                  src={selectedImage.url}
                  alt={selectedImage.caption}
                  className="max-h-full max-w-full object-contain rounded-lg shadow-2xl"
                />
              </div>

              <p className="text-xs text-slate-300 font-serif text-center max-w-2xl leading-relaxed">
                {selectedImage.caption}
              </p>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
