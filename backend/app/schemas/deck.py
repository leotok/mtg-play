from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from app.schemas.deck_card import DeckCardResponse


class DeckBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Deck name")
    description: Optional[str] = Field(None, max_length=500, description="Deck description")
    commander_scryfall_id: str = Field(..., description="Scryfall ID of the commander card")
    is_public: bool = Field(False, description="Whether deck is public")


class DeckCreate(DeckBase):
    pass


class DeckUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    commander_scryfall_id: Optional[str] = None
    is_public: Optional[bool] = None


class CardBasic(BaseModel):
    scryfall_id: str
    name: str
    mana_cost: Optional[str]
    cmc: Optional[int]
    type_line: str
    colors: Optional[List[str]]
    color_identity: Optional[List[str]]
    
    class Config:
        from_attributes = True


class DeckResponse(DeckBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    cards: List[DeckCardResponse] = []
    commander: Optional[CardBasic] = None
    
    class Config:
        from_attributes = True


class DeckList(BaseModel):
    id: int
    name: str
    description: Optional[str]
    commander_scryfall_id: str
    is_public: bool
    created_at: datetime
    commander: Optional[CardBasic] = None
    commander_image_uris: Optional[dict] = None
    color_identity: Optional[List[str]] = None
    
    class Config:
        from_attributes = True


class DeckStats(BaseModel):
    deck_id: int
    total_cards: int
    commander_count: int
    main_deck_count: int
    is_valid: bool
    validation_errors: List[str] = []
    deck_name: Optional[str] = None
    unique_cards: Optional[int] = None
    is_complete: Optional[bool] = None
