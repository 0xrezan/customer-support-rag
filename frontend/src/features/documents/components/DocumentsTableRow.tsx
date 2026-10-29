import { TableRow, TableCell } from "@/shared/ui/table";
import { DocumentStatusBadge } from "./DocumentStatusBadge";
import { DocumentActionsMenu } from "./DocumentActionsMenu";
import { formatBytes } from "@/shared/lib/formatBytes";
import { formatDate } from "@/shared/lib/formatDate";
import type { DocumentItem } from "../types/documents.types";

interface DocumentsTableRowProps {
  doc: DocumentItem;
}

export function DocumentsTableRow({ doc }: DocumentsTableRowProps) {
  return (
    <TableRow>
      <TableCell className="font-medium">{doc.filename}</TableCell>
      <TableCell>
        <DocumentStatusBadge status={doc.status} />
      </TableCell>
      <TableCell>{doc.version}</TableCell>
      <TableCell>
        {doc.chunk_count_actual ?? 0}/{doc.chunk_count_expected ?? 0}
      </TableCell>
      <TableCell>{formatBytes(doc.file_size)}</TableCell>
      <TableCell>{formatDate(doc.created_at)}</TableCell>
      <TableCell>
        <DocumentActionsMenu doc={doc} />
      </TableCell>
    </TableRow>
  );
}
