"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useWorkspaceStore } from "@/hooks/useWorkspaceStore";
import { api } from "@/lib/api-client";
import { Navbar } from "@/components/landing/Navbar";
import { HeroSection } from "@/components/landing/HeroSection";
import { InteractiveUpload } from "@/components/landing/InteractiveUpload";
import { DemoPaperSelector } from "@/components/landing/DemoPaperSelector";
import { FeatureGrid } from "@/components/landing/FeatureGrid";
import { Footer } from "@/components/landing/Footer";

export default function LandingPage() {
  const router = useRouter();
  const { currentUser, loginUser } = useWorkspaceStore();
  const [authChecked, setAuthChecked] = useState(false);

  useEffect(() => {
    const token = typeof window !== "undefined" ? localStorage.getItem("papermind_token") : null;
    if (!token) {
      router.push("/auth");
      return;
    }

    if (!currentUser) {
      api
        .getMe()
        .then((res) => {
          if (res.user) {
            loginUser({
              id: res.user.id,
              username: res.user.username,
              email: res.user.email,
              token: token,
            });
          }
          setAuthChecked(true);
        })
        .catch(() => {
          if (typeof window !== "undefined") {
            localStorage.removeItem("papermind_token");
          }
          router.push("/auth");
        });
    } else {
      setAuthChecked(true);
    }
  }, [currentUser, loginUser, router]);

  if (!authChecked) {
    return (
      <div className="min-h-screen bg-[#060812] flex items-center justify-center text-slate-400 font-mono text-xs">
        <div className="flex flex-col items-center gap-3">
          <div className="w-6 h-6 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
          <span>Verifying Authentication...</span>
        </div>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-[#080c14] text-slate-100 relative overflow-hidden">
      <Navbar />
      <HeroSection />
      <InteractiveUpload />
      <DemoPaperSelector />
      <FeatureGrid />
      <Footer />
    </main>
  );
}
