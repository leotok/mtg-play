// Deck types
export interface Deck {
  id: number;
  name: string;
  description?: string;
  commander_name?: string;
  commander_scryfall_id?: string;
  commander_image_uris?: {
    small?: string;
    normal?: string;
    large?: string;
    art_crop?: string;
    border_crop?: string;
  };
  owner_id: number;
  is_public: boolean;
  created_at: string;
  updated_at: string;
  total_cards?: number;
  color_identity?: string[];
}

export interface DeckCard {
  id: number;
  deck_id: number;
  card_scryfall_id: string;
  quantity: number;
  is_commander: boolean;
  card_name?: string;
  mana_cost?: string;
  cmc?: number;
  type_line?: string;
  colors?: string[];
  color_identity?: string[];
  rarity?: string;
  set?: string;
  power?: string;
  toughness?: string;
  keywords?: string[];
  oracle_text?: string;
  image_uris?: {
    small?: string;
    normal?: string;
  };
  card_faces?: DeckCardFace[];
}

export interface DeckCardFace {
  name?: string;
  mana_cost?: string;
  type_line?: string;
  oracle_text?: string;
  power?: string;
  toughness?: string;
  image_uris?: {
    small?: string;
    normal?: string;
  };
}

export interface DeckDetail extends Deck {
  cards: DeckCard[];
  commander?: {
    scryfall_id: string;
    name: string;
    mana_cost?: string;
    type_line?: string;
    colors?: string[];
    color_identity?: string[];
    image_uris?: {
      small?: string;
      normal?: string;
    };
  };
}

export interface DeckCreate {
  name: string;
  description?: string;
  commander_scryfall_id: string;
  is_public?: boolean;
}

export interface DeckUpdate {
  name?: string;
  description?: string;
  commander_scryfall_id?: string;
  is_public?: boolean;
}

export interface DeckListResponse {
  items: Deck[];
  total: number;
  page: number;
  per_page: number;
}
