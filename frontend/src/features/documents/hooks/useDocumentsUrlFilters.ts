import { useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import type { DocumentsFilter } from "./useDocumentsSort";

/**
 * Syncs document filters with URL search params.
 * Allows users to share/bookmark filtered views.
 */
export function useDocumentsUrlFilters() {
  const [searchParams, setSearchParams] = useSearchParams();

  const filter: DocumentsFilter = {
    search: searchParams.get("q") ?? "",
    status: searchParams.get("status") ?? "",
  };

  const updateFilter = useCallback(
    (patch: Partial<DocumentsFilter>) => {
      setSearchParams(
        (prev) => {
          const next = new URLSearchParams(prev);

          if ("search" in patch) {
            if (patch.search) {
              next.set("q", patch.search);
            } else {
              next.delete("q");
            }
          }

          if ("status" in patch) {
            if (patch.status) {
              next.set("status", patch.status);
            } else {
              next.delete("status");
            }
          }

          return next;
        },
        { replace: true },
      );
    },
    [setSearchParams],
  );

  return { filter, updateFilter };
}
