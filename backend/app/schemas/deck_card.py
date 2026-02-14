from pydantic import BaseModel, Field
from typing import Optional, List


class DeckCardBase(BaseModel):
    card_scryfall_id: str = Field(..., description="Scryfall ID of the card to add")
    quantity: int = Field(1, ge=1, description="Quantity of cards (1-N)")
    is_commander: bool = Field(False, description="Whether this is the commander")


class DeckCardCreate(DeckCardBase):
    deck_id: int = Field(..., description="ID of the deck")


class DeckCardUpdate(BaseModel):
    quantity: Optional[int] = Field(None, ge=1, le=4)
    is_commander: Optional[bool] = None


class DeckCardFace(BaseModel):
    name: Optional[str] = None
    mana_cost: Optional[str] = None
    type_line: Optional[str] = None
    oracle_text: Optional[str] = None
    power: Optional[str] = None
    toughness: Optional[str] = None
    image_uris: Optional[dict] = None


class DeckCardResponse(BaseModel):
    id: int
    card_scryfall_id: str
    quantity: int
    is_commander: bool
    card_name: Optional[str] = None
    name: Optional[str] = None
    mana_cost: Optional[str] = None
    cmc: Optional[float] = None
    type_line: Optional[str] = None
    colors: Optional[list] = None
    color_identity: Optional[list] = None
    rarity: Optional[str] = None
    set: Optional[str] = None
    power: Optional[str] = None
    toughness: Optional[str] = None
    keywords: Optional[list] = None
    oracle_text: Optional[str] = None
    image_uris: Optional[dict] = None
    card_faces: Optional[List[DeckCardFace]] = None
    
    class Config:
        from_attributes = True
