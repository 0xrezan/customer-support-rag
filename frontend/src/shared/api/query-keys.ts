export const queryKeys = {
  health: ["health"] as const,
  documents: {
    all: ["documents"] as const,
    list: () => [...queryKeys.documents.all, "list"] as const,
  },
  metrics: {
    all: ["metrics"] as const,
  },
} as const;
