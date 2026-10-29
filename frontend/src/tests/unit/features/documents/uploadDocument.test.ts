import { describe, it, expect, vi } from "vitest";
import { apiClient } from "@/shared/api/client";

vi.mock("@/shared/api/client", () => ({
  apiClient: {
    post: vi.fn(),
  },
}));

// Import after mock
const { uploadDocument } = await import(
  "@/features/documents/api/uploadDocument"
);

describe("uploadDocument", () => {
  it("uploads a file and returns response", async () => {
    const mockResponse = {
      data: {
        document: {
          id: "doc-003",
          filename: "new-doc.pdf",
          content_hash: "abc123",
          file_size: 1024,
          mime_type: "application/pdf",
          version: 1,
          is_active_version: true,
          status: "processing",
          chunk_count_expected: null,
          chunk_count_actual: null,
          page_count: null,
          error_message: null,
          created_at: "2024-01-01T00:00:00Z",
          updated_at: "2024-01-01T00:00:00Z",
        },
        is_new: true,
        message: "Document registered and ingestion enqueued",
      },
    };

    vi.mocked(apiClient.post).mockResolvedValueOnce(mockResponse);

    const file = new File(["test content"], "test.pdf", {
      type: "application/pdf",
    });

    const result = await uploadDocument({ file });

    expect(result.document.id).toBe("doc-003");
    expect(result.document.filename).toBe("new-doc.pdf");
    expect(result.document.status).toBe("processing");
    expect(result.is_new).toBe(true);

    // Verify FormData was used
    const call = vi.mocked(apiClient.post).mock.calls[0];
    expect(call?.[0]).toBe("/api/v1/admin/documents/upload");
    expect(call?.[1]).toBeInstanceOf(FormData);
  });

  it("passes onProgress callback in config", async () => {
    const mockResponse = {
      data: {
        document: {
          id: "doc-004",
          filename: "test.pdf",
          content_hash: "def456",
          file_size: 512,
          mime_type: "application/pdf",
          version: 1,
          is_active_version: true,
          status: "processing",
          chunk_count_expected: null,
          chunk_count_actual: null,
          page_count: null,
          error_message: null,
          created_at: "2024-01-01T00:00:00Z",
          updated_at: "2024-01-01T00:00:00Z",
        },
        is_new: true,
        message: "Document registered and ingestion enqueued",
      },
    };

    vi.mocked(apiClient.post).mockResolvedValueOnce(mockResponse);

    const file = new File(["test"], "test.pdf", {
      type: "application/pdf",
    });
    const onProgress = vi.fn();

    await uploadDocument({ file, onProgress });

    const call = vi.mocked(apiClient.post).mock.calls[0];
    const config = call?.[2] as Record<string, unknown> | undefined;
    expect(config?.onUploadProgress).toBeDefined();
  });
});
