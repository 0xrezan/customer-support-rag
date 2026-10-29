import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "@/shared/api/query-keys";
import { uploadDocument } from "../api/uploadDocument";
import { useToast } from "@/shared/hooks/useToast";
import { mapApiError } from "@/shared/api/error-map";
import type { DocumentUploadResponse } from "../types/documents.types";

export function useUploadDocument() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [progress, setProgress] = useState(0);

  const mutation = useMutation<DocumentUploadResponse, Error, File>({
    mutationFn: (file: File) =>
      uploadDocument({ file, onProgress: setProgress }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.documents.all });
      setProgress(0);
      toast.success(
        data.is_new
          ? `"${data.document.filename}" uploaded successfully`
          : `"${data.document.filename}" is a duplicate — skipped`,
      );
    },
    onError: (error) => {
      setProgress(0);
      toast.error(mapApiError(error).message);
    },
  });

  return { ...mutation, progress };
}
