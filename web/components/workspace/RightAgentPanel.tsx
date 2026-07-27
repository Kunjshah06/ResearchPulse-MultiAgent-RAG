"use client";

import React, { useState, useRef, useEffect } from "react";
import { useWorkspaceStore, ChatMessage } from "@/hooks/useWorkspaceStore";
import { api } from "@/lib/api-client";
import { motion } from "framer-motion";
import {
  Brain,
  Send,
  Trash2,
  ExternalLink,
  Bot,
  Loader2,
  ChevronRight,
  GripVertical,
  Sparkles,
} from "lucide-react";

const SUGGESTIONS = [
  "Explain the core methodology of this paper",
  "Summarize key findings & experimental results",
  "What is the mathematical formulation in Section 3?",
];

// Formatting Helper for Markdown rendering
function renderFormattedContent(text: string) {
  if (!text) return null;

  const lines = text.split("\n");

  return (
    <div className="space-y-2 font-sans text-xs leading-relaxed text-slate-200">
      {lines.map((line, idx) => {
        const trimmed = line.trim();
        if (!trimmed) return <div key={idx} className="h-1" />;

        // Headings: ###
        if (trimmed.startsWith("### ")) {
          return (
            <h3 key={idx} className="text-sm font-bold text-cyan-300 mt-2 mb-1 flex items-center gap-1.5 border-b border-slate-800 pb-1">
              <Sparkles className="w-3.5 h-3.5 text-amber-300" />
              <span>{trimmed.replace(/^###\s+/, "")}</span>
            </h3>
          );
        }

        if (trimmed.startsWith("## ")) {
          return (
            <h2 key={idx} className="text-sm font-extrabold text-blue-300 mt-3 mb-1">
              {trimmed.replace(/^##\s+/, "")}
            </h2>
          );
        }

        // Bullet Points: - or *
        if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
          const content = trimmed.replace(/^[-*]\s+/, "");
          return (
            <div key={idx} className="flex items-start gap-2 pl-2">
              <span className="text-blue-400 font-bold">•</span>
              <span>{parseInlineStyles(content)}</span>
            </div>
          );
        }

        // Blockquotes: >
        if (trimmed.startsWith("> ")) {
          const quote = trimmed.replace(/^>\s+/, "");
          return (
            <blockquote key={idx} className="p-2.5 my-1.5 rounded-r-xl border-l-4 border-blue-500 bg-blue-950/30 text-blue-200 italic font-serif text-[11px]">
              {parseInlineStyles(quote)}
            </blockquote>
          );
        }

        return <p key={idx}>{parseInlineStyles(line)}</p>;
      })}
    </div>
  );
}

// Inline styling parser for **bold** and `code`
function parseInlineStyles(str: string) {
  const parts = str.split(/(\*\*.*?\*\*|`.*?`)/g);

  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={i} className="font-bold text-white">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return (
        <code key={i} className="px-1.5 py-0.5 rounded bg-slate-950 border border-slate-800 font-mono text-[11px] text-amber-300">
          {part.slice(1, -1)}
        </code>
      );
    }
    return part;
  });
}

