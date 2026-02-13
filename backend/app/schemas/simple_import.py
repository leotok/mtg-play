from pydantic import BaseModel, Field
from typing import List, Optional


class SimpleDeckImport(BaseModel):
    """Simple deck import with card names"""
    name: str = Field(..., min_length=1, max_length=100, description="Deck name")
    description: Optional[str] = Field(None, max_length=500, description="Deck description")
    commander: str = Field(..., description="Commander name")
    cards: List[str] = Field(..., description="List of card names")
    is_public: bool = Field(False, description="Whether deck is public")


class SimpleImportResult(BaseModel):
    """Result of simple deck import"""
    success: bool
    deck_id: Optional[int] = None
    deck_name: Optional[str] = None
    imported_cards: List[dict] = []
    failed_cards: List[dict] = []
    warnings: List[str] = []
    errors: List[str] = []
    total_cards: int = 0
