import { useMutation, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "@/shared/api/query-keys";
import { reindexDocument } from "../api/reindexDocument";
import { useToast } from "@/shared/hooks/useToast";
import { mapApiError } from "@/shared/api/error-map";
import type { ReindexResponse } from "../types/documents.types";

export function useReindexDocument() {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation<ReindexResponse, Error, string>({
    mutationFn: (docId: string) => reindexDocument(docId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.documents.all });
      toast.success("Reindex started");
    },
    onError: (error) => {
      toast.error(mapApiError(error).message);
    },
  });
}
