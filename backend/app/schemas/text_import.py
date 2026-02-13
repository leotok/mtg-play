from pydantic import BaseModel, Field
from typing import List, Optional


class TextDeckImport(BaseModel):
    """Text deck import - accepts raw decklist text"""
    name: str = Field(..., min_length=1, max_length=100, description="Deck name")
    description: Optional[str] = Field(None, max_length=500, description="Deck description")
    deck_text: str = Field(..., description="Raw decklist text (one card per line)")
    is_public: bool = Field(False, description="Whether deck is public")


class TextImportResult(BaseModel):
    """Result of text deck import"""
    success: bool
    deck_id: Optional[int] = None
    deck_name: Optional[str] = None
    imported_cards: List[dict] = []
    failed_cards: List[dict] = []
    warnings: List[str] = []
    errors: List[str] = []
    total_cards: int = 0
    parsed_cards: int = 0
