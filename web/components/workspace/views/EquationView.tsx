"use client";

import React, { useState, useMemo } from "react";
import { useWorkspaceStore } from "@/hooks/useWorkspaceStore";
import { motion } from "framer-motion";
import { FunctionSquare, Copy, Check, Eye, BookOpen } from "lucide-react";
import katex from "katex";
import "katex/dist/katex.min.css";

function RenderedMath({ formula, displayMode = true }: { formula: string; displayMode?: boolean }) {
  const html = useMemo(() => {
    if (!formula) return "";
    try {
      // Clean leading and trailing delimiters
      let clean = formula.trim();
      clean = clean.replace(/^\$\$\s*/, "").replace(/\s*\$\$$/, "").trim();
      clean = clean.replace(/^\$\s*/, "").replace(/\s*\$$/, "").trim();

      return katex.renderToString(clean, {
        throwOnError: false,
        displayMode,
      });
    } catch (e) {
      return "";
    }
  }, [formula, displayMode]);

  if (!html) {
    return (
      <div className="font-mono text-xs text-blue-300 whitespace-pre-wrap leading-relaxed">
        {formula}
      </div>
    );
  }

  return <div className="text-blue-200 text-sm md:text-base leading-relaxed overflow-x-auto py-2" dangerouslySetInnerHTML={{ __html: html }} />;
}

export function EquationView() {
  const { fullDocumentData, setActivePageNumber, setSelectedBoundingBox } = useWorkspaceStore();
  const realEquations = fullDocumentData?.equations || [];
  const isDynamic = realEquations.length > 0;

  const [copiedId, setCopiedId] = useState<string | null>(null);

  const handleCopy = (id: string, latex: string) => {
    const clean = latex.replace(/^\$\$\s*/, "").replace(/\s*\$\$$/, "").trim();
    navigator.clipboard.writeText(clean);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="h-full bg-[#070a12] p-8 overflow-y-auto">
      <div className="max-w-4xl mx-auto space-y-6">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <FunctionSquare className="w-5 h-5 text-amber-400" />
            Extracted LaTeX Equations {isDynamic && (
              <span className="text-xs font-mono text-emerald-400 font-normal px-2.5 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20">
                LIVE FASTAPI DATA ({realEquations.length} Formulas)
              </span>
            )}
          </h2>
          <p className="text-xs text-slate-400 mt-1 font-mono">
            EquationExtractor • KaTeX Mathematical Typesetting
          </p>
        </div>

        <div className="space-y-6">
          {isDynamic ? (
            realEquations.map((eq, idx) => {
              const eqId = eq.id || eq.equation_id || `eq-${idx}`;
              const latexText = eq.latex || eq.raw_text || eq.latex_expression || "";

              // Clean text separation for prose vs mathematical formula
              const hasLongText = latexText.length > 120 && !latexText.includes("\\frac") && !latexText.includes("\\sum");
              
              return (
                <motion.div
                  key={eqId}
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: Math.min(idx * 0.03, 0.4) }}
                  className="glass-panel rounded-2xl p-6 border-slate-800 space-y-4 hover:border-amber-500/30 transition-all"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono text-amber-400 px-2.5 py-1 rounded bg-amber-500/10 border border-amber-500/20 uppercase font-semibold">
                      {eq.is_inline ? "Inline Expression" : "Display Formula"}
                    </span>
                    <span className="text-[10px] font-mono text-slate-500 font-semibold">
                      Page {eq.page_number}
                    </span>
                  </div>

                  {/* KaTeX High-Res Typeset Rendered Container */}
                  <div className="p-6 rounded-xl bg-slate-950 border border-slate-800/80 flex flex-col items-center justify-center min-h-[90px] shadow-inner overflow-x-auto">
                    <RenderedMath formula={latexText} displayMode={!eq.is_inline} />
                  </div>

                  {/* Variables */}
                  {eq.variables && eq.variables.length > 0 && (
                    <div className="space-y-1.5 pt-1">
                      <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider block">
                        Extracted Variables:
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {eq.variables.map((v, vIdx) => (
                          <span
                            key={vIdx}
                            className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-amber-300 font-bold"
                          >
                            {v}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Context Explanation */}
                  {eq.explanation && (
                    <p className="text-xs text-slate-300 font-serif bg-slate-900/40 p-3.5 rounded-xl border border-slate-800/60 leading-relaxed">
                      {eq.explanation}
                    </p>
                  )}

                  <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between">
                    <button
                      onClick={() => handleCopy(eqId, latexText)}
                      className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors"
                    >
                      {copiedId === eqId ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      <span>{copiedId === eqId ? "LaTeX Copied!" : "Copy LaTeX"}</span>
                    </button>

                    <button
                      onClick={() => {
                        setActivePageNumber(eq.page_number);
                        if (eq.bounding_box) {
                          setSelectedBoundingBox(eq.bounding_box, eq.page_number);
                        }
                      }}
                      className="flex items-center gap-1.5 text-xs text-blue-400 hover:text-blue-300 transition-colors font-medium"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      View Page {eq.page_number} Context
                    </button>
                  </div>
                </motion.div>
              );
            })
          ) : (
            <div className="p-8 text-center text-xs font-mono text-slate-400">Loading equations...</div>
          )}
        </div>
      </div>
    </div>
  );
}
