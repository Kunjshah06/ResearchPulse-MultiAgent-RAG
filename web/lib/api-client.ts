import axios from "axios";
import { DocumentSummary, RAGQueryResponse } from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 120000,
});

apiClient.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("papermind_token");
    if (token && !config.headers.Authorization) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

export const api = {
  // Check backend health
  checkHealth: async () => {
    const res = await apiClient.get("/health");
    return res.data;
  },

  // Upload PDF research document
  uploadDocument: async (file: File): Promise<DocumentSummary> => {
    const formData = new FormData();
    formData.append("file", file);
    const res = await apiClient.post("/documents/upload", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return res.data;
  },

  // Get full document extraction details
  getDocument: async (docId: string) => {
    const res = await apiClient.get(`/documents/${docId}`);
    return res.data;
  },

  // List all uploaded documents
  listDocuments: async () => {
    const res = await apiClient.get("/documents");
    return res.data;
  },

  // Search documents
  searchDocuments: async (query: string, topK: number = 5) => {
    const res = await apiClient.post("/search/", { query, top_k: topK });
    return res.data;
  },

  // Query LangGraph Agent RAG Workflow
  queryRAGAgent: async (query: string, filterDocIds?: string[]): Promise<RAGQueryResponse> => {
    const res = await apiClient.post(
      "/query/",
      {
        query,
        filter_doc_ids: filterDocIds,
      },
      { timeout: 120000 }
    );
    return res.data;
  },

  // Download 10-slide PowerPoint PPTX presentation deck
  generatePresentation: async (docId: string) => {
    const response = await apiClient.post(
      `/documents/${docId}/generate-presentation`,
      {},
      { responseType: "blob" }
    );
    const blob = new Blob([response.data], {
      type: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `${docId}_10_Slide_Deck.pptx`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  // Auth: Register / Signup User
  register: async (username: string, email: string, password: string) => {
    const res = await apiClient.post("/auth/register", { username, email, password });
    return res.data;
  },

  signup: async (data: { username: string; email: string; password: string }) => {
    const res = await apiClient.post("/auth/register", data);
    return res.data;
  },

  // Auth: Login User
  login: async (usernameOrData: string | { username_or_email: string; password: string }, password?: string) => {
    const payload = typeof usernameOrData === "object"
      ? usernameOrData
      : { username_or_email: usernameOrData, password: password || "" };
    const res = await apiClient.post("/auth/login", payload);
    return res.data;
  },

  // Auth: Get Current Profile
  getMe: async (token?: string) => {
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const res = await apiClient.get("/auth/me", { headers });
    return res.data;
  },

  // Peer Review: Run Autonomous Peer Review Agent
  getPeerReview: async (docId: string) => {
    const res = await apiClient.post("/query/peer-review", { doc_id: docId }, { timeout: 45000 });
    return res.data;
  },
};
