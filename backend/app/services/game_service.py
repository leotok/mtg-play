from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from app.core.database import get_db
from app.models.user import User
from app.models.game import GameRoom, GameRoomPlayer, GameStatus, PlayerStatus, TurnPhase, CardZone
from app.models.game_state import GameState, PlayerGameState, GameCard
from app.repositories.game import GameRoomRepository, GameRoomPlayerRepository
from app.repositories import DeckRepository
from app.repositories.game_state import GameStateRepository, PlayerGameStateRepository, GameCardRepository
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
)
from app.services.scryfall import get_scryfall_service
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
    ):
        self.game_repo = game_repo
        self.player_repo = player_repo
        self.deck_repo = deck_repo
        self.game_state_repo = game_state_repo
        self.player_game_state_repo = player_game_state_repo
        self.game_card_repo = game_card_repo
    
    @classmethod
    def create_with_repositories(cls, db: Session):
        game_repo = GameRoomRepository(db)
        player_repo = GameRoomPlayerRepository(db)
        deck_repo = DeckRepository(db)
        game_state_repo = GameStateRepository(db)
        player_game_state_repo = PlayerGameStateRepository(db)
        game_card_repo = GameCardRepository(db)
        return cls(
            game_repo, 
            player_repo, 
            deck_repo,
            game_state_repo,
            player_game_state_repo,
            game_card_repo,
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
                hand=[GameCardResponse(**self._card_to_dict(c, is_current_user)) for c in hand] if is_current_user else [],
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
        
        self.game_card_repo.draw_cards(player_state.id, 1)
        
        return await self.get_game_state(game_id, current_user)
    
    async def play_card(
        self, 
        game_id: int, 
        card_id: int, 
        current_user: User,
        target_zone: CardZone = CardZone.BATTLEFIELD
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
        
        if card.zone != CardZone.HAND.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Card is not in hand"
            )
        
        hand_cards = self.game_card_repo.get_player_cards_in_zone(player_state.id, CardZone.HAND)
        new_position = len(self.game_card_repo.get_player_cards_in_zone(player_state.id, target_zone))
        
        self.game_card_repo.move_card(card_id, target_zone, new_position)
        
        return await self.get_game_state(game_id, current_user)
    
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
        
        self.game_card_repo.move_card(card_id, target_zone, position)
        
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
        
        self.game_card_repo.toggle_tapped(card_id)
        
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
        
        battlefield_cards = self.game_card_repo.get_player_cards_in_zone(
            player_state.id, CardZone.BATTLEFIELD
        )
        
        for card in battlefield_cards:
            if card.is_tapped:
                card.is_tapped = False
        
        self.game_card_repo.db.commit()
        
        return await self.get_game_state(game_id, current_user)
    
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
