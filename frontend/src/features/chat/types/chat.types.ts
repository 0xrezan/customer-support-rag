export interface Citation {
  document_name: string;
  page: number;
  chunk_id: string;
}

export interface AskRequest {
  question: string;
  source?: string;
  user_id?: string;
  bypass_cache?: boolean;
}

export interface AskResponse {
  status: string;
  answer: string;
  citations: Citation[];
  latency_ms: number;
}

export type FeedbackRating = "up" | "down";

export interface FeedbackRequest {
  answer_id: string;
  rating: "thumbs_up" | "thumbs_down";
  comment?: string;
  user_id?: string;
}

export interface FeedbackResponse {
  id: string;
  answer_id: string;
  rating: string;
}

export type MessageRole = "user" | "bot";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  citations?: Citation[];
  latencyMs?: number;
  answerId?: string;
  feedbackRating?: FeedbackRating | null;
  isLoading?: boolean;
  isError?: boolean;
  /** Original question text, stored for retry on failure. */
  failedQuestion?: string;
}
