import { useMutation } from "@tanstack/react-query";
import { submitFeedback } from "../api/submitFeedback";
import type { FeedbackRequest, FeedbackResponse } from "../types/chat.types";

export function useSubmitFeedback() {
  return useMutation<FeedbackResponse, Error, FeedbackRequest>({
    mutationFn: submitFeedback,
  });
}
