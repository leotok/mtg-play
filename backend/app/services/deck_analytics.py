from typing import Dict, Any
from sqlalchemy.orm import Session

from app.models import Deck, DeckCard
from app.repositories import DeckRepository


class DeckAnalytics:
    """Deck analytics service using repositories for data access"""
    
    def __init__(self, deck_repo: DeckRepository):
        self.deck_repo = deck_repo
    
    @classmethod
    def create_with_repositories(cls, db_session: Session):
        """Factory method to create analytics with repositories"""
        deck_repo = DeckRepository(db_session)
        return cls(deck_repo)

    def get_deck_stats(self, deck_id: int) -> Dict[str, Any]:
        """Get basic deck statistics"""
        # Verify deck exists
        deck = self.deck_repo.get_by_id(deck_id)
        if not deck:
            return {"error": "Deck not found"}
        
        # Get all cards in deck
        deck_cards = self.deck_repo.get_deck_cards(deck_id)
        
        # Count cards
        commander_count = 0
        main_deck_count = 0
        total_quantity = 0
        
        for deck_card in deck_cards:
            if deck_card.is_commander:
                commander_count += deck_card.quantity
            else:
                main_deck_count += deck_card.quantity
            total_quantity += deck_card.quantity
        
        # Get unique card count
        unique_cards = len([dc for dc in deck_cards if not dc.is_commander])
        
        return {
            "deck_id": deck_id,
            "deck_name": deck.name,
            "total_cards": total_quantity,
            "commander_count": commander_count,
            "main_deck_count": main_deck_count,
            "unique_cards": unique_cards,
            "is_complete": total_quantity == 100
        }

    def export_deck_basic(self, deck_id: int) -> Dict[str, Any]:
        """Export deck in basic format (deck metadata + card scryfall IDs).
        For full card details, use deck_service.export_deck which fetches from Scryfall."""
        deck = self.deck_repo.get_by_id(deck_id)
        if not deck:
            return {"error": "Deck not found"}
        
        deck_cards = self.deck_repo.get_deck_cards(deck_id)
        commander_cards = [{"card_scryfall_id": dc.card_scryfall_id, "quantity": dc.quantity} for dc in deck_cards if dc.is_commander]
        main_deck = [{"card_scryfall_id": dc.card_scryfall_id, "quantity": dc.quantity} for dc in deck_cards if not dc.is_commander]
        
        return {
            "deck": {
                "id": deck.id,
                "name": deck.name,
                "description": deck.description,
                "commander_scryfall_id": deck.commander_scryfall_id,
                "created_at": deck.created_at.isoformat() if deck.created_at else None,
                "is_public": deck.is_public
            },
            "cards": {
                "commander": commander_cards,
                "main_deck": main_deck
            }
        }
