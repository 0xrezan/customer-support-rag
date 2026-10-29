import { useMutation, useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "@/shared/api/query-keys";
import { deleteDocument } from "../api/deleteDocument";
import { useToast } from "@/shared/hooks/useToast";
import { mapApiError } from "@/shared/api/error-map";
import type { DeleteResponse } from "../types/documents.types";

export function useDeleteDocument() {
  const queryClient = useQueryClient();
  const toast = useToast();

  return useMutation<DeleteResponse, Error, string>({
    mutationFn: (docId: string) => deleteDocument(docId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.documents.all });
      toast.success("Document deleted");
    },
    onError: (error) => {
      toast.error(mapApiError(error).message);
    },
  });
}
