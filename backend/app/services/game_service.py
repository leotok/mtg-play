from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from app.core.database import get_db
from app.models.user import User
from app.models.game import GameRoom, GameStatus, PlayerStatus, TurnPhase, CardZone, GameMode
from app.models.game_state import GameState, PlayerGameState, GameCard
from app.repositories.game import GameRoomRepository, GameRoomPlayerRepository
from app.repositories import DeckRepository
from app.repositories.game_state import GameStateRepository, PlayerGameStateRepository, GameCardRepository, GameLogRepository
from app.schemas.game import (
    GameRoomCreate,
    GameRoomResponse,
    GameRoomListItem,
    JoinResponse,
    DeckSelectionRequest,
    DeckInfo,
    GameRoomPlayerResponse,
)
from app.schemas.game_state import (
    GameStateResponse,
    PlayerGameStateResponse,
    GameCardResponse,
    GameCardInBattlefieldResponse,
    GameLogResponse,
)
from app.services.scryfall import get_scryfall_service
from app.engine.game_engine import create_engine_from_db, sync_engine_to_db
from app.engine.models import MoveCardInput, ManaColor
from app.engine.exceptions import TooManyLandsError, InvalidPhaseForLandError
from app.socket import get_sio
import logging
import secrets
import string
import random

logger = logging.getLogger(__name__)


