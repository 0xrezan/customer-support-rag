import { apiClient } from "@/shared/api/client";
import type { ReindexResponse } from "../types/documents.types";

export async function reindexDocument(
  docId: string,
): Promise<ReindexResponse> {
  const response = await apiClient.post<ReindexResponse>(
    `/api/v1/admin/documents/${docId}/reindex`,
  );
  return response.data;
}
