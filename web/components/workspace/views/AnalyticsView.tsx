"use client";

import React from "react";
import { useWorkspaceStore } from "@/hooks/useWorkspaceStore";
import { motion } from "framer-motion";
import { BarChart3, Clock, Table, Layers, FunctionSquare } from "lucide-react";

export function AnalyticsView() {
  const { fullDocumentData, activePaperTitle } = useWorkspaceStore();

  const isDynamic = Boolean(fullDocumentData);
  const metadata = fullDocumentData?.metadata;
  const pageCount = metadata?.page_count || 15;
  const chunkCount = fullDocumentData?.chunks?.length || 42;
  const tableCount = fullDocumentData?.tables?.length || 4;
  const figureCount = fullDocumentData?.figures?.length || 7;
  const equationCount = fullDocumentData?.equations?.length || 8;

  return (
    <div className="h-full bg-[#070a12] p-8 overflow-y-auto">
      <div className="max-w-5xl mx-auto space-y-6">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-blue-400" />
            Paper Analytics & Ingestion Metrics {isDynamic && <span className="text-xs font-mono text-emerald-400 font-normal px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20">LIVE FASTAPI DATA</span>}
          </h2>
          <p className="text-xs text-slate-400 mt-1 font-mono">
            Extracted document metrics for {activePaperTitle}
          </p>
        </div>

        {/* Top Metric Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="glass-panel p-5 rounded-2xl border-slate-800">
            <div className="flex items-center justify-between text-slate-400 text-xs font-mono mb-2">
              <span>Total Pages</span>
              <Clock className="w-4 h-4 text-blue-400" />
            </div>
            <div className="text-2xl font-bold text-white">{pageCount} Pages</div>
            <div className="text-[10px] text-slate-500 font-mono mt-1">Est. {pageCount * 2} min reading time</div>
          </div>

          <div className="glass-panel p-5 rounded-2xl border-slate-800">
            <div className="flex items-center justify-between text-slate-400 text-xs font-mono mb-2">
              <span>Semantic Chunks</span>
              <Layers className="w-4 h-4 text-purple-400" />
            </div>
            <div className="text-2xl font-bold text-purple-400">{chunkCount} Chunks</div>
            <div className="text-[10px] text-slate-500 font-mono mt-1">Qdrant Indexed</div>
          </div>

          <div className="glass-panel p-5 rounded-2xl border-slate-800">
            <div className="flex items-center justify-between text-slate-400 text-xs font-mono mb-2">
              <span>Tables & Figures</span>
              <Table className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-2xl font-bold text-emerald-400">{tableCount + figureCount} Items</div>
            <div className="text-[10px] text-slate-500 font-mono mt-1">{tableCount} Tables • {figureCount} Figures</div>
          </div>

          <div className="glass-panel p-5 rounded-2xl border-slate-800">
            <div className="flex items-center justify-between text-slate-400 text-xs font-mono mb-2">
              <span>Equations</span>
              <FunctionSquare className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-2xl font-bold text-amber-400">{equationCount} Formulas</div>
            <div className="text-[10px] text-slate-500 font-mono mt-1">LaTeX Standard Form</div>
          </div>
        </div>

        {/* Chunk Type Distribution Breakdown */}
        <div className="glass-panel p-6 rounded-2xl border-slate-800 space-y-4">
          <h3 className="text-sm font-semibold text-white">Extracted Structure Breakdown</h3>
          <div className="space-y-3 font-mono text-xs">
            <div>
              <div className="flex justify-between text-slate-400 mb-1">
                <span>Text Chunks</span>
                <span className="text-white">{chunkCount}</span>
              </div>
              <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden">
                <div className="h-full bg-blue-500 rounded-full w-[75%]" />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-slate-400 mb-1">
                <span>Tables & Datasets</span>
                <span className="text-emerald-400">{tableCount}</span>
              </div>
              <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden">
                <div className="h-full bg-emerald-500 rounded-full w-[15%]" />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-slate-400 mb-1">
                <span>Equations & Math Formulas</span>
                <span className="text-amber-400">{equationCount}</span>
              </div>
              <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden">
                <div className="h-full bg-amber-500 rounded-full w-[10%]" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
