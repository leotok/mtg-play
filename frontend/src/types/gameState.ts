export type TurnPhase = 
  | 'untap' 
  | 'upkeep' 
  | 'draw' 
  | 'main1' 
  | 'combat_start' 
  | 'combat_attack' 
  | 'combat_block' 
  | 'combat_damage' 
  | 'combat_end' 
  | 'main2' 
  | 'end' 
  | 'cleanup';

export type CardZone = 
  | 'library' 
  | 'hand' 
  | 'battlefield' 
  | 'graveyard' 
  | 'exile' 
  | 'commander';

export interface GameCardImageUris {
  small?: string;
  normal?: string;
  large?: string;
  art_crop?: string;
  border_crop?: string;
}

export interface GameCardFace {
  name?: string;
  mana_cost?: string;
  type_line?: string;
  oracle_text?: string;
  power?: string;
  toughness?: string;
  image_uris?: GameCardImageUris;
}

export interface GameCard {
  id: number;
  card_scryfall_id: string;
  card_name: string;
  mana_cost?: string;
  cmc?: number;
  type_line?: string;
  oracle_text?: string;
  colors?: string[];
  power?: string;
  toughness?: string;
  keywords?: string[];
  image_uris?: GameCardImageUris;
  card_faces?: GameCardFace[];
  zone: CardZone;
  position: number;
  is_tapped: boolean;
  is_face_up: boolean;
  battlefield_x?: number;
  battlefield_y?: number;
  is_attacking: boolean;
  is_blocking: boolean;
  damage_received: number;
}

export interface GameCardInBattlefield extends Omit<GameCard, 'zone' | 'position' | 'damage_received'> {
  battlefield_x?: number;
  battlefield_y?: number;
}

export interface PlayerGameState {
  id: number;
  user_id: number;
  username: string;
  player_order: number;
  is_active: boolean;
  life_total: number;
  poison_counters: number;
  library: GameCard[];
  hand: GameCard[];
  battlefield: GameCardInBattlefield[];
  graveyard: GameCard[];
  exile: GameCard[];
  commander: GameCard[];
}

export interface GameState {
  id: number;
  game_room_id: number;
  current_turn: number;
  active_player_id: number;
  active_player_username: string;
  current_phase: TurnPhase;
  starting_player_id: number;
  players: PlayerGameState[];
  created_at: string;
}

export const TURN_PHASE_LABELS: Record<TurnPhase, string> = {
  untap: 'Untap',
  upkeep: 'Upkeep',
  draw: 'Draw',
  main1: 'Main Phase',
  combat_start: 'Combat Start',
  combat_attack: 'Attack',
  combat_block: 'Block',
  combat_damage: 'Combat Damage',
  combat_end: 'Combat End',
  main2: 'Main Phase 2',
  end: 'End',
  cleanup: 'Cleanup',
};
