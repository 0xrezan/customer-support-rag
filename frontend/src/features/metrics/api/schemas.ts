import { z } from "zod/v4";

export const metricsResponseSchema = z.object({
  total_questions: z.number(),
  avg_latency_ms: z.number(),
  positive_feedback: z.number(),
  negative_feedback: z.number(),
});

export type MetricsResponse = z.infer<typeof metricsResponseSchema>;