class GameService:
    def __init__(
        self,
        game_repo: GameRoomRepository,
        player_repo: GameRoomPlayerRepository,
        deck_repo: DeckRepository,
        game_state_repo: Optional[GameStateRepository] = None,
        player_game_state_repo: Optional[PlayerGameStateRepository] = None,
        game_card_repo: Optional[GameCardRepository] = None,
        game_log_repo: Optional[GameLogRepository] = None,
    ):
        self.game_repo = game_repo
        self.player_repo = player_repo
        self.deck_repo = deck_repo
        self.game_state_repo = game_state_repo
        self.player_game_state_repo = player_game_state_repo
        self.game_card_repo = game_card_repo
        self.game_log_repo = game_log_repo
    
    @classmethod
    def create_with_repositories(cls, db: Session):
        game_repo = GameRoomRepository(db)
        player_repo = GameRoomPlayerRepository(db)
        deck_repo = DeckRepository(db)
        game_state_repo = GameStateRepository(db)
        player_game_state_repo = PlayerGameStateRepository(db)
        game_card_repo = GameCardRepository(db)
        game_log_repo = GameLogRepository(db)
        return cls(
            game_repo, 
            player_repo, 
            deck_repo,
            game_state_repo,
            player_game_state_repo,
            game_card_repo,
            game_log_repo,
        )
    
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
    
    def _use_engine(self, game: GameRoom) -> bool:
        return game.game_mode == GameMode.RULES_ENFORCED
    
    def _get_cards_by_player(self, player_states):
        cards_by_player = {}
        for ps in player_states:
            player_id = ps.user_id
            cards_by_player[player_id] = {
                "library": self.game_card_repo.get_player_cards_in_zone(ps.id, CardZone.LIBRARY),
                "hand": self.game_card_repo.get_player_cards_in_zone(ps.id, CardZone.HAND),
                "battlefield": self.game_card_repo.get_player_cards_in_zone(ps.id, CardZone.BATTLEFIELD),
                "graveyard": self.game_card_repo.get_player_cards_in_zone(ps.id, CardZone.GRAVEYARD),
                "exile": self.game_card_repo.get_player_cards_in_zone(ps.id, CardZone.EXILE),
                "commander": self.game_card_repo.get_player_cards_in_zone(ps.id, CardZone.COMMANDER),
            }
        return cards_by_player
    
    def _get_usernames(self, player_states):
        user_ids = [ps.user_id for ps in player_states]
        users = self.game_state_repo.db.query(User).filter(User.id.in_(user_ids)).all()
        return {u.id: u.username for u in users}
    
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
            "game_mode": game_data.game_mode,
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
            is_host = game.host_id == current_user.id
            result.append(GameRoomListItem(
                id=game.id,
                name=game.name,
                description=game.description,
                host_username=game.host.username if game.host else "Unknown",
                is_public=game.is_public,
                max_players=game.max_players,
                current_players=current_players,
                power_bracket=game.power_bracket,
                game_mode=game.game_mode,
                status=game.status,
                created_at=game.created_at,
                is_in_game=is_in_game,
                is_host=is_host,
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
        
        existing_game_state = self.game_state_repo.get_by_game_room_id(game_id)
        if existing_game_state:
            self.game_state_repo.db.query(GameState).filter(GameState.id == existing_game_state.id).delete()
            self.game_state_repo.db.commit()
        
        starting_player = random.choice(accepted_players)
        
        game_state = self.game_state_repo.create({
            "game_room_id": game_id,
            "current_turn": 1,
            "active_player_id": starting_player.user_id,
            "current_phase": TurnPhase.UNTAP.value,
            "starting_player_id": starting_player.user_id,
        })
        
        player_order = list(range(len(accepted_players)))
        random.shuffle(player_order)
        
        for i, player in enumerate(accepted_players):
            player_state = self.player_game_state_repo.create({
                "game_state_id": game_state.id,
                "user_id": player.user_id,
                "player_order": i,
                "is_active": player.user_id == starting_player.user_id,
                "life_total": 40,
                "poison_counters": 0,
            })
            
            deck = self.deck_repo.get_by_id(player.deck_id)
            if not deck:
                continue
            
            deck_cards = self.deck_repo.get_deck_cards(player.deck_id)
            
            if not deck_cards:
                logger.warning(f"Player {player.user_id} has no cards in deck {player.deck_id}")
                continue
            
            scryfall_service = get_scryfall_service()
            
            cards_data = []
            for deck_card in deck_cards:
                try:
                    card_data = await scryfall_service.get_card_by_scryfall_id(deck_card.card_scryfall_id)
                except Exception as e:
                    logger.error(f"Error fetching card {deck_card.card_scryfall_id}: {e}")
                    card_data = None
                    
                if not card_data:
                    logger.warning(f"Could not fetch card data for {deck_card.card_scryfall_id}")
                    continue
                
                for _ in range(deck_card.quantity):
                    cards_data.append({
                        "game_state_id": game_state.id,
                        "player_game_state_id": player_state.id,
                        "deck_card_id": deck_card.id,
                        "card_scryfall_id": deck_card.card_scryfall_id,
                        "card_name": card_data.get("name", "Unknown"),
                        "mana_cost": card_data.get("mana_cost"),
                        "cmc": card_data.get("cmc"),
                        "type_line": card_data.get("type_line"),
                        "oracle_text": card_data.get("oracle_text"),
                        "colors": card_data.get("colors"),
                        "power": card_data.get("power"),
                        "toughness": card_data.get("toughness"),
                        "keywords": card_data.get("keywords"),
                        "image_uris": card_data.get("image_uris"),
                        "card_faces": card_data.get("card_faces"),
                        "zone": CardZone.LIBRARY.value,
                        "position": len(cards_data),
                        "is_tapped": False,
                        "is_face_up": True,
                        "is_attacking": False,
                        "is_blocking": False,
                        "damage_received": 0,
                    })
            
            if cards_data:
                self.game_card_repo.create_cards(cards_data)
            
            all_cards = self.game_card_repo.get_player_cards_in_zone(player_state.id, CardZone.LIBRARY)
            
            if all_cards:
                positions = list(range(len(all_cards)))
                random.shuffle(positions)
                for i, card in enumerate(all_cards):
                    card.position = positions[i]
                self.game_card_repo.db.commit()
                
                commander_card_ids = [dc.id for dc in deck_cards if dc.is_commander]
                if commander_card_ids:
                    commander_cards = self.game_card_repo.db.query(GameCard).filter(
                        GameCard.player_game_state_id == player_state.id,
                        GameCard.deck_card_id.in_(commander_card_ids)
                    ).all()
                    
                    for commander in commander_cards:
                        commander.zone = CardZone.COMMANDER.value
                        commander.position = 0
                    self.game_card_repo.db.commit()
                
                drawn = self.game_card_repo.draw_cards(player_state.id, 7)
                logger.info(f"Drew {len(drawn)} cards for player {player.user_id}")
            else:
                logger.warning(f"No cards found in library for player {player.user_id}")
        
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
        
        game_state = self.game_state_repo.get_by_game_room_id(game_id)
        if game_state:
            self.game_state_repo.db.query(GameCard).filter(GameCard.game_state_id == game_state.id).delete()
            self.game_state_repo.db.query(PlayerGameState).filter(PlayerGameState.game_state_id == game_state.id).delete()
            self.game_state_repo.db.query(GameState).filter(GameState.id == game_state.id).delete()
            self.game_state_repo.db.commit()
        
        self.game_repo.update_status(game.id, GameStatus.WAITING)
        
        game = self._get_game_or_404(game_id)
        return await self._build_game_response(game)
    
    async def get_game_state(self, game_id: int, current_user: User) -> GameStateResponse:
        logger.info(f"Getting game state for game {game_id}, user {current_user.id}")
        
        game = self._get_game_or_404(game_id)
        logger.info(f"Game found: status={game.status}")
        
        player = self.player_repo.get_player(game.id, current_user.id)
        logger.info(f"Player in game: {player}, status: {player.status if player else 'None'}")
        
        if not player or player.status != PlayerStatus.ACCEPTED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not in this game"
            )
        
        game_state = self.game_state_repo.get_by_game_room_id(game_id)
        logger.info(f"Game state: {game_state}")
        
        if not game_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game state not found"
            )
        
        player_states = self.player_game_state_repo.get_by_game_state(game_state.id)
        
        active_user = self.game_state_repo.db.query(User).filter(User.id == game_state.active_player_id).first()
        
        player_responses = []
        for ps in player_states:
            user = self.game_state_repo.db.query(User).filter(User.id == ps.user_id).first()
            
            library = self.game_card_repo.get_player_cards_in_zone(ps.id, CardZone.LIBRARY)
            hand = self.game_card_repo.get_player_cards_in_zone(ps.id, CardZone.HAND)
            battlefield = self.game_card_repo.get_player_cards_in_zone(ps.id, CardZone.BATTLEFIELD)
            graveyard = self.game_card_repo.get_player_cards_in_zone(ps.id, CardZone.GRAVEYARD)
            exile = self.game_card_repo.get_player_cards_in_zone(ps.id, CardZone.EXILE)
            commander = self.game_card_repo.get_player_cards_in_zone(ps.id, CardZone.COMMANDER)
            
            is_current_user = ps.user_id == current_user.id
            
            player_responses.append(PlayerGameStateResponse(
                id=ps.id,
                user_id=ps.user_id,
                username=user.username if user else "Unknown",
                player_order=ps.player_order,
                is_active=ps.is_active,
                life_total=ps.life_total,
                poison_counters=ps.poison_counters,
                library=[GameCardResponse(**self._card_to_dict(c, is_current_user)) for c in library] if is_current_user else [],
                hand=[GameCardResponse(**self._card_to_dict(c, is_current_user)) for c in hand] if is_current_user else [GameCardResponse(**self._card_to_dict(c, False)) for c in hand],
                battlefield=[GameCardInBattlefieldResponse(**self._card_to_battlefield_dict(c)) for c in battlefield],
                graveyard=[GameCardResponse(**self._card_to_dict(c, True)) for c in graveyard],
                exile=[GameCardResponse(**self._card_to_dict(c, True)) for c in exile],
                commander=[GameCardResponse(**self._card_to_dict(c, True)) for c in commander],
            ))
        
        return GameStateResponse(
            id=game_state.id,
            game_room_id=game_state.game_room_id,
            current_turn=game_state.current_turn,
            active_player_id=game_state.active_player_id,
            active_player_username=active_user.username if active_user else "Unknown",
            current_phase=TurnPhase(game_state.current_phase),
            starting_player_id=game_state.starting_player_id,
            players=player_responses,
            created_at=game_state.created_at,
            logs=[GameLogResponse.model_validate(log) for log in self.game_log_repo.get_game_logs(game_state.id, 50)] if self.game_log_repo else [],
            game_mode=game.game_mode,
        )
    
    def _card_to_dict(self, card: GameCard, reveal: bool) -> dict:
        """Convert card to dict, hiding info if not revealed to this player"""
        data = {
            "id": card.id,
            "card_scryfall_id": card.card_scryfall_id,
            "card_name": card.card_name if reveal else "Unknown",
            "mana_cost": card.mana_cost if reveal else None,
            "cmc": card.cmc if reveal else None,
            "type_line": card.type_line if reveal else None,
            "oracle_text": card.oracle_text if reveal else None,
            "colors": card.colors if reveal else None,
            "power": card.power if reveal else None,
            "toughness": card.toughness if reveal else None,
            "keywords": card.keywords if reveal else None,
            "image_uris": card.image_uris if reveal else None,
            "card_faces": card.card_faces if reveal else None,
            "zone": CardZone(card.zone),
            "position": card.position,
            "is_tapped": card.is_tapped,
            "is_face_up": card.is_face_up if reveal else False,
            "battlefield_x": card.battlefield_x,
            "battlefield_y": card.battlefield_y,
            "is_attacking": card.is_attacking,
            "is_blocking": card.is_blocking,
            "damage_received": card.damage_received,
        }
        return data
    
    def _card_to_battlefield_dict(self, card: GameCard) -> dict:
        """Convert card to battlefield response dict"""
        return {
            "id": card.id,
            "card_scryfall_id": card.card_scryfall_id,
            "card_name": card.card_name,
            "mana_cost": card.mana_cost,
            "type_line": card.type_line,
            "oracle_text": card.oracle_text,
            "power": card.power,
            "toughness": card.toughness,
            "image_uris": card.image_uris,
            "card_faces": card.card_faces,
            "is_tapped": card.is_tapped,
            "is_face_up": card.is_face_up,
            "battlefield_x": card.battlefield_x,
            "battlefield_y": card.battlefield_y,
            "is_attacking": card.is_attacking,
            "is_blocking": card.is_blocking,
            "position": card.position,
        }
    
    async def draw_card(self, game_id: int, current_user: User) -> GameStateResponse:
        game = self._get_game_or_404(game_id)
        
        if game.status != GameStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Game is not in progress"
            )
        
        game_state = self.game_state_repo.get_by_game_room_id(game_id)
        if not game_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game state not found"
            )
        
        player_state = self.player_game_state_repo.get_by_game_state_and_user(
            game_state.id, current_user.id
        )
        if not player_state:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not in this game"
            )
        
        
        if self._use_engine(game):
            player_states = self.player_game_state_repo.get_by_game_state(game_state.id)
            cards_by_player = self._get_cards_by_player(player_states)
            usernames = self._get_usernames(player_states)
            
            engine = create_engine_from_db(game_state, player_states, cards_by_player, usernames)
            
            engine.draw_cards(player_state.user_id, 1)
            
            sync_engine_to_db(engine, self.game_state_repo.db)
            
            if self.game_log_repo:
                self.game_log_repo.create_log(
                    game_id=game_state.id,
                    player_id=current_user.id,
                    action_type="draw",
                    message=f"{current_user.username} drew a card"
                )
        else:
            self.game_card_repo.draw_cards(player_state.id, 1)
            
            if self.game_log_repo:
                self.game_log_repo.create_log(
                    game_id=game_state.id,
                    player_id=current_user.id,
                    action_type="draw",
                    message=f"{current_user.username} drew a card"
                )
        
        return await self.get_game_state(game_id, current_user)
    
    async def play_card(
        self, 
        game_id: int, 
        card_id: int, 
        current_user: User,
        target_zone: CardZone = CardZone.BATTLEFIELD,
        position: int = 0,
        battlefield_x: Optional[float] = None,
        battlefield_y: Optional[float] = None,
        side_index: Optional[int] = None,
    ) -> GameStateResponse:
        game = self._get_game_or_404(game_id)
        
        if game.status != GameStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Game is not in progress"
            )
        
        game_state = self.game_state_repo.get_by_game_room_id(game_id)
        if not game_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game state not found"
            )
        
        player_state = self.player_game_state_repo.get_by_game_state_and_user(
            game_state.id, current_user.id
        )
        if not player_state:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not in this game"
            )
        
        card = self.game_card_repo.get_card_by_id(card_id)
        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Card not found"
            )
        
        if card.player_game_state_id != player_state.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This card is not yours"
            )
        
        if self._use_engine(game):
            player_states = self.player_game_state_repo.get_by_game_state(game_state.id)
            cards_by_player = self._get_cards_by_player(player_states)
            usernames = self._get_usernames(player_states)
            
            engine = create_engine_from_db(game_state, player_states, cards_by_player, usernames)
            
            from_zone = card.zone
            
            if target_zone == CardZone.BATTLEFIELD:
                existing_cards = self.game_card_repo.get_player_cards_in_zone(player_state.id, CardZone.BATTLEFIELD)
                if existing_cards:
                    max_pos = max(c.position for c in existing_cards)
                else:
                    max_pos = 0
                position = max_pos + 1
            
            try:
                engine.play_card(
                    card_id,
                    target_zone,
                    position,
                    battlefield_x,
                    battlefield_y,
                    side_index
                )
            except TooManyLandsError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
            except InvalidPhaseForLandError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
            
            sync_engine_to_db(engine, self.game_state_repo.db)
            
            if self.game_log_repo:
                self.game_log_repo.create_log(
                    game_id=game_state.id,
                    player_id=current_user.id,
                    action_type="play",
                    message=f"{current_user.username} played {card.card_name} from {from_zone}",
                    card_id=card.id,
                    card_name=card.card_name,
                    from_zone=from_zone,
                    to_zone=target_zone.value
                )
        else:
            zone_cards = self.game_card_repo.get_player_cards_in_zone(player_state.id, target_zone)
            if zone_cards:
                max_position = sorted(zone_cards, key=lambda c: c.position if c else 1)[-1].position
            else:
                max_position = 1
            
            from_zone = card.zone
            
            self.game_card_repo.move_card(
                card_id, 
                target_zone, 
                max_position + 1,
                battlefield_x=battlefield_x,
                battlefield_y=battlefield_y
            )
            
            if self.game_log_repo:
                self.game_log_repo.create_log(
                    game_id=game_state.id,
                    player_id=current_user.id,
                    action_type="play",
                    message=f"{current_user.username} played {card.card_name} from {from_zone}",
                    card_id=card.id,
                    card_name=card.card_name,
                    from_zone=from_zone,
                    to_zone=target_zone.value
                )
        
        return await self.get_game_state(game_id, current_user)
    
    async def get_valid_plays(
        self,
        game_id: int,
        current_user: User
    ):
        from app.schemas.game_state import ValidPlayCard as SchemaValidPlayCard, ValidPlaysResponse
        from app.engine.exceptions import TooManyLandsError, InvalidPhaseForLandError
        
        game = self._get_game_or_404(game_id)
        
        if game.status != GameStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Game is not in progress"
            )
        
        game_state = self.game_state_repo.get_by_game_room_id(game_id)
        if not game_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game state not found"
            )
        
        player_state = self.player_game_state_repo.get_by_game_state_and_user(
            game_state.id, current_user.id
        )
        if not player_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Player not found in game"
            )
        
        player_states = self.player_game_state_repo.get_by_game_state(game_state.id)
        cards_by_player = self._get_cards_by_player(player_states)
        usernames = self._get_usernames(player_states)
        
        engine = create_engine_from_db(game_state, player_states, cards_by_player, usernames)
        
        valid_plays = engine.get_valid_plays(player_state.user_id)
        
        plays = [
            SchemaValidPlayCard(
                card_id=p['card_id'],
                card_name=p['card_name'],
                zone=p['zone'],
                mana_cost=p['mana_cost'],
                can_afford_mana=p['can_afford_mana'],
                needs_side_selection=p['needs_side_selection'],
                sides=p.get('sides')
            )
            for p in valid_plays['plays']
        ]
        
        return ValidPlaysResponse(
            current_phase=valid_plays['current_phase'],
            can_cast_spells=valid_plays['can_cast_spells'],
            can_play_land=valid_plays['can_play_land'],
            available_mana=valid_plays['available_mana'],
            untapped_lands_count=valid_plays['untapped_lands_count'],
            plays=plays
        )
    
    async def move_card(
        self,
        game_id: int,
        card_id: int,
        target_zone: CardZone,
        position: int,
        current_user: User
    ) -> GameStateResponse:
        game = self._get_game_or_404(game_id)
        
        if game.status != GameStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Game is not in progress"
            )
        
        game_state = self.game_state_repo.get_by_game_room_id(game_id)
        if not game_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game state not found"
            )
        
        player_state = self.player_game_state_repo.get_by_game_state_and_user(
            game_state.id, current_user.id
        )
        if not player_state:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not in this game"
            )
        
        card = self.game_card_repo.get_card_by_id(card_id)
        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Card not found"
            )
        
        if card.player_game_state_id != player_state.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This card is not yours"
            )
        
        if self._use_engine(game):
            player_states = self.player_game_state_repo.get_by_game_state(game_state.id)
            cards_by_player = self._get_cards_by_player(player_states)
            usernames = self._get_usernames(player_states)
            
            engine = create_engine_from_db(game_state, player_states, cards_by_player, usernames)
            
            from_zone = card.zone
            
            engine.move_card(
                card_id,
                target_zone,
                position,
                None,
                None
            )
            
            sync_engine_to_db(engine, self.game_state_repo.db)
            
            if self.game_log_repo:
                self.game_log_repo.create_log(
                    game_id=game_state.id,
                    player_id=current_user.id,
                    action_type="move",
                    message=f"{current_user.username} moved {card.card_name} from {from_zone} to {target_zone.value}",
                    card_id=card.id,
                    card_name=card.card_name,
                    from_zone=from_zone,
                    to_zone=target_zone.value
                )
        else:
            if target_zone in (CardZone.GRAVEYARD, CardZone.EXILE, CardZone.BATTLEFIELD):
                existing_cards = self.game_card_repo.get_player_cards_in_zone(
                    player_state.id, target_zone
                )
                position = len(existing_cards)
            
            from_zone = card.zone
            
            if card.zone == CardZone.BATTLEFIELD and target_zone != CardZone.BATTLEFIELD:
                if card.is_tapped:
                    card.is_tapped = False
                    self.game_card_repo.db.commit()
            
            self.game_card_repo.move_card(card_id, target_zone, position)
            
            if self.game_log_repo:
                self.game_log_repo.create_log(
                    game_id=game_state.id,
                    player_id=current_user.id,
                    action_type="move",
                    message=f"{current_user.username} moved {card.card_name} from {from_zone} to {target_zone.value}",
                    card_id=card.id,
                    card_name=card.card_name,
                    from_zone=from_zone,
                    to_zone=target_zone.value
                )
        
        return await self.get_game_state(game_id, current_user)
    
    async def move_cards(
        self,
        game_id: int,
        cards: list,
        current_user: User
    ) -> GameStateResponse:
        game = self._get_game_or_404(game_id)
        
        if game.status != GameStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Game is not in progress"
            )
        
        game_state = self.game_state_repo.get_by_game_room_id(game_id)
        if not game_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game state not found"
            )
        
        player_state = self.player_game_state_repo.get_by_game_state_and_user(
            game_state.id, current_user.id
        )
        if not player_state:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not in this game"
            )
        
        if self._use_engine(game):
            player_states = self.player_game_state_repo.get_by_game_state(game_state.id)
            cards_by_player = self._get_cards_by_player(player_states)
            usernames = self._get_usernames(player_states)
            
            engine = create_engine_from_db(game_state, player_states, cards_by_player, usernames)
            
            card_moves = [
                MoveCardInput(
                    card_id=card_move.card_id,
                    target_zone=card_move.target_zone,
                    position=card_move.position,
                    battlefield_x=None,
                    battlefield_y=None
                )
                for card_move in cards
            ]
            
            engine.move_cards(card_moves)
            
            sync_engine_to_db(engine, self.game_state_repo.db)
            
            if self.game_log_repo and cards:
                card_count = len(cards)
                if card_count == 1:
                    card = self.game_card_repo.get_card_by_id(cards[0].card_id)
                    if card:
                        from_zone = card.zone
                        self.game_log_repo.create_log(
                            game_id=game_state.id,
                            player_id=current_user.id,
                            action_type="move",
                            message=f"{current_user.username} moved {card.card_name} from {from_zone} to {cards[0].target_zone.value}",
                            card_id=card.id,
                            card_name=card.card_name,
                            from_zone=from_zone,
                            to_zone=cards[0].target_zone.value
                        )
                else:
                    self.game_log_repo.create_log(
                        game_id=game_state.id,
                        player_id=current_user.id,
                        action_type="move",
                        message=f"{current_user.username} moved {card_count} cards to {cards[0].target_zone.value}"
                    )
        else:
            for card_move in cards:
                card_id = card_move.card_id
                target_zone = card_move.target_zone
                position = card_move.position
                
                card = self.game_card_repo.get_card_by_id(card_id)
                if not card:
                    continue
                
                if card.player_game_state_id != player_state.id:
                    continue
                
                from_zone = card.zone
                
                if target_zone in (CardZone.GRAVEYARD, CardZone.EXILE, CardZone.BATTLEFIELD):
                    existing_cards = self.game_card_repo.get_player_cards_in_zone(
                        player_state.id, target_zone
                    )
                    position = len(existing_cards)
                
                if card.zone == CardZone.BATTLEFIELD and target_zone != CardZone.BATTLEFIELD:
                    if card.is_tapped:
                        card.is_tapped = False
                        self.game_card_repo.db.commit()
                
                self.game_card_repo.move_card(card_id, target_zone, position)
            
            if self.game_log_repo and cards:
                card_count = len(cards)
                if card_count == 1:
                    card = self.game_card_repo.get_card_by_id(cards[0].card_id)
                    if card:
                        from_zone = card.zone
                        self.game_log_repo.create_log(
                            game_id=game_state.id,
                            player_id=current_user.id,
                            action_type="move",
                            message=f"{current_user.username} moved {card.card_name} from {from_zone} to {cards[0].target_zone.value}",
                            card_id=card.id,
                            card_name=card.card_name,
                            from_zone=from_zone,
                            to_zone=cards[0].target_zone.value
                        )
                else:
                    self.game_log_repo.create_log(
                        game_id=game_state.id,
                        player_id=current_user.id,
                        action_type="move",
                        message=f"{current_user.username} moved {card_count} cards to {cards[0].target_zone.value}"
                    )
        
        return await self.get_game_state(game_id, current_user)
    
    async def tap_card(
        self,
        game_id: int,
        card_id: int,
        current_user: User
    ) -> GameStateResponse:
        game = self._get_game_or_404(game_id)
        
        if game.status != GameStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Game is not in progress"
            )
        
        game_state = self.game_state_repo.get_by_game_room_id(game_id)
        if not game_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game state not found"
            )
        
        player_state = self.player_game_state_repo.get_by_game_state_and_user(
            game_state.id, current_user.id
        )
        if not player_state:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not in this game"
            )
        
        card = self.game_card_repo.get_card_by_id(card_id)
        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Card not found"
            )
        
        if card.player_game_state_id != player_state.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This card is not yours"
            )
        
        if self._use_engine(game):
            player_states = self.player_game_state_repo.get_by_game_state(game_state.id)
            cards_by_player = self._get_cards_by_player(player_states)
            usernames = self._get_usernames(player_states)
            
            engine = create_engine_from_db(game_state, player_states, cards_by_player, usernames)
            
            was_tapped = card.is_tapped
            
            engine.tap_card(card_id)
            
            sync_engine_to_db(engine, self.game_state_repo.db)
            
            if self.game_log_repo:
                tap_action = "untapped" if was_tapped else "tapped"
                self.game_log_repo.create_log(
                    game_id=game_state.id,
                    player_id=current_user.id,
                    action_type="tap",
                    message=f"{current_user.username} {tap_action} {card.card_name}",
                    card_id=card.id,
                    card_name=card.card_name
                )
        else:
            was_tapped = card.is_tapped
            
            self.game_card_repo.toggle_tapped(card_id)
            
            if self.game_log_repo:
                tap_action = "untapped" if was_tapped else "tapped"
                self.game_log_repo.create_log(
                    game_id=game_state.id,
                    player_id=current_user.id,
                    action_type="tap",
                    message=f"{current_user.username} {tap_action} {card.card_name}",
                    card_id=card.id,
                    card_name=card.card_name
                )
        
        return await self.get_game_state(game_id, current_user)
    
    async def update_battlefield_position(
        self,
        game_id: int,
        card_id: int,
        x: float,
        y: float,
        current_user: User
    ) -> GameStateResponse:
        game = self._get_game_or_404(game_id)
        
        if game.status != GameStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Game is not in progress"
            )
        
        game_state = self.game_state_repo.get_by_game_room_id(game_id)
        if not game_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game state not found"
            )
        
        player_state = self.player_game_state_repo.get_by_game_state_and_user(
            game_state.id, current_user.id
        )
        if not player_state:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not in this game"
            )
        
        card = self.game_card_repo.get_card_by_id(card_id)
        if not card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Card not found"
            )
        
        if card.player_game_state_id != player_state.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This card is not yours"
            )
        
        if card.zone != CardZone.BATTLEFIELD.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Card is not on the battlefield"
            )
        
        self.game_card_repo.update_battlefield_position(card_id, x, y)
        
        return await self.get_game_state(game_id, current_user)
    
    async def pass_priority(
        self,
        game_id: int,
        current_user: User
    ) -> GameStateResponse:
        game = self._get_game_or_404(game_id)
        
        if game.status != GameStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Game is not in progress"
            )
        
        game_state = self.game_state_repo.get_by_game_room_id(game_id)
        if not game_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game state not found"
            )
        
        player_state = self.player_game_state_repo.get_by_game_state_and_user(
            game_state.id, current_user.id
        )
        if not player_state:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not in this game"
            )
        
        if player_state.user_id != game_state.active_player_id:
            if game_state.current_phase != TurnPhase.CLEANUP.value:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only the active player can pass priority"
                )
        
        if self._use_engine(game):
            player_states = self.player_game_state_repo.get_by_game_state(game_state.id)
            cards_by_player = self._get_cards_by_player(player_states)
            usernames = self._get_usernames(player_states)
            
            engine = create_engine_from_db(game_state, player_states, cards_by_player, usernames)
            
            result = engine.pass_priority()
            
            sync_engine_to_db(engine, self.game_state_repo.db)
            
            sio = get_sio()
            if sio:
                await sio.emit("game_state_updated", {"game_id": game_id}, room=f"game_{game_id}")
            
            if self.game_log_repo:
                if result.turn_changed:
                    self.game_log_repo.create_log(
                        game_id=game_state.id,
                        player_id=current_user.id,
                        action_type="turn_change",
                        message=f"→ Turn {engine.game_state.current_turn} - {engine.game_state.current_phase.value.replace('_', ' ').title()}"
                    )
                else:
                    self.game_log_repo.create_log(
                        game_id=game_state.id,
                        player_id=current_user.id,
                        action_type="phase_change",
                        message=f"{current_user.username} passed priority → {engine.game_state.current_phase.value.replace('_', ' ').title()}"
                    )
        else:
            phase_order = [
                TurnPhase.UNTAP,
                TurnPhase.UPKEEP,
                TurnPhase.DRAW,
                TurnPhase.MAIN1,
                TurnPhase.COMBAT_START,
                TurnPhase.COMBAT_ATTACK,
                TurnPhase.COMBAT_BLOCK,
                TurnPhase.COMBAT_DAMAGE,
                TurnPhase.COMBAT_END,
                TurnPhase.MAIN2,
                TurnPhase.END,
                TurnPhase.CLEANUP,
            ]
            
            current_phase = TurnPhase(game_state.current_phase)
            current_index = phase_order.index(current_phase)
            
            if current_index < len(phase_order) - 1:
                next_phase = phase_order[current_index + 1]
                game_state.current_phase = next_phase.value
                player_states = None
                is_turn_change = False
            else:
                player_states = self.player_game_state_repo.get_by_game_state(game_state.id)
                current_player_state = next((p for p in player_states if p.user_id == game_state.active_player_id), None)
                
                if current_player_state:
                    current_order = current_player_state.player_order
                    next_order = (current_order + 1) % len(player_states)
                    next_player_state = next((p for p in player_states if p.player_order == next_order), None)
                    
                    if next_player_state:
                        game_state.active_player_id = next_player_state.user_id
                        game_state.current_turn += 1
                        game_state.current_phase = TurnPhase.UNTAP.value
                        
                        for p in player_states:
                            p.is_active = (p.user_id == next_player_state.user_id)
                
                next_phase = TurnPhase(game_state.current_phase)
                is_turn_change = True
            
            self.game_state_repo.db.commit()
            
            if self.game_log_repo:
                if is_turn_change:
                    self.game_log_repo.create_log(
                        game_id=game_state.id,
                        player_id=current_user.id,
                        action_type="turn_change",
                        message=f"→ Turn {game_state.current_turn} - {next_phase.value.replace('_', ' ').title()}"
                    )
                else:
                    self.game_log_repo.create_log(
                        game_id=game_state.id,
                        player_id=current_user.id,
                        action_type="phase_change",
                        message=f"{current_user.username} passed priority → {next_phase.value.replace('_', ' ').title()}"
                    )
        
        return await self.get_game_state(game_id, current_user)

    async def untap_all(
        self,
        game_id: int,
        current_user: User
    ) -> GameStateResponse:
        game = self._get_game_or_404(game_id)
        
        if game.status != GameStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Game is not in progress"
            )
        
        game_state = self.game_state_repo.get_by_game_room_id(game_id)
        if not game_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game state not found"
            )
        
        player_state = self.player_game_state_repo.get_by_game_state_and_user(
            game_state.id, current_user.id
        )
        if not player_state:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not in this game"
            )
        
        if self._use_engine(game):
            player_states = self.player_game_state_repo.get_by_game_state(game_state.id)
            cards_by_player = self._get_cards_by_player(player_states)
            usernames = self._get_usernames(player_states)
            
            engine = create_engine_from_db(game_state, player_states, cards_by_player, usernames)
            
            engine.untap_all(player_state.user_id)
            
            sync_engine_to_db(engine, self.game_state_repo.db)
            
            if self.game_log_repo:
                self.game_log_repo.create_log(
                    game_id=game_state.id,
                    player_id=current_user.id,
                    action_type="untap_all",
                    message=f"{current_user.username} untaps all"
                )
        else:
            battlefield_cards = self.game_card_repo.get_player_cards_in_zone(
                player_state.id, CardZone.BATTLEFIELD
            )
            
            for card in battlefield_cards:
                if card.is_tapped:
                    card.is_tapped = False
            
            self.game_card_repo.db.commit()
            
            if self.game_log_repo:
                self.game_log_repo.create_log(
                    game_id=game_state.id,
                    player_id=current_user.id,
                    action_type="untap_all",
                    message=f"{current_user.username} untaps all"
                )
        
        return await self.get_game_state(game_id, current_user)
    
    async def adjust_life(
        self,
        game_id: int,
        amount: int,
        current_user: User
    ) -> GameStateResponse:
        game = self._get_game_or_404(game_id)
        
        if game.status != GameStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Game is not in progress"
            )
        
        game_state = self.game_state_repo.get_by_game_room_id(game_id)
        if not game_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game state not found"
            )
        
        player_state = self.player_game_state_repo.get_by_game_state_and_user(
            game_state.id, current_user.id
        )
        if not player_state:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not in this game"
            )
        
        if self._use_engine(game):
            player_states = self.player_game_state_repo.get_by_game_state(game_state.id)
            cards_by_player = self._get_cards_by_player(player_states)
            usernames = self._get_usernames(player_states)
            
            engine = create_engine_from_db(game_state, player_states, cards_by_player, usernames)
            
            engine.adjust_life(player_state.user_id, amount)
            
            sync_engine_to_db(engine, self.game_state_repo.db)
            
            if self.game_log_repo:
                if amount > 0:
                    message = f"{current_user.username} gained {amount} life"
                else:
                    message = f"{current_user.username} lost {abs(amount)} life"
                self.game_log_repo.create_log(
                    game_id=game_state.id,
                    player_id=current_user.id,
                    action_type="adjust_life",
                    message=message
                )
        else:
            player_state.life_total += amount
            if player_state.life_total < 0:
                player_state.life_total = 0
            
            self.player_game_state_repo.db.commit()
            
            if self.game_log_repo:
                if amount > 0:
                    message = f"{current_user.username} gained {amount} life"
                else:
                    message = f"{current_user.username} lost {abs(amount)} life"
                self.game_log_repo.create_log(
                    game_id=game_state.id,
                    player_id=current_user.id,
                    action_type="adjust_life",
                    message=message
                )
        
        return await self.get_game_state(game_id, current_user)
    
    async def add_mana(
        self,
        game_id: int,
        color: str,
        amount: int,
        current_user: User
    ) -> GameStateResponse:
        game = self._get_game_or_404(game_id)
        
        if game.status != GameStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Game is not in progress"
            )
        
        game_state = self.game_state_repo.get_by_game_room_id(game_id)
        if not game_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game state not found"
            )
        
        player_state = self.player_game_state_repo.get_by_game_state_and_user(
            game_state.id, current_user.id
        )
        if not player_state:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not in this game"
            )
        
        try:
            mana_color = ManaColor(color)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid mana color: {color}"
            )
        
        if self._use_engine(game):
            player_states = self.player_game_state_repo.get_by_game_state(game_state.id)
            cards_by_player = self._get_cards_by_player(player_states)
            usernames = self._get_usernames(player_states)
            
            engine = create_engine_from_db(game_state, player_states, cards_by_player, usernames)
            
            engine.add_mana(player_state.user_id, mana_color, amount)
            
            sync_engine_to_db(engine, self.game_state_repo.db)
            
            if self.game_log_repo:
                self.game_log_repo.create_log(
                    game_id=game_state.id,
                    player_id=current_user.id,
                    action_type="add_mana",
                    message=f"{current_user.username} added {amount} {mana_color.value} mana"
                )
        else:
            mana_field = f"{mana_color.value}_mana"
            if hasattr(player_state, mana_field):
                setattr(player_state, mana_field, getattr(player_state, mana_field) + amount)
                self.player_game_state_repo.db.commit()
                
                if self.game_log_repo:
                    self.game_log_repo.create_log(
                        game_id=game_state.id,
                        player_id=current_user.id,
                        action_type="add_mana",
                        message=f"{current_user.username} added {amount} {mana_color.value} mana"
                    )
        
        return await self.get_game_state(game_id, current_user)
    
    async def get_game_logs(
        self,
        game_id: int,
        limit: int = 50
    ) -> List[GameLogResponse]:
        self._get_game_or_404(game_id)
        
        game_state = self.game_state_repo.get_by_game_room_id(game_id)
        if not game_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game state not found"
            )
        
        if not self.game_log_repo:
            return []
        
        logs = self.game_log_repo.get_game_logs(game_state.id, limit)
        
        return [GameLogResponse.model_validate(log) for log in logs]
    
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
            game_mode=game.game_mode,
            status=game.status,
            players=player_responses,
            created_at=game.created_at,
        )


def get_game_service(db: Session = Depends(get_db)) -> GameService:
    return GameService.create_with_repositories(db)
