"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useWorkspaceStore } from "@/hooks/useWorkspaceStore";
import { motion } from "framer-motion";
import {
  FileText,
  Plus,
  Brain,
  Settings,
  Sparkles,
} from "lucide-react";
import { api } from "@/lib/api-client";

export function Sidebar() {
  const router = useRouter();
  const {
    activePaperId,
    setActivePaper,
    uploadedPapers,
    setUploadedPapers,
    leftSidebarOpen,
    currentUser,
    setAuthModalOpen,
    logoutUser,
  } = useWorkspaceStore();

  useEffect(() => {
    api.listDocuments().then((docs) => {
      if (Array.isArray(docs)) {
        setUploadedPapers(
          docs.map((doc) => ({
            id: doc.id,
            title: doc.title,
            authors: doc.authors,
            timestamp: doc.timestamp || "Saved",
          }))
        );
      }
    }).catch(() => {});
  }, [setUploadedPapers]);

  if (!leftSidebarOpen) return null;

  return (
    <motion.aside
      initial={{ x: -260, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: -260, opacity: 0 }}
      transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
      className="w-64 bg-[#090d16] border-r border-slate-800/80 flex flex-col justify-between shrink-0 select-none z-20"
    >
      <div className="p-4 space-y-6 overflow-y-auto">
        {/* Workspace Selector Dropdown */}
        <div className="p-2.5 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between cursor-pointer hover:border-slate-700 transition-colors">
          <div className="flex items-center gap-2.5">
            <div className="w-6 h-6 rounded-lg bg-blue-500/20 border border-blue-500/30 flex items-center justify-center text-blue-400">
              <Brain className="w-3.5 h-3.5" />
            </div>
            <div className="flex flex-col">
              <span className="text-xs font-semibold text-white">AI Research Lab</span>
              <span className="text-[10px] text-slate-400 font-mono">Personal Workspace</span>
            </div>
          </div>
        </div>

        {/* Upload Action Button */}
        <Link
          href="/#upload"
          className="flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/30 text-blue-400 text-xs font-semibold transition-all group"
        >
          <Plus className="w-4 h-4 group-hover:rotate-90 transition-transform duration-300" />
          <span>Upload New Manuscript</span>
        </Link>

        {/* Navigation Sections — Clean Real Uploaded Papers */}
        <div className="space-y-4">
          <div>
            <div className="text-[11px] font-mono text-emerald-400 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
              <Sparkles className="w-3 h-3" />
              <span>Your Uploaded Papers</span>
            </div>

            {uploadedPapers.length > 0 ? (
              <div className="space-y-1.5">
                {uploadedPapers.map((paper) => {
                  const isActive = activePaperId === paper.id;
                  return (
                    <button
                      key={paper.id}
                      onClick={() => {
                        setActivePaper(paper.id, paper.title, paper.authors);
                        router.push(`/workspace?docId=${paper.id}`);
                      }}
                      className={`w-full text-left p-2.5 rounded-xl text-xs flex items-start gap-2.5 transition-all group ${
                        isActive
                          ? "bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 shadow-sm"
                          : "text-slate-300 hover:text-white hover:bg-slate-900/60 border border-transparent"
                      }`}
                    >
                      <FileText className={`w-4 h-4 shrink-0 mt-0.5 ${isActive ? "text-emerald-400" : "text-slate-400"}`} />
                      <div className="flex flex-col overflow-hidden">
                        <span className="font-semibold truncate group-hover:text-white transition-colors">
                          {paper.title}
                        </span>
                        <span className="text-[10px] text-slate-500 font-mono truncate">
                          {paper.authors || "Extracted Authors"}
                        </span>
                      </div>
                    </button>
                  );
                })}
              </div>
            ) : (
              <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/60 text-center space-y-2">
                <FileText className="w-6 h-6 text-slate-600 mx-auto" />
                <p className="text-xs text-slate-400">No manuscripts uploaded yet</p>
                <Link
                  href="/#upload"
                  className="inline-block text-[11px] text-blue-400 font-medium hover:underline"
                >
                  Upload your first PDF &rarr;
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* User Profile & System Status Footer */}
      <div className="p-3 border-t border-slate-800/80 bg-slate-950/60 space-y-3">
        <div className="flex items-center justify-between px-2 py-1 text-[10px] font-mono text-slate-400">
          <span className="flex items-center gap-1.5 text-emerald-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            FastAPI Connected
          </span>
          <span className="text-slate-500">v1.0</span>
        </div>

        <div className="flex items-center justify-between p-2 rounded-xl bg-slate-900/80 border border-slate-800">
          {currentUser ? (
            <div className="flex items-center justify-between w-full">
              <div className="flex items-center gap-2 overflow-hidden">
                <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-xs uppercase shrink-0">
                  {currentUser.username.slice(0, 2)}
                </div>
                <div className="flex flex-col overflow-hidden">
                  <span className="text-xs font-semibold text-slate-200 truncate">{currentUser.username}</span>
                  <span className="text-[10px] text-slate-500 font-mono truncate">{currentUser.email}</span>
                </div>
              </div>
              <button
                onClick={logoutUser}
                className="text-slate-500 hover:text-rose-400 p-1 font-mono text-[10px] transition-colors shrink-0"
                title="Log Out"
              >
                Logout
              </button>
            </div>
          ) : (
            <button
              onClick={() => setAuthModalOpen(true)}
              className="flex items-center justify-between w-full text-slate-400 hover:text-white transition-colors"
            >
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg bg-slate-800 flex items-center justify-center text-slate-400 text-xs">
                  ?
                </div>
                <div className="flex flex-col text-left">
                  <span className="text-xs font-semibold text-slate-300">Guest User</span>
                  <span className="text-[10px] text-blue-400 font-mono">Sign In / Register &rarr;</span>
                </div>
              </div>
            </button>
          )}
        </div>
      </div>
    </motion.aside>
  );
}
