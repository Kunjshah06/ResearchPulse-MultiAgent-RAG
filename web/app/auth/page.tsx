"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useWorkspaceStore } from "@/hooks/useWorkspaceStore";
import { api } from "@/lib/api-client";
import { motion, AnimatePresence } from "framer-motion";
import {
  Brain,
  Lock,
  User,
  Mail,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Cpu,
  Layers,
  FileText,
  AlertCircle,
} from "lucide-react";

export default function AuthPage() {
  const router = useRouter();
  const { loginUser } = useWorkspaceStore();

  const [mode, setMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg("");
    setIsLoading(true);

    try {
      if (mode === "register") {
        if (!username.trim() || !email.trim() || !password.trim()) {
          setErrorMsg("Please fill in all fields.");
          setIsLoading(false);
          return;
        }
        const res = await api.register(username, email, password);
        loginUser({
          id: res.user.id,
          username: res.user.username,
          email: res.user.email,
          token: res.token,
        });
        router.push("/");
      } else {
        if (!username.trim() || !password.trim()) {
          setErrorMsg("Please enter your username and password.");
          setIsLoading(false);
          return;
        }
        const res = await api.login(username, password);
        loginUser({
          id: res.user.id,
          username: res.user.username,
          email: res.user.email,
          token: res.token,
        });
        router.push("/");
      }
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || "Authentication failed. Please check your credentials.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#060812] text-slate-100 flex flex-col justify-between relative overflow-hidden select-none">
      {/* Background Ambient Glow Effects */}
      <div className="absolute top-[-15%] left-[-10%] w-[500px] h-[500px] bg-blue-600/15 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute bottom-[-15%] right-[-10%] w-[600px] h-[600px] bg-purple-600/15 rounded-full blur-[160px] pointer-events-none" />
      <div className="absolute top-[40%] left-[35%] w-[400px] h-[400px] bg-cyan-500/10 rounded-full blur-[130px] pointer-events-none" />

      {/* Top Header Logo Bar */}
      <header className="px-8 py-6 relative z-10 flex items-center justify-between max-w-7xl mx-auto w-full">
        <div className="flex items-center gap-3 cursor-pointer" onClick={() => router.push("/")}>
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 via-blue-600 to-purple-600 p-[1px] shadow-lg shadow-cyan-500/20">
            <div className="w-full h-full bg-[#090d16] rounded-xl flex items-center justify-center">
              <Brain className="w-5 h-5 text-cyan-400" />
            </div>
          </div>
          <div>
            <h1 className="text-xl font-black tracking-tight text-white flex items-center gap-1.5 font-sans">
              PaperMind <span className="text-xs font-mono text-cyan-400 px-2 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/20">AI</span>
            </h1>
            <p className="text-[10px] font-mono text-slate-400">Scientific Intelligence Platform</p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>Enterprise Encrypted Auth</span>
        </div>
      </header>

      {/* Main Authentication Grid Container */}
      <main className="relative z-10 my-auto px-4 py-10 max-w-5xl mx-auto w-full grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
        {/* Left Side: Product Showcase & Value Proposition */}
        <div className="lg:col-span-6 space-y-6 text-left pr-0 lg:pr-4">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-300 text-xs font-mono">
            <Sparkles className="w-3.5 h-3.5 text-amber-300" />
            <span>Multi-Agent LangGraph RAG Platform</span>
          </div>

          <h2 className="text-3xl lg:text-4xl font-extrabold text-white leading-tight">
            Unlock Deep Research Intelligence for Scientific Papers
          </h2>

          <p className="text-sm text-slate-400 leading-relaxed">
            PaperMind AI transforms complex academic PDFs into interactive knowledge graphs, zero-shot QA agents, and citation network orbits.
          </p>

          {/* Feature Highlights Grid */}
          <div className="space-y-3.5 pt-2">
            <div className="flex items-start gap-3 p-3 rounded-xl bg-slate-900/60 border border-slate-800/80">
              <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center shrink-0 text-blue-400">
                <Cpu className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-white font-mono">Domain Fine-Tuned Model</h4>
                <p className="text-[11px] text-slate-400">Powered by Qwen 2.5 3B trained on AllenAI SciRIFF dataset.</p>
              </div>
            </div>

            <div className="flex items-start gap-3 p-3 rounded-xl bg-slate-900/60 border border-slate-800/80">
              <div className="w-8 h-8 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center shrink-0 text-purple-400">
                <Layers className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-white font-mono">Connected LitReview Radar™</h4>
                <p className="text-[11px] text-slate-400">Visual citation orbit mapping prior art and foundational papers.</p>
              </div>
            </div>

            <div className="flex items-start gap-3 p-3 rounded-xl bg-slate-900/60 border border-slate-800/80">
              <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center shrink-0 text-emerald-400">
                <ShieldCheck className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-white font-mono">User Document Isolation</h4>
                <p className="text-[11px] text-slate-400">Strict per-user JWT encryption & isolated paper chat histories.</p>
              </div>
            </div>
          </div>
        </div>

        {/* Right Side: Dedicated Auth Card Form */}
        <div className="lg:col-span-6">
          <div className="glass-panel p-8 rounded-3xl border-slate-800 bg-[#090d18]/90 shadow-2xl relative overflow-hidden">
            {/* Form Header Tabs */}
            <div className="flex items-center bg-slate-900/90 p-1 rounded-xl border border-slate-800 mb-6 text-xs font-mono">
              <button
                type="button"
                onClick={() => { setMode("login"); setErrorMsg(""); }}
                className={`flex-1 py-2 rounded-lg font-bold transition-all text-center ${
                  mode === "login"
                    ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-lg shadow-cyan-500/10"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                Sign In
              </button>
              <button
                type="button"
                onClick={() => { setMode("register"); setErrorMsg(""); }}
                className={`flex-1 py-2 rounded-lg font-bold transition-all text-center ${
                  mode === "register"
                    ? "bg-purple-500/20 text-purple-300 border border-purple-500/40 shadow-lg shadow-purple-500/10"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                Create Account
              </button>
            </div>

            {/* Title & Subtitle */}
            <div className="mb-6 space-y-1">
              <h3 className="text-xl font-bold text-white">
                {mode === "login" ? "Welcome Back to PaperMind" : "Start Scientific Research"}
              </h3>
              <p className="text-xs text-slate-400 font-mono">
                {mode === "login"
                  ? "Enter your credentials to access your protected workspace."
                  : "Create a free account to upload and analyze manuscripts."}
              </p>
            </div>

            {/* Error Feedback Alert */}
            <AnimatePresence>
              {errorMsg && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="mb-5 p-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-xs flex items-center gap-2 font-mono"
                >
                  <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
                  <span>{errorMsg}</span>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Form Inputs */}
            <form onSubmit={handleSubmit} className="space-y-4 text-xs font-mono">
              {/* Username Input */}
              <div className="space-y-1.5">
                <label className="text-slate-300 font-semibold flex items-center gap-1.5">
                  <User className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Username</span>
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. het_2518"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full bg-slate-900/90 border border-slate-800 rounded-xl px-3.5 py-2.5 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500/60 focus:ring-1 focus:ring-cyan-500/40 transition-all"
                />
              </div>

              {/* Email Input (Register Only) */}
              {mode === "register" && (
                <div className="space-y-1.5">
                  <label className="text-slate-300 font-semibold flex items-center gap-1.5">
                    <Mail className="w-3.5 h-3.5 text-purple-400" />
                    <span>Email Address</span>
                  </label>
                  <input
                    type="email"
                    required
                    placeholder="name@university.edu"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full bg-slate-900/90 border border-slate-800 rounded-xl px-3.5 py-2.5 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-purple-500/60 focus:ring-1 focus:ring-purple-500/40 transition-all"
                  />
                </div>
              )}

              {/* Password Input */}
              <div className="space-y-1.5">
                <label className="text-slate-300 font-semibold flex items-center gap-1.5">
                  <Lock className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Password</span>
                </label>
                <input
                  type="password"
                  required
                  placeholder="••••••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-slate-900/90 border border-slate-800 rounded-xl px-3.5 py-2.5 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500/60 focus:ring-1 focus:ring-emerald-500/40 transition-all"
                />
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isLoading}
                className="w-full mt-2 py-3 rounded-xl bg-gradient-to-r from-cyan-500 via-blue-600 to-purple-600 hover:from-cyan-400 hover:to-purple-500 text-white font-bold text-xs shadow-lg shadow-cyan-500/20 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
              >
                {isLoading ? (
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <>
                    <span>{mode === "login" ? "Sign In & Access Workspace" : "Create Account & Continue"}</span>
                    <ArrowRight className="w-4 h-4 text-cyan-200" />
                  </>
                )}
              </button>
            </form>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="px-8 py-4 relative z-10 text-center text-[11px] font-mono text-slate-500 max-w-7xl mx-auto w-full">
        PaperMind AI © 2026 • Scientific Research Intelligence Engine
      </footer>
    </div>
  );
}
