from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


class CardBasic(BaseModel):
    """Basic card information for gameplay"""
    model_config = ConfigDict(from_attributes=False)

    scryfall_id: str
    name: str
    mana_cost: Optional[str]
    cmc: Optional[int]
    type_line: str
    oracle_text: Optional[str]
    colors: Optional[List[str]]
    color_identity: Optional[List[str]]
    power: Optional[str]
    toughness: Optional[str]
    loyalty: Optional[str]
    image_uris: Optional[Dict[str, str]]
    legalities: Optional[Dict[str, str]]


class CardSearchResult(BaseModel):
    """Card search result"""
    model_config = ConfigDict(from_attributes=False)

    scryfall_id: str
    name: str
    mana_cost: Optional[str]
    type_line: str
    colors: Optional[List[str]]
    image_uris: Optional[Dict[str, str]]


class CardValidationResult(BaseModel):
    """Result of card validation"""
    name: str
    found: bool
    scryfall_id: Optional[str] = None
    error: Optional[str] = None


class CardBatchValidation(BaseModel):
    """Batch validation results"""
    valid_cards: List[CardValidationResult]
    invalid_cards: List[CardValidationResult]
    total_valid: int
    total_invalid: int
    errors: List[str] = []


# Scryfall API response models (for reference, not used directly in database)
class ScryfallCard(BaseModel):
    """Scryfall API card response model"""
    id: str
    name: str
    mana_cost: Optional[str]
    cmc: Optional[int]
    type_line: str
    oracle_text: Optional[str]
    colors: Optional[List[str]]
    color_identity: Optional[List[str]]
    keywords: Optional[List[str]]
    power: Optional[str]
    toughness: Optional[str]
    loyalty: Optional[str]
    image_uris: Optional[Dict[str, str]]
    legalities: Optional[Dict[str, str]]
    set: Optional[str]
    set_name: Optional[str]
    rarity: Optional[str]
    artist: Optional[str]
