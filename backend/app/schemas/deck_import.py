from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from enum import Enum


class ImportFormat(str, Enum):
    """Supported import formats"""
    JSON = "json"
    ARENA = "arena"


class JsonImportCard(BaseModel):
    """Card in JSON import format"""
    scryfall_id: str = Field(..., description="Scryfall card ID")
    quantity: int = Field(..., ge=1, le=4, description="Card quantity (1-4)")
    is_commander: bool = Field(False, description="Whether this is the commander")


class JsonImportRequest(BaseModel):
    """JSON deck import request"""
    name: str = Field(..., min_length=1, max_length=100, description="Deck name")
    description: Optional[str] = Field(None, max_length=500, description="Deck description")
    commander: Optional[str] = Field(None, description="Commander name (optional, will validate against cards)")
    cards: List[JsonImportCard] = Field(..., description="List of cards in deck")
    is_public: bool = Field(False, description="Whether deck is public")


class ArenaImportRequest(BaseModel):
    """Arena deck import request"""
    name: str = Field(..., min_length=1, max_length=100, description="Deck name")
    description: Optional[str] = Field(None, max_length=500, description="Deck description")
    deck_text: str = Field(..., description="Raw deck text from MTG Arena export")
    is_public: bool = Field(False, description="Whether deck is public")


class ImportRequest(BaseModel):
    """Generic import request that handles multiple formats"""
    format: ImportFormat = Field(..., description="Import format")
    json_data: Optional[JsonImportRequest] = Field(None, description="JSON import data")
    arena_data: Optional[ArenaImportRequest] = Field(None, description="Arena import data")


class ImportedCard(BaseModel):
    """Result of importing a card"""
    name: str
    scryfall_id: str
    quantity: int
    is_commander: bool
    found: bool


class ImportResult(BaseModel):
    """Result of deck import"""
    success: bool
    deck_id: Optional[int] = None
    deck_name: Optional[str] = None
    imported_cards: List[ImportedCard] = []
    failed_cards: List[Dict[str, Any]] = []
    warnings: List[str] = []
    errors: List[str] = []
    validation_errors: List[str] = []


class CardLookupRequest(BaseModel):
    """Card lookup request"""
    identifier: str = Field(..., description="Card name or Scryfall ID")
    by_name: bool = Field(True, description="Whether to search by name (true) or Scryfall ID (false)")


class CardValidationRequest(BaseModel):
    """Card validation request"""
    card_names: List[str] = Field(..., description="List of card names to validate")


class ValidatedCard(BaseModel):
    """Validated card result"""
    name: str
    found: bool
    scryfall_id: Optional[str] = None
    error: Optional[str] = None


class CardValidationResponse(BaseModel):
    """Card validation response"""
    valid_cards: List[ValidatedCard]
    invalid_cards: List[ValidatedCard]
    total_valid: int
    total_invalid: int
    errors: List[str] = []
