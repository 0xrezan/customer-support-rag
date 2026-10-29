import { apiClient } from "@/shared/api/client";
import type { DeleteResponse } from "../types/documents.types";

export async function deleteDocument(
  docId: string,
  hard = false,
): Promise<DeleteResponse> {
  const response = await apiClient.delete<DeleteResponse>(
    `/api/v1/admin/documents/${docId}`,
    { params: { hard } },
  );
  return response.data;
}
