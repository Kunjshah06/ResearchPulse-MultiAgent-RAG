import { create } from "zustand";
import { BoundingBox, FullDocumentData } from "@/types";

export type WorkspaceTab = "pdf" | "tree" | "tables" | "figures" | "equations" | "graph" | "analytics" | "presentation" | "radar" | "review";

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: {
    source_id: string;
    doc_id: string;
    page_number: number;
    section?: string;
    snippet: string;
    bounding_box?: BoundingBox;
  }[];
  timestamp: string;
  confidence?: number;
}

export interface UploadedPaperItem {
  id: string;
  title: string;
  authors: string;
  timestamp: string;
}

export interface UserProfile {
  id: string;
  username: string;
  email: string;
  created_at?: string;
  token?: string;
}

interface WorkspaceState {
  // User Authentication
  currentUser: UserProfile | null;
  authModalOpen: boolean;
  setAuthModalOpen: (open: boolean) => void;
  loginUser: (user: UserProfile) => void;
  logoutUser: () => void;

  // Active Paper Metadata
  activePaperId: string;
  activePaperTitle: string;
  activePaperAuthors: string;
  activeTab: WorkspaceTab;
  
  // List of Uploaded Real Papers in Current Session
  uploadedPapers: UploadedPaperItem[];

  // Real Backend Full Document Data Entity
  fullDocumentData: FullDocumentData | null;
  isLoadingDocument: boolean;
  
  // Layout Controls
  leftSidebarOpen: boolean;
  rightPanelOpen: boolean;
  commandPaletteOpen: boolean;
  
  // Bounding Box Jump / Highlight State
  selectedBoundingBox: BoundingBox | null;
  activePageNumber: number;
  
  // Chat History per paper
  paperMessages: Record<string, ChatMessage[]>;
  messages: ChatMessage[];
  isAgentThinking: boolean;

  // Actions
  setActivePaper: (id: string, title: string, authors: string) => void;
  setUploadedPapers: (papers: UploadedPaperItem[]) => void;
  addUploadedPaper: (paper: UploadedPaperItem) => void;
  setFullDocumentData: (data: FullDocumentData | null) => void;
  setIsLoadingDocument: (loading: boolean) => void;
  setActiveTab: (tab: WorkspaceTab) => void;
  toggleLeftSidebar: () => void;
  toggleRightPanel: () => void;
  setRightPanelOpen: (open: boolean) => void;
  setCommandPaletteOpen: (open: boolean) => void;
  setSelectedBoundingBox: (box: BoundingBox | null, page?: number) => void;
  setActivePageNumber: (page: number) => void;
  addMessage: (message: ChatMessage) => void;
  setIsAgentThinking: (thinking: boolean) => void;
  clearChat: () => void;
}

const DEFAULT_WELCOME: ChatMessage = {
  id: "welcome-1",
  role: "assistant",
  content: "Welcome to **PaperMind AI** workspace. I am your multi-agent research assistant powered by LangGraph. What would you like to explore in this document?",
  timestamp: "Just now",
};

export const useWorkspaceStore = create<WorkspaceState>((set) => ({
  currentUser: null,
  authModalOpen: false,
  setAuthModalOpen: (open) => set({ authModalOpen: open }),
  loginUser: (user) => {
    if (typeof window !== "undefined" && user.token) {
      localStorage.setItem("papermind_token", user.token);
    }
    set({ currentUser: user, authModalOpen: false });
  },
  logoutUser: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("papermind_token");
    }
    set({ currentUser: null });
  },

  activePaperId: "attention-is-all-you-need",
  activePaperTitle: "Attention Is All You Need",
  activePaperAuthors: "Vaswani et al. (Google Brain & Research)",
  activeTab: "pdf",

  uploadedPapers: [],
  fullDocumentData: null,
  isLoadingDocument: false,

  leftSidebarOpen: true,
  rightPanelOpen: true,
  commandPaletteOpen: false,

  selectedBoundingBox: null,
  activePageNumber: 1,

  paperMessages: {},
  messages: [DEFAULT_WELCOME],
  isAgentThinking: false,

  setActivePaper: (id, title, authors) =>
    set((state) => {
      const activeMsgs = state.paperMessages[id] || [DEFAULT_WELCOME];
      if (typeof window !== "undefined") {
        window.history.pushState(null, "", `/workspace?docId=${id}`);
      }
      return {
        activePaperId: id,
        activePaperTitle: title,
        activePaperAuthors: authors,
        fullDocumentData: state.activePaperId === id ? state.fullDocumentData : null,
        selectedBoundingBox: null,
        activePageNumber: 1,
        messages: activeMsgs,
      };
    }),

  setUploadedPapers: (papers) => set({ uploadedPapers: papers }),

  addUploadedPaper: (paper) =>
    set((state) => ({
      uploadedPapers: [paper, ...state.uploadedPapers.filter((p) => p.id !== paper.id)],
    })),

  setFullDocumentData: (data) => set({ fullDocumentData: data }),
  setIsLoadingDocument: (loading) => set({ isLoadingDocument: loading }),

  setActiveTab: (tab) => set({ activeTab: tab }),
  toggleLeftSidebar: () => set((state) => ({ leftSidebarOpen: !state.leftSidebarOpen })),
  toggleRightPanel: () => set((state) => ({ rightPanelOpen: !state.rightPanelOpen })),
  setRightPanelOpen: (open) => set({ rightPanelOpen: open }),
  setCommandPaletteOpen: (open) => set({ commandPaletteOpen: open }),

  setSelectedBoundingBox: (box, page) =>
    set((state) => ({
      selectedBoundingBox: box,
      activePageNumber: page !== undefined ? page : box ? box.page : state.activePageNumber,
      activeTab: box ? "pdf" : state.activeTab,
    })),

  setActivePageNumber: (page) => set({ activePageNumber: page }),

  addMessage: (message) =>
    set((state) => {
      const newMsgs = [...state.messages, message];
      return {
        messages: newMsgs,
        paperMessages: {
          ...state.paperMessages,
          [state.activePaperId]: newMsgs,
        },
      };
    }),

  setIsAgentThinking: (thinking) => set({ isAgentThinking: thinking }),

  clearChat: () =>
    set((state) => {
      const resetMsgs = [
        {
          id: `welcome-reset-${Date.now()}`,
          role: "assistant" as const,
          content: "Chat history cleared. How can I assist you with this document?",
          timestamp: "Just now",
        },
      ];
      return {
        messages: resetMsgs,
        paperMessages: {
          ...state.paperMessages,
          [state.activePaperId]: resetMsgs,
        },
      };
    }),
}));
