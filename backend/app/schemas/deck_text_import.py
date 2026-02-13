from pydantic import BaseModel, Field
from typing import List, Optional


class DeckTextImport(BaseModel):
    """Text import for adding cards to existing deck"""
    deck_text: str = Field(..., description="Raw decklist text (one card per line)")


class DeckImportResult(BaseModel):
    """Result of importing cards into existing deck"""
    success: bool
    imported_count: int = 0
    failed_cards: List[str] = []
    errors: List[str] = []