from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from app.core.database import get_db
from app.models.user import User
from app.models.game import GameRoom, GameRoomPlayer, GameStatus, PlayerStatus
from app.repositories.game import GameRoomRepository, GameRoomPlayerRepository
from app.repositories import DeckRepository
from app.schemas.game import (
    GameRoomCreate,
    GameRoomResponse,
    GameRoomListItem,
    JoinResponse,
    DeckSelectionRequest,
    DeckInfo,
    GameRoomPlayerResponse,
)
from app.services.scryfall import get_scryfall_service
import logging
import secrets
import string

logger = logging.getLogger(__name__)


class GameService:
    def __init__(
        self,
        game_repo: GameRoomRepository,
        player_repo: GameRoomPlayerRepository,
        deck_repo: DeckRepository,
    ):
        self.game_repo = game_repo
        self.player_repo = player_repo
        self.deck_repo = deck_repo
    
    @classmethod
    def create_with_repositories(cls, db: Session):
        game_repo = GameRoomRepository(db)
        player_repo = GameRoomPlayerRepository(db)
        deck_repo = DeckRepository(db)
        return cls(game_repo, player_repo, deck_repo)
    
    def _get_game_or_404(self, game_id: int) -> GameRoom:
        game = self.game_repo.get_by_id(game_id)
        if not game:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game room not found"
            )
        return game
    
    def _is_host(self, game: GameRoom, user_id: int) -> bool:
        return game.host_id == user_id
    
    def _generate_unique_invite_code(self) -> str:
        chars = string.ascii_uppercase + string.digits
        code = ''.join(secrets.choice(chars) for _ in range(8))
        while self.game_repo.get_by_invite_code(code):
            code = ''.join(secrets.choice(chars) for _ in range(8))
        return code
    
    async def create_game(
        self,
        game_data: GameRoomCreate,
        current_user: User
    ) -> GameRoomResponse:
        invite_code = self._generate_unique_invite_code()
        
        game = self.game_repo.create({
            "name": game_data.name,
            "description": game_data.description,
            "host_id": current_user.id,
            "invite_code": invite_code,
            "is_public": game_data.is_public,
            "max_players": game_data.max_players,
            "power_bracket": game_data.power_bracket,
            "status": GameStatus.WAITING,
        })
        
        self.player_repo.create_player({
            "game_room_id": game.id,
            "user_id": current_user.id,
            "status": PlayerStatus.ACCEPTED,
            "is_host": True,
        })
        
        return await self._build_game_response(game)
    
    def list_games(self, current_user: User) -> List[GameRoomListItem]:
        public_games = self.game_repo.get_public_waiting_games()
        user_games = self.game_repo.get_user_games(current_user.id)
        
        user_game_ids = {game.id for game in user_games}
        
        all_games = {game.id: game for game in public_games + user_games}
        
        result = []
        for game in all_games.values():
            current_players = self.player_repo.count_accepted(game.id)
            is_in_game = game.id in user_game_ids
            result.append(GameRoomListItem(
                id=game.id,
                name=game.name,
                description=game.description,
                host_username=game.host.username if game.host else "Unknown",
                is_public=game.is_public,
                max_players=game.max_players,
                current_players=current_players,
                power_bracket=game.power_bracket,
                status=game.status,
                created_at=game.created_at,
                is_in_game=is_in_game,
            ))
        return result
    
    async def get_game(self, game_id: int, current_user: User) -> GameRoomResponse:
        game = self._get_game_or_404(game_id)
        
        player = self.player_repo.get_player(game.id, current_user.id)
        if not player and not game.is_public and not self._is_host(game, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this game"
            )
        
        return await self._build_game_response(game)
    
    async def get_game_by_invite(self, invite_code: str, current_user: User) -> GameRoomResponse:
        game = self.game_repo.get_by_invite_code(invite_code)
        if not game:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game not found"
            )
        return await self._build_game_response(game)
    
    def join_game(self, game_id: int, current_user: User) -> JoinResponse:
        game = self._get_game_or_404(game_id)
        
        existing_player = self.player_repo.get_player(game.id, current_user.id)
        if existing_player:
            if existing_player.status == PlayerStatus.ACCEPTED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="You are already in this game"
                )
            elif existing_player.status == PlayerStatus.PENDING:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Your join request is pending"
                )
        
        current_players = self.player_repo.count_accepted(game.id)
        if current_players >= game.max_players:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Game is full"
            )
        
        if game.status != GameStatus.WAITING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Game has already started"
            )
        
        self.player_repo.create_player({
            "game_room_id": game.id,
            "user_id": current_user.id,
            "status": PlayerStatus.PENDING,
            "is_host": False,
        })
        
        return JoinResponse(
            message="Join request sent to host",
            game_room=None,
        )
    
    async def accept_player(
        self,
        game_id: int,
        player_id: int,
        current_user: User
    ) -> GameRoomResponse:
        game = self._get_game_or_404(game_id)
        
        if not self._is_host(game, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the host can accept players"
            )
        
        player = self.player_repo.get_player_by_id(player_id, game.id)
        if not player:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Player not found in this game"
            )
        
        if player.status != PlayerStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Player is not pending"
            )
        
        current_players = self.player_repo.count_accepted(game.id)
        if current_players >= game.max_players:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Game is full"
            )
        
        self.player_repo.update_status(player_id, PlayerStatus.ACCEPTED)
        
        return await self._build_game_response(game)
    
    async def reject_player(
        self,
        game_id: int,
        player_id: int,
        current_user: User
    ) -> GameRoomResponse:
        game = self._get_game_or_404(game_id)
        
        if not self._is_host(game, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the host can reject players"
            )
        
        player = self.player_repo.get_player_by_id(player_id, game.id)
        if not player:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Player not found in this game"
            )
        
        if player.status != PlayerStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Player is not pending"
            )
        
        self.player_repo.update_status(player_id, PlayerStatus.REJECTED)
        
        return await self._build_game_response(game)
    
    def leave_game(self, game_id: int, current_user: User) -> None:
        game = self._get_game_or_404(game_id)
        
        player = self.player_repo.get_player(game.id, current_user.id)
        if not player:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="You are not in this game"
            )
        
        if player.is_host:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Host cannot leave. Delete the game instead."
            )
        
        self.player_repo.delete(player.id)
    
    def delete_game(self, game_id: int, current_user: User) -> None:
        game = self._get_game_or_404(game_id)
        
        if not self._is_host(game, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the host can delete this game"
            )
        
        self.game_repo.delete(game_id)
    
    async def start_game(self, game_id: int, current_user: User) -> GameRoomResponse:
        game = self._get_game_or_404(game_id)
        
        if not self._is_host(game, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the host can start the game"
            )
        
        accepted_players = self.player_repo.get_accepted_players(game.id)
        
        if len(accepted_players) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Need at least 2 players to start"
            )
        
        players_without_decks = [p for p in accepted_players if not p.deck_id]
        if players_without_decks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="All players must select their decks before starting"
            )
        
        self.game_repo.update_status(game.id, GameStatus.IN_PROGRESS)
        
        game = self._get_game_or_404(game_id)
        return await self._build_game_response(game)
    
    async def stop_game(self, game_id: int, current_user: User) -> GameRoomResponse:
        game = self._get_game_or_404(game_id)
        
        if not self._is_host(game, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the host can stop the game"
            )
        
        if game.status != GameStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Game is not in progress"
            )
        
        self.game_repo.update_status(game.id, GameStatus.WAITING)
        
        game = self._get_game_or_404(game_id)
        return await self._build_game_response(game)
    
    async def select_deck(
        self,
        game_id: int,
        deck_selection: DeckSelectionRequest,
        current_user: User
    ) -> GameRoomResponse:
        game = self._get_game_or_404(game_id)
        
        player = self.player_repo.get_player(game.id, current_user.id)
        if not player:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="You are not in this game"
            )
        
        if player.status != PlayerStatus.ACCEPTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Your join request must be accepted first"
            )
        
        deck = self.deck_repo.get_by_id(deck_selection.deck_id)
        if not deck or deck.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Deck not found or does not belong to you"
            )
        
        self.player_repo.set_deck(player.id, deck_selection.deck_id)
        
        return await self._build_game_response(game)
    
    async def _build_game_response(self, game: GameRoom) -> GameRoomResponse:
        from app.models.game import PlayerStatus
        # Get all players (both accepted and pending) so hosts can see pending requests
        players = self.player_repo.get_all_players(game.id)
        
        scryfall_service = get_scryfall_service()
        
        player_responses = []
        for p in players:
            user = self.game_repo.db.query(User).filter(User.id == p.user_id).first()
            
            deck_info = None
            if p.deck_id:
                deck = self.deck_repo.get_by_id(p.deck_id)
                if deck:
                    commander_name = None
                    commander_image_uris = None
                    
                    if deck.commander_scryfall_id:
                        card_data = await scryfall_service.get_card_by_scryfall_id(
                            deck.commander_scryfall_id
                        )
                        if card_data:
                            commander_name = card_data.get('name', deck.name)
                            commander_image_uris = card_data.get('image_uris')
                            if not commander_image_uris and card_data.get('card_faces'):
                                commander_image_uris = card_data['card_faces'][0].get('image_uris')
                    
                    deck_info = DeckInfo(
                        id=deck.id,
                        name=deck.name,
                        commander_name=commander_name,
                        commander_image_uris=commander_image_uris,
                    )
            
            player_responses.append(GameRoomPlayerResponse(
                id=p.id,
                user_id=p.user_id,
                username=user.username if user else "Unknown",
                status=p.status,
                is_host=p.is_host,
                deck_id=p.deck_id,
                deck=deck_info,
                joined_at=p.joined_at,
            ))
        
        return GameRoomResponse(
            id=game.id,
            name=game.name,
            description=game.description,
            host_id=game.host_id,
            host_username=game.host.username if game.host else "Unknown",
            invite_code=game.invite_code,
            is_public=game.is_public,
            max_players=game.max_players,
            power_bracket=game.power_bracket,
            status=game.status,
            players=player_responses,
            created_at=game.created_at,
        )


def get_game_service(db: Session = Depends(get_db)) -> GameService:
    return GameService.create_with_repositories(db)
