export interface DocumentItem {
  id: string;
  filename: string;
  content_hash: string;
  file_size: number;
  mime_type: string;
  version: number;
  is_active_version: boolean;
  status: string;
  chunk_count_expected: number | null;
  chunk_count_actual: number | null;
  page_count: number | null;
  error_message: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface DocumentListEnvelope {
  documents: DocumentItem[];
  total: number;
}

export interface DocumentUploadResponse {
  document: DocumentItem;
  is_new: boolean;
  message: string;
}

export interface DeleteResponse {
  message: string;
  document_id: string;
}

export interface ReindexResponse {
  message: string;
  document_id: string;
}
