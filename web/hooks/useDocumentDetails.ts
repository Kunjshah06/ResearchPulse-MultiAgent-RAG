import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import { FullDocumentData } from "@/types";

// Standard 36-character UUID v4 regex pattern (e.g. 828e8d12-1841-47ad-93e0-4981a447e051)
const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export function useDocumentDetails(docId: string | null) {
  // Only query FastAPI if docId is a real 36-character backend UUID
  const isRealBackendDoc = Boolean(docId && UUID_REGEX.test(docId));

  return useQuery<FullDocumentData | null>({
    queryKey: ["document", docId],
    queryFn: async () => {
      if (!docId || !isRealBackendDoc) return null;
      try {
        const data = await api.getDocument(docId);
        return data as FullDocumentData;
      } catch (err) {
        console.warn("Failed to fetch document details from FastAPI backend:", err);
        return null;
      }
    },
    enabled: isRealBackendDoc,
    staleTime: 1000 * 60 * 5, // Cache for 5 minutes
  });
}
