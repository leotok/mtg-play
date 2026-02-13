import axios from 'axios';
import type { AxiosInstance, AxiosError } from 'axios';
import type { Token, ApiError } from '../types/auth';

const API_BASE_URL = 'http://localhost:8000/api/v1';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor - add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor - handle token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError<ApiError>) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && originalRequest) {
          try {
            await this.refreshToken();
            const token = localStorage.getItem('access_token');
            if (token && originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return this.client(originalRequest);
          } catch (refreshError) {
            // Refresh failed, logout user
            this.clearTokens();
            window.location.href = '/login';
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  private async refreshToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await axios.post<Token>(`${API_BASE_URL}/refresh`, {
      refresh_token: refreshToken,
    });

    this.setTokens(response.data);
  }

  private setTokens(tokens: Token) {
    localStorage.setItem('access_token', tokens.access_token);
    localStorage.setItem('refresh_token', tokens.refresh_token);
    localStorage.setItem('token_expires', new Date(Date.now() + tokens.expires_in * 1000).toISOString());
  }

  private clearTokens() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('token_expires');
  }

  // Public methods
  public async login(email: string, password: string): Promise<Token> {
    console.log('ApiClient: Making login request to /login');
    const response = await this.client.post<Token>('/login', {
      email,
      password,
    });
    console.log('ApiClient: Login response received');
    this.setTokens(response.data);
    return response.data;
  }

  public async register(userData: {
    email: string;
    username: string;
    password: string;
    confirm_password: string;
  }): Promise<any> {
    const response = await this.client.post('/register', userData);
    return response.data;
  }

  public async logout(): Promise<void> {
    try {
      await this.client.post('/logout');
    } finally {
      this.clearTokens();
    }
  }

  public async getCurrentUser(): Promise<any> {
    const response = await this.client.get('/me');
    return response.data;
  }

  // Generic request methods
  public get<T = any>(url: string, params?: any): Promise<T> {
    return this.client.get(url, { params }).then(res => res.data);
  }

  public post<T = any>(url: string, data?: any): Promise<T> {
    return this.client.post(url, data).then(res => res.data);
  }

  public put<T = any>(url: string, data?: any): Promise<T> {
    return this.client.put(url, data).then(res => res.data);
  }

  public delete<T = any>(url: string): Promise<T> {
    return this.client.delete(url).then(res => res.data);
  }
}

export const apiClient = new ApiClient();
