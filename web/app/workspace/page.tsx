"use client";

import React, { useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useWorkspaceStore } from "@/hooks/useWorkspaceStore";
import { useDocumentDetails } from "@/hooks/useDocumentDetails";
import { HeaderBar } from "@/components/workspace/HeaderBar";
import { Sidebar } from "@/components/workspace/Sidebar";
import { CenterPanel } from "@/components/workspace/CenterPanel";
import { RightAgentPanel } from "@/components/workspace/RightAgentPanel";
import { CommandPalette } from "@/components/workspace/CommandPalette";
import { AuthModal } from "@/components/auth/AuthModal";
import { api } from "@/lib/api-client";

function WorkspaceContent() {
  const searchParams = useSearchParams();
  const docIdParam = searchParams.get("docId");
  
  const {
    activePaperId,
    setActivePaper,
    setFullDocumentData,
    setIsLoadingDocument,
    currentUser,
    loginUser,
  } = useWorkspaceStore();

  const router = useRouter();

  // Automatic Session Recovery from saved JWT token
  useEffect(() => {
    const token = typeof window !== "undefined" ? localStorage.getItem("papermind_token") : null;
    if (token && !currentUser) {
      api.getMe(token).then((res) => {
        if (res.user) {
          loginUser({
            id: res.user.id,
            username: res.user.username,
            email: res.user.email,
            token: token,
          });
        }
      }).catch(() => {
        localStorage.removeItem("papermind_token");
        router.push("/auth");
      });
    } else if (!token && !currentUser) {
      router.push("/auth");
    }
  }, [currentUser, loginUser, router]);

  // Sync URL ?docId=... on page load / navigation
  useEffect(() => {
    if (docIdParam) {
      setActivePaper(docIdParam, "Uploaded Research Paper", "Extracted Authors");
    }
  }, [docIdParam]);

  // Fetch full document details from FastAPI backend
  const { data: documentData, isLoading } = useDocumentDetails(activePaperId);

  // Sync fetched backend document entity into Zustand store
  useEffect(() => {
    setIsLoadingDocument(isLoading);
    if (documentData) {
      setFullDocumentData(documentData);
      if (documentData.metadata?.title) {
        setActivePaper(
          documentData.id || activePaperId,
          documentData.metadata.title,
          Array.isArray(documentData.metadata.authors)
            ? documentData.metadata.authors.join(", ")
            : (documentData.metadata.authors || "Extracted Authors")
        );
      }
    }
  }, [documentData, isLoading, activePaperId, setFullDocumentData, setIsLoadingDocument, setActivePaper]);

  return (
    <div className="h-screen w-screen flex flex-col bg-[#070a12] text-slate-100 overflow-hidden relative font-sans select-none">
      {/* Top Application Header */}
      <HeaderBar />

      {/* Main 3-Panel Workspace Container */}
      <div className="flex-1 flex min-h-0 overflow-hidden relative">
        {/* Panel 1: Left Navigation Sidebar */}
        <Sidebar />

        {/* Panel 2: Center Main View Host */}
        <CenterPanel />

        {/* Panel 3: Right AI Agent Streaming Panel */}
        <RightAgentPanel />
      </div>

      {/* Global Search & Auth Modals */}
      <CommandPalette />
      <AuthModal />
    </div>
  );
}

export default function WorkspacePage() {
  return (
    <Suspense fallback={<div className="h-screen w-screen bg-[#070a12] flex items-center justify-center text-xs font-mono text-slate-400">Loading Workspace...</div>}>
      <WorkspaceContent />
    </Suspense>
  );
}
