from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.game_state import GameState, PlayerGameState, GameCard
from app.models.game import CardZone
from app.repositories.base import BaseRepository
import random


class GameStateRepository(BaseRepository[GameState]):
    """Repository for GameState model operations"""
    
    def __init__(self, db: Session):
        super().__init__(db, GameState)
    
    def get_by_game_room_id(self, game_room_id: int) -> Optional[GameState]:
        """Get game state by game room ID"""
        return self.db.query(GameState).filter(
            GameState.game_room_id == game_room_id
        ).first()
    
    def get_by_id_with_relations(self, game_state_id: int) -> Optional[GameState]:
        """Get game state with all relationships"""
        return self.db.query(GameState).filter(
            GameState.id == game_state_id
        ).first()


class PlayerGameStateRepository(BaseRepository[PlayerGameState]):
    """Repository for PlayerGameState model operations"""
    
    def __init__(self, db: Session):
        super().__init__(db, PlayerGameState)
    
    def get_by_game_state_and_user(self, game_state_id: int, user_id: int) -> Optional[PlayerGameState]:
        """Get player game state by game state and user ID"""
        return self.db.query(PlayerGameState).filter(
            PlayerGameState.game_state_id == game_state_id,
            PlayerGameState.user_id == user_id
        ).first()
    
    def get_by_game_state(self, game_state_id: int) -> List[PlayerGameState]:
        """Get all player states for a game state"""
        return self.db.query(PlayerGameState).filter(
            PlayerGameState.game_state_id == game_state_id
        ).order_by(PlayerGameState.player_order).all()
    
    def get_active_player(self, game_state_id: int) -> Optional[PlayerGameState]:
        """Get the active player for a game state"""
        return self.db.query(PlayerGameState).filter(
            PlayerGameState.game_state_id == game_state_id,
            PlayerGameState.is_active == True
        ).first()


class GameCardRepository(BaseRepository[GameCard]):
    """Repository for GameCard model operations"""
    
    def __init__(self, db: Session):
        super().__init__(db, GameCard)
    
    def get_player_cards_in_zone(
        self, 
        player_state_id: int, 
        zone: CardZone
    ) -> List[GameCard]:
        """Get all cards for a player in a specific zone"""
        return self.db.query(GameCard).filter(
            GameCard.player_game_state_id == player_state_id,
            GameCard.zone == zone.value
        ).order_by(GameCard.position).all()
    
    def get_card_by_id(self, card_id: int) -> Optional[GameCard]:
        """Get a card by ID"""
        return self.db.query(GameCard).filter(GameCard.id == card_id).first()
    
    def create_cards(self, cards_data: List[dict]) -> List[GameCard]:
        """Bulk create cards"""
        cards = [GameCard(**data) for data in cards_data]
        self.db.add_all(cards)
        self.db.commit()
        for card in cards:
            self.db.refresh(card)
        return cards
    
    def move_card(
        self, 
        card_id: int, 
        new_zone: CardZone, 
        new_position: int,
        player_state_id: Optional[int] = None
    ) -> Optional[GameCard]:
        """Move a card to a new zone"""
        card = self.get_card_by_id(card_id)
        if not card:
            return None
        
        card.zone = new_zone.value
        card.position = new_position
        
        if player_state_id:
            card.player_game_state_id = player_state_id
        
        self.db.commit()
        self.db.refresh(card)
        return card
    
    def shuffle_zone(self, player_state_id: int, zone: CardZone) -> None:
        """Shuffle cards in a zone (randomize positions)"""
        cards = self.get_player_cards_in_zone(player_state_id, zone)
        positions = list(range(len(cards)))
        random.shuffle(positions)
        
        for i, card in enumerate(cards):
            card.position = positions[i]
        
        self.db.commit()
    
    def draw_cards(
        self, 
        player_state_id: int, 
        count: int
    ) -> List[GameCard]:
        """Draw cards from library to hand"""
        library_cards = self.get_player_cards_in_zone(player_state_id, CardZone.LIBRARY)
        
        if not library_cards:
            return []
        
        drawn_cards = []
        for i in range(min(count, len(library_cards))):
            card = library_cards[i]
            card.zone = CardZone.HAND.value
            card.position = i
            drawn_cards.append(card)
        
        self.db.commit()
        return drawn_cards
    
    def update_battlefield_position(
        self, 
        card_id: int, 
        x: float, 
        y: float
    ) -> Optional[GameCard]:
        """Update card position on battlefield"""
        card = self.get_card_by_id(card_id)
        if not card:
            return None
        
        card.battlefield_x = x
        card.battlefield_y = y
        
        self.db.commit()
        self.db.refresh(card)
        return card
    
    def toggle_tapped(self, card_id: int) -> Optional[GameCard]:
        """Toggle card tapped status"""
        card = self.get_card_by_id(card_id)
        if not card:
            return None
        
        card.is_tapped = not card.is_tapped
        
        self.db.commit()
        self.db.refresh(card)
        return card
