"use client";

import React, { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { useWorkspaceStore } from "@/hooks/useWorkspaceStore";
import { api } from "@/lib/api-client";
import { motion } from "framer-motion";
import { UploadCloud, FileText, CheckCircle2, AlertCircle, Loader2, ArrowRight, Sparkles, Layers, Cpu, Database } from "lucide-react";
import confetti from "canvas-confetti";

export function InteractiveUpload() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { setActivePaper, addUploadedPaper, currentUser, setAuthModalOpen } = useWorkspaceStore();

  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progressStage, setProgressStage] = useState<number>(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const stages = [
    { label: "Uploading & Validating PDF", icon: FileText, detail: "Sending to FastAPI /documents/upload" },
    { label: "Dual-Path Ingestion & OCR", icon: Cpu, detail: "Routing native text vs scanned pages" },
    { label: "Extracting Layout & Equations", icon: Layers, detail: "Building document hierarchy tree" },
    { label: "Constructing Knowledge Graph", icon: Database, detail: "Indexing vectors into Qdrant & Neo4j" },
  ];

  const handleFileSelect = (selectedFile: File) => {
    if (!currentUser) {
      setAuthModalOpen(true);
      return;
    }
    if (selectedFile.type !== "application/pdf") {
      setErrorMessage("Please select a valid PDF research paper.");
      return;
    }
    if (selectedFile.size > 50 * 1024 * 1024) {
      setErrorMessage("File size exceeds 50MB limit.");
      return;
    }
    setErrorMessage(null);
    setFile(selectedFile);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const processPaper = async () => {
    if (!file) return;
    setIsProcessing(true);
    setProgressStage(0);
    setErrorMessage(null);

    const stageInterval = setInterval(() => {
      setProgressStage((prev) => (prev < stages.length - 1 ? prev + 1 : prev));
    }, 1200);

    try {
      const docSummary = await api.uploadDocument(file);
      
      clearInterval(stageInterval);
      setProgressStage(3);

      const paperTitle = docSummary.title || file.name.replace(".pdf", "");
      const paperAuthors = docSummary.authors && docSummary.authors.length > 0 ? docSummary.authors.join(", ") : "Extracted Authors";

      // Register uploaded paper item in Zustand store
      addUploadedPaper({
        id: docSummary.id,
        title: paperTitle,
        authors: paperAuthors,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      });

      // Set active paper in Zustand
      setActivePaper(docSummary.id, paperTitle, paperAuthors);

      confetti({
        particleCount: 90,
        spread: 80,
        origin: { y: 0.6 },
      });

      setTimeout(() => {
        router.push(`/workspace?docId=${docSummary.id}`);
      }, 500);

    } catch (err: any) {
      clearInterval(stageInterval);
      setIsProcessing(false);
      console.error("FastAPI Upload Error:", err);
      const msg = err?.response?.data?.detail || err?.message || "Failed to connect to FastAPI backend on port 8000.";
      setErrorMessage(`Ingestion Error: ${msg}`);
    }
  };

  return (
    <div id="upload" className="max-w-4xl mx-auto px-6 mb-24 relative z-10">
      <motion.div
        initial={{ opacity: 0, scale: 0.96 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5, delay: 0.4 }}
        className="glass-panel rounded-3xl p-8 md:p-10 border-glow shadow-2xl relative overflow-hidden"
      >
        <div className="text-center mb-8">
          <h2 className="text-2xl md:text-3xl font-bold text-white tracking-tight flex items-center justify-center gap-2">
            <UploadCloud className="w-6 h-6 text-blue-400" />
            Upload Research Paper
          </h2>
          <p className="text-sm text-slate-400 mt-2">
            Upload a real PDF to trigger the PaperMind FastAPI pipeline (OCR, Layout Parsing, Vector Indexing, Graph Building).
          </p>
        </div>

        {!isProcessing ? (
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-2xl p-10 md:p-14 text-center cursor-pointer transition-all duration-300 ${
              isDragging
                ? "border-blue-500 bg-blue-500/10 scale-[1.01]"
                : file
                ? "border-emerald-500/50 bg-emerald-500/5"
                : "border-slate-800 hover:border-slate-700 bg-slate-950/40 hover:bg-slate-900/40"
            }`}
          >
            <input
              type="file"
              ref={fileInputRef}
              accept="application/pdf"
              className="hidden"
              onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
            />

            {!file ? (
              <div className="flex flex-col items-center gap-4">
                <div className="w-16 h-16 rounded-2xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400 group-hover:scale-110 transition-transform">
                  <UploadCloud className="w-8 h-8" />
                </div>
                <div>
                  <p className="text-base font-semibold text-slate-200">
                    <span className="text-blue-400">Click to upload PDF</span> or drag and drop
                  </p>
                  <p className="text-xs text-slate-500 mt-1 font-mono">PDF files up to 50MB supported</p>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-4">
                <div className="w-14 h-14 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                  <FileText className="w-7 h-7" />
                </div>
                <div>
                  <p className="text-base font-semibold text-emerald-300">{file.name}</p>
                  <p className="text-xs text-slate-400 mt-1 font-mono">{(file.size / (1024 * 1024)).toFixed(2)} MB PDF</p>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="py-8 px-4">
            <div className="max-w-md mx-auto space-y-6">
              <div className="flex items-center justify-between text-xs font-mono text-slate-400 mb-2">
                <span>FastAPI Ingestion Pipeline</span>
                <span>{Math.round(((progressStage + 1) / stages.length) * 100)}%</span>
              </div>
              <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden p-0.5 border border-slate-800">
                <motion.div
                  className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full"
                  initial={{ width: "0%" }}
                  animate={{ width: `${((progressStage + 1) / stages.length) * 100}%` }}
                  transition={{ duration: 0.4 }}
                />
              </div>

              <div className="space-y-3 mt-6">
                {stages.map((stage, idx) => {
                  const Icon = stage.icon;
                  const isDone = idx < progressStage;
                  const isCurrent = idx === progressStage;
                  return (
                    <div
                      key={idx}
                      className={`flex items-center gap-3 p-3 rounded-xl border transition-all ${
                        isDone
                          ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-300"
                          : isCurrent
                          ? "bg-blue-500/10 border-blue-500/30 text-blue-300"
                          : "bg-slate-950/20 border-slate-900 text-slate-600"
                      }`}
                    >
                      {isDone ? (
                        <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
                      ) : isCurrent ? (
                        <Loader2 className="w-5 h-5 text-blue-400 animate-spin shrink-0" />
                      ) : (
                        <Icon className="w-5 h-5 shrink-0 opacity-40" />
                      )}
                      <div className="flex flex-col text-left">
                        <span className="text-xs font-semibold">{stage.label}</span>
                        <span className="text-[10px] opacity-70 font-mono">{stage.detail}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {errorMessage && (
          <div className="mt-4 p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{errorMessage}</span>
            </div>
            <button
              onClick={() => {
                setErrorMessage(null);
                setIsProcessing(false);
              }}
              className="text-[10px] underline font-mono text-slate-300 hover:text-white"
            >
              Dismiss
            </button>
          </div>
        )}

        {file && !isProcessing && (
          <div className="mt-8 flex justify-center">
            <button
              onClick={processPaper}
              className="relative group overflow-hidden rounded-xl px-8 py-3.5 font-medium text-sm text-white shadow-xl shadow-blue-500/25 hover:shadow-blue-500/40 transition-all duration-300"
            >
              <span className="absolute inset-0 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 group-hover:scale-105 transition-transform" />
              <span className="relative flex items-center gap-2 font-semibold">
                <Sparkles className="w-4 h-4 text-blue-300" />
                Ingest & Process PDF
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </span>
            </button>
          </div>
        )}
      </motion.div>
    </div>
  );
}
