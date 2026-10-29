export interface AuthState {
  token: string | null;
  isAuthenticated: boolean;
}

export interface AuthActions {
  login: (token: string) => void;
  logout: () => void;
}

export type AuthContextValue = AuthState & AuthActions;