export function RightAgentPanel() {
  const {
    rightPanelOpen,
    messages,
    addMessage,
    isAgentThinking,
    setIsAgentThinking,
    clearChat,
    setSelectedBoundingBox,
    activePaperId,
  } = useWorkspaceStore();

  const [inputQuery, setInputQuery] = useState("");
  const [panelWidth, setPanelWidth] = useState(420);
  const [isResizing, setIsResizing] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isAgentThinking]);

  // Resizable panel mouse handlers
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;
      const newWidth = window.innerWidth - e.clientX;
      if (newWidth >= 280 && newWidth <= 680) {
        setPanelWidth(newWidth);
      }
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    if (isResizing) {
      window.addEventListener("mousemove", handleMouseMove);
      window.addEventListener("mouseup", handleMouseUp);
    }

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isResizing]);

  if (!rightPanelOpen) return null;

  const handleSend = async (queryText?: string) => {
    const q = queryText || inputQuery;
    if (!q.trim() || isAgentThinking) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: q,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    addMessage(userMsg);
    setInputQuery("");
    setIsAgentThinking(true);

    try {
      const res = await api.queryRAGAgent(q, [activePaperId]);

      const assistantMsg: ChatMessage = {
        id: `ai-${Date.now()}`,
        role: "assistant",
        content: res.answer || "I could not generate an answer for this query.",
        citations: res.citations || [],
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        confidence: res.confidence_score || 0.85,
      };

      addMessage(assistantMsg);
    } catch (err) {
      console.error("RAG Agent Query Failed:", err);
      const fallbackMsg: ChatMessage = {
        id: `ai-${Date.now()}`,
        role: "assistant",
        content: `Unable to process your query right now. Please check if the backend FastAPI service is running.`,
        citations: [],
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        confidence: 0.0,
      };
      addMessage(fallbackMsg);
    } finally {
      setIsAgentThinking(false);
    }
  };

  return (
    <motion.aside
      initial={{ x: 320, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: 320, opacity: 0 }}
      transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
      style={{ width: `${panelWidth}px` }}
      className="bg-[#090d16] border-l border-slate-800/80 flex flex-col justify-between shrink-0 select-none z-20 relative"
    >
      {/* Resizable Left Edge Drag Handle */}
      <div
        onMouseDown={(e) => {
          e.preventDefault();
          setIsResizing(true);
        }}
        className="absolute top-0 bottom-0 left-0 w-1.5 hover:w-2 cursor-col-resize bg-transparent hover:bg-blue-500/50 transition-all z-30 flex items-center justify-center group"
        title="Drag to resize AI Agent panel width"
      >
        <GripVertical className="w-3 h-3 text-slate-600 group-hover:text-white opacity-0 group-hover:opacity-100 transition-opacity" />
      </div>

      {/* Header */}
      <div className="h-11 px-4 border-b border-slate-800/80 bg-slate-950/60 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-lg bg-blue-500/20 border border-blue-500/30 flex items-center justify-center text-blue-400">
            <Brain className="w-3.5 h-3.5" />
          </div>
          <span className="text-xs font-bold text-white tracking-tight">PaperMind Assistant</span>
          <span className="text-[9px] font-mono text-emerald-400 px-1.5 py-0.2 rounded bg-emerald-500/10 border border-emerald-500/20">
            Grounded RAG
          </span>
        </div>

        <button
          onClick={clearChat}
          className="p-1.5 text-slate-500 hover:text-slate-300 hover:bg-slate-900 rounded-lg transition-colors"
          title="Clear Chat History"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Messages List */}
      <div className="flex-1 p-4 overflow-y-auto space-y-4">
        {messages.map((msg) => {
          const isUser = msg.role === "user";
          return (
            <div key={msg.id} className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}>
              {!isUser && (
                <div className="w-7 h-7 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white shrink-0 mt-1 shadow-md">
                  <Bot className="w-4 h-4" />
                </div>
              )}

              <div
                className={`max-w-[88%] rounded-2xl p-3.5 text-xs leading-relaxed ${
                  isUser
                    ? "bg-blue-600 text-white rounded-br-none font-medium"
                    : "bg-slate-900/90 border border-slate-800 text-slate-200 rounded-bl-none shadow-xl"
                }`}
              >
                {/* Formatted Markdown Content */}
                {isUser ? (
                  <div className="whitespace-pre-wrap font-sans">{msg.content}</div>
                ) : (
                  renderFormattedContent(msg.content)
                )}

                {/* Evidence Citations Badges */}
                {msg.citations && msg.citations.length > 0 && (
                  <div className="mt-3 pt-2.5 border-t border-slate-800/80 space-y-1.5">
                    <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">
                      Evidence Grounding
                    </span>
                    {msg.citations.map((cite, i) => (
                      <button
                        key={i}
                        onClick={() => cite.bounding_box && setSelectedBoundingBox(cite.bounding_box, cite.page_number)}
                        className="w-full text-left p-2 rounded-lg bg-slate-950/80 hover:bg-slate-950 border border-slate-800 hover:border-amber-500/40 text-[11px] font-mono text-amber-300 flex items-center justify-between transition-all group"
                      >
                        <div className="flex items-center gap-1.5 truncate">
                          <span className="font-bold text-amber-400">[{cite.source_id}]</span>
                          <span className="text-slate-400 truncate">Page {cite.page_number} ({cite.section})</span>
                        </div>
                        <ExternalLink className="w-3 h-3 text-slate-500 group-hover:text-amber-400 shrink-0" />
                      </button>
                    ))}
                  </div>
                )}

                <div suppressHydrationWarning className="mt-2 text-[9px] font-mono text-slate-500 text-right">
                  {msg.timestamp} {msg.confidence && `• Confidence ${(msg.confidence * 100).toFixed(0)}%`}
                </div>
              </div>
            </div>
          );
        })}

        {isAgentThinking && (
          <div className="flex gap-3 items-center text-xs font-mono text-blue-400 p-2 rounded-xl bg-blue-500/5 border border-blue-500/20">
            <div className="w-6 h-6 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center">
              <Loader2 className="w-3.5 h-3.5 animate-spin text-blue-400" />
            </div>
            <span>LangGraph Multi-Agent RAG reasoning...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Questions */}
      <div className="p-3 bg-slate-950/40 border-t border-slate-800/60 space-y-1.5">
        <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider block px-1">
          Suggested Research Queries
        </span>
        <div className="space-y-1">
          {SUGGESTIONS.map((s, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(s)}
              className="w-full text-left p-2 rounded-lg bg-slate-900/60 hover:bg-slate-800/80 border border-slate-800/80 text-[11px] text-slate-300 hover:text-white transition-all flex items-center justify-between group"
            >
              <span className="truncate">{s}</span>
              <ChevronRight className="w-3 h-3 text-slate-500 group-hover:translate-x-0.5 transition-transform shrink-0" />
            </button>
          ))}
        </div>
      </div>

      {/* Chat Input */}
      <div className="p-3 bg-slate-950 border-t border-slate-800/80">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-2 p-1.5 rounded-xl bg-slate-900 border border-slate-800 focus-within:border-blue-500/50 transition-colors"
        >
          <input
            type="text"
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            placeholder="Ask question about document..."
            className="flex-1 bg-transparent px-2 text-xs text-white placeholder-slate-500 outline-none"
          />
          <button
            type="submit"
            disabled={!inputQuery.trim() || isAgentThinking}
            className="p-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white disabled:opacity-40 transition-colors"
          >
            <Send className="w-3.5 h-3.5" />
          </button>
        </form>
      </div>
    </motion.aside>
  );
}
