/**
 * In-memory admin token store.
 * Token is intentionally NOT persisted — a page reload clears it.
 */
let token: string | null = null;

const listeners = new Set<() => void>();

export function getToken(): string | null {
  return token;
}

export function setToken(newToken: string | null): void {
  token = newToken;
  listeners.forEach((fn) => fn());
}

export function clearToken(): void {
  setToken(null);
}

export function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}
