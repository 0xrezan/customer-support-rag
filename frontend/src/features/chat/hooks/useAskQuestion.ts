import { useMutation } from "@tanstack/react-query";
import { askQuestion } from "../api/askQuestion";
import type { AskRequest, AskResponse } from "../types/chat.types";

export function useAskQuestion() {
  return useMutation<AskResponse, Error, AskRequest>({
    mutationFn: askQuestion,
  });
}
