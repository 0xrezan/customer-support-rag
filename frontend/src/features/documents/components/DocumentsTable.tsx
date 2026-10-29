import { ArrowUp, ArrowDown, ArrowUpDown } from "lucide-react";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
} from "@/shared/ui/table";
import { DocumentsTableRow } from "./DocumentsTableRow";
import type { DocumentItem } from "../types/documents.types";
import type {
  SortField,
  SortState,
} from "../hooks/useDocumentsSort";
import { cn } from "@/shared/lib/cn";

interface DocumentsTableProps {
  documents: DocumentItem[];
  sort: SortState;
  onSort: (field: SortField) => void;
}

function SortIcon({
  field,
  sort,
}: {
  field: SortField;
  sort: SortState;
}) {
  if (sort.field !== field) {
    return <ArrowUpDown className="ml-1 inline h-3 w-3 opacity-40" />;
  }
  return sort.direction === "asc" ? (
    <ArrowUp className="ml-1 inline h-3 w-3" />
  ) : (
    <ArrowDown className="ml-1 inline h-3 w-3" />
  );
}

interface SortableHeadProps {
  field: SortField;
  sort: SortState;
  onSort: (field: SortField) => void;
  children: React.ReactNode;
  className?: string;
}

function SortableHead({
  field,
  sort,
  onSort,
  children,
  className,
}: SortableHeadProps) {
  return (
    <TableHead className={className}>
      <button
        type="button"
        className={cn(
          "inline-flex items-center gap-0.5 hover:text-foreground",
          sort.field === field
            ? "text-foreground"
            : "text-muted-foreground",
        )}
        onClick={() => onSort(field)}
        aria-label={`Sort by ${String(children)}`}
      >
        {children}
        <SortIcon field={field} sort={sort} />
      </button>
    </TableHead>
  );
}

export function DocumentsTable({
  documents,
  sort,
  onSort,
}: DocumentsTableProps) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <SortableHead field="filename" sort={sort} onSort={onSort}>
            Filename
          </SortableHead>
          <SortableHead field="status" sort={sort} onSort={onSort}>
            Status
          </SortableHead>
          <SortableHead field="version" sort={sort} onSort={onSort}>
            Version
          </SortableHead>
          <TableHead>Chunks</TableHead>
          <SortableHead field="file_size" sort={sort} onSort={onSort}>
            Size
          </SortableHead>
          <SortableHead field="created_at" sort={sort} onSort={onSort}>
            Created
          </SortableHead>
          <TableHead className="w-[100px]">Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {documents.map((doc) => (
          <DocumentsTableRow key={doc.id} doc={doc} />
        ))}
      </TableBody>
    </Table>
  );
}
