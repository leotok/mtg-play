from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.models import Deck, DeckCard
from app.repositories import DeckRepository


class DeckValidator:
    """Deck validator using repositories for data access"""
    
    def __init__(self, deck_repo: DeckRepository):
        self.deck_repo = deck_repo
    
    @classmethod
    def create_with_repositories(cls, db_session: Session):
        """Factory method to create validator with repositories"""
        deck_repo = DeckRepository(db_session)
        return cls(deck_repo)

    def validate_deck(self, deck_id: int) -> Dict[str, Any]:
        """Validate a deck against Commander format rules"""
        errors = []
        
        # Get deck info
        deck = self.deck_repo.get_by_id(deck_id)
        if not deck:
            return {"is_valid": False, "errors": ["Deck not found"]}
        
        # Get all cards in deck
        deck_cards = self.deck_repo.get_deck_cards(deck_id)
        
        # Count cards (excluding commander from main count)
        commander_count = 0
        main_deck_count = 0
        
        for deck_card in deck_cards:
            if deck_card.is_commander:
                commander_count += deck_card.quantity
            else:
                main_deck_count += deck_card.quantity
        
        total_cards = commander_count + main_deck_count
        
        # Validation rules
        errors.extend(self._validate_deck_size(total_cards, commander_count))
        errors.extend(self._validate_commander(deck, deck_cards))
        errors.extend(self._validate_color_identity(deck, deck_cards))
        errors.extend(self._validate_card_legality(deck, deck_cards))
        errors.extend(self._validate_card_uniqueness(deck_cards))
        
        return {
            "deck_id": deck_id,
            "total_cards": total_cards,
            "commander_count": commander_count,
            "main_deck_count": main_deck_count,
            "is_valid": len(errors) == 0,
            "validation_errors": errors
        }

    def _validate_deck_size(self, total_cards: int, commander_count: int) -> List[str]:
        """Validate deck size requirements"""
        errors = []
        
        if total_cards != 100:
            errors.append(f"Deck must have exactly 100 cards (has {total_cards})")
        
        if commander_count != 1:
            errors.append(f"Deck must have exactly 1 commander (has {commander_count})")
        
        return errors

    def _validate_commander(self, deck: Deck, deck_cards: List[DeckCard]) -> List[str]:
        """Validate commander requirements"""
        errors = []
        
        # Check if commander exists in deck cards
        commander_cards = [dc for dc in deck_cards if dc.is_commander]
        if not commander_cards:
            errors.append("Commander card not found in deck")
            return errors
        
        # Basic validation - commander validation will be handled by ScryfallService
        return errors

    def _validate_color_identity(self, deck: Deck, deck_cards: List[DeckCard]) -> List[str]:
        """Validate color identity - would require Scryfall API for full validation."""
        return []

    def _validate_card_count(self, deck: Deck, deck_cards: List[DeckCard]) -> List[str]:
        """Validate card count limits"""
        errors = []
        
        total_cards = sum(dc.quantity for dc in deck_cards)
        
        # Commander format rules (basic)
        if total_cards < 100:
            errors.append("Deck must have at least 100 cards (commander excluded)")
        
        if total_cards > 10000:  # Reasonable upper limit
            errors.append("Deck has too many cards")
        
        return errors

    def _validate_card_legality(self, deck: Deck, deck_cards: List[DeckCard]) -> List[str]:
        """Validate card legality"""
        # Skip legality validation for now since we don't have local card data
        # This would require Scryfall API calls to implement properly
        return []

    def _validate_card_uniqueness(self, deck_cards: List[DeckCard]) -> List[str]:
        """Validate singleton format (no duplicates except basic lands)"""
        # Skip uniqueness validation for now since we don't have local card data
        # This would require Scryfall API calls to implement properly
        return []
