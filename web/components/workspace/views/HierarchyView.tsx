"use client";

import React, { useState, useMemo } from "react";
import { useWorkspaceStore } from "@/hooks/useWorkspaceStore";
import { ExtractedElement } from "@/types";
import { motion, AnimatePresence } from "framer-motion";
import { Layers, ChevronRight, ChevronDown, FileText, Hash, Bookmark } from "lucide-react";

interface SectionNode {
  id: string;
  title: string;
  type: string;
  page_number: number;
  level: number;
  elements: ExtractedElement[];
}

export function HierarchyView() {
  const { fullDocumentData, setActivePageNumber, setSelectedBoundingBox } = useWorkspaceStore();
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({});

  const realElements = fullDocumentData?.elements || [];
  const isDynamic = realElements.length > 0;

  // Group elements into structured major sections
  const sections: SectionNode[] = useMemo(() => {
    if (!realElements.length) return [];

    const result: SectionNode[] = [];
    let currentSection: SectionNode | null = null;
    let fallbackCounter = 1;

    // Keywords or element types that signify a section header
    const isHeaderElement = (el: ExtractedElement) => {
      const type = (el.element_type || "").toLowerCase();
      if (type === "title" || type === "heading" || type === "subheading" || type === "abstract" || type === "references") {
        return true;
      }
      const txt = (el.content || el.text || "").trim();
      // Match section patterns like "1. Introduction", "Abstract", "3. Methodology", "References"
      if (/^(abstract|references|bibliography|introduction|related work|background|methodology|experiments|results|discussion|conclusion|appendix)/i.test(txt)) {
        return true;
      }
      if (/^\d+(\.\d+)*\s+[A-Z]/.test(txt) && txt.length < 80) {
        return true;
      }
      return false;
    };

    realElements.forEach((el, index) => {
      const text = (el.content || el.text || "").trim();
      if (!text) return;

      if (isHeaderElement(el)) {
        currentSection = {
          id: el.id || el.element_id || `sec-${index}`,
          title: text,
          type: el.element_type || "HEADING",
          page_number: el.page_number,
          level: (el.element_type || "").toLowerCase() === "subheading" ? 2 : 1,
          elements: [],
        };
        result.push(currentSection);
      } else {
        if (!currentSection) {
          // If content appears before first explicit heading, create an Initial Overview / Metadata section
          currentSection = {
            id: `sec-overview-${fallbackCounter++}`,
            title: "Document Title & Author Metadata",
            type: "HEADING",
            page_number: el.page_number,
            level: 1,
            elements: [],
          };
          result.push(currentSection);
        }
        currentSection.elements.push(el);
      }
    });

    return result;
  }, [realElements]);

  const toggleSection = (id: string) => {
    setExpandedSections((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className="h-full bg-[#070a12] p-8 overflow-y-auto">
      <div className="max-w-4xl mx-auto space-y-6">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Layers className="w-5 h-5 text-purple-400" />
            Document Hierarchy Tree {isDynamic && (
              <span className="text-xs font-mono text-emerald-400 font-normal px-2.5 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20">
                {sections.length} Major Sections • {realElements.length} Total Elements
              </span>
            )}
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Section-aware outline grouped by PaperMind DocumentTreeBuilder to maintain context propagation.
          </p>
        </div>

        <div className="space-y-3">
          {isDynamic ? (
            sections.map((section, idx) => {
              const isExpanded = expandedSections[section.id] ?? (idx === 0 || idx === 1);
              return (
                <div
                  key={section.id}
                  className="glass-panel rounded-2xl border-slate-800 overflow-hidden transition-all hover:border-slate-700"
                >
                  {/* Section Header Button */}
                  <div
                    onClick={() => toggleSection(section.id)}
                    className="w-full p-4 flex items-center justify-between cursor-pointer hover:bg-slate-900/60 transition-colors select-none"
                  >
                    <div className="flex items-center gap-3 overflow-hidden">
                      <div className="w-6 h-6 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 shrink-0">
                        {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                      </div>
                      <div className="flex flex-col truncate">
                        <span className="text-xs font-bold text-white truncate">
                          {section.title}
                        </span>
                        <span className="text-[10px] font-mono text-slate-500 uppercase">
                          {section.type} • {section.elements.length} Content Blocks
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 text-[10px] font-mono shrink-0">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setActivePageNumber(section.page_number);
                        }}
                        className="px-2.5 py-1 rounded-lg bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/20 text-blue-400 font-semibold transition-colors"
                      >
                        Page {section.page_number}
                      </button>
                    </div>
                  </div>

                  {/* Section Child Content Blocks */}
                  <AnimatePresence>
                    {isExpanded && section.elements.length > 0 && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="border-t border-slate-800/80 bg-slate-950/40 p-3 space-y-2"
                      >
                        {section.elements.map((el, elIdx) => (
                          <div
                            key={el.id || el.element_id || elIdx}
                            onClick={() => {
                              setActivePageNumber(el.page_number);
                              if (el.bounding_box) {
                                setSelectedBoundingBox(el.bounding_box, el.page_number);
                              }
                            }}
                            className="p-3 rounded-xl bg-slate-900/50 hover:bg-slate-900 border border-slate-800/60 hover:border-blue-500/30 transition-all cursor-pointer flex items-start justify-between gap-3 group"
                          >
                            <div className="flex items-start gap-2 overflow-hidden">
                              <FileText className="w-3.5 h-3.5 text-slate-500 group-hover:text-blue-400 shrink-0 mt-0.5" />
                              <p className="text-xs text-slate-300 line-clamp-2 font-serif leading-relaxed">
                                {el.content || el.text}
                              </p>
                            </div>
                            <span className="text-[9px] font-mono text-slate-500 shrink-0 uppercase px-1.5 py-0.5 rounded bg-slate-950 border border-slate-800">
                              {el.element_type}
                            </span>
                          </div>
                        ))}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              );
            })
          ) : (
            <div className="p-8 text-center text-xs font-mono text-slate-400">Loading hierarchy tree...</div>
          )}
        </div>
      </div>
    </div>
  );
}
