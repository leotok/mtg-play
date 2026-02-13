// Authentication types
export interface User {
  id: number;
  email: string;
  username: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_login: string;
  email_verified: boolean;
}

export interface UserCreate {
  email: string;
  username: string;
  password: string;
  confirm_password: string;
  is_active?: boolean;
}

export interface UserLogin {
  email: string;
  password: string;
}

export interface Token {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface TokenRefresh {
  refresh_token: string;
}

export interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export interface AuthContextType {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (userData: UserCreate) => Promise<void>;
  logout: () => void;
  refreshAccessToken: () => Promise<void>;
  clearError: () => void;
}

// API Response types
export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface ApiError {
  detail: string;
  status?: number;
}
