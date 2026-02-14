from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.game import GameRoom, GameRoomPlayer, GameStatus, PlayerStatus
from app.repositories.base import BaseRepository


class GameRoomRepository(BaseRepository[GameRoom]):
    def __init__(self, db: Session):
        super().__init__(db, GameRoom)
    
    def get_by_invite_code(self, invite_code: str) -> Optional[GameRoom]:
        return self.db.query(GameRoom).filter(
            GameRoom.invite_code == invite_code
        ).first()
    
    def get_public_waiting_games(self) -> List[GameRoom]:
        return self.db.query(GameRoom).filter(
            GameRoom.is_public == True,
            GameRoom.status == GameStatus.WAITING
        ).all()
    
    def get_user_games(self, user_id: int) -> List[GameRoom]:
        return self.db.query(GameRoom).join(GameRoomPlayer).filter(
            GameRoomPlayer.user_id == user_id
        ).all()
    
    def create(self, game_data: dict) -> GameRoom:
        game = GameRoom(**game_data)
        self.db.add(game)
        self.db.commit()
        self.db.refresh(game)
        return game
    
    def update_status(self, game_id: int, status: GameStatus) -> GameRoom:
        game = self.db.query(GameRoom).filter(GameRoom.id == game_id).first()
        if game:
            game.status = status
            self.db.commit()
            self.db.refresh(game)
        return game


class GameRoomPlayerRepository(BaseRepository[GameRoomPlayer]):
    def __init__(self, db: Session):
        super().__init__(db, GameRoomPlayer)
    
    def get_player(self, game_room_id: int, user_id: int) -> Optional[GameRoomPlayer]:
        return self.db.query(GameRoomPlayer).filter(
            GameRoomPlayer.game_room_id == game_room_id,
            GameRoomPlayer.user_id == user_id
        ).first()
    
    def get_accepted_players(self, game_room_id: int) -> List[GameRoomPlayer]:
        return self.db.query(GameRoomPlayer).filter(
            GameRoomPlayer.game_room_id == game_room_id,
            GameRoomPlayer.status == PlayerStatus.ACCEPTED
        ).all()
    
    def get_pending_players(self, game_room_id: int) -> List[GameRoomPlayer]:
        return self.db.query(GameRoomPlayer).filter(
            GameRoomPlayer.game_room_id == game_room_id,
            GameRoomPlayer.status == PlayerStatus.PENDING
        ).all()
    
    def get_all_players(self, game_room_id: int) -> List[GameRoomPlayer]:
        return self.db.query(GameRoomPlayer).filter(
            GameRoomPlayer.game_room_id == game_room_id
        ).all()
    
    def get_player_by_id(self, player_id: int, game_room_id: int) -> Optional[GameRoomPlayer]:
        return self.db.query(GameRoomPlayer).filter(
            GameRoomPlayer.id == player_id,
            GameRoomPlayer.game_room_id == game_room_id
        ).first()
    
    def count_accepted(self, game_room_id: int) -> int:
        return self.db.query(GameRoomPlayer).filter(
            GameRoomPlayer.game_room_id == game_room_id,
            GameRoomPlayer.status == PlayerStatus.ACCEPTED
        ).count()
    
    def create_player(self, player_data: dict) -> GameRoomPlayer:
        player = GameRoomPlayer(**player_data)
        self.db.add(player)
        self.db.commit()
        self.db.refresh(player)
        return player
    
    def update_status(self, player_id: int, status: PlayerStatus) -> GameRoomPlayer:
        player = self.db.query(GameRoomPlayer).filter(
            GameRoomPlayer.id == player_id
        ).first()
        if player:
            player.status = status
            self.db.commit()
            self.db.refresh(player)
        return player
    
    def set_deck(self, player_id: int, deck_id: int) -> GameRoomPlayer:
        player = self.db.query(GameRoomPlayer).filter(
            GameRoomPlayer.id == player_id
        ).first()
        if player:
            player.deck_id = deck_id
            self.db.commit()
            self.db.refresh(player)
        return player
