import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "PaperMind AI — Multimodal Research Paper Intelligence Platform",
  description: "An end-to-end multimodal research paper intelligence platform featuring dual-path OCR, structural layout parsing, table/figure understanding, and LangGraph multi-agent RAG.",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${inter.variable} ${jetbrainsMono.variable} antialiased bg-[#080c14] text-slate-100 min-h-screen relative selection:bg-blue-500/30`}
      >
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
