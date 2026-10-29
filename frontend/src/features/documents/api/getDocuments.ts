import { apiClient } from "@/shared/api/client";
import type { DocumentItem, DocumentListEnvelope } from "../types/documents.types";

export async function getDocuments(): Promise<DocumentItem[]> {
  const response = await apiClient.get<DocumentListEnvelope>(
    "/api/v1/admin/documents",
  );
  return response.data.documents;
}
