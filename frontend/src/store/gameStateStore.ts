import { create } from 'zustand';
import { apiClient } from '../services/apiClient';
import type { GameState, GameLog, ChooseCardSideResponse, ValidPlaysResponse } from '../types/gameState';

type HoveredCard = GameState['players'][0]['hand'][0] | null;

interface GameStateStore {
  gameState: GameState | null;
  gameLogs: GameLog[];
  isLoading: boolean;
  error: string | null;
  gameId: number | null;
  toast: { message: string; isVisible: boolean };
  hoveredCard: HoveredCard;
  sideSelection: ChooseCardSideResponse | null;
  validPlays: ValidPlaysResponse | null;
  
  fetchGameState: (gameId: number) => Promise<void>;
  fetchGameLogs: (gameId: number) => Promise<void>;
  fetchValidPlays: (gameId: number) => Promise<void>;
  drawCard: (gameId: number) => Promise<void>;
  untapAll: (gameId: number) => Promise<void>;
  playCard: (gameId: number, cardId: number, battlefieldX?: number, battlefieldY?: number, sideIndex?: number) => Promise<void>;
  tapCard: (gameId: number, cardId: number) => Promise<void>;
  tapLandForMana: (gameId: number, cardId: number, color?: string) => Promise<void>;
  getLandColors: (gameId: number, cardId: number) => Promise<string[]>;
  updateBattlefieldPosition: (gameId: number, cardId: number, x: number, y: number) => Promise<void>;
  moveCard: (gameId: number, cardId: number, targetZone: string, position: number) => Promise<void>;
  moveCards: (gameId: number, cards: { card_id: number; target_zone: string; position: number }[]) => Promise<void>;
  passPriority: (gameId: number) => Promise<void>;
  adjustLife: (gameId: number, amount: number) => Promise<void>;
  setGameState: (state: GameState) => void;
  clearGameState: () => void;
  showToast: (message: string) => void;
  hideToast: () => void;
  setHoveredCard: (card: HoveredCard) => void;
  clearSideSelection: () => void;
}

export const useGameStateStore = create<GameStateStore>((set) => ({
  gameState: null,
  gameLogs: [],
  isLoading: false,
  error: null,
  gameId: null,
  toast: { message: '', isVisible: false },
  hoveredCard: null,
  sideSelection: null,
  validPlays: null,

  showToast: (message: string) => set({ toast: { message, isVisible: true } }),
  hideToast: () => set({ toast: { message: '', isVisible: false } }),
  setHoveredCard: (card) => set({ hoveredCard: card }),
  clearSideSelection: () => set({ sideSelection: null }),

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

  fetchGameLogs: async (gameId: number) => {
    try {
      const response = await apiClient.get<GameLog[]>(`/games/${gameId}/logs`);
      set({ gameLogs: response });
    } catch (err: any) {
      console.error('Failed to fetch game logs:', err);
    }
  },

  fetchValidPlays: async (gameId: number) => {
    try {
      const response = await apiClient.get<ValidPlaysResponse>(`/games/${gameId}/valid-plays`);
      set({ validPlays: response });
    } catch (err: any) {
      console.error('Failed to fetch valid plays:', err);
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

  playCard: async (gameId: number, cardId: number, battlefieldX?: number, battlefieldY?: number, sideIndex?: number) => {
    set({ isLoading: true, error: null, hoveredCard: null });
    try {
      const response = await apiClient.post<GameState | ChooseCardSideResponse>(`/games/${gameId}/play-card`, {
        card_id: cardId,
        target_zone: 'battlefield',
        position: 0,
        battlefield_x: battlefieldX ?? null,
        battlefield_y: battlefieldY ?? null,
        side_index: sideIndex ?? null,
      });
      
      if ('requires_side_selection' in response && response.requires_side_selection) {
        set({ sideSelection: response as ChooseCardSideResponse, isLoading: false });
      } else {
        set({ gameState: response as GameState, isLoading: false, hoveredCard: null });
      }
    } catch (err: any) {
      const errorData = err.response?.data?.detail;
      if (errorData) {
        const message = typeof errorData === 'string' ? errorData : errorData.message;
        set({ toast: { message, isVisible: true }, isLoading: false, hoveredCard: null });
      } else {
        set({ toast: { message: 'Failed to play card', isVisible: true }, isLoading: false, hoveredCard: null });
      }
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

  tapLandForMana: async (gameId: number, cardId: number, color?: string) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.post<GameState>(`/games/${gameId}/tap-land/${cardId}`, {
        color: color ?? null,
      });
      set({ gameState: response, isLoading: false });
    } catch (err: any) {
      set({ 
        error: err.response?.data?.detail || 'Failed to tap land for mana', 
        isLoading: false 
      });
    }
  },

  getLandColors: async (gameId: number, cardId: number): Promise<string[]> => {
    try {
      const response = await apiClient.get<string[]>(`/games/${gameId}/lands/${cardId}/colors`);
      return response;
    } catch (err: any) {
      console.error('Failed to get land colors:', err);
      return ['colorless'];
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

  moveCards: async (gameId: number, cards: { card_id: number; target_zone: string; position: number }[]) => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.post<GameState>(`/games/${gameId}/move-cards`, { cards });
      set({ gameState: response, isLoading: false });
    } catch (err: any) {
      set({ 
        error: err.response?.data?.detail || 'Failed to move cards', 
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
    set({ gameState: null, gameId: null, error: null, sideSelection: null, validPlays: null });
  },
}));
