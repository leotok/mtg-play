import React, { createContext, useContext, useReducer, useEffect } from 'react';
import type { ReactNode } from 'react';
import type { User, UserCreate, AuthState, AuthContextType } from '../types/auth';
import { apiClient } from '../services/apiClient';

// Auth action types
type AuthAction =
  | { type: 'AUTH_START' }
  | { type: 'AUTH_SUCCESS'; payload: { user: User; accessToken: string; refreshToken: string } }
  | { type: 'AUTH_FAILURE'; payload: string }
  | { type: 'LOGOUT' }
  | { type: 'CLEAR_ERROR' }
  | { type: 'SET_USER'; payload: User };

// Initial state
const initialState: AuthState = {
  user: null,
  accessToken: localStorage.getItem('access_token'),
  refreshToken: localStorage.getItem('refresh_token'),
  isAuthenticated: false,
  isLoading: true,
  error: null,
};

// Auth reducer
const authReducer = (state: AuthState, action: AuthAction): AuthState => {
  switch (action.type) {
    case 'AUTH_START':
      return {
        ...state,
        isLoading: true,
        error: null,
      };
    case 'AUTH_SUCCESS':
      return {
        ...state,
        user: action.payload.user,
        accessToken: action.payload.accessToken,
        refreshToken: action.payload.refreshToken,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      };
    case 'AUTH_FAILURE':
      return {
        ...state,
        user: null,
        accessToken: null,
        refreshToken: null,
        isAuthenticated: false,
        isLoading: false,
        error: action.payload,
      };
    case 'LOGOUT':
      return {
        ...state,
        user: null,
        accessToken: null,
        refreshToken: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      };
    case 'CLEAR_ERROR':
      return {
        ...state,
        error: null,
      };
    case 'SET_USER':
      return {
        ...state,
        user: action.payload,
        isAuthenticated: true,
        isLoading: false,
      };
    default:
      return state;
  }
};

// Create context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Auth provider component
export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Check authentication on mount
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          const user = await apiClient.getCurrentUser();
          dispatch({ type: 'SET_USER', payload: user });
        } catch (error) {
          // Token is invalid, clear it
          dispatch({ type: 'LOGOUT' });
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
        }
      } else {
        dispatch({ type: 'AUTH_SUCCESS', payload: { 
          user: null as any, 
          accessToken: '', 
          refreshToken: '' 
        }});
      }
    };

    checkAuth();
  }, []);

  // Login method
  const login = async (email: string, password: string): Promise<void> => {
    console.log('AuthContext: Starting login...');
    dispatch({ type: 'AUTH_START' });
    try {
      console.log('AuthContext: Calling API login...');
      const tokens = await apiClient.login(email, password);
      console.log('AuthContext: Got tokens, fetching user...');
      const user = await apiClient.getCurrentUser();
      console.log('AuthContext: Got user, dispatching success');
      dispatch({ 
        type: 'AUTH_SUCCESS', 
        payload: { 
          user, 
          accessToken: tokens.access_token, 
          refreshToken: tokens.refresh_token 
        } 
      });
      console.log('AuthContext: Login complete');
    } catch (error: any) {
      console.error('AuthContext: Login failed:', error);
      const errorMessage = error.response?.data?.detail || 'Login failed';
      dispatch({ type: 'AUTH_FAILURE', payload: errorMessage });
      throw error;
    }
  };

  // Register method
  const register = async (userData: UserCreate): Promise<void> => {
    dispatch({ type: 'AUTH_START' });
    try {
      await apiClient.register(userData);
      // Auto-login after successful registration
      await login(userData.email, userData.password);
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Registration failed';
      dispatch({ type: 'AUTH_FAILURE', payload: errorMessage });
      throw error;
    }
  };

  // Logout method
  const logout = async (): Promise<void> => {
    try {
      await apiClient.logout();
    } catch (error) {
      // Continue with logout even if API call fails
    } finally {
      dispatch({ type: 'LOGOUT' });
    }
  };

  // Refresh token method
  const refreshAccessToken = async (): Promise<void> => {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }
      // The API client handles token refresh automatically
    } catch (error) {
      dispatch({ type: 'LOGOUT' });
      throw error;
    }
  };

  // Clear error method
  const clearError = (): void => {
    dispatch({ type: 'CLEAR_ERROR' });
  };

  const value: AuthContextType = {
    ...state,
    login,
    register,
    logout,
    refreshAccessToken,
    clearError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Hook to use auth context
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
