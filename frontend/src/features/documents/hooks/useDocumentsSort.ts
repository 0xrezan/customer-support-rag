import { useState, useMemo, useCallback } from "react";
import type { DocumentItem } from "../types/documents.types";

export type SortField =
  | "filename"
  | "status"
  | "version"
  | "file_size"
  | "created_at";

export type SortDirection = "asc" | "desc";

export interface SortState {
  field: SortField;
  direction: SortDirection;
}

export interface DocumentsFilter {
  search: string;
  status: string;
}

function compareValues(
  a: unknown,
  b: unknown,
  direction: SortDirection,
): number {
  const multiplier = direction === "asc" ? 1 : -1;

  if (a == null && b == null) return 0;
  if (a == null) return multiplier;
  if (b == null) return -multiplier;

  if (typeof a === "string" && typeof b === "string") {
    return multiplier * a.localeCompare(b);
  }
  if (typeof a === "number" && typeof b === "number") {
    return multiplier * (a - b);
  }
  return 0;
}

interface UseDocumentsSortOptions {
  documents: DocumentItem[];
  /** When provided, external filter state is used instead of internal state. */
  externalFilter?: DocumentsFilter;
  /** When provided, external filter updater is used. */
  onFilterChange?: (patch: Partial<DocumentsFilter>) => void;
}

export function useDocumentsSort({
  documents,
  externalFilter,
  onFilterChange,
}: UseDocumentsSortOptions) {
  const [sort, setSort] = useState<SortState>({
    field: "created_at",
    direction: "desc",
  });

  const [internalFilter, setInternalFilter] = useState<DocumentsFilter>({
    search: "",
    status: "",
  });

  const filter = externalFilter ?? internalFilter;

  const toggleSort = useCallback((field: SortField) => {
    setSort((prev) => ({
      field,
      direction:
        prev.field === field && prev.direction === "asc" ? "desc" : "asc",
    }));
  }, []);

  const updateFilter = useCallback(
    (patch: Partial<DocumentsFilter>) => {
      if (onFilterChange) {
        onFilterChange(patch);
      } else {
        setInternalFilter((prev) => ({ ...prev, ...patch }));
      }
    },
    [onFilterChange],
  );

  const processed = useMemo(() => {
    let result = [...documents];

    // Apply search filter
    if (filter.search) {
      const q = filter.search.toLowerCase();
      result = result.filter((d) => d.filename.toLowerCase().includes(q));
    }

    // Apply status filter
    if (filter.status) {
      result = result.filter((d) => d.status === filter.status);
    }

    // Apply sorting
    result.sort((a, b) =>
      compareValues(a[sort.field], b[sort.field], sort.direction),
    );

    return result;
  }, [documents, sort, filter]);

  return {
    sort,
    filter,
    toggleSort,
    updateFilter,
    documents: processed,
  };
}
