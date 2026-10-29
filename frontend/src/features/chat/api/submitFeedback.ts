import { apiClient } from "@/shared/api/client";
import type { FeedbackRequest, FeedbackResponse } from "../types/chat.types";

export async function submitFeedback(
  data: FeedbackRequest,
): Promise<FeedbackResponse> {
  const response = await apiClient.post<FeedbackResponse>(
    "/api/v1/feedback/submit",
    data,
  );
  return response.data;
}
