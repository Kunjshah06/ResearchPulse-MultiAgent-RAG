"use client";

import React, { useState, useRef } from "react";
import { useWorkspaceStore } from "@/hooks/useWorkspaceStore";
import { motion, AnimatePresence } from "framer-motion";
import {
  ZoomIn,
  ZoomOut,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  BookOpen,
  Lightbulb,
  X,
  FileText,
} from "lucide-react";
import { api } from "@/lib/api-client";

export function PdfView() {
  const {
    activePageNumber,
    setActivePageNumber,
    fullDocumentData,
    activePaperId,
    activePaperTitle,
    setRightPanelOpen,
    addMessage,
    setIsAgentThinking,
  } = useWorkspaceStore();

  const [zoom, setZoom] = useState(100);
  const [selectionRange, setSelectionRange] = useState<{
    text: string;
    x: number;
    y: number;
  } | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);

  // Determine actual page count from full document metadata or element max page
  const pageCount =
    fullDocumentData?.metadata?.page_count ||
    (fullDocumentData?.elements && fullDocumentData.elements.length > 0
      ? Math.max(...fullDocumentData.elements.map((el) => el.page_number))
      : (activePaperId ? 1 : 0));

  // Generate exact array of available pages
  const pageNumbers = Array.from({ length: pageCount }, (_, i) => i + 1);

  // Text selection handler over transparent text layer
  const handleMouseUp = () => {
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed) {
      setSelectionRange(null);
      return;
    }

    const text = selection.toString().trim();
    if (text.length > 3) {
      const range = selection.getRangeAt(0);
      const rect = range.getBoundingClientRect();
      if (rect) {
        setSelectionRange({
          text,
          x: rect.left + rect.width / 2,
          y: rect.top - 12,
        });
      }
    } else {
      setSelectionRange(null);
    }
  };

  // Trigger AI explanation in the right-side panel
  const handleExplainSelection = async (mode: "explain" | "simplify") => {
    if (!selectionRange) return;

    const selectedText = selectionRange.text;
    setSelectionRange(null);
    setRightPanelOpen(true);

    const promptText =
      mode === "explain"
        ? `Explain this excerpt from Page ${activePageNumber}: "${selectedText}"`
        : `Simplify the concept/math in this line from Page ${activePageNumber}: "${selectedText}"`;

    const userMsg = {
      id: `user-${Date.now()}`,
      role: "user" as const,
      content: promptText,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    addMessage(userMsg);
    setIsAgentThinking(true);

    try {
      const res = await api.queryRAGAgent(promptText, [activePaperId]);
      const assistantMsg = {
        id: `ai-${Date.now()}`,
        role: "assistant" as const,
        content: res.answer || `I could not locate specific context for this excerpt in the document.`,
        citations: res.citations || [],
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        confidence: res.confidence_score || 0.85,
      };
      addMessage(assistantMsg);
    } catch (err) {
      const fallbackMsg = {
        id: `ai-${Date.now()}`,
        role: "assistant" as const,
        content: `Could not connect to backend AI service for selection explanation.`,
        citations: [],
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        confidence: 0.0,
      };
      addMessage(fallbackMsg);
    } finally {
      setIsAgentThinking(false);
    }
  };

  return (
    <div
      ref={containerRef}
      onMouseUp={handleMouseUp}
      className="h-full flex flex-col bg-[#070a12] relative overflow-hidden"
    >
      {/* Top PDF Controls Toolbar */}
      <div className="h-11 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md px-4 flex items-center justify-between text-xs text-slate-300 z-10 select-none">
        <div className="flex items-center gap-3 font-mono">
          <div className="flex items-center gap-1">
            <button
              disabled={activePageNumber <= 1}
              onClick={() => setActivePageNumber(activePageNumber - 1)}
              className="p-1 rounded hover:bg-slate-800 disabled:opacity-40"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span>
              Page <span className="text-white font-bold">{activePageNumber}</span> of {pageCount}
            </span>
            <button
              disabled={activePageNumber >= pageCount}
              onClick={() => setActivePageNumber(activePageNumber + 1)}
              className="p-1 rounded hover:bg-slate-800 disabled:opacity-40"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          <span className="text-slate-600">|</span>
          <span className="text-[11px] text-slate-400 truncate max-w-[320px]">
            {activePaperTitle || "Uploaded Manuscript"}
          </span>
        </div>

        <div className="flex items-center gap-3">
          {/* Zoom Control */}
          <div className="flex items-center gap-1 bg-slate-900 px-2 py-1 rounded-lg border border-slate-800 font-mono text-[11px]">
            <button onClick={() => setZoom(Math.max(60, zoom - 10))} className="p-0.5 hover:text-white">
              <ZoomOut className="w-3.5 h-3.5" />
            </button>
            <span className="w-10 text-center">{zoom}%</span>
            <button onClick={() => setZoom(Math.min(180, zoom + 10))} className="p-0.5 hover:text-white">
              <ZoomIn className="w-3.5 h-3.5" />
            </button>
          </div>

          <span className="text-[10px] font-mono px-2.5 py-1 rounded bg-blue-500/10 border border-blue-500/20 text-blue-400 font-bold uppercase">
            Select text on paper to ask AI
          </span>
        </div>
      </div>

      {/* Main Continuous Vertical Scroll Paper Canvas Container */}
      <div className="flex-1 overflow-y-auto p-8 flex flex-col items-center gap-8 relative bg-[#090d16] scroll-smooth">
        {pageNumbers.map((pNum) => {
          const pageImgUrl = `http://localhost:8000/figures/${activePaperId}/page_${pNum}.png`;

          // Get spatial text bounding box elements for this page to build the transparent text layer
          const pageElements =
            fullDocumentData?.elements?.filter(
              (el) => el.page_number === pNum && el.bounding_box
            ) || [];

          return (
            <motion.div
              key={pNum}
              animate={{ scale: zoom / 100 }}
              transition={{ duration: 0.2 }}
              className="w-[820px] min-h-[1060px] aspect-[8.5/11] bg-white rounded-xl border border-slate-300 shadow-2xl overflow-hidden relative flex flex-col shrink-0 group"
              onViewportEnter={() => setActivePageNumber(pNum)}
            >
              {/* Paper Image Layer */}
              <div className="w-full h-full flex-1 bg-white relative flex items-center justify-center overflow-hidden">
                <img
                  src={pageImgUrl}
                  alt={`Page ${pNum}`}
                  className="w-full h-full object-contain block pointer-events-none select-none"
                />

                {/* Transparent OCR Text Layer Overlay for Precise Mouse Drag Selection */}
                <div className="absolute inset-0 select-text overflow-hidden pointer-events-auto z-10">
                  {pageElements.map((el, elIdx) => {
                    const box = el.bounding_box;
                    if (!box) return null;

                    const leftPct = `${box.x0 * 100}%`;
                    const topPct = `${box.y0 * 100}%`;
                    const widthPct = `${Math.max(0.01, box.x1 - box.x0) * 100}%`;
                    const heightPct = `${Math.max(0.01, box.y1 - box.y0) * 100}%`;

                    return (
                      <span
                        key={el.id || `text-layer-${pNum}-${elIdx}`}
                        style={{
                          position: "absolute",
                          left: leftPct,
                          top: topPct,
                          width: widthPct,
                          height: heightPct,
                          color: "transparent",
                          userSelect: "text",
                          cursor: "text",
                          fontSize: "11px",
                          lineHeight: "1.1",
                          overflow: "hidden",
                          whiteSpace: "pre-wrap",
                        }}
                        className="selection:bg-blue-500/30 selection:text-transparent hover:bg-blue-500/5 transition-colors"
                      >
                        {el.content}
                      </span>
                    );
                  })}
                </div>
              </div>

              {/* Page Footer Marker */}
              <div className="p-2 bg-slate-100 border-t border-slate-200 text-center text-[10px] font-mono text-slate-500 select-none shrink-0 z-20">
                Page {pNum} of {pageCount}
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Floating Selection Tooltip for Asking AI Doubts */}
      <AnimatePresence>
        {selectionRange && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.95 }}
            style={{
              position: "fixed",
              left: Math.min(window.innerWidth - 280, Math.max(20, selectionRange.x - 140)),
              top: Math.max(60, selectionRange.y - 45),
            }}
            className="z-50 bg-slate-900/95 backdrop-blur-xl border border-blue-500/40 text-white rounded-xl p-1.5 shadow-2xl flex items-center gap-1.5"
          >
            <button
              onClick={() => handleExplainSelection("explain")}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs font-semibold text-white transition-colors"
            >
              <Sparkles className="w-3.5 h-3.5 text-amber-300" />
              <span>Ask AI to Explain</span>
            </button>

            <button
              onClick={() => handleExplainSelection("simplify")}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 transition-colors"
            >
              <Lightbulb className="w-3.5 h-3.5 text-amber-400" />
              <span>Simplify Math</span>
            </button>

            <button
              onClick={() => setSelectionRange(null)}
              className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
