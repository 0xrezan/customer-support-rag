import { z } from "zod/v4";

export const documentItemSchema = z.object({
  id: z.string(),
  filename: z.string(),
  content_hash: z.string(),
  file_size: z.number(),
  mime_type: z.string(),
  version: z.number(),
  is_active_version: z.boolean(),
  status: z.string(),
  chunk_count_expected: z.number().nullable(),
  chunk_count_actual: z.number().nullable(),
  page_count: z.number().nullable(),
  error_message: z.string().nullable(),
  created_at: z.string().nullable(),
  updated_at: z.string().nullable(),
});

export const documentsListSchema = z.object({
  documents: z.array(documentItemSchema),
  total: z.number(),
});

export const uploadResponseSchema = z.object({
  document: documentItemSchema,
  is_new: z.boolean(),
  message: z.string(),
});

export const deleteResponseSchema = z.object({
  message: z.string(),
  document_id: z.string(),
});

export const reindexResponseSchema = z.object({
  message: z.string(),
  document_id: z.string(),
});
