"use client";

import React, { useState } from "react";
import { useWorkspaceStore } from "@/hooks/useWorkspaceStore";
import { motion, AnimatePresence } from "framer-motion";
import { Table as TableIcon, FileSpreadsheet, Maximize2, Eye, X, Check } from "lucide-react";

export function TableView() {
  const { fullDocumentData, activePaperId, setActivePageNumber, setSelectedBoundingBox } = useWorkspaceStore();
  const [selectedTable, setSelectedTable] = useState<{ url: string; caption: string } | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const realTables = fullDocumentData?.tables || [];
  const isDynamic = realTables.length > 0;

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

  const exportCSV = (tableId: string, csvContent?: string) => {
    const textToExport = csvContent || "No data available";
    const blob = new Blob([textToExport], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `extracted_table_${tableId}.csv`;
    a.click();
    setCopiedId(tableId);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="h-full bg-[#070a12] p-8 overflow-y-auto relative">
      <div className="max-w-5xl mx-auto space-y-6">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <TableIcon className="w-5 h-5 text-emerald-400" />
            Extracted Manuscript Tables {isDynamic && (
              <span className="text-xs font-mono text-emerald-400 font-normal px-2.5 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20">
                LIVE FASTAPI DATA ({realTables.length} Tables)
              </span>
            )}
          </h2>
          <p className="text-xs text-slate-400 mt-1 font-mono">
            TableExtractor • 100% Visual Fidelity High-Res Cropping & CSV Export
          </p>
        </div>

        <div className="space-y-6">
          {isDynamic ? (
            realTables.map((table, tIdx) => {
              const tableId = table.id || table.table_id || `table-${tIdx}`;
              const imageUrl = getImageUrl(table.image_path, table.page_number);
              const captionText = table.caption || `Table on Page ${table.page_number}`;

              return (
                <motion.div
                  key={tableId}
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: Math.min(tIdx * 0.05, 0.4) }}
                  className="glass-panel rounded-2xl p-6 border-slate-800 space-y-4 hover:border-emerald-500/40 transition-all"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono text-emerald-400 px-2.5 py-1 rounded bg-emerald-500/10 border border-emerald-500/20 font-bold uppercase">
                      Table {tIdx + 1}
                    </span>
                    <span className="text-[10px] font-mono text-slate-500 font-semibold">
                      Page {table.page_number}
                    </span>
                  </div>

                  {/* Caption */}
                  <p className="text-xs text-slate-200 font-serif leading-relaxed bg-slate-950/60 p-3.5 rounded-xl border border-slate-800/80">
                    {captionText}
                  </p>

                  {/* High-Res Table Visual Crop Container */}
                  <div className="w-full min-h-[160px] max-h-[420px] rounded-xl bg-slate-950 border border-slate-800/80 flex items-center justify-center p-4 relative overflow-hidden group hover:border-emerald-500/30 transition-colors">
                    {imageUrl ? (
                      <div
                        className="w-full h-full relative flex items-center justify-center cursor-pointer overflow-hidden group/img"
                        onClick={() => setSelectedTable({ url: imageUrl, caption: captionText })}
                      >
                        <img
                          src={imageUrl}
                          alt={captionText}
                          className="max-h-[380px] max-w-full object-contain rounded-lg group-hover/img:scale-105 transition-transform duration-300 shadow-xl"
                          onError={(e) => {
                            (e.target as HTMLElement).style.display = "none";
                          }}
                        />
                        <div className="absolute inset-0 bg-slate-950/40 opacity-0 group-hover/img:opacity-100 transition-opacity flex items-center justify-center">
                          <span className="text-xs font-mono text-white bg-slate-900/90 px-3 py-1.5 rounded-lg border border-slate-700 flex items-center gap-1.5 shadow-lg">
                            <Maximize2 className="w-3.5 h-3.5 text-emerald-400" />
                            Expand High-Res View
                          </span>
                        </div>
                      </div>
                    ) : (
                      <div className="flex flex-col items-center justify-center text-slate-500">
                        <TableIcon className="w-8 h-8 mb-1" />
                        <span className="text-xs font-mono">Table on Page {table.page_number}</span>
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
                    <button
                      onClick={() => exportCSV(tableId, table.csv_repr)}
                      className="flex items-center gap-1.5 text-xs text-slate-300 hover:text-white transition-colors font-mono"
                    >
                      {copiedId === tableId ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-400" />}
                      <span>{copiedId === tableId ? "CSV Exported!" : "Export CSV"}</span>
                    </button>

                    <button
                      onClick={() => {
                        setActivePageNumber(table.page_number);
                        if (table.bounding_box) {
                          setSelectedBoundingBox(table.bounding_box, table.page_number);
                        }
                      }}
                      className="flex items-center gap-1.5 text-xs text-blue-400 hover:text-blue-300 transition-colors font-medium"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      View Page {table.page_number} Context
                    </button>
                  </div>
                </motion.div>
              );
            })
          ) : (
            <div className="p-12 text-center text-xs font-mono text-slate-400">Loading tables...</div>
          )}
        </div>
      </div>

      {/* Lightbox High-Res Table Image Modal */}
      <AnimatePresence>
        {selectedTable && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/90 backdrop-blur-md flex items-center justify-center p-6"
            onClick={() => setSelectedTable(null)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="max-w-5xl max-h-[90vh] bg-slate-900 rounded-2xl border border-slate-800 p-6 space-y-4 relative flex flex-col items-center"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="w-full flex items-center justify-between">
                <span className="text-xs font-mono text-emerald-400 font-bold uppercase">
                  Extracted Table High-Res View
                </span>
                <button
                  onClick={() => setSelectedTable(null)}
                  className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="flex-1 overflow-hidden flex items-center justify-center bg-slate-950 p-4 rounded-xl border border-slate-800 max-h-[68vh]">
                <img
                  src={selectedTable.url}
                  alt={selectedTable.caption}
                  className="max-h-full max-w-full object-contain rounded-lg shadow-2xl"
                />
              </div>

              <p className="text-xs text-slate-300 font-serif text-center max-w-3xl leading-relaxed">
                {selectedTable.caption}
              </p>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
