"use client";

import React, { useState, useEffect } from "react";
import { useWorkspaceStore } from "@/hooks/useWorkspaceStore";
import { motion, AnimatePresence } from "framer-motion";
import { Search, X, FileText, Table, Image, FunctionSquare, Layers } from "lucide-react";

const QUICK_SEARCH_ITEMS = [
  { label: "Section 3.2 Scaled Dot-Product Attention", type: "section", tab: "tree" },
  { label: "Equation (3) Attention Formula", type: "equation", tab: "equations" },
  { label: "Table 1 WMT 14 Translation Benchmarks", type: "table", tab: "tables" },
  { label: "Figure 1 Transformer Model Stack", type: "figure", tab: "figures" },
  { label: "Section 3.2.2 Multi-Head Attention", type: "section", tab: "tree" },
];

export function CommandPalette() {
  const { commandPaletteOpen, setCommandPaletteOpen, setActiveTab } = useWorkspaceStore();
  const [query, setQuery] = useState("");

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setCommandPaletteOpen(!commandPaletteOpen);
      }
      if (e.key === "Escape") {
        setCommandPaletteOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [commandPaletteOpen, setCommandPaletteOpen]);

  if (!commandPaletteOpen) return null;

  const filtered = QUICK_SEARCH_ITEMS.filter((item) =>
    item.label.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-md flex items-start justify-center pt-24 px-4 select-none">
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: -20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: -20 }}
          className="w-full max-w-xl glass-panel rounded-2xl border-slate-700 shadow-2xl overflow-hidden"
        >
          {/* Header Bar */}
          <div className="p-4 border-b border-slate-800 flex items-center gap-3">
            <Search className="w-5 h-5 text-blue-400" />
            <input
              type="text"
              autoFocus
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search paper sections, equations, tables, figures..."
              className="flex-1 bg-transparent text-sm text-white placeholder-slate-500 outline-none"
            />
            <button
              onClick={() => setCommandPaletteOpen(false)}
              className="p-1 rounded text-slate-400 hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Results List */}
          <div className="p-2 max-h-80 overflow-y-auto space-y-1">
            {filtered.length === 0 ? (
              <div className="p-8 text-center text-xs font-mono text-slate-500">
                No elements found matching "{query}"
              </div>
            ) : (
              filtered.map((item, idx) => (
                <div
                  key={idx}
                  onClick={() => {
                    setActiveTab(item.tab as any);
                    setCommandPaletteOpen(false);
                  }}
                  className="flex items-center justify-between p-3 rounded-xl hover:bg-slate-800/80 cursor-pointer transition-colors text-xs"
                >
                  <span className="text-slate-200 font-medium">{item.label}</span>
                  <span className="text-[10px] font-mono text-blue-400 px-2 py-0.5 rounded bg-blue-500/10 border border-blue-500/20 uppercase">
                    {item.type}
                  </span>
                </div>
              ))
            )}
          </div>

          {/* Footer Shortcuts */}
          <div className="p-3 bg-slate-950/80 border-t border-slate-800/80 flex items-center justify-between text-[10px] font-mono text-slate-500">
            <span>Use ↑↓ to navigate</span>
            <span>ESC to close</span>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
