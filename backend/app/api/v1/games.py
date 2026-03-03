from fastapi import APIRouter, Depends, status, HTTPException
from typing import List

from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.game import (
    GameRoomCreate,
    GameRoomResponse,
    GameRoomListItem,
    JoinResponse,
    DeckSelectionRequest,
)
from app.schemas.game_state import (
    GameStateResponse,
    PlayCardRequest,
    MoveCardRequest,
    MoveCardsRequest,
    BattlefieldPositionRequest,
    AdjustLifeRequest,
    AddManaRequest,
    GameLogResponse,
    ChooseCardSideResponse,
    CardSideOption,
    ValidPlaysResponse,
)
from app.services.game_service import get_game_service, GameService
from app.socket import get_sio
from app.engine.exceptions import GameActionError
from app.engine.models import card_needs_side_selection, get_card_sides_info
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/games", tags=["games"])


@router.post("", response_model=GameRoomResponse, status_code=status.HTTP_201_CREATED)
async def create_game(
    game_data: GameRoomCreate,
    current_user: User = Depends(get_current_user),
    game_service: GameService = Depends(get_game_service)
):
    """Create a new game room"""
    game = await game_service.create_game(game_data, current_user)
    
    try:
        sio_instance = get_sio()
        await sio_instance.emit('game_created', {
            'game_id': game.id,
            'name': game.name,
        })
    except Exception as e:
        logger.error(f'Failed to emit WebSocket event: {e}')
    
    return game


@router.get("", response_model=List[GameRoomListItem])
def list_games(
    current_user: User = Depends(get_current_user),
    game_service: GameService = Depends(get_game_service)
):
    """List public games and user's games"""
    return game_service.list_games(current_user)


@router.get("/{game_id}", response_model=GameRoomResponse)
async def get_game(
    game_id: int,
    current_user: User = Depends(get_current_user),
    game_service: GameService = Depends(get_game_service)
):
    """Get a specific game room"""
    return await game_service.get_game(game_id, current_user)


@router.get("/invite/{invite_code}", response_model=GameRoomResponse)
async def get_game_by_invite(
    invite_code: str,
    current_user: User = Depends(get_current_user),
    game_service: GameService = Depends(get_game_service)
):
    """Get a game room by invite code"""
    return await game_service.get_game_by_invite(invite_code, current_user)


@router.post("/{game_id}/join", response_model=JoinResponse)
async def join_game(
    game_id: int,
    current_user: User = Depends(get_current_user),
    game_service: GameService = Depends(get_game_service)
):
    """Request to join a game"""
    result = game_service.join_game(game_id, current_user)
    
    try:
        sio_instance = get_sio()
        # Emit to room for host and other players
        await sio_instance.emit('player_join_request', {
            'game_id': game_id,
            'user_id': current_user.id,
            'username': current_user.username,
        }, room=f'game_{game_id}')
        logger.info(f'Emitted player_join_request for user {current_user.id} in game {game_id} to room game_{game_id}')
    except Exception as e:
        logger.error(f'Failed to emit WebSocket event: {e}')
    
    return result


@router.post("/{game_id}/accept/{player_id}", response_model=GameRoomResponse)
async def accept_player(
    game_id: int,
    player_id: int,
    current_user: User = Depends(get_current_user),
    game_service: GameService = Depends(get_game_service)
):
    """Accept a player's join request (host only)"""
    game = await game_service.accept_player(game_id, player_id, current_user)
    
    try:
        sio_instance = get_sio()
        await sio_instance.emit('player_accepted', {
            'game_id': game_id,
            'user_id': player_id,
        }, room=f'game_{game_id}')
        logger.info(f'Emitted player_accepted for user {player_id} in game {game_id}')
    except Exception as e:
        logger.error(f'Failed to emit WebSocket event: {e}')
    
    return game


@router.post("/{game_id}/reject/{player_id}", response_model=GameRoomResponse)
async def reject_player(
    game_id: int,
    player_id: int,
    current_user: User = Depends(get_current_user),
    game_service: GameService = Depends(get_game_service)
):
    """Reject a player's join request (host only)"""
    game = await game_service.reject_player(game_id, player_id, current_user)
    
    try:
        sio_instance = get_sio()
        await sio_instance.emit('player_rejected', {
            'game_id': game_id,
            'user_id': player_id,
        }, room=f'game_{game_id}')
        logger.info(f'Emitted player_rejected for user {player_id} in game {game_id}')
    except Exception as e:
        logger.error(f'Failed to emit WebSocket event: {e}')
    
    return game


