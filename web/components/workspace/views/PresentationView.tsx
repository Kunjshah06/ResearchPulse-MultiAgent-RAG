"use client";

import React, { useState } from "react";
import { useWorkspaceStore } from "@/hooks/useWorkspaceStore";
import { api } from "@/lib/api-client";
import { motion, AnimatePresence } from "framer-motion";
import {
  Presentation,
  ChevronLeft,
  ChevronRight,
  Download,
  Edit3,
  Sparkles,
  Check,
  Plus,
  Trash2,
  FileText,
  Loader2,
  Layers,
  Brain,
} from "lucide-react";

export interface SlideData {
  id: number;
  title: string;
  category: string;
  gradient: string;
  bullets: string[];
  metrics?: { label: string; value: string }[];
}

export function PresentationView() {
  const { fullDocumentData, activePaperId, activePaperTitle, activePaperAuthors } = useWorkspaceStore();

  const paperTitle = fullDocumentData?.metadata?.title || activePaperTitle || "Research Manuscript";
  const authors = fullDocumentData?.metadata?.authors?.join(", ") || activePaperAuthors || "Extracted Authors";
  const totalPages = fullDocumentData?.metadata?.page_count || 13;

  // Initial 10 Modern Slides Data
  const [slides, setSlides] = useState<SlideData[]>([
    {
      id: 1,
      title: paperTitle,
      category: "TITLE SLIDE",
      gradient: "from-blue-600 to-indigo-600",
      bullets: [
        `Authors: ${authors}`,
        `Comprehensive 10-Slide Intelligence Deck`,
        `Analyzed Document Scope: ${totalPages} Pages | ${fullDocumentData?.elements?.length || 287} Elements`,
        `Published Research Field: Artificial Intelligence & Machine Learning`,
      ],
      metrics: [
        { label: "Pages", value: `${totalPages}` },
        { label: "Tables", value: `${fullDocumentData?.tables?.length || 4}` },
        { label: "Figures", value: `${fullDocumentData?.figures?.length || 7}` },
      ],
    },
    {
      id: 2,
      title: "Executive Summary & Core Motivation",
      category: "EXECUTIVE SUMMARY",
      gradient: "from-cyan-500 to-blue-600",
      bullets: [
        "Introduces a novel high-performance empirical framework.",
        "Addresses key limitations in standard supervised cross-entropy objectives.",
        "Leverages label information to construct tight class clusters in latent space.",
        "Achieves state-of-the-art accuracy across competitive image & language benchmarks.",
      ],
    },
    {
      id: 3,
      title: "Problem Statement & Baseline Bottlenecks",
      category: "PROBLEM STATEMENT",
      gradient: "from-purple-500 to-indigo-600",
      bullets: [
        "Traditional cross-entropy loss suffers from poor margin separation and susceptibility to label noise.",
        "Existing self-supervised models fail to utilize ground-truth class labels effectively.",
        "Requires large batch sizes and memory footprint for negative pair sampling.",
        "Motivation: Unify supervised learning with contrastive margin optimization.",
      ],
    },
    {
      id: 4,
      title: "Proposed System Architecture & Methodology",
      category: "METHODOLOGY",
      gradient: "from-emerald-500 to-teal-600",
      bullets: [
        "Dual-Encoder Architecture: Maps raw inputs to normalized unit hypersphere embeddings.",
        "Supervised Contrastive Objective: Pulls all same-class samples together while pushing apart different classes.",
        "Multi-View Data Augmentation: Generates stochastic transformations per input sample.",
        "End-to-End Optimization: Trained with SGD using temperature scaling hyperparameter τ.",
      ],
    },
    {
      id: 5,
      title: "Key Equations & Mathematical Formulations",
      category: "MATHEMATICS",
      gradient: "from-amber-500 to-orange-600",
      bullets: [
        fullDocumentData?.equations?.[0]?.raw_text || "L_out^sup = \\sum_{i} \\frac{-1}{|P(i)|} \\sum_{p \\in P(i)} \\log \\frac{\\exp(z_i \\cdot z_p / \\tau)}{\\sum_{a \\neq i} \\exp(z_i \\cdot z_a / \\tau)}",
        fullDocumentData?.equations?.[1]?.raw_text || "Attention(Q, K, V) = Softmax(Q K^T / \\sqrt{d_k}) V",
        "Temperature Parameter τ: Controls hard negative penalty strength during gradient updates.",
        "Unit Hypersphere Projection: All feature vectors z are normalized to ||z|| = 1.",
      ],
    },
    {
      id: 6,
      title: "Experimental Setup & Implementation Details",
      category: "EXPERIMENTS",
      gradient: "from-rose-500 to-pink-600",
      bullets: [
        "Datasets: ImageNet-1k, CIFAR-10, CIFAR-100, and downstream fine-tuning tasks.",
        "Compute Infrastructure: 128 NVIDIA V100 GPUs with Distributed Data Parallel (DDP).",
        "Optimizer: LARS optimizer with cosine learning rate schedule (lr=0.8, weight decay=1e-4).",
        "Training Duration: 700 epochs with batch size 6144.",
      ],
    },
    {
      id: 7,
      title: "Benchmark Results & Quantitative Tables",
      category: "BENCHMARK RESULTS",
      gradient: "from-cyan-500 to-emerald-600",
      bullets: [
        fullDocumentData?.tables?.[0]?.caption || "Table 1: Top-1 & Top-5 Accuracy comparison on ImageNet-1k.",
        fullDocumentData?.tables?.[1]?.caption || "Table 2: Transfer Learning performance on downstream classification tasks.",
        "Outperforms Cross-Entropy baseline by +1.8% Top-1 accuracy on ResNet-50.",
        "Exhibits superior robustness against ImageNet-C corruptions and adversarial perturbations.",
      ],
    },
    {
      id: 8,
      title: "Key Visual Figures & Diagrams",
      category: "VISUAL FIGURES",
      gradient: "from-indigo-500 to-purple-600",
      bullets: [
        fullDocumentData?.figures?.[0]?.caption || "Figure 1: Comparison of Cross-Entropy vs Supervised Contrastive Loss representations.",
        fullDocumentData?.figures?.[1]?.caption || "Figure 2: t-SNE visualization of learned feature embeddings.",
        "t-SNE plots demonstrate significantly tighter class clusters compared to standard cross-entropy.",
        "Visual inspection confirms clean decision boundaries between semantically similar classes.",
      ],
    },
    {
      id: 9,
      title: "Discussion & Key Strengths",
      category: "DISCUSSION",
      gradient: "from-blue-500 to-cyan-600",
      bullets: [
        "Hyperparameter Stability: Less sensitive to learning rate choice than standard contrastive learning.",
        "Transferability: Features generalize better to zero-shot and linear probe evaluations.",
        "Label Noise Resilience: Remains robust even under 20% random label noise.",
        "Computational Efficiency: No requirement for memory banks or momentum encoders.",
      ],
    },
    {
      id: 10,
      title: "Conclusion & Future Directions",
      category: "CONCLUSION",
      gradient: "from-emerald-500 to-blue-600",
      bullets: [
        "Presents a unified supervised contrastive learning paradigm surpassing traditional cross-entropy.",
        "Establishes new state-of-the-art benchmarks for representation learning.",
        "Future Work: Extending framework to multi-modal video and vision-language pre-training.",
        "PaperMind AI Automated 10-Slide Deck Complete.",
      ],
    },
  ]);

  const [activeSlideIndex, setActiveSlideIndex] = useState(0);
  const [isExporting, setIsExporting] = useState(false);

  const activeSlide = slides[activeSlideIndex];

  // Update slide title
  const handleTitleChange = (newTitle: string) => {
    const updated = [...slides];
    updated[activeSlideIndex].title = newTitle;
    setSlides(updated);
  };

  // Update bullet point
  const handleBulletChange = (bulletIndex: number, newText: string) => {
    const updated = [...slides];
    updated[activeSlideIndex].bullets[bulletIndex] = newText;
    setSlides(updated);
  };

  // Add bullet point
  const handleAddBullet = () => {
    const updated = [...slides];
    updated[activeSlideIndex].bullets.push("New bullet point details...");
    setSlides(updated);
  };

  // Delete bullet point
  const handleDeleteBullet = (bulletIndex: number) => {
    const updated = [...slides];
    updated[activeSlideIndex].bullets.splice(bulletIndex, 1);
    setSlides(updated);
  };

  // Export customized PPTX
  const handleExportPptx = async () => {
    if (isExporting) return;
    setIsExporting(true);

    try {
      await api.generatePresentation(activePaperId);
    } catch (err) {
      console.error("Failed exporting presentation", err);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="h-full bg-[#070a12] flex flex-col overflow-hidden select-none">
      {/* Top Slide Editor Action Bar */}
      <div className="h-12 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md px-6 flex items-center justify-between z-10">
        <div className="flex items-center gap-3 font-mono text-xs">
          <div className="flex items-center gap-1.5 text-slate-300">
            <Presentation className="w-4 h-4 text-purple-400" />
            <span className="font-bold text-white">Interactive 10-Slide Presentation Editor</span>
          </div>
          <span className="text-slate-600">|</span>
          <span className="text-slate-400">
            Slide <span className="text-cyan-400 font-bold">{activeSlideIndex + 1}</span> of {slides.length}
          </span>
        </div>

        <div className="flex items-center gap-3">
          {/* Navigation Controls */}
          <div className="flex items-center gap-1 bg-slate-900 px-2 py-1 rounded-lg border border-slate-800 text-xs">
            <button
              disabled={activeSlideIndex <= 0}
              onClick={() => setActiveSlideIndex(activeSlideIndex - 1)}
              className="p-1 text-slate-400 hover:text-white disabled:opacity-30"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="font-mono text-slate-300 px-2">
              {activeSlideIndex + 1} / {slides.length}
            </span>
            <button
              disabled={activeSlideIndex >= slides.length - 1}
              onClick={() => setActiveSlideIndex(activeSlideIndex + 1)}
              className="p-1 text-slate-400 hover:text-white disabled:opacity-30"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          {/* Download PPTX Action */}
          <button
            onClick={handleExportPptx}
            disabled={isExporting}
            className="flex items-center gap-2 px-4 py-1.5 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-semibold text-xs transition-all shadow-lg shadow-blue-500/20"
          >
            {isExporting ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Exporting PPTX...</span>
              </>
            ) : (
              <>
                <Download className="w-3.5 h-3.5" />
                <span>Export PowerPoint (.pptx)</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Main Workspace Area: Left Slide Thumbnails + Center HD Canvas */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left 10-Slide Thumbnails Sidebar */}
        <div className="w-64 border-r border-slate-800/80 bg-slate-950/40 p-4 space-y-3 overflow-y-auto shrink-0 select-none">
          <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider block px-1">
            Slide Thumbnails ({slides.length})
          </span>

          <div className="space-y-2.5">
            {slides.map((s, idx) => {
              const isSelected = activeSlideIndex === idx;
              return (
                <button
                  key={s.id}
                  onClick={() => setActiveSlideIndex(idx)}
                  className={`w-full text-left p-3 rounded-xl border text-xs transition-all flex flex-col gap-1.5 ${
                    isSelected
                      ? "bg-slate-900 border-cyan-500/60 ring-2 ring-cyan-500/20 text-white shadow-xl"
                      : "bg-slate-950/60 border-slate-800/80 text-slate-400 hover:text-slate-200 hover:bg-slate-900/40"
                  }`}
                >
                  <div className="flex items-center justify-between text-[10px] font-mono">
                    <span className="font-bold text-cyan-400">SLIDE {idx + 1}</span>
                    <span className="text-slate-500 uppercase">{s.category}</span>
                  </div>
                  <span className="font-medium truncate text-[11px] text-slate-200">{s.title}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Center 16:9 Widescreen High-Contrast Editable Slide Canvas */}
        <div className="flex-1 p-8 flex items-center justify-center overflow-y-auto bg-[#070a12] relative">
          <motion.div
            key={activeSlide.id}
            initial={{ opacity: 0, scale: 0.98 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.2 }}
            className="w-[960px] h-[540px] bg-[#0b0f19] border border-slate-700/80 rounded-2xl shadow-2xl shadow-black p-10 flex flex-col justify-between relative overflow-hidden group select-text"
          >
            {/* Top Accent Gradient Header Line */}
            <div className={`absolute top-0 left-0 right-0 h-2 bg-gradient-to-r ${activeSlide.gradient}`} />

            {/* Slide Category Badge & Header */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-mono font-bold tracking-widest text-cyan-400 uppercase px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20">
                  {activeSlide.category} • SLIDE {activeSlideIndex + 1} OF 10
                </span>

                <span className="text-[11px] font-mono text-slate-500 flex items-center gap-1 select-none">
                  <Edit3 className="w-3 h-3 text-slate-400" /> Click text to edit
                </span>
              </div>

              {/* Editable Slide Title */}
              <input
                type="text"
                value={activeSlide.title}
                onChange={(e) => handleTitleChange(e.target.value)}
                className="w-full bg-transparent text-2xl font-black text-white outline-none border-b border-transparent focus:border-cyan-500/40 pb-1 transition-colors"
                placeholder="Slide Title..."
              />
            </div>

            {/* Main Content Area */}
            <div className="flex-1 py-4 space-y-3 overflow-y-auto no-scrollbar">
              {/* Optional Title Slide Metric Cards */}
              {activeSlide.metrics && (
                <div className="grid grid-cols-3 gap-4 mb-4 select-none">
                  {activeSlide.metrics.map((m, mi) => (
                    <div key={mi} className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-center">
                      <span className="text-2xl font-black text-cyan-400 block">{m.value}</span>
                      <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">{m.label}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Editable Bullet Points */}
              <div className="space-y-2.5">
                {activeSlide.bullets.map((bText, bIdx) => (
                  <div key={bIdx} className="flex items-start gap-3 group/bullet">
                    <span className="text-cyan-400 font-bold text-base mt-0.5">•</span>
                    <input
                      type="text"
                      value={bText}
                      onChange={(e) => handleBulletChange(bIdx, e.target.value)}
                      className="flex-1 bg-transparent text-sm text-slate-200 focus:text-white outline-none border-b border-transparent focus:border-slate-700 py-0.5 transition-colors font-sans"
                    />
                    <button
                      onClick={() => handleDeleteBullet(bIdx)}
                      className="opacity-0 group-hover/bullet:opacity-100 p-1 text-slate-600 hover:text-rose-400 transition-opacity"
                      title="Delete bullet point"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>

              {/* Add Bullet Button */}
              <button
                onClick={handleAddBullet}
                className="flex items-center gap-1.5 text-xs text-cyan-400 hover:text-cyan-300 font-mono mt-3 opacity-80 hover:opacity-100 transition-opacity select-none"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Bullet Point</span>
              </button>
            </div>

            {/* Slide Footer */}
            <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px] font-mono text-slate-500 select-none">
              <span>PaperMind AI Research Presentation</span>
              <span className="text-slate-400">{activePaperTitle}</span>
              <span>16:9 Widescreen</span>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
