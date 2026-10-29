import { z } from "zod/v4";

export const citationSchema = z.object({
  document_name: z.string(),
  page: z.number(),
  chunk_id: z.string(),
});

export const askRequestSchema = z.object({
  question: z.string().min(1).max(2000),
  source: z.string().optional(),
  user_id: z.string().optional(),
  bypass_cache: z.boolean().optional(),
});

export const askResponseSchema = z.object({
  status: z.string(),
  answer: z.string(),
  citations: z.array(citationSchema),
  latency_ms: z.number(),
});

export const feedbackRequestSchema = z.object({
  answer_id: z.string(),
  rating: z.enum(["thumbs_up", "thumbs_down"]),
  comment: z.string().optional(),
  user_id: z.string().optional(),
});

export const feedbackResponseSchema = z.object({
  id: z.string(),
  answer_id: z.string(),
  rating: z.string(),
});
