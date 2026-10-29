import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Upload } from "lucide-react";
import { cn } from "@/shared/lib/cn";
import { UploadProgressBar } from "./UploadProgressBar";
import { useUploadDocument } from "../hooks/useUploadDocument";
import {
  MAX_UPLOAD_SIZE_BYTES,
  ACCEPTED_FILE_TYPES,
} from "@/shared/constants/limits";

export function UploadDropzone() {
  const { mutate, isPending, progress } = useUploadDocument();

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      const file = acceptedFiles[0];
      if (file) {
        mutate(file);
      }
    },
    [mutate],
  );

  const { getRootProps, getInputProps, isDragActive, fileRejections } =
    useDropzone({
      onDrop,
      accept: ACCEPTED_FILE_TYPES,
      maxSize: MAX_UPLOAD_SIZE_BYTES,
      maxFiles: 1,
      disabled: isPending,
    });

  const lastRejection = fileRejections[0];

  return (
    <div className="space-y-2">
      <div
        {...getRootProps()}
        className={cn(
          "flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed p-8 text-center transition-colors",
          isDragActive && "border-primary bg-primary/5",
          isPending && "pointer-events-none opacity-50",
          !isDragActive && !isPending && "hover:border-primary/50",
        )}
      >
        <input {...getInputProps()} aria-label="Upload document file" />
        <Upload className="h-8 w-8 text-muted-foreground" />
        <div>
          <p className="text-sm font-medium">
            {isDragActive ? "Drop file here" : "Drag & drop a file, or click to browse"}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            PDF, TXT, MD, or DOCX up to 50 MB
          </p>
        </div>
      </div>

      {isPending && <UploadProgressBar progress={progress} />}

      {lastRejection && (
        <p className="text-sm text-destructive">
          {lastRejection.errors.map((e) => e.message).join(". ")}
        </p>
      )}
    </div>
  );
}
