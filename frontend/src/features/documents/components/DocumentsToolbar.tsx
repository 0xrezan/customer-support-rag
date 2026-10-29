import { Button } from "@/shared/ui/button";
import { Input } from "@/shared/ui/input";
import { RefreshCw, Search, X } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import { queryKeys } from "@/shared/api/query-keys";
import type { DocumentsFilter } from "../hooks/useDocumentsSort";

const STATUS_OPTIONS = [
  { value: "", label: "All statuses" },
  { value: "pending", label: "Pending" },
  { value: "processing", label: "Processing" },
  { value: "indexed", label: "Indexed" },
  { value: "failed", label: "Failed" },
  { value: "deleted", label: "Deleted" },
] as const;

interface DocumentsToolbarProps {
  filter: DocumentsFilter;
  onFilterChange: (patch: Partial<DocumentsFilter>) => void;
  total: number;
  filtered: number;
}

export function DocumentsToolbar({
  filter,
  onFilterChange,
  total,
  filtered,
}: DocumentsToolbarProps) {
  const queryClient = useQueryClient();

  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.documents.all });
  };

  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-2">
        <h2 className="text-lg font-semibold">Documents</h2>
        <span className="text-sm text-muted-foreground">
          {filtered === total ? total : `${filtered} of ${total}`}
        </span>
      </div>
      <div className="flex items-center gap-2">
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={filter.search}
            onChange={(e) => onFilterChange({ search: e.target.value })}
            placeholder="Search files..."
            className="h-9 w-48 pl-8 pr-8"
            aria-label="Search documents"
          />
          {filter.search && (
            <button
              type="button"
              className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              onClick={() => onFilterChange({ search: "" })}
              aria-label="Clear search"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
        <select
          value={filter.status}
          onChange={(e) => onFilterChange({ status: e.target.value })}
          className="h-9 rounded-md border border-input bg-background px-3 text-sm"
          aria-label="Filter by status"
        >
          {STATUS_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        <Button variant="outline" size="sm" onClick={handleRefresh}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>
    </div>
  );
}
