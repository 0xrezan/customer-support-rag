import { apiClient } from "@/shared/api/client";
import type { AskRequest, AskResponse } from "../types/chat.types";

export async function askQuestion(data: AskRequest): Promise<AskResponse> {
  const response = await apiClient.post<AskResponse>(
    "/api/v1/chat/ask",
    data,
  );
  return response.data;
}
