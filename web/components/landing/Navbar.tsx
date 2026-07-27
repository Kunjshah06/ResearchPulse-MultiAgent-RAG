"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Brain, Sparkles, BookOpen, Code2, Cpu, ArrowRight } from "lucide-react";
import { motion } from "framer-motion";

import { useWorkspaceStore } from "@/hooks/useWorkspaceStore";

export function Navbar() {
  const { currentUser, logoutUser } = useWorkspaceStore();
  const [scrolled, setScrolled] = useState(false);
  const [backendStatus, setBackendStatus] = useState<"online" | "checking">("online");

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <motion.header
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5 }}
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? "bg-[#080c14]/80 backdrop-blur-xl border-b border-slate-800/80 py-3.5 shadow-2xl shadow-black/40"
          : "bg-transparent py-5"
      }`}
    >
      <div className="max-w-7xl mx-auto px-6 flex items-center justify-between">
        {/* Brand Logo */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-purple-600 p-[1px] shadow-lg shadow-blue-500/20 group-hover:shadow-blue-500/40 transition-all duration-300">
            <div className="w-full h-full bg-[#0d1322] rounded-[11px] flex items-center justify-center">
              <Brain className="w-5 h-5 text-blue-400 group-hover:scale-110 transition-transform duration-300" />
            </div>
          </div>
          <div className="flex flex-col">
            <span className="text-lg font-bold tracking-tight text-white flex items-center gap-1.5">
              PaperMind <span className="text-gradient text-xs font-semibold px-1.5 py-0.5 rounded-md bg-blue-500/10 border border-blue-500/20">AI</span>
            </span>
            <span className="text-[10px] text-slate-400 font-mono">Multimodal Document Intelligence</span>
          </div>
        </Link>

        {/* Center Nav Links */}
        <nav className="hidden md:flex items-center gap-1 px-4 py-1.5 rounded-full bg-slate-900/60 border border-slate-800/80 backdrop-blur-md">
          <a
            href="#features"
            className="px-4 py-1.5 text-xs font-medium text-slate-300 hover:text-white rounded-full hover:bg-slate-800/50 transition-colors"
          >
            Capabilities
          </a>
          <a
            href="#demo-papers"
            className="px-4 py-1.5 text-xs font-medium text-slate-300 hover:text-white rounded-full hover:bg-slate-800/50 transition-colors"
          >
            Sample Papers
          </a>
          <a
            href="#architecture"
            className="px-4 py-1.5 text-xs font-medium text-slate-300 hover:text-white rounded-full hover:bg-slate-800/50 transition-colors"
          >
            System Design
          </a>
        </nav>

        {/* Right CTA Actions */}
        <div className="flex items-center gap-3">
          {/* User Profile & Auth Status */}
          {currentUser ? (
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-2 text-xs font-mono text-cyan-300 bg-slate-900/90 border border-slate-800 px-3 py-1.5 rounded-xl">
                <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                <span>{currentUser.username}</span>
              </div>
              <button
                onClick={logoutUser}
                className="text-xs font-mono text-slate-400 hover:text-red-400 px-3 py-1.5 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-red-500/40 transition-all cursor-pointer"
              >
                Logout
              </button>
            </div>
          ) : (
            <Link
              href="/auth"
              className="text-xs font-mono text-cyan-400 hover:text-cyan-300 px-3.5 py-2 rounded-xl bg-cyan-500/10 border border-cyan-500/20 hover:border-cyan-500/40 transition-all font-semibold"
            >
              Sign In / Register
            </Link>
          )}

          {/* Launch Workspace CTA Button */}
          <Link
            href="/workspace"
            className="relative group overflow-hidden rounded-xl p-[1px] font-medium text-xs shadow-lg shadow-blue-500/20 hover:shadow-blue-500/40 transition-all duration-300"
          >
            <span className="absolute inset-0 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 group-hover:scale-105 transition-transform duration-300" />
            <span className="relative flex items-center gap-2 px-4 py-2.5 rounded-[11px] bg-[#0d1322] text-white font-semibold transition-colors group-hover:bg-[#0d1322]/80">
              <Sparkles className="w-3.5 h-3.5 text-blue-400 animate-spin-slow" />
              Launch Workspace
              <ArrowRight className="w-3.5 h-3.5 text-slate-400 group-hover:translate-x-0.5 transition-transform" />
            </span>
          </Link>
        </div>
      </div>
    </motion.header>
  );
}
