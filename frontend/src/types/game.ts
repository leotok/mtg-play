export type PowerBracket = 'precon' | 'casual' | 'optimized' | 'cedh';

export type GameMode = 'rules_enforced' | 'manual';

export type GameStatus = 'waiting' | 'in_progress' | 'completed';

export type PlayerStatus = 'pending' | 'accepted' | 'rejected';

export interface DeckInfo {
  id: number;
  name: string;
  commander_name?: string;
  commander_image_uris?: {
    small?: string;
    normal?: string;
    large?: string;
    art_crop?: string;
    border_crop?: string;
  };
}

export interface GameRoomPlayer {
  id: number;
  user_id: number;
  username: string;
  status: PlayerStatus;
  is_host: boolean;
  deck_id?: number;
  deck?: DeckInfo;
  joined_at: string;
}

export interface GameRoom {
  id: number;
  name: string;
  description?: string;
  host_id: number;
  host_username: string;
  invite_code: string;
  is_public: boolean;
  max_players: number;
  power_bracket: PowerBracket;
  game_mode: GameMode;
  status: GameStatus;
  players: GameRoomPlayer[];
  created_at: string;
}

export interface GameRoomListItem {
  id: number;
  name: string;
  description?: string;
  host_username: string;
  is_public: boolean;
  max_players: number;
  current_players: number;
  power_bracket: PowerBracket;
  game_mode: GameMode;
  status: GameStatus;
  created_at: string;
  is_in_game: boolean;
  is_host: boolean;
}

export interface GameRoomCreate {
  name: string;
  description?: string;
  is_public: boolean;
  max_players: number;
  power_bracket: PowerBracket;
  game_mode: GameMode;
}

export const POWER_BRACKET_LABELS: Record<PowerBracket, string> = {
  precon: 'Precon',
  casual: 'Casual',
  optimized: 'Optimized',
  cedh: 'cEDH',
};

export const POWER_BRACKET_COLORS: Record<PowerBracket, string> = {
  precon: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  casual: 'bg-green-500/20 text-green-400 border-green-500/30',
  optimized: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  cedh: 'bg-red-500/20 text-red-400 border-red-500/30',
};

export const GAME_MODE_LABELS: Record<GameMode, string> = {
  rules_enforced: 'Rules Enforced',
  manual: 'Manual Mode',
};

export const GAME_MODE_COLORS: Record<GameMode, string> = {
  rules_enforced: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  manual: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
};
