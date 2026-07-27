"use client";

import React from "react";
import { useWorkspaceStore, WorkspaceTab } from "@/hooks/useWorkspaceStore";
import { PdfView } from "./views/PdfView";
import { HierarchyView } from "./views/HierarchyView";
import { TableView } from "./views/TableView";
import { FigureView } from "./views/FigureView";
import { EquationView } from "./views/EquationView";
import { GraphView } from "./views/GraphView";
import { AnalyticsView } from "./views/AnalyticsView";
import { PresentationView } from "./views/PresentationView";
import { LitReviewRadarView } from "./views/LitReviewRadarView";
import { PeerReviewView } from "./views/PeerReviewView";
import {
  FileText,
  Layers,
  Table,
  Image as ImageIcon,
  FunctionSquare,
  Network,
  BarChart3,
  Presentation,
  Compass,
  Scale,
} from "lucide-react";

export function CenterPanel() {
  const { activeTab, setActiveTab, fullDocumentData } = useWorkspaceStore();

  const isDynamic = Boolean(fullDocumentData);
  const tableCount = fullDocumentData ? fullDocumentData.tables?.length || 0 : 4;
  const figureCount = fullDocumentData ? fullDocumentData.figures?.length || 0 : 7;
  const referenceCount = fullDocumentData ? fullDocumentData.references?.length || 0 : 64;

  // Active workspace navigation tabs
  const tabs: { id: WorkspaceTab; label: string; icon: React.ElementType; badge?: string }[] = [
    { id: "pdf", label: "PDF View", icon: FileText },
    { id: "review", label: "AI Peer Review", icon: Scale, badge: "AI Referee" },
    { id: "radar", label: "LitReview Radar", icon: Compass, badge: `${referenceCount}` },
    { id: "presentation", label: "Slide Deck", icon: Presentation, badge: "10 Slides" },
    { id: "tables", label: "Tables", icon: Table, badge: `${tableCount}` },
    { id: "figures", label: "Figures", icon: ImageIcon, badge: `${figureCount}` },
    { id: "analytics", label: "Analytics", icon: BarChart3 },
  ];

  return (
    <div className="flex-1 flex flex-col bg-[#070a12] min-w-0 overflow-hidden relative">
      {/* Top Tab Bar Navigation */}
      <div className="h-11 border-b border-slate-800/80 bg-[#090d16]/90 backdrop-blur-md px-4 flex items-center gap-1 overflow-x-auto shrink-0 select-none no-scrollbar">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all shrink-0 ${
                isActive
                  ? "bg-slate-800/90 text-white shadow-sm border border-slate-700/60"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/60"
              }`}
            >
              <Icon className={`w-3.5 h-3.5 ${isActive ? "text-purple-400" : "text-slate-500"}`} />
              <span>{tab.label}</span>
              {tab.badge !== undefined && (
                <span
                  className={`text-[9px] font-mono px-1.5 py-0.2 rounded-full ${
                    isActive ? "bg-purple-500/20 text-purple-300 font-bold" : "bg-slate-900 text-slate-500"
                  }`}
                >
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Main Tab View Host */}
      <div className="flex-1 relative overflow-hidden">
        {activeTab === "pdf" && <PdfView />}
        {activeTab === "review" && <PeerReviewView />}
        {activeTab === "radar" && <LitReviewRadarView />}
        {activeTab === "presentation" && <PresentationView />}
        {activeTab === "tree" && <HierarchyView />}
        {activeTab === "tables" && <TableView />}
        {activeTab === "figures" && <FigureView />}
        {activeTab === "equations" && <EquationView />}
        {activeTab === "graph" && <GraphView />}
        {activeTab === "analytics" && <AnalyticsView />}
      </div>
    </div>
  );
}
