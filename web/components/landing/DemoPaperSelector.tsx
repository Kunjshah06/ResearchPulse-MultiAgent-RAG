"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { FileText, ArrowUpRight, Table, Image, FunctionSquare, Layers, Tag } from "lucide-react";
import { SamplePaper } from "@/types";

const DEMO_PAPERS: SamplePaper[] = [
  {
    id: "attention-is-all-you-need",
    title: "Attention Is All You Need",
    authors: "Vaswani et al. (Google Brain & Research)",
    year: "2017",
    venue: "NeurIPS 2017",
    abstract: "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks. We propose the Transformer, a model architecture relying entirely on attention mechanisms.",
    filename: "Attention_Is_All_You_Need.pdf",
    size: "2.1 MB",
    pages: 15,
    tables: 4,
    figures: 7,
    equations: 8,
    tags: ["Transformers", "Self-Attention", "NLP"],
  },
  {
    id: "bert-pretraining",
    title: "BERT: Pre-training of Deep Bidirectional Transformers",
    authors: "Devlin et al. (Google AI Language)",
    year: "2018",
    venue: "NAACL 2019",
    abstract: "We introduce BERT, which stands for Bidirectional Encoder Representations from Transformers. Unlike recent language representation models, BERT is designed to pretrain deep bidirectional representations.",
    filename: "BERT_Pretraining.pdf",
    size: "1.8 MB",
    pages: 16,
    tables: 11,
    figures: 5,
    equations: 3,
    tags: ["BERT", "Pre-training", "Language Model"],
  },
  {
    id: "resnet-deep-residual",
    title: "Deep Residual Learning for Image Recognition",
    authors: "He et al. (Microsoft Research)",
    year: "2015",
    venue: "CVPR 2016",
    abstract: "Deeper neural networks are more difficult to train. We present a residual learning framework to ease the training of networks that are substantially deeper than those previously used.",
    filename: "ResNet_Deep_Residual.pdf",
    size: "3.4 MB",
    pages: 12,
    tables: 6,
    figures: 13,
    equations: 4,
    tags: ["Computer Vision", "ResNet", "Skip Connections"],
  },
];

export function DemoPaperSelector() {
  const router = useRouter();

  const handleSelect = (paper: SamplePaper) => {
    router.push(`/workspace?demo=${paper.id}`);
  };

  return (
    <section id="demo-papers" className="max-w-7xl mx-auto px-6 mb-24">
      <div className="text-center mb-12">
        <span className="text-xs font-mono text-blue-400 uppercase tracking-widest px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20">
          Instant Demo Mode
        </span>
        <h2 className="text-3xl md:text-4xl font-bold text-white tracking-tight mt-3">
          Explore Pre-Parsed Benchmark Papers
        </h2>
        <p className="text-sm text-slate-400 mt-2 max-w-xl mx-auto">
          Test PaperMind AI instantly without uploading your own file. Click any paper below to launch the workspace with pre-computed layout trees, tables, and knowledge graphs.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {DEMO_PAPERS.map((paper, index) => (
          <motion.div
            key={paper.id}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: index * 0.1 }}
            onClick={() => handleSelect(paper)}
            className="glass-panel-interactive rounded-2xl p-6 cursor-pointer flex flex-col justify-between group relative overflow-hidden"
          >
            <div className="space-y-4">
              {/* Header Badge */}
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-mono text-purple-400 px-2.5 py-1 rounded-md bg-purple-500/10 border border-purple-500/20">
                  {paper.venue} ({paper.year})
                </span>
                <div className="w-8 h-8 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-400 group-hover:text-blue-400 group-hover:border-blue-500/30 transition-all">
                  <ArrowUpRight className="w-4 h-4 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
                </div>
              </div>

              {/* Title & Author */}
              <div>
                <h3 className="text-lg font-semibold text-white group-hover:text-blue-300 transition-colors line-clamp-2">
                  {paper.title}
                </h3>
                <p className="text-xs text-slate-400 mt-1 font-mono">{paper.authors}</p>
              </div>

              {/* Abstract */}
              <p className="text-xs text-slate-400 leading-relaxed line-clamp-3">
                {paper.abstract}
              </p>

              {/* Tags */}
              <div className="flex flex-wrap gap-1.5 pt-2">
                {paper.tags.map((tag) => (
                  <span
                    key={tag}
                    className="text-[10px] text-slate-300 px-2 py-0.5 rounded bg-slate-900/80 border border-slate-800"
                  >
                    #{tag}
                  </span>
                ))}
              </div>
            </div>

            {/* Extracted Metrics Footer */}
            <div className="pt-6 mt-6 border-t border-slate-800/80 grid grid-cols-4 gap-2 text-center text-[11px] font-mono text-slate-400">
              <div className="flex flex-col items-center">
                <span className="text-slate-200 font-bold">{paper.pages}</span>
                <span className="text-[9px] text-slate-500">Pages</span>
              </div>
              <div className="flex flex-col items-center">
                <span className="text-blue-400 font-bold">{paper.tables}</span>
                <span className="text-[9px] text-slate-500">Tables</span>
              </div>
              <div className="flex flex-col items-center">
                <span className="text-purple-400 font-bold">{paper.figures}</span>
                <span className="text-[9px] text-slate-500">Figures</span>
              </div>
              <div className="flex flex-col items-center">
                <span className="text-emerald-400 font-bold">{paper.equations}</span>
                <span className="text-[9px] text-slate-500">Equations</span>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
