from fastapi import APIRouter, Depends, status
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
from app.services.game_service import get_game_service, GameService
from app.socket import get_sio
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
