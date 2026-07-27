"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useWorkspaceStore } from "@/hooks/useWorkspaceStore";
import { api } from "@/lib/api-client";
import {
  Brain,
  PanelLeft,
  PanelRight,
  Search,
  Share2,
  Download,
  Presentation,
  Loader2,
  Sparkles,
  CheckCircle2,
  User,
  LogIn,
  LogOut,
} from "lucide-react";

export function HeaderBar() {
  const {
    activePaperId,
    activePaperTitle,
    leftSidebarOpen,
    rightPanelOpen,
    toggleLeftSidebar,
    toggleRightPanel,
    setCommandPaletteOpen,
    activeTab,
    currentUser,
    setAuthModalOpen,
    logoutUser,
  } = useWorkspaceStore();

  const [isGeneratingPpt, setIsGeneratingPpt] = useState(false);
  const [downloadSuccess, setDownloadSuccess] = useState(false);

  const { setActiveTab } = useWorkspaceStore();

  const handleGenerateDeck = () => {
    setActiveTab("presentation");
  };

  return (
    <header className="h-14 bg-[#090d16]/90 border-b border-slate-800/80 backdrop-blur-xl px-4 flex items-center justify-between z-30 shrink-0 select-none">
      {/* Left Group */}
      <div className="flex items-center gap-3">
        <button
          onClick={toggleLeftSidebar}
          className={`p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 transition-colors ${
            !leftSidebarOpen ? "bg-blue-500/10 text-blue-400 border border-blue-500/20" : ""
          }`}
          title="Toggle Navigation Sidebar"
        >
          <PanelLeft className="w-4 h-4" />
        </button>

        <Link href="/" className="flex items-center gap-2 mr-2">
          <div className="w-7 h-7 rounded-lg bg-blue-600/20 border border-blue-500/30 flex items-center justify-center text-blue-400">
            <Brain className="w-3.5 h-3.5" />
          </div>
          <span className="text-sm font-bold text-white tracking-tight hidden sm:inline">
            PaperMind
          </span>
        </Link>

        <div className="h-4 w-[1px] bg-slate-800 hidden sm:block" />

        {/* Paper Breadcrumb */}
        <div className="flex items-center gap-2 overflow-hidden">
          <span className="text-xs text-slate-300 truncate max-w-[180px] md:max-w-[280px] font-medium">
            {activePaperTitle}
          </span>
          <span className="text-[10px] font-mono text-purple-400 px-2 py-0.5 rounded bg-purple-500/10 border border-purple-500/20 hidden md:inline">
            {activeTab.toUpperCase()}
          </span>
        </div>
      </div>

      {/* Center Search Input Trigger */}
      <button
        onClick={() => setCommandPaletteOpen(true)}
        className="flex items-center gap-3 px-3.5 py-1.5 rounded-xl bg-slate-900/80 border border-slate-800/80 text-slate-400 hover:text-slate-200 hover:border-slate-700 text-xs transition-all w-36 md:w-72 justify-between group shadow-inner"
      >
        <div className="flex items-center gap-2">
          <Search className="w-3.5 h-3.5 text-slate-500 group-hover:text-blue-400 transition-colors" />
          <span className="truncate">Search document chunks...</span>
        </div>
        <kbd className="hidden sm:inline-block text-[10px] font-mono text-slate-500 px-1.5 py-0.5 rounded bg-slate-950 border border-slate-800">
          ⌘K
        </kbd>
      </button>

      {/* Right Actions — User Auth & PowerPoint 10-Slide Deck Generator */}
      <div className="flex items-center gap-2">
        <button
          onClick={handleGenerateDeck}
          disabled={isGeneratingPpt}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all border shadow-lg ${
            downloadSuccess
              ? "bg-emerald-500/20 border-emerald-500/40 text-emerald-300"
              : "bg-gradient-to-r from-purple-600/30 to-blue-600/30 hover:from-purple-600/40 hover:to-blue-600/40 border-purple-500/40 text-purple-200 hover:text-white"
          }`}
          title="Generate 10-Slide PowerPoint Presentation Deck (.pptx)"
        >
          {isGeneratingPpt ? (
            <>
              <Loader2 className="w-3.5 h-3.5 animate-spin text-purple-400" />
              <span className="hidden sm:inline">Generating 10 Slides...</span>
            </>
          ) : downloadSuccess ? (
            <>
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span className="hidden sm:inline">10-Slide PPTX Downloaded!</span>
            </>
          ) : (
            <>
              <Presentation className="w-3.5 h-3.5 text-amber-400" />
              <span className="hidden sm:inline">Generate 10-Slide Deck</span>
            </>
          )}
        </button>

        <div className="h-4 w-[1px] bg-slate-800 hidden sm:block" />

        {/* User Account Login Button / Profile Badge */}
        {currentUser ? (
          <div className="flex items-center gap-2 px-2.5 py-1 rounded-xl bg-blue-500/10 border border-blue-500/20 text-xs font-mono text-blue-300">
            <User className="w-3.5 h-3.5 text-blue-400" />
            <span className="font-bold truncate max-w-[100px]">{currentUser.username}</span>
            <button
              onClick={logoutUser}
              className="ml-1 p-0.5 rounded text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition-colors"
              title="Log Out"
            >
              <LogOut className="w-3 h-3" />
            </button>
          </div>
        ) : (
          <button
            onClick={() => setAuthModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold shadow-md transition-all"
          >
            <LogIn className="w-3.5 h-3.5" />
            <span>Sign In</span>
          </button>
        )}

        <button
          onClick={toggleRightPanel}
          className={`p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/60 transition-colors ${
            rightPanelOpen ? "bg-purple-500/10 text-purple-400 border border-purple-500/20" : ""
          }`}
          title="Toggle AI Agent Panel"
        >
          <PanelRight className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
}
