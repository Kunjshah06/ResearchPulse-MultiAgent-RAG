"use client";

import React, { useState } from "react";
import { useWorkspaceStore } from "@/hooks/useWorkspaceStore";
import { api } from "@/lib/api-client";
import { motion, AnimatePresence } from "framer-motion";
import {
  X,
  User,
  Lock,
  Mail,
  LogIn,
  UserPlus,
  Brain,
  AlertCircle,
  Loader2,
  CheckCircle2,
} from "lucide-react";

export function AuthModal() {
  const { authModalOpen, setAuthModalOpen, loginUser } = useWorkspaceStore();
  const [mode, setMode] = useState<"login" | "signup">("login");

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [errorMsg, setErrorMsg] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");

  if (!authModalOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg("");
    setSuccessMsg("");

    if (!username.trim() || !password.trim()) {
      setErrorMsg("Username and Password are required.");
      return;
    }

    if (mode === "signup") {
      if (!email.trim()) {
        setErrorMsg("Email address is required for registration.");
        return;
      }
      if (password !== confirmPassword) {
        setErrorMsg("Passwords do not match.");
        return;
      }
      if (password.length < 6) {
        setErrorMsg("Password must be at least 6 characters long.");
        return;
      }
    }

    setIsLoading(true);

    try {
      if (mode === "signup") {
        const res = await api.signup({
          username: username.trim(),
          email: email.trim(),
          password,
        });

        localStorage.setItem("papermind_token", res.token);
        setSuccessMsg("Account created! Logging you in...");
        setTimeout(() => {
          loginUser({
            id: res.user.id,
            username: res.user.username,
            email: res.user.email,
            token: res.token,
          });
        }, 1000);
      } else {
        const res = await api.login({
          username_or_email: username.trim(),
          password,
        });

        localStorage.setItem("papermind_token", res.token);
        setSuccessMsg("Sign in successful!");
        setTimeout(() => {
          loginUser({
            id: res.user.id,
            username: res.user.username,
            email: res.user.email,
            token: res.token,
          });
        }, 800);
      }
    } catch (err: any) {
      const msg =
        err.response?.data?.detail ||
        (mode === "signup" ? "Failed creating account." : "Invalid username or password.");
      setErrorMsg(msg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md">
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 10 }}
          className="w-full max-w-md bg-[#090d16] border border-slate-800 rounded-2xl shadow-2xl p-6 relative overflow-hidden select-none"
        >
          {/* Top Decorative Gradient */}
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 via-purple-500 to-emerald-500" />

          {/* Close Button */}
          <button
            onClick={() => setAuthModalOpen(false)}
            className="absolute top-4 right-4 p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800/80 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>

          {/* Header Branding */}
          <div className="flex items-center gap-3 mb-6">
            <div className="w-9 h-9 rounded-xl bg-blue-500/20 border border-blue-500/30 flex items-center justify-center text-blue-400">
              <Brain className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white tracking-tight">PaperMind Account</h2>
              <p className="text-xs text-slate-400 font-mono">
                {mode === "login" ? "Sign in to access your personal papers" : "Create a new user account"}
              </p>
            </div>
          </div>

          {/* Tab Switcher */}
          <div className="flex bg-slate-900/80 p-1 rounded-xl border border-slate-800 mb-5">
            <button
              onClick={() => {
                setMode("login");
                setErrorMsg("");
                setSuccessMsg("");
              }}
              className={`flex-1 py-1.5 rounded-lg text-xs font-semibold flex items-center justify-center gap-2 transition-all ${
                mode === "login"
                  ? "bg-blue-600 text-white shadow-md"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <LogIn className="w-3.5 h-3.5" />
              <span>Sign In</span>
            </button>
            <button
              onClick={() => {
                setMode("signup");
                setErrorMsg("");
                setSuccessMsg("");
              }}
              className={`flex-1 py-1.5 rounded-lg text-xs font-semibold flex items-center justify-center gap-2 transition-all ${
                mode === "signup"
                  ? "bg-purple-600 text-white shadow-md"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <UserPlus className="w-3.5 h-3.5" />
              <span>Register</span>
            </button>
          </div>

          {/* Error & Success Alerts */}
          {errorMsg && (
            <div className="mb-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {successMsg && (
            <div className="mb-4 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>{successMsg}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Username Input */}
            <div className="space-y-1">
              <label className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block">
                Username
              </label>
              <div className="flex items-center gap-2.5 px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 focus-within:border-blue-500/60 transition-colors">
                <User className="w-4 h-4 text-slate-500" />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Enter your username"
                  className="flex-1 bg-transparent text-xs text-white placeholder-slate-500 outline-none"
                  required
                />
              </div>
            </div>

            {/* Email Input (Signup Mode Only) */}
            {mode === "signup" && (
              <div className="space-y-1">
                <label className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block">
                  Email Address
                </label>
                <div className="flex items-center gap-2.5 px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 focus-within:border-purple-500/60 transition-colors">
                  <Mail className="w-4 h-4 text-slate-500" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@domain.com"
                    className="flex-1 bg-transparent text-xs text-white placeholder-slate-500 outline-none"
                    required
                  />
                </div>
              </div>
            )}

            {/* Password Input */}
            <div className="space-y-1">
              <label className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block">
                Password
              </label>
              <div className="flex items-center gap-2.5 px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 focus-within:border-blue-500/60 transition-colors">
                <Lock className="w-4 h-4 text-slate-500" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="flex-1 bg-transparent text-xs text-white placeholder-slate-500 outline-none"
                  required
                />
              </div>
            </div>

            {/* Confirm Password (Signup Mode Only) */}
            {mode === "signup" && (
              <div className="space-y-1">
                <label className="text-[11px] font-mono text-slate-400 uppercase tracking-wider block">
                  Confirm Password
                </label>
                <div className="flex items-center gap-2.5 px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 focus-within:border-purple-500/60 transition-colors">
                  <Lock className="w-4 h-4 text-slate-500" />
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="••••••••"
                    className="flex-1 bg-transparent text-xs text-white placeholder-slate-500 outline-none"
                    required
                  />
                </div>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className={`w-full py-2.5 rounded-xl font-semibold text-xs text-white transition-all flex items-center justify-center gap-2 shadow-lg ${
                mode === "login"
                  ? "bg-blue-600 hover:bg-blue-500 shadow-blue-500/20"
                  : "bg-purple-600 hover:bg-purple-500 shadow-purple-500/20"
              }`}
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Processing...</span>
                </>
              ) : mode === "login" ? (
                <>
                  <LogIn className="w-4 h-4" />
                  <span>Sign In</span>
                </>
              ) : (
                <>
                  <UserPlus className="w-4 h-4" />
                  <span>Create Account</span>
                </>
              )}
            </button>
          </form>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
