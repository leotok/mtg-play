from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.deck import Deck, DeckCard
from .base import BaseRepository


class DeckRepository(BaseRepository[Deck]):
    """Repository for Deck model operations"""
    
    def __init__(self, db: Session):
        super().__init__(db, Deck)
    
    def get_user_decks(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Deck]:
        """Get all decks for a specific user"""
        return self.db.query(Deck).filter(
            Deck.owner_id == user_id
        ).offset(skip).limit(limit).all()
    
    def get_public_decks(self, skip: int = 0, limit: int = 100) -> List[Deck]:
        """Get all public decks"""
        return self.db.query(Deck).filter(
            Deck.is_public == True
        ).offset(skip).limit(limit).all()
    
    def get_deck_with_cards(self, deck_id: int) -> Optional[Deck]:
        """Get deck with all its cards loaded"""
        return self.db.query(Deck).filter(Deck.id == deck_id).first()
    
    def get_deck_by_name(self, name: str, user_id: Optional[int] = None) -> Optional[Deck]:
        """Get deck by name, optionally filtered by user"""
        query = self.db.query(Deck).filter(Deck.name == name)
        
        if user_id:
            query = query.filter(Deck.owner_id == user_id)
        
        return query.first()
    
    def search_decks(self, query: str, user_id: Optional[int] = None, limit: int = 20) -> List[Deck]:
        """Search decks by name or description"""
        search_pattern = f"%{query}%"
        db_query = self.db.query(Deck).filter(
            or_(
                Deck.name.ilike(search_pattern),
                Deck.description.ilike(search_pattern)
            )
        )
        
        if user_id:
            db_query = db_query.filter(Deck.owner_id == user_id)
        else:
            # Only search public decks if no user specified
            db_query = db_query.filter(Deck.is_public == True)
        
        return db_query.limit(limit).all()
    
    def get_decks_by_commander(self, commander_scryfall_id: str, user_id: Optional[int] = None) -> List[Deck]:
        """Get decks that use a specific commander"""
        query = self.db.query(Deck).filter(Deck.commander_scryfall_id == commander_scryfall_id)
        
        if user_id:
            query = query.filter(Deck.owner_id == user_id)
        else:
            query = query.filter(Deck.is_public == True)
        
        return query.all()
    
    def get_decks_by_color_identity(self, colors: List[str], user_id: Optional[int] = None) -> List[Deck]:
        """Get decks with specific color identity (more complex implementation needed)"""
        # This would require analyzing the cards in each deck
        # For now, return empty list as placeholder
        return []
    
    def update_deck_visibility(self, deck_id: int, is_public: bool) -> bool:
        """Update deck visibility"""
        deck = self.get_by_id(deck_id)
        if deck:
            deck.is_public = is_public
            self.db.commit()
            return True
        return False
    
    def get_deck_card_count(self, deck_id: int) -> int:
        """Get total number of cards in a deck"""
        return self.db.query(DeckCard).filter(DeckCard.deck_id == deck_id).count()
    
    def get_deck_cards(self, deck_id: int) -> List[DeckCard]:
        """Get all cards in a deck"""
        return self.db.query(DeckCard).filter(DeckCard.deck_id == deck_id).all()
    
    def get_deck_commander(self, deck_id: int) -> Optional[DeckCard]:
        """Get the commander card for a deck"""
        return self.db.query(DeckCard).filter(
            and_(DeckCard.deck_id == deck_id, DeckCard.is_commander == True)
        ).first()
    
    def get_deck_non_commander_cards(self, deck_id: int) -> List[DeckCard]:
        """Get all non-commander cards in a deck"""
        return self.db.query(DeckCard).filter(
            and_(DeckCard.deck_id == deck_id, DeckCard.is_commander == False)
        ).all()
    
    def add_card_to_deck(self, deck_id: int, card_scryfall_id: str, quantity: int = 1, is_commander: bool = False) -> DeckCard:
        """Add a card to a deck"""
        deck_card_data = {
            "deck_id": deck_id,
            "card_scryfall_id": card_scryfall_id,
            "quantity": quantity,
            "is_commander": is_commander
        }
        
        # Check if card already exists in deck
        existing = self.db.query(DeckCard).filter(
            and_(DeckCard.deck_id == deck_id, DeckCard.card_scryfall_id == card_scryfall_id)
        ).first()
        
        if existing:
            # Update quantity instead of creating new
            existing.quantity += quantity
            if is_commander:
                existing.is_commander = True
            self.db.commit()
            self.db.refresh(existing)
            return existing
        
        # Create new deck card manually (not using self.create which would create a Deck)
        deck_card = DeckCard(**deck_card_data)
        self.db.add(deck_card)
        self.db.commit()
        self.db.refresh(deck_card)
        return deck_card
    
    def remove_card_from_deck(self, deck_id: int, card_scryfall_id: str) -> bool:
        """Remove a card from a deck by Scryfall ID"""
        deck_card = self.db.query(DeckCard).filter(
            and_(DeckCard.deck_id == deck_id, DeckCard.card_scryfall_id == card_scryfall_id)
        ).first()
        
        if deck_card:
            self.db.delete(deck_card)
            self.db.commit()
            return True
        return False

    def get_deck_card_by_id(self, deck_id: int, deck_card_id: int) -> Optional[DeckCard]:
        """Get a deck card by its ID"""
        return self.db.query(DeckCard).filter(
            and_(DeckCard.deck_id == deck_id, DeckCard.id == deck_card_id)
        ).first()

    def remove_card_from_deck_by_id(self, deck_id: int, deck_card_id: int) -> bool:
        """Remove a card from a deck by DeckCard ID"""
        deck_card = self.get_deck_card_by_id(deck_id, deck_card_id)
        if deck_card:
            self.db.delete(deck_card)
            self.db.commit()
            return True
        return False
    
    def update_card_in_deck(self, deck_id: int, card_scryfall_id: str, quantity: int, is_commander: bool = False) -> Optional[DeckCard]:
        """Update a card in a deck by Scryfall ID"""
        deck_card = self.db.query(DeckCard).filter(
            and_(DeckCard.deck_id == deck_id, DeckCard.card_scryfall_id == card_scryfall_id)
        ).first()
        
        if deck_card:
            deck_card.quantity = quantity
            deck_card.is_commander = is_commander
            self.db.commit()
            self.db.refresh(deck_card)
            return deck_card
        return None

    def update_card_in_deck_by_id(self, deck_id: int, deck_card_id: int, quantity: int, is_commander: bool = False) -> Optional[DeckCard]:
        """Update a card in a deck by DeckCard ID"""
        deck_card = self.get_deck_card_by_id(deck_id, deck_card_id)
        if deck_card:
            deck_card.quantity = quantity
            deck_card.is_commander = is_commander
            self.db.commit()
            self.db.refresh(deck_card)
            return deck_card
        return None
    
    def clear_deck_cards(self, deck_id: int) -> int:
        """Remove all cards from a deck"""
        count = self.db.query(DeckCard).filter(DeckCard.deck_id == deck_id).count()
        self.db.query(DeckCard).filter(DeckCard.deck_id == deck_id).delete()
        self.db.commit()
        return count
    
    def get_deck_statistics(self, deck_id: int) -> Dict[str, Any]:
        """Get detailed statistics for a deck"""
        deck = self.get_by_id(deck_id)
        if not deck:
            return {}
        
        cards = self.get_deck_cards(deck_id)
        
        total_cards = sum(card.quantity for card in cards)
        unique_cards = len(cards)
        commander_count = sum(1 for card in cards if card.is_commander)
        
        # Get card details for color analysis (removed since we don't have local cards table)
        card_scryfall_ids = [card.card_scryfall_id for card in cards]
        
        # For now, just return basic stats without color analysis
        # Color analysis would require Scryfall API calls
        
        return {
            "deck_id": deck_id,
            "deck_name": deck.name,
            "total_cards": total_cards,
            "unique_cards": unique_cards,
            "commander_count": commander_count,
            "colors": [],  # Would need Scryfall API call
            "is_public": deck.is_public,
            "created_at": deck.created_at.isoformat() if deck.created_at else None,
            "updated_at": deck.updated_at.isoformat() if deck.updated_at else None
        }
    
    def get_user_deck_count(self, user_id: int) -> int:
        """Get total number of decks for a user"""
        return self.db.query(Deck).filter(Deck.owner_id == user_id).count()
    
    def get_public_deck_count(self) -> int:
        """Get total number of public decks"""
        return self.db.query(Deck).filter(Deck.is_public == True).count()
    
    def get_recent_decks(self, user_id: Optional[int] = None, limit: int = 10) -> List[Deck]:
        """Get recently created decks"""
        query = self.db.query(Deck).order_by(Deck.created_at.desc())
        
        if user_id:
            query = query.filter(Deck.owner_id == user_id)
        else:
            query = query.filter(Deck.is_public == True)
        
        return query.limit(limit).all()
    
    def get_updated_decks(self, user_id: Optional[int] = None, limit: int = 10) -> List[Deck]:
        """Get recently updated decks"""
        query = self.db.query(Deck).order_by(Deck.updated_at.desc())
        
        if user_id:
            query = query.filter(Deck.owner_id == user_id)
        else:
            query = query.filter(Deck.is_public == True)
        
        return query.limit(limit).all()
    
    def duplicate_deck(self, deck_id: int, new_name: str, new_owner_id: int) -> Optional[Deck]:
        """Duplicate a deck for another user"""
        original_deck = self.get_by_id(deck_id)
        if not original_deck:
            return None
        
        # Create new deck
        new_deck_data = {
            "name": new_name,
            "description": original_deck.description,
            "commander_scryfall_id": original_deck.commander_scryfall_id,
            "owner_id": new_owner_id,
            "is_public": False  # Duplicated decks are private by default
        }
        
        new_deck = self.create(new_deck_data)
        
        # Copy all cards
        original_cards = self.get_deck_cards(deck_id)
        for card in original_cards:
            self.add_card_to_deck(
                new_deck.id, 
                card.card_scryfall_id, 
                card.quantity, 
                card.is_commander
            )
        
        return new_deck
