"use client";

import React from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Sparkles, ArrowRight, Zap, Shield, FileText, Cpu, Network, Layers } from "lucide-react";

export function HeroSection() {
  return (
    <section className="relative pt-32 pb-16 md:pt-44 md:pb-24 overflow-hidden">
      {/* Background Glowing Lights */}
      <div className="glow-ambient-blue top-12 left-1/2 -translate-x-1/2" />
      <div className="glow-ambient-purple top-32 right-1/4" />

      <div className="max-w-7xl mx-auto px-6 relative z-10 text-center">
        {/* Top Floating Badge */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-semibold mb-8 backdrop-blur-md shadow-inner shadow-blue-500/10"
        >
          <Sparkles className="w-3.5 h-3.5 text-blue-400 animate-pulse" />
          <span>Next-Generation Multimodal Research Intelligence</span>
          <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
          <span className="text-slate-400 font-mono">v1.0 Production</span>
        </motion.div>

        {/* Main Headline */}
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="text-4xl md:text-6xl lg:text-7xl font-bold tracking-tight text-white max-w-5xl mx-auto leading-[1.15]"
        >
          Transform Research Papers into <br className="hidden sm:inline" />
          <span className="text-gradient">Actionable Intelligence</span>
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="mt-6 text-base md:text-xl text-slate-300 max-w-3xl mx-auto font-normal leading-relaxed"
        >
          PaperMind AI parses complex academic PDFs into deep structural trees, extracts math equations, 
          figures, and tables, and powers evidence-grounded multi-agent reasoning.
        </motion.p>

        {/* Metric Badges / Specs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="mt-10 flex flex-wrap items-center justify-center gap-3 md:gap-4 max-w-4xl mx-auto"
        >
          <div className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-300 font-medium backdrop-blur-md">
            <Cpu className="w-4 h-4 text-blue-400" />
            <span>Dual-Path PDF Routing (Native + OCR)</span>
          </div>
          <div className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-300 font-medium backdrop-blur-md">
            <Layers className="w-4 h-4 text-purple-400" />
            <span>LangGraph Autonomous Multi-Agent RAG</span>
          </div>
          <div className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-300 font-medium backdrop-blur-md">
            <Network className="w-4 h-4 text-emerald-400" />
            <span>Document Knowledge Graph (NetworkX/Neo4j)</span>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
