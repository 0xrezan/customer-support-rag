import { useQuery } from "@tanstack/react-query";
import { queryKeys } from "@/shared/api/query-keys";
import { getDocuments } from "../api/getDocuments";
import { usePageVisibility } from "@/shared/hooks/usePageVisibility";
import { DOCUMENTS_POLL_INTERVAL } from "@/shared/constants/limits";

export function useDocumentsQuery() {
  const isVisible = usePageVisibility();

  return useQuery({
    queryKey: queryKeys.documents.list(),
    queryFn: getDocuments,
    refetchInterval: isVisible ? DOCUMENTS_POLL_INTERVAL : false,
  });
}
