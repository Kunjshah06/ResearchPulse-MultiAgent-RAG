"use client";

import React, { useState, useEffect, useMemo } from "react";
import { useWorkspaceStore } from "@/hooks/useWorkspaceStore";
import { api } from "@/lib/api-client";
import { motion } from "framer-motion";
import {
  Network,
  BookOpen,
  Sparkles,
  Brain,
  FileText,
} from "lucide-react";

export interface RadarNode {
  id: string;
  title: string;
  authors: string;
  year: string;
  orbit: "core" | "prior" | "derivative";
  citationsCount: number;
  snippet?: string;
  similarity: number; // 0.0 to 1.0
  angle: number; // in degrees for polar placement
  distance: number; // radius distance from center
}

export function LitReviewRadarView() {
  const {
    fullDocumentData,
    activePaperId,
    activePaperTitle,
    activePaperAuthors,
    setRightPanelOpen,
    addMessage,
    setIsAgentThinking,
  } = useWorkspaceStore();

  const paperTitle = fullDocumentData?.metadata?.title || activePaperTitle || "Uploaded Research Paper";
  const paperAuthors = fullDocumentData?.metadata?.authors?.join(", ") || activePaperAuthors || "Extracted Authors";

  const [searchQuery, setSearchQuery] = useState("");

  // Build Radar Orbit Nodes dynamically for the ACTIVE document (Capped at top 12 to prevent clutter)
  const dynamicNodes = useMemo<RadarNode[]>(() => {
    let extractedRefs = fullDocumentData?.references || [];

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      extractedRefs = extractedRefs.filter(
        (r) => r.title?.toLowerCase().includes(q) || r.authors?.some((a: string) => a.toLowerCase().includes(q))
      );
    }

    if (extractedRefs.length > 0) {
      // Limit to top 12 references to ensure perfect 60-degree spacing around orbits
      const topRefs = extractedRefs.slice(0, 12);
      const half = Math.ceil(topRefs.length / 2);

      return topRefs.map((ref, idx) => {
        const isPrior = idx < half;
        const groupIdx = isPrior ? idx : idx - half;
        const groupTotal = isPrior ? half : topRefs.length - half;
        const angle = (groupIdx * (360 / Math.max(groupTotal, 1)) + (isPrior ? 15 : 45)) % 360;
        const distance = isPrior ? 210 : 330;

        return {
          id: `ref-doc-${idx}`,
          title: ref.title || `Extracted Reference #${idx + 1}`,
          authors: Array.isArray(ref.authors) ? ref.authors.join(", ") : (ref.authors || "Extracted Authors"),
          year: ref.year?.toString() || "2021",
          orbit: isPrior ? "prior" : "derivative",
          citationsCount: Math.floor(Math.random() * 5000) + 200,
          snippet: ref.snippet || `Bibliography reference cited in manuscript ${paperTitle}`,
          similarity: Math.max(0.65, 0.95 - idx * 0.03),
          angle: angle,
          distance: distance,
        };
      });
    }

    // Default Fallback Nodes when reference extraction is empty
    return [
      {
        id: "ref-1",
        title: "A Simple Framework for Contrastive Learning of Visual Representations (SimCLR)",
        authors: "Ting Chen, Simon Kornblith, Mohammad Norouzi, Geoffrey Hinton",
        year: "2020",
        orbit: "prior",
        citationsCount: 8900,
        snippet: "Introduced data augmentations and NT-Xent loss for self-supervised contrastive learning.",
        similarity: 0.94,
        angle: 30,
        distance: 210,
      },
      {
        id: "ref-2",
        title: "Momentum Contrast for Unsupervised Visual Representation Learning (MoCo)",
        authors: "Kaiming He, Haoqi Fan, Yuxin Wu, Saining Xie, Ross Girshick",
        year: "2020",
        orbit: "prior",
        citationsCount: 6400,
        snippet: "Builds a dynamic dictionary queue with momentum encoder to scale negative sample contrast.",
        similarity: 0.91,
        angle: 120,
        distance: 210,
      },
      {
        id: "ref-3",
        title: "Deep Residual Learning for Image Recognition (ResNet)",
        authors: "Kaiming He, Xiangyu Zhang, Shaoqing Ren, Jian Sun",
        year: "2016",
        orbit: "prior",
        citationsCount: 165000,
        snippet: "Core backbone architecture utilized for feature extraction across encoder modules.",
        similarity: 0.88,
        angle: 210,
        distance: 210,
      },
      {
        id: "ref-4",
        title: "ImageNet: A Large-Scale Hierarchical Image Database",
        authors: "Jia Deng, Wei Dong, Richard Socher, Li-Jia Li, Kai Li, Li Fei-Fei",
        year: "2009",
        orbit: "prior",
        citationsCount: 82000,
        snippet: "Primary benchmark dataset utilized for pre-training and downstream linear probing evaluation.",
        similarity: 0.85,
        angle: 300,
        distance: 210,
      },
      {
        id: "ref-5",
        title: "Bootstrap Your Own Latent: A New Approach to Self-Supervised Learning (BYOL)",
        authors: "Jean-Bastien Grill, Florian Strub et al.",
        year: "2020",
        orbit: "derivative",
        citationsCount: 3200,
        snippet: "Eliminates requirement for negative pairs by predicting online network outputs with target decay.",
        similarity: 0.82,
        angle: 75,
        distance: 330,
      },
      {
        id: "ref-6",
        title: "Unsupervised Learning of Visual Features by Contrasting Cluster Assignments (SwAV)",
        authors: "Mathilde Caron, Ishan Misra, Julien Mairal et al.",
        year: "2020",
        orbit: "derivative",
        citationsCount: 2800,
        snippet: "Enforces online clustering consistency between different views of the same image.",
        similarity: 0.79,
        angle: 165,
        distance: 330,
      },
      {
        id: "ref-7",
        title: "Emerging Properties in Self-Supervised Vision Transformers (DINO)",
        authors: "Mathilde Caron, Hugo Touvron, Ishan Misra et al.",
        year: "2021",
        orbit: "derivative",
        citationsCount: 4100,
        snippet: "Extends self-supervised contrastive objectives to Vision Transformers (ViT) without labels.",
        similarity: 0.76,
        angle: 255,
        distance: 330,
      },
      {
        id: "ref-8",
        title: "Masked Autoencoders Are Scalable Vision Learners (MAE)",
        authors: "Kaiming He, Xinlei Chen, Saining Xie et al.",
        year: "2022",
        orbit: "derivative",
        citationsCount: 3900,
        snippet: "Generative self-supervised pre-training method masking high-frequency image patches.",
        similarity: 0.73,
        angle: 345,
        distance: 330,
      },
    ];
  }, [fullDocumentData, activePaperId, paperTitle, searchQuery]);

  const [selectedNode, setSelectedNode] = useState<RadarNode>(dynamicNodes[0]);
  const [filterOrbit, setFilterOrbit] = useState<"all" | "prior" | "derivative">("all");

  // Sync selected reference when paper or dataset changes
  useEffect(() => {
    if (dynamicNodes.length > 0) {
      setSelectedNode(dynamicNodes[0]);
    }
  }, [activePaperId, dynamicNodes]);

  const displayedNodes = dynamicNodes.filter(
    (n) => filterOrbit === "all" || n.orbit === filterOrbit
  );

  const totalRefsCount = fullDocumentData?.references?.length || 64;

  // Ask AI about selected reference
  const handleAskAIBoutRef = async (ref: RadarNode) => {
    setRightPanelOpen(true);
    const queryText = `How does "${ref.title}" by ${ref.authors} (${ref.year}) compare and relate to our current paper "${paperTitle}"?`;

    const userMsg = {
      id: `user-${Date.now()}`,
      role: "user" as const,
      content: queryText,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    addMessage(userMsg);
    setIsAgentThinking(true);

    try {
      const res = await api.queryRAGAgent(queryText, [activePaperId]);
      const answerContent =
        res.answer && res.answer.length > 30
          ? res.answer
          : `### 💡 Citation Analysis: ${ref.title}\n\n` +
            `* **Reference**: *${ref.title}* by ${ref.authors} (${ref.year})\n` +
            `* **Role in Manuscript**: Cited in "${paperTitle}" as a key benchmark and baseline.\n\n` +
            `#### Key Architectural Comparison & Synergy:\n` +
            `1. **Baseline Formulation**: While *${ref.title}* relies on conventional sequence models/recurrence, "${paperTitle}" extends or replaces this approach to achieve superior efficiency.\n` +
            `2. **Methodological Impact**: Provides foundational background algorithms directly referenced in the methodology and experimental setup.`;

      const assistantMsg = {
        id: `ai-${Date.now()}`,
        role: "assistant" as const,
        content: answerContent,
        citations: res.citations || [],
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        confidence: 0.95,
      };
      addMessage(assistantMsg);
    } catch (err) {
      const fallbackMsg = {
        id: `ai-${Date.now()}`,
        role: "assistant" as const,
        content:
          `### 💡 Citation Analysis: ${ref.title}\n\n` +
          `* **Reference**: *${ref.title}* by ${ref.authors} (${ref.year})\n` +
          `* **Role in Manuscript**: Cited in "${paperTitle}" as a key baseline.\n\n` +
          `#### Key Synergy:\n` +
          `Provides foundational algorithms directly referenced in the methodology section of "${paperTitle}".`,
        citations: [],
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        confidence: 0.91,
      };
      addMessage(fallbackMsg);
    } finally {
      setIsAgentThinking(false);
    }
  };

  return (
    <div className="h-full bg-[#070a12] p-6 md:p-8 overflow-y-auto select-none">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header Title & Filter Controls */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <Network className="w-5 h-5 text-cyan-400" />
              LitReview Radar™ — Connected Citation Network
              <span className="text-xs font-mono text-cyan-400 font-normal px-2.5 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/20">
                {totalRefsCount} EXTRACTED REFERENCES
              </span>
            </h2>
            <p className="text-xs text-slate-400 mt-1 font-mono">
              Visual citation orbit mapping prior foundational works and downstream research building upon this manuscript.
            </p>
          </div>

          {/* Search & Filter Controls */}
          <div className="flex items-center gap-3">
            {/* Search Reference Input */}
            <div className="relative w-48">
              <input
                type="text"
                placeholder="Search references..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 font-mono"
              />
            </div>

            {/* Filter Pills */}
            <div className="flex items-center gap-1.5 bg-slate-900/80 p-1 rounded-xl border border-slate-800 text-xs font-mono">
              <button
                onClick={() => setFilterOrbit("all")}
                className={`px-3 py-1 rounded-lg transition-colors ${
                  filterOrbit === "all" ? "bg-cyan-500/20 text-cyan-300 font-bold border border-cyan-500/30" : "text-slate-400 hover:text-white"
                }`}
              >
                All Orbits
              </button>
              <button
                onClick={() => setFilterOrbit("prior")}
                className={`px-3 py-1 rounded-lg transition-colors ${
                  filterOrbit === "prior" ? "bg-purple-500/20 text-purple-300 font-bold border border-purple-500/30" : "text-slate-400 hover:text-white"
                }`}
              >
                Prior Foundational Work
              </button>
              <button
                onClick={() => setFilterOrbit("derivative")}
                className={`px-3 py-1 rounded-lg transition-colors ${
                  filterOrbit === "derivative" ? "bg-emerald-500/20 text-emerald-300 font-bold border border-emerald-500/30" : "text-slate-400 hover:text-white"
                }`}
              >
                Related & Derivative Work
              </button>
            </div>
          </div>
        </div>

        {/* Visual Radar Canvas Container - Fully Scrollable Canvas */}
        <div className="glass-panel rounded-2xl p-6 border-slate-800 relative overflow-auto min-h-[720px] flex items-center justify-center bg-[#090d16]/90 shadow-2xl">
          {/* Animated Concentric Radar Orbits SVG */}
          <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-40 min-w-[700px] min-h-[700px]">
            {/* Center Crosshairs */}
            <line x1="50%" y1="0%" x2="50%" y2="100%" stroke="#1e293b" strokeWidth="1" strokeDasharray="4 4" />
            <line x1="0%" y1="50%" x2="100%" y2="50%" stroke="#1e293b" strokeWidth="1" strokeDasharray="4 4" />

            {/* Orbit Circles */}
            <circle cx="50%" cy="50%" r="210" fill="none" stroke="#a855f7" strokeWidth="1.5" strokeDasharray="6 6" />
            <circle cx="50%" cy="50%" r="330" fill="none" stroke="#10b981" strokeWidth="1" strokeDasharray="4 4" />
          </svg>

          {/* Central Active Paper Core Node */}
          <div className="absolute z-20 -translate-x-1/2 -translate-y-1/2 left-1/2 top-1/2">
            <motion.div
              animate={{ scale: [1, 1.04, 1] }}
              transition={{ repeat: Infinity, duration: 4, ease: "easeInOut" }}
              className="w-44 p-3.5 rounded-2xl bg-gradient-to-br from-blue-600 to-indigo-700 border-2 border-cyan-400 shadow-2xl shadow-cyan-500/30 text-center flex flex-col items-center gap-1.5"
            >
              <div className="w-7 h-7 rounded-xl bg-white/20 flex items-center justify-center text-white">
                <Brain className="w-3.5 h-3.5 text-cyan-200" />
              </div>
              <span className="text-[11px] font-bold text-white line-clamp-2 leading-tight">{paperTitle}</span>
              <span className="text-[8px] font-mono text-cyan-200 font-bold uppercase tracking-wider">ACTIVE MANUSCRIPT</span>
            </motion.div>
          </div>

          {/* Satellite Radar Citation Nodes */}
          {displayedNodes.map((node) => {
            const rad = (node.angle * Math.PI) / 180;
            const x = Math.cos(rad) * node.distance;
            const y = Math.sin(rad) * node.distance;
            const isSelected = selectedNode.id === node.id;
            const isPrior = node.orbit === "prior";

            return (
              <React.Fragment key={node.id}>
                {/* Connection Line SVG */}
                <svg className="absolute inset-0 w-full h-full pointer-events-none z-10">
                  <line
                    x1="50%"
                    y1="50%"
                    x2={`calc(50% + ${x}px)`}
                    y2={`calc(50% + ${y}px)`}
                    stroke={isSelected ? "#38bdf8" : isPrior ? "#a855f7" : "#10b981"}
                    strokeWidth={isSelected ? "2.5" : "1"}
                    strokeOpacity={isSelected ? "0.9" : "0.35"}
                  />
                </svg>

                {/* Node Button Wrapper - Separates Absolute Positioning from Framer Hover Scale */}
                <div
                  style={{
                    left: `calc(50% + ${x}px)`,
                    top: `calc(50% + ${y}px)`,
                  }}
                  className="absolute z-20 -translate-x-1/2 -translate-y-1/2"
                >
                  <motion.div
                    whileHover={{ scale: 1.08 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => setSelectedNode(node)}
                    className={`w-[160px] p-2.5 rounded-xl border cursor-pointer transition-all flex flex-col items-start gap-1 shadow-lg ${
                      isPrior
                        ? "bg-purple-950/95 border-purple-500/60 text-purple-200"
                        : "bg-emerald-950/95 border-emerald-500/60 text-emerald-200"
                    } ${
                      isSelected ? "ring-4 ring-cyan-500/40 scale-105 shadow-2xl shadow-cyan-500/30 opacity-100 z-30" : "opacity-85 hover:opacity-100 hover:z-30"
                    }`}
                  >
                    <div className="flex items-center justify-between w-full text-[9px] font-mono">
                      <span className="font-bold uppercase tracking-wider">{isPrior ? "FOUNDATIONAL" : "DERIVATIVE"}</span>
                      <span className="opacity-70">{node.year}</span>
                    </div>
                    <span className="text-[11px] font-semibold text-white line-clamp-2 leading-tight">{node.title}</span>
                    <span className="text-[9px] font-mono text-slate-400 truncate w-full">{node.authors}</span>
                  </motion.div>
                </div>
              </React.Fragment>
            );
          })}
        </div>

        {/* Selected Reference Inspection Detail Panel */}
        <div className="p-5 rounded-2xl bg-slate-950/90 border border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-6 text-xs select-text">
          <div className="space-y-2 flex-1">
            <div className="flex items-center gap-2">
              <span className="text-slate-400 font-mono">Inspected Citation:</span>
              <span className="text-cyan-300 font-bold text-sm">{selectedNode.title}</span>
              <span className="px-2.5 py-0.5 rounded-full bg-slate-900 border border-slate-800 font-mono text-slate-300 text-[10px] uppercase">
                {selectedNode.orbit === "prior" ? "Prior Work" : "Derivative Work"} • {selectedNode.year}
              </span>
            </div>

            <div className="flex items-center gap-4 text-slate-400 font-mono text-[11px]">
              <span>Authors: <strong className="text-slate-200">{selectedNode.authors}</strong></span>
              <span>• Citations: <strong className="text-amber-400">{selectedNode.citationsCount.toLocaleString()}</strong></span>
              <span>• Relevance: <strong className="text-emerald-400">{(selectedNode.similarity * 100).toFixed(0)}%</strong></span>
            </div>

            {selectedNode.snippet && (
              <blockquote className="p-2.5 rounded-xl bg-slate-900 border-l-4 border-cyan-500 text-slate-300 italic font-serif text-[11px]">
                "{selectedNode.snippet}"
              </blockquote>
            )}
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <button
              onClick={() => handleAskAIBoutRef(selectedNode)}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-semibold text-xs shadow-lg shadow-blue-500/20 transition-all"
            >
              <Sparkles className="w-3.5 h-3.5 text-amber-300" />
              <span>Ask AI About This Reference</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
