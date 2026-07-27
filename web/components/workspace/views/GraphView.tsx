"use client";

import React, { useState } from "react";
import { useWorkspaceStore } from "@/hooks/useWorkspaceStore";
import { motion } from "framer-motion";
import {
  Network,
  Brain,
  FileText,
  Table as TableIcon,
  Image as ImageIcon,
  FunctionSquare,
  User,
  Layers,
  ArrowUpRight,
  Eye,
} from "lucide-react";

export interface KnowledgeGraphNode {
  id: string;
  label: string;
  type: "document" | "author" | "section" | "table" | "figure" | "equation" | "concept";
  pageNumber?: number;
  snippet?: string;
  color: string;
  icon: any;
}

export function GraphView() {
  const {
    fullDocumentData,
    activePaperTitle,
    activePaperAuthors,
    setActivePageNumber,
    setSelectedBoundingBox,
  } = useWorkspaceStore();

  const isDynamic = Boolean(fullDocumentData);

  // Dynamically extract real nodes from uploaded document data
  const documentNode: KnowledgeGraphNode = {
    id: "node-doc",
    label: fullDocumentData?.metadata?.title || activePaperTitle || "Research Manuscript",
    type: "document",
    color: "border-blue-500 text-blue-400 bg-blue-500/10",
    icon: FileText,
  };

  const authorNode: KnowledgeGraphNode = {
    id: "node-author",
    label:
      fullDocumentData?.metadata?.authors && fullDocumentData.metadata.authors.length > 0
        ? fullDocumentData.metadata.authors.join(", ")
        : activePaperAuthors || "Research Authors",
    type: "author",
    color: "border-indigo-500 text-indigo-400 bg-indigo-500/10",
    icon: User,
  };

  // Extract Section Headings (Top 4)
  const sectionNodes: KnowledgeGraphNode[] = (fullDocumentData?.elements || [])
    .filter((el) => el.element_type === "heading" || el.element_type === "subheading")
    .slice(0, 4)
    .map((el, i) => ({
      id: `node-sec-${i}`,
      label: el.content || el.text || `Section ${i + 1}`,
      type: "section",
      pageNumber: el.page_number,
      snippet: el.content,
      color: "border-purple-500 text-purple-400 bg-purple-500/10",
      icon: Layers,
    }));

  // Extract Tables (Top 4)
  const tableNodes: KnowledgeGraphNode[] = (fullDocumentData?.tables || []).slice(0, 4).map((tb, i) => ({
    id: `node-tbl-${i}`,
    label: tb.caption ? (tb.caption.length > 35 ? tb.caption.slice(0, 35) + "..." : tb.caption) : `Table ${i + 1}`,
    type: "table",
    pageNumber: tb.page_number,
    snippet: tb.caption || `Extracted Table on Page ${tb.page_number}`,
    color: "border-cyan-500 text-cyan-400 bg-cyan-500/10",
    icon: TableIcon,
  }));

  // Extract Figures (Top 4)
  const figureNodes: KnowledgeGraphNode[] = (fullDocumentData?.figures || []).slice(0, 4).map((fg, i) => ({
    id: `node-fig-${i}`,
    label: fg.caption ? (fg.caption.length > 35 ? fg.caption.slice(0, 35) + "..." : fg.caption) : `Figure ${i + 1}`,
    type: "figure",
    pageNumber: fg.page_number,
    snippet: fg.caption || `Extracted Figure on Page ${fg.page_number}`,
    color: "border-rose-500 text-rose-400 bg-rose-500/10",
    icon: ImageIcon,
  }));

  // Extract Equations (Top 3)
  const equationNodes: KnowledgeGraphNode[] = (fullDocumentData?.equations || []).slice(0, 3).map((eq, i) => ({
    id: `node-eq-${i}`,
    label: `Equation (${i + 1}): ${eq.raw_text ? (eq.raw_text.length > 25 ? eq.raw_text.slice(0, 25) + "..." : eq.raw_text) : `Formula ${i + 1}`}`,
    type: "equation",
    pageNumber: eq.page_number,
    snippet: eq.raw_text || `Equation on Page ${eq.page_number}`,
    color: "border-amber-500 text-amber-400 bg-amber-500/10",
    icon: FunctionSquare,
  }));

  // Combine all nodes
  const allNodes: KnowledgeGraphNode[] = [
    documentNode,
    authorNode,
    ...sectionNodes,
    ...tableNodes,
    ...figureNodes,
    ...equationNodes,
  ];

  const [selectedNode, setSelectedNode] = useState<KnowledgeGraphNode>(allNodes[0]);

  return (
    <div className="h-full bg-[#070a12] p-8 overflow-y-auto">
      <div className="max-w-6xl mx-auto space-y-6">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Network className="w-5 h-5 text-cyan-400" />
            Document Knowledge Graph {isDynamic && (
              <span className="text-xs font-mono text-cyan-400 font-normal px-2.5 py-0.5 rounded bg-cyan-500/10 border border-cyan-500/20">
                LIVE FASTAPI ENTITIES ({allNodes.length} Graph Nodes)
              </span>
            )}
          </h2>
          <p className="text-xs text-slate-400 mt-1 font-mono">
            Network Graph linking document sections, concepts, equations, tables, and authors from uploaded PDF.
          </p>
        </div>

        {/* Visual Graph Canvas Container */}
        <div className="glass-panel rounded-2xl p-8 border-slate-800 relative overflow-hidden min-h-[480px] flex flex-col justify-between">
          <div className="flex flex-wrap items-center justify-center gap-5 py-8 relative z-10">
            {allNodes.map((node) => {
              const Icon = node.icon;
              const isSelected = selectedNode.id === node.id;
              return (
                <motion.div
                  key={node.id}
                  whileHover={{ scale: 1.06 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={() => setSelectedNode(node)}
                  className={`p-4 rounded-2xl border-2 cursor-pointer transition-all flex flex-col items-center gap-2 max-w-[220px] text-center ${node.color} ${
                    isSelected ? "ring-4 ring-cyan-500/30 scale-105 shadow-2xl shadow-cyan-500/20 opacity-100" : "opacity-80 hover:opacity-100"
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span className="text-xs font-semibold text-white leading-tight line-clamp-2">{node.label}</span>
                  <span className="text-[9px] font-mono uppercase tracking-wider opacity-70 flex items-center gap-1">
                    {node.type} {node.pageNumber && `• Page ${node.pageNumber}`}
                  </span>
                </motion.div>
              );
            })}
          </div>

          {/* Selected Node Details Card */}
          <div className="p-5 rounded-xl bg-slate-950/90 border border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 text-xs font-mono">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-slate-400">Selected Node:</span>
                <span className="text-cyan-300 font-bold">{selectedNode.label}</span>
                <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-400 text-[10px] uppercase">
                  {selectedNode.type}
                </span>
              </div>
              {selectedNode.snippet && (
                <p className="text-[11px] text-slate-300 font-serif line-clamp-1 italic">
                  "{selectedNode.snippet}"
                </p>
              )}
            </div>

            {selectedNode.pageNumber && (
              <button
                onClick={() => setActivePageNumber(selectedNode.pageNumber!)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium transition-colors shrink-0"
              >
                <Eye className="w-3.5 h-3.5" />
                <span>View Page {selectedNode.pageNumber} Context</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
