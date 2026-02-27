import { create } from 'zustand';
import { apiClient } from '../services/apiClient';
import type { GameState } from '../types/gameState';

interface GameStateStore {
  gameState: GameState | null;
  isLoading: boolean;
  error: string | null;
  gameId: number | null;
  
  fetchGameState: (gameId: number) => Promise<void>;
  drawCard: (gameId: number) => Promise<void>;
  untapAll: (gameId: number) => Promise<void>;
  playCard: (gameId: number, cardId: number, battlefieldX?: number, battlefieldY?: number) => Promise<void>;
  tapCard: (gameId: number, cardId: number) => Promise<void>;
  updateBattlefieldPosition: (gameId: number, cardId: number, x: number, y: number) => Promise<void>;
  moveCard: (gameId: number, cardId: number, targetZone: string, position: number) => Promise<void>;
  passPriority: (gameId: number) => Promise<void>;
  adjustLife: (gameId: number, amount: number) => Promise<void>;
  setGameState: (state: GameState) => void;
  clearGameState: () => void;
}

export const useGameStateStore = create<GameStateStore>((set) => ({
  gameState: null,
  isLoading: false,
  error: null,
  gameId: null,

  fetchGameState: async (gameId: number) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.get<GameState>(`/games/${gameId}/state`);
      set({ gameState: response, isLoading: false, gameId });
    } catch (err: any) {
      console.error('Failed to fetch game state:', err);
      console.error('Error response:', err.response?.data);
      set({ 
        error: err.response?.data?.detail || 'Failed to fetch game state', 
        isLoading: false 
      });
    }
  },

  drawCard: async (gameId: number) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.post<GameState>(`/games/${gameId}/draw`);
      set({ gameState: response, isLoading: false });
    } catch (err: any) {
      set({ 
        error: err.response?.data?.detail || 'Failed to draw card', 
        isLoading: false 
      });
    }
  },

  untapAll: async (gameId: number) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.post<GameState>(`/games/${gameId}/untap-all`);
      set({ gameState: response, isLoading: false });
    } catch (err: any) {
      set({ 
        error: err.response?.data?.detail || 'Failed to untap cards', 
        isLoading: false 
      });
    }
  },

  playCard: async (gameId: number, cardId: number, battlefieldX?: number, battlefieldY?: number) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.post<GameState>(`/games/${gameId}/play-card`, {
        card_id: cardId,
        target_zone: 'battlefield',
        position: 0,
        battlefield_x: battlefieldX ?? null,
        battlefield_y: battlefieldY ?? null,
      });
      set({ gameState: response, isLoading: false });
    } catch (err: any) {
      set({ 
        error: err.response?.data?.detail || 'Failed to play card', 
        isLoading: false 
      });
    }
  },

  tapCard: async (gameId: number, cardId: number) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.post<GameState>(`/games/${gameId}/tap/${cardId}`);
      set({ gameState: response, isLoading: false });
    } catch (err: any) {
      set({ 
        error: err.response?.data?.detail || 'Failed to tap card', 
        isLoading: false 
      });
    }
  },

  updateBattlefieldPosition: async (gameId: number, cardId: number, x: number, y: number) => {
    try {
      const response = await apiClient.post<GameState>(`/games/${gameId}/battlefield-position`, {
        card_id: cardId,
        x,
        y,
      });
      set({ gameState: response });
    } catch (err: any) {
      console.error('Failed to update card position:', err);
    }
  },

  moveCard: async (gameId: number, cardId: number, targetZone: string, position: number) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.post<GameState>(`/games/${gameId}/move-card`, {
        card_id: cardId,
        target_zone: targetZone,
        position,
      });
      set({ gameState: response, isLoading: false });
    } catch (err: any) {
      set({ 
        error: err.response?.data?.detail || 'Failed to move card', 
        isLoading: false 
      });
    }
  },

  passPriority: async (gameId: number) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.post<GameState>(`/games/${gameId}/pass-priority`);
      set({ gameState: response, isLoading: false });
    } catch (err: any) {
      set({ 
        error: err.response?.data?.detail || 'Failed to pass priority', 
        isLoading: false 
      });
    }
  },

  adjustLife: async (gameId: number, amount: number) => {
    try {
      const response = await apiClient.post<GameState>(`/games/${gameId}/adjust-life`, { amount });
      set({ gameState: response });
    } catch (err: any) {
      set({ 
        error: err.response?.data?.detail || 'Failed to adjust life'
      });
    }
  },

  setGameState: (state: GameState) => {
    set({ gameState: state });
  },

  clearGameState: () => {
    set({ gameState: null, gameId: null, error: null });
  },
}));
