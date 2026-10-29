import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import chatFixtures from "../fixtures/api/chat.json";
import documentsFixtures from "../fixtures/api/documents.json";

const API_ORIGINS = ["http://localhost:8000", "http://localhost:18000"] as const;

export const handlers = API_ORIGINS.flatMap((origin) => [
  http.post(`${origin}/api/v1/chat/ask`, () => {
    return HttpResponse.json(chatFixtures.askResponse);
  }),

  http.post(`${origin}/api/v1/feedback/submit`, () => {
    return HttpResponse.json(chatFixtures.feedbackResponse);
  }),

  http.get(`${origin}/api/v1/admin/documents`, () => {
    return HttpResponse.json(documentsFixtures.documentsList);
  }),

  http.post(`${origin}/api/v1/admin/documents/upload`, () => {
    return HttpResponse.json(documentsFixtures.uploadResponse);
  }),

  http.delete(`${origin}/api/v1/admin/documents/:docId`, () => {
    return HttpResponse.json(documentsFixtures.deleteResponse);
  }),

  http.post(`${origin}/api/v1/admin/documents/:docId/reindex`, () => {
      return HttpResponse.json(documentsFixtures.reindexResponse);
  }),

  http.get(`${origin}/api/v1/health/live`, () => {
    return HttpResponse.json({ status: "ok" });
  }),
]);

export const server = setupServer(...handlers);
