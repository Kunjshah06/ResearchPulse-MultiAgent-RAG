"use client";

import React from "react";
import Link from "next/link";
import { Brain, Heart, Terminal, Sparkles } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t border-slate-800/80 bg-[#060911] relative z-10 py-12">
      <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-6">
        {/* Left Brand */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400">
            <Brain className="w-4 h-4" />
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-bold text-white tracking-tight">PaperMind AI</span>
            <span className="text-[10px] text-slate-500 font-mono">Enterprise Multimodal Research Platform</span>
          </div>
        </div>

        {/* Tech Stack Badges */}
        <div className="flex flex-wrap items-center justify-center gap-2 text-[10px] font-mono text-slate-400">
          <span className="px-2.5 py-1 rounded-md bg-slate-900 border border-slate-800">Next.js 15</span>
          <span className="px-2.5 py-1 rounded-md bg-slate-900 border border-slate-800">FastAPI</span>
          <span className="px-2.5 py-1 rounded-md bg-slate-900 border border-slate-800">LangGraph</span>
          <span className="px-2.5 py-1 rounded-md bg-slate-900 border border-slate-800">Qdrant VectorDB</span>
          <span className="px-2.5 py-1 rounded-md bg-slate-900 border border-slate-800">Groq LLM</span>
        </div>

        {/* Right Info */}
        <div className="text-xs text-slate-500 font-mono text-center md:text-right">
          <span>Architected for High-Performance Document AI</span>
        </div>
      </div>
    </footer>
  );
}
