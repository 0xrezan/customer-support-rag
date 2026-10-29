/** Maximum file size for document uploads (50 MB). */
export const MAX_UPLOAD_SIZE_BYTES = 50 * 1024 * 1024;

/** Accepted MIME types for document uploads. */
export const ACCEPTED_FILE_TYPES: Record<string, string[]> = {
  "application/pdf": [".pdf"],
  "text/plain": [".txt"],
  "text/markdown": [".md"],
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [
    ".docx",
  ],
};

/** Documents polling interval in ms (30 seconds). */
export const DOCUMENTS_POLL_INTERVAL = 30_000;

/** Health polling interval in ms (60 seconds). */
export const HEALTH_POLL_INTERVAL = 60_000;
