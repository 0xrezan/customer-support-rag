import { apiClient } from "@/shared/api/client";
import type { DocumentUploadResponse } from "../types/documents.types";

interface UploadDocumentOptions {
  file: File;
  onProgress?: (percent: number) => void;
}

export async function uploadDocument({
  file,
  onProgress,
}: UploadDocumentOptions): Promise<DocumentUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await apiClient.post<DocumentUploadResponse>(
    "/api/v1/admin/documents/upload",
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const percent = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total,
          );
          onProgress(percent);
        }
      },
    },
  );
  return response.data;
}
