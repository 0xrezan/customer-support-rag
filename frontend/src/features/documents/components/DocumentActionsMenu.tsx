import { useState } from "react";
import { Button } from "@/shared/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/shared/ui/dialog";
import { RotateCw, Trash2 } from "lucide-react";
import { Tooltip } from "@/shared/ui/tooltip";
import { useDeleteDocument } from "../hooks/useDeleteDocument";
import { useReindexDocument } from "../hooks/useReindexDocument";
import type { DocumentItem } from "../types/documents.types";

interface DocumentActionsMenuProps {
  doc: DocumentItem;
}

type ConfirmAction = "delete" | "reindex" | null;

export function DocumentActionsMenu({ doc }: DocumentActionsMenuProps) {
  const [confirmAction, setConfirmAction] = useState<ConfirmAction>(null);
  const deleteMutation = useDeleteDocument();
  const reindexMutation = useReindexDocument();

  const handleConfirm = async () => {
    if (confirmAction === "delete") {
      await deleteMutation.mutateAsync(doc.id);
    } else if (confirmAction === "reindex") {
      await reindexMutation.mutateAsync(doc.id);
    }
    setConfirmAction(null);
  };

  const isPending =
    deleteMutation.isPending || reindexMutation.isPending;

  const dialogTitle = confirmAction === "delete" ? "Delete Document" : "Reindex Document";
  const dialogDescription =
    confirmAction === "delete"
      ? `Are you sure you want to delete "${doc.filename}"? This action cannot be undone.`
      : `Are you sure you want to reindex "${doc.filename}"? This will reprocess the document.`;

  return (
    <>
      <div className="flex items-center gap-1">
        <Tooltip content="Reindex">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={() => setConfirmAction("reindex")}
            disabled={isPending}
            aria-label={`Reindex ${doc.filename}`}
          >
            <RotateCw className="h-4 w-4" />
          </Button>
        </Tooltip>
        <Tooltip content="Delete">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 text-destructive hover:text-destructive"
            onClick={() => setConfirmAction("delete")}
            disabled={isPending}
            aria-label={`Delete ${doc.filename}`}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </Tooltip>
      </div>

      <Dialog
        open={confirmAction !== null}
        onOpenChange={(open) => {
          if (!open) setConfirmAction(null);
        }}
      >
        <DialogContent onClose={() => setConfirmAction(null)}>
          <DialogHeader>
            <DialogTitle>{dialogTitle}</DialogTitle>
            <DialogDescription>{dialogDescription}</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setConfirmAction(null)}
              disabled={isPending}
            >
              Cancel
            </Button>
            <Button
              variant={confirmAction === "delete" ? "destructive" : "default"}
              onClick={handleConfirm}
              disabled={isPending}
            >
              {isPending ? "Processing..." : "Confirm"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