@router.delete("/{game_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_game(
    game_id: int,
    current_user: User = Depends(get_current_user),
    game_service: GameService = Depends(get_game_service)
):
    """Leave a game"""
    game_service.leave_game(game_id, current_user)
    
    try:
        sio_instance = get_sio()
        await sio_instance.emit('player_left', {
            'game_id': game_id,
            'user_id': current_user.id,
        }, room=f'game_{game_id}')
        logger.info(f'Emitted player_left for user {current_user.id} in game {game_id}')
    except Exception as e:
        logger.error(f'Failed to emit WebSocket event: {e}')


@router.delete("/{game_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_game(
    game_id: int,
    current_user: User = Depends(get_current_user),
    game_service: GameService = Depends(get_game_service)
):
    """Delete a game (host only)"""
    game_service.delete_game(game_id, current_user)


@router.post("/{game_id}/start", response_model=GameRoomResponse)
async def start_game(
    game_id: int,
    current_user: User = Depends(get_current_user),
    game_service: GameService = Depends(get_game_service)
):
    """Start a game (host only)"""
    game = await game_service.start_game(game_id, current_user)
    
    try:
        sio_instance = get_sio()
        await sio_instance.emit('game_started', {
            'game_id': game_id,
        }, room=f'game_{game_id}')
        logger.info(f'Emitted game_started for game {game_id}')
    except Exception as e:
        logger.error(f'Failed to emit WebSocket event: {e}')
    
    return game


@router.post("/{game_id}/stop", response_model=GameRoomResponse)
async def stop_game(
    game_id: int,
    current_user: User = Depends(get_current_user),
    game_service: GameService = Depends(get_game_service)
):
    """Stop a game and return to waiting state (host only)"""
    game = await game_service.stop_game(game_id, current_user)
    
    try:
        sio_instance = get_sio()
        await sio_instance.emit('game_stopped', {
            'game_id': game_id,
        }, room=f'game_{game_id}')
        logger.info(f'Emitted game_stopped for game {game_id}')
    except Exception as e:
        logger.error(f'Failed to emit WebSocket event: {e}')
    
    return game


@router.post("/{game_id}/select-deck", response_model=GameRoomResponse)
async def select_deck(
    game_id: int,
    deck_selection: DeckSelectionRequest,
    current_user: User = Depends(get_current_user),
    game_service: GameService = Depends(get_game_service)
):
    """Select a deck for the game"""
    game = await game_service.select_deck(game_id, deck_selection, current_user)
    
    try:
        sio_instance = get_sio()
        await sio_instance.emit('deck_selected', {
            'game_id': game_id,
            'user_id': current_user.id,
            'deck_id': deck_selection.deck_id,
        }, room=f'game_{game_id}')
    except Exception as e:
        logger.error(f'Failed to emit WebSocket event: {e}')
    
    return game


@router.get("/{game_id}/state", response_model=GameStateResponse)
async def get_game_state(
    game_id: int,
    current_user: User = Depends(get_current_user),
    game_service: GameService = Depends(get_game_service)
):
    """Get current game state"""
    return await game_service.get_game_state(game_id, current_user)


@router.post("/{game_id}/draw", response_model=GameStateResponse)
async def draw_card(
    game_id: int,
    current_user: User = Depends(get_current_user),
    game_service: GameService = Depends(get_game_service)
):
    """Draw a card from library"""
    return await game_service.draw_card(game_id, current_user)


@router.post("/{game_id}/play-card")
async def play_card(
    game_id: int,
    request: PlayCardRequest,
    current_user: User = Depends(get_current_user),
    game_service: GameService = Depends(get_game_service)
):
    """Play a card from hand to battlefield"""
    try:
        game_state = await game_service.get_game_state(game_id, current_user)
        
        if request.side_index is None:
            current_user_state = None
            for player in game_state.players:
                if player.user_id == current_user.id:
                    current_user_state = player
                    break
            
            if current_user_state:
                all_cards = (
                    current_user_state.hand + 
                    current_user_state.commander
                )
                card = next((c for c in all_cards if c.id == request.card_id), None)
                
                if card and card_needs_side_selection(card):
                    sides_info = get_card_sides_info(card)
                    sides = [
                        CardSideOption(
                            side_index=s['side_index'],
                            name=s['name'],
                            mana_cost=s['mana_cost'],
                            type_line=s['type_line'],
                            image_url=s['image_url'],
                        )
                        for s in sides_info
                    ]
                    return ChooseCardSideResponse(
                        card_id=card.id,
                        card_name=card.card_name,
                        sides=sides
                    )
        
        result = await game_service.play_card(
            game_id, 
            request.card_id, 
            current_user, 
            request.target_zone,
            request.position,
            request.battlefield_x,
            request.battlefield_y,
            request.side_index
        )
        return result
    except GameActionError as e:
        error_type = type(e).__name__
        code_map = {
            "InvalidCardError": "INVALID_CARD",
            "InvalidZoneError": "INVALID_ZONE",
            "InsufficientResourcesError": "INSUFFICIENT_RESOURCES",
            "EmptyLibraryError": "EMPTY_LIBRARY",
            "InvalidPhaseError": "INVALID_PHASE",
        }
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_type": error_type,
                "message": str(e),
                "code": code_map.get(error_type, "UNKNOWN_ERROR"),
            }
        )


