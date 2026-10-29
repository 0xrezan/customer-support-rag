import type { Citation } from "../types/chat.types";
import { FileText } from "lucide-react";

interface CitationListProps {
  citations: Citation[];
}

export function CitationList({ citations }: CitationListProps) {
  if (citations.length === 0) return null;

  return (
    <div className="mt-3 space-y-1">
      <p className="text-xs font-medium text-muted-foreground">Sources:</p>
      <ul className="space-y-1">
        {citations.map((citation, index) => (
          <li
            key={`${citation.document_name}-${citation.page}-${index}`}
            className="flex items-start gap-1.5 text-xs text-muted-foreground"
          >
            <FileText className="mt-0.5 h-3 w-3 shrink-0" aria-hidden="true" />
            <span>
              <span className="font-medium">{citation.document_name}</span>
              {citation.page > 0 && (
                <span className="ml-1 text-muted-foreground">
                  (p. {citation.page})
                </span>
              )}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
