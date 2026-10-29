import { FileX } from "lucide-react";

export function DocumentsEmptyState() {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-12 text-center">
      <div className="rounded-full bg-muted p-3">
        <FileX className="h-6 w-6 text-muted-foreground" />
      </div>
      <div>
        <p className="font-medium">No documents yet</p>
        <p className="mt-1 text-sm text-muted-foreground">
          Upload your first document using the dropzone above.
        </p>
      </div>
    </div>
  );
}
