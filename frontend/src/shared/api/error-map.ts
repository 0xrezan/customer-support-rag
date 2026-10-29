import { AxiosError } from "axios";

export interface AppError {
  message: string;
  status: number | null;
}

/**
 * Maps an Axios error (or unknown error) to a user-safe AppError.
 */
export function mapApiError(error: unknown): AppError {
  if (error instanceof AxiosError) {
    const status = error.response?.status ?? null;

    if (status === 401) {
      return { message: "Invalid or expired admin token.", status };
    }
    if (status === 403) {
      return { message: "You do not have permission for this action.", status };
    }
    if (status === 404) {
      return { message: "The requested resource was not found.", status };
    }
    if (status === 413) {
      return { message: "The file is too large to upload.", status };
    }
    if (status === 422) {
      return { message: "The request data is invalid.", status };
    }
    if (status !== null && status >= 500) {
      return {
        message: "A server error occurred. Please try again later.",
        status,
      };
    }
    if (error.code === "ECONNABORTED") {
      return { message: "The request timed out. Please try again.", status };
    }
    if (!error.response) {
      return {
        message: "Network error. Check your connection and try again.",
        status: null,
      };
    }

    return {
      message: "An unexpected error occurred.",
      status,
    };
  }

  return {
    message: "An unexpected error occurred.",
    status: null,
  };
}