@router.post("/{game_id}/move-card", response_model=GameStateResponse)
async def move_card(
    game_id: int,
    request: MoveCardRequest,
    current_user: User = Depends(get_current_user),
    game_service: GameService = Depends(get_game_service)
):
    """Move card between zones"""
    return await game_service.move_card(
        game_id,
        request.card_id,
        request.target_zone,
        request.position,
        current_user
    )


@router.post("/{game_id}/move-cards", response_model=GameStateResponse)
async def move_cards(
    game_id: int,
    request: MoveCardsRequest,
    current_user: User = Depends(get_current_user),
    game_service: GameService = Depends(get_game_service)
):
    """Move multiple cards between zones"""
    return await game_service.move_cards(
        game_id,
        request.cards,
        current_user
    )


@router.post("/{game_id}/tap/{card_id}", response_model=GameStateResponse)
async def tap_card(
    game_id: int,
    card_id: int,
    current_user: User = Depends(get_current_user),
    game_service: GameService = Depends(get_game_service)
):
    """Tap or untap a card"""
    return await game_service.tap_card(game_id, card_id, current_user)


@router.post("/{game_id}/battlefield-position", response_model=GameStateResponse)
async def update_battlefield_position(
    game_id: int,
    request: BattlefieldPositionRequest,
    current_user: User = Depends(get_current_user),
    game_service: GameService = Depends(get_game_service)
):
    """Update card position on battlefield"""
    return await game_service.update_battlefield_position(
        game_id,
        request.card_id,
        request.x,
        request.y,
        current_user
    )


@router.post("/{game_id}/untap-all", response_model=GameStateResponse)
async def untap_all(
    game_id: int,
    current_user: User = Depends(get_current_user),
    game_service: GameService = Depends(get_game_service)
):
    """Untap all of the current player's cards"""
    return await game_service.untap_all(game_id, current_user)


@router.post("/{game_id}/pass-priority", response_model=GameStateResponse)
async def pass_priority(
    game_id: int,
    current_user: User = Depends(get_current_user),
    game_service: GameService = Depends(get_game_service)
):
    """Pass priority and advance the game phase"""
    return await game_service.pass_priority(game_id, current_user)


@router.post("/{game_id}/adjust-life", response_model=GameStateResponse)
async def adjust_life(
    game_id: int,
    request: AdjustLifeRequest,
    current_user: User = Depends(get_current_user),
    game_service: GameService = Depends(get_game_service)
):
    """Adjust the current player's life total"""
    return await game_service.adjust_life(game_id, request.amount, current_user)


@router.get("/{game_id}/logs", response_model=List[GameLogResponse])
async def get_game_logs(
    game_id: int,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    game_service: GameService = Depends(get_game_service)
):
    """Get game log entries"""
    return await game_service.get_game_logs(game_id, limit)


@router.post("/{game_id}/add-mana", response_model=GameStateResponse)
async def add_mana(
    game_id: int,
    request: AddManaRequest,
    current_user: User = Depends(get_current_user),
    game_service: GameService = Depends(get_game_service)
):
    """Add mana to the current player's mana pool"""
    return await game_service.add_mana(game_id, request.color, request.amount, current_user)


@router.get("/{game_id}/valid-plays", response_model=ValidPlaysResponse)
async def get_valid_plays(
    game_id: int,
    current_user: User = Depends(get_current_user),
    game_service: GameService = Depends(get_game_service)
):
    """Get all valid plays for the current player"""
    return await game_service.get_valid_plays(game_id, current_user)
