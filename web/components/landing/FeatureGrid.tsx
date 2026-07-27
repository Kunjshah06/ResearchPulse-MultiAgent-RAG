"use client";

import React from "react";
import { motion } from "framer-motion";
import { Cpu, Layers, Table, Image, FunctionSquare, Network, ShieldCheck, Sparkles, Check } from "lucide-react";

const FEATURES = [
  {
    icon: Cpu,
    title: "Dual-Path Ingestion Pipeline",
    description: "Automatically analyzes PDF character density to dynamically route native digital text vs scanned pages requiring deskewing, denoising, and fallback Tesseract/PaddleOCR parsing.",
    badge: "Ingestion Engine",
    color: "from-blue-500/20 to-indigo-500/20",
    iconColor: "text-blue-400",
    bullets: ["Auto-routing based on char density", "High-pass image deskewing", "PaddleOCR & Tesseract fallback"],
  },
  {
    icon: Layers,
    title: "Document Layout & Tree Hierarchy",
    description: "Detects headers, section numbers, titles, and body paragraphs to build a structured DocumentTree schema. Ensures chunks retain full parent-section context.",
    badge: "Structural Intelligence",
    color: "from-purple-500/20 to-pink-500/20",
    iconColor: "text-purple-400",
    bullets: ["Section-aware semantic chunking", "Parent-child tree propagation", "Bounding box spatial tracking"],
  },
  {
    icon: Table,
    title: "Table & Figure Understanding",
    description: "Extracts tabular data into clean DataGrids with CSV/JSON exports. Automatically pairs figure graphics with their caption blocks across page breaks.",
    badge: "Multimodal Extractors",
    color: "from-emerald-500/20 to-teal-500/20",
    iconColor: "text-emerald-400",
    bullets: ["Interactive DataGrid viewer", "Caption & bounding-box pairing", "CSV & JSON dataset export"],
  },
  {
    icon: FunctionSquare,
    title: "LaTeX Equation Extraction",
    description: "Detects inline and display equations, converts them into standard LaTeX representations, and extracts symbol definitions for mathematical reasoning.",
    badge: "Math Engine",
    color: "from-amber-500/20 to-orange-500/20",
    iconColor: "text-amber-400",
    bullets: ["Display & inline LaTeX parsing", "Symbol definition mapping", "KaTeX beautiful rendering"],
  },
  {
    icon: Sparkles,
    title: "LangGraph Multi-Agent RAG",
    description: "State-machine agent graph with dedicated Router, Summary, Table, Figure, Equation, Citation, and Research agents that collaborate to answer complex research queries.",
    badge: "Agentic Orchestration",
    color: "from-cyan-500/20 to-blue-500/20",
    iconColor: "text-cyan-400",
    bullets: ["7 Specialized agent nodes", "Strict evidence citation check", "Zero hallucination guardrails"],
  },
  {
    icon: Network,
    title: "Document Knowledge Graph",
    description: "Constructs in-memory NetworkX and persistent Neo4j knowledge graphs connecting sections, concepts, tables, figures, citations, and authors.",
    badge: "Graph Reasoning",
    color: "from-rose-500/20 to-red-500/20",
    iconColor: "text-rose-400",
    bullets: ["Entity & concept relation linking", "NetworkX & Neo4j backend", "Cross-paper citation graph"],
  },
];

export function FeatureGrid() {
  return (
    <section id="features" className="max-w-7xl mx-auto px-6 mb-24">
      <div className="text-center mb-16">
        <span className="text-xs font-mono text-purple-400 uppercase tracking-widest px-3 py-1 rounded-full bg-purple-500/10 border border-purple-500/20">
          Core System Capabilities
        </span>
        <h2 className="text-3xl md:text-5xl font-bold text-white tracking-tight mt-3">
          Built for Production Document Intelligence
        </h2>
        <p className="text-sm md:text-base text-slate-400 mt-3 max-w-2xl mx-auto">
          Every layer of PaperMind AI is engineered to handle complex scientific manuscripts with surgical precision.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {FEATURES.map((feature, index) => {
          const Icon = feature.icon;
          return (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.08 }}
              className="glass-panel-interactive rounded-2xl p-7 flex flex-col justify-between group"
            >
              <div>
                <div className="flex items-center justify-between mb-6">
                  <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${feature.color} border border-white/10 flex items-center justify-center`}>
                    <Icon className={`w-6 h-6 ${feature.iconColor}`} />
                  </div>
                  <span className="text-[10px] font-mono text-slate-400 px-2.5 py-1 rounded-md bg-slate-900 border border-slate-800">
                    {feature.badge}
                  </span>
                </div>

                <h3 className="text-lg font-semibold text-white group-hover:text-blue-300 transition-colors">
                  {feature.title}
                </h3>
                <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                  {feature.description}
                </p>
              </div>

              <div className="mt-6 pt-6 border-t border-slate-800/80 space-y-2">
                {feature.bullets.map((bullet) => (
                  <div key={bullet} className="flex items-center gap-2 text-xs text-slate-300">
                    <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                    <span>{bullet}</span>
                  </div>
                ))}
              </div>
            </motion.div>
          );
        })}
      </div>
    </section>
  );
}
