from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import secrets
import string
import asyncio

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.deck import Deck
from app.models.game import GameRoom, GameRoomPlayer, GameStatus, PlayerStatus, PowerBracket
from app.schemas.game import (
    GameRoomCreate,
    GameRoomUpdate,
    GameRoomResponse,
    GameRoomListItem,
    JoinResponse,
    GameRoomPlayerResponse,
    DeckInfo,
    DeckSelectionRequest,
)
from app.socket import get_sio
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/games", tags=["games"])


def generate_invite_code(length: int = 8) -> str:
    """Generate a unique invite code"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


def get_game_room_or_404(db: Session, game_id: int) -> GameRoom:
    """Get a game room by ID or raise 404"""
    game = db.query(GameRoom).filter(GameRoom.id == game_id).first()
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game room not found"
        )
    return game


def is_host(db: Session, game: GameRoom, user_id: int) -> bool:
    """Check if user is the host"""
    return game.host_id == user_id


def is_player(db: Session, game: GameRoom, user_id: int) -> GameRoomPlayer | None:
    """Check if user is a player in the game"""
    return db.query(GameRoomPlayer).filter(
        GameRoomPlayer.game_room_id == game.id,
        GameRoomPlayer.user_id == user_id
    ).first()


@router.post("", response_model=GameRoomResponse, status_code=status.HTTP_201_CREATED)
async def create_game(
    game_data: GameRoomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new game room"""
    # Generate unique invite code
    invite_code = generate_invite_code()
    while db.query(GameRoom).filter(GameRoom.invite_code == invite_code).first():
        invite_code = generate_invite_code()

    # Create game room
    game = GameRoom(
        name=game_data.name,
        description=game_data.description,
        host_id=current_user.id,
        invite_code=invite_code,
        is_public=game_data.is_public,
        max_players=game_data.max_players,
        power_bracket=game_data.power_bracket,
        status=GameStatus.WAITING
    )
    db.add(game)
    db.flush()

    # Add host as first player (automatically accepted)
    host_player = GameRoomPlayer(
        game_room_id=game.id,
        user_id=current_user.id,
        status=PlayerStatus.ACCEPTED,
        is_host=True
    )
    db.add(host_player)
    db.commit()
    db.refresh(game)

    return await _build_game_response(game, db)


@router.get("", response_model=List[GameRoomListItem])
def list_games(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List public games and user's games"""
    # Get public games that are waiting
    public_games = db.query(GameRoom).filter(
        GameRoom.is_public == True,
        GameRoom.status == GameStatus.WAITING
    ).all()

    # Get games where user is a participant
    user_games = db.query(GameRoom).join(GameRoomPlayer).filter(
        GameRoomPlayer.user_id == current_user.id
    ).all()

    # Combine and deduplicate
    all_games = {game.id: game for game in public_games + user_games}

    result = []
    for game in all_games.values():
        current_players = db.query(GameRoomPlayer).filter(
            GameRoomPlayer.game_room_id == game.id,
            GameRoomPlayer.status == PlayerStatus.ACCEPTED
        ).count()

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
            created_at=game.created_at
        ))

    return result


@router.get("/{game_id}", response_model=GameRoomResponse)
async def get_game(
    game_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific game room"""
    game = get_game_room_or_404(db, game_id)
    
    # Check if user is a participant or it's public
    player = is_player(db, game, current_user.id)
    if not player and not game.is_public and not is_host(db, game, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this game"
        )
    
    return await _build_game_response(game, db)


@router.get("/invite/{invite_code}", response_model=GameRoomResponse)
async def get_game_by_invite(
    invite_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a game room by invite code"""
    game = db.query(GameRoom).filter(GameRoom.invite_code == invite_code).first()
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game not found"
        )
    
    return await _build_game_response(game, db)


@router.post("/{game_id}/join", response_model=JoinResponse)
async def join_game(
    game_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Request to join a game"""
    game = get_game_room_or_404(db, game_id)

    # Check if user is already a player
    existing_player = is_player(db, game, current_user.id)
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

    # Check if game is full
    current_players = db.query(GameRoomPlayer).filter(
        GameRoomPlayer.game_room_id == game.id,
        GameRoomPlayer.status == PlayerStatus.ACCEPTED
    ).count()

    if current_players >= game.max_players:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Game is full"
        )

    # Check if game is still waiting
    if game.status != GameStatus.WAITING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Game has already started"
        )

    # Both public and private games require host approval
    player_status = PlayerStatus.PENDING

    # Create player entry
    player = GameRoomPlayer(
        game_room_id=game.id,
        user_id=current_user.id,
        status=player_status,
        is_host=False
    )
    db.add(player)
    db.commit()
    db.refresh(player)

    # Emit WebSocket event to notify players in the game room
    try:
        sio_instance = get_sio()
        # Always emit join request - both public and private games require host approval
        await sio_instance.emit('player_join_request', {
            'game_id': game.id,
            'user_id': current_user.id,
            'username': current_user.username,
        }, room=f'game_{game.id}')
        logger.info(f'Emitted player_join_request for user {current_user.id} in game {game.id}')
    except Exception as e:
        logger.error(f'Failed to emit WebSocket event: {e}')

    return JoinResponse(
        message="Join request sent to host",
        game_room=None
    )


@router.post("/{game_id}/accept/{player_id}", response_model=GameRoomResponse)
async def accept_player(
    game_id: int,
    player_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Accept a player's join request (host only)"""
    game = get_game_room_or_404(db, game_id)

    # Verify host
    if not is_host(db, game, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the host can accept players"
        )

    # Get player
    player = db.query(GameRoomPlayer).filter(
        GameRoomPlayer.id == player_id,
        GameRoomPlayer.game_room_id == game.id
    ).first()

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

    # Check if game is full
    current_players = db.query(GameRoomPlayer).filter(
        GameRoomPlayer.game_room_id == game.id,
        GameRoomPlayer.status == PlayerStatus.ACCEPTED
    ).count()

    if current_players >= game.max_players:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Game is full"
        )

    # Accept player
    player.status = PlayerStatus.ACCEPTED
    db.commit()
    db.refresh(player)

    # Get player username
    player_user = db.query(User).filter(User.id == player.user_id).first()

    # Emit WebSocket event
    try:
        sio_instance = get_sio()
        await sio_instance.emit('player_accepted', {
            'game_id': game.id,
            'user_id': player.user_id,
            'username': player_user.username if player_user else 'Unknown',
        }, room=f'game_{game.id}')
        logger.info(f'Emitted player_accepted for user {player.user_id} in game {game.id}')
    except Exception as e:
        logger.error(f'Failed to emit WebSocket event: {e}')

    return await _build_game_response(game, db)


@router.post("/{game_id}/reject/{player_id}", response_model=GameRoomResponse)
async def reject_player(
    game_id: int,
    player_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reject a player's join request (host only)"""
    game = get_game_room_or_404(db, game_id)

    # Verify host
    if not is_host(db, game, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the host can reject players"
        )

    # Get player
    player = db.query(GameRoomPlayer).filter(
        GameRoomPlayer.id == player_id,
        GameRoomPlayer.game_room_id == game.id
    ).first()

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

    # Reject player
    player.status = PlayerStatus.REJECTED
    db.commit()

    # Emit WebSocket event
    try:
        sio_instance = get_sio()
        await sio_instance.emit('player_rejected', {
            'game_id': game.id,
            'user_id': player.user_id,
        }, room=f'game_{game.id}')
        logger.info(f'Emitted player_rejected for user {player.user_id} in game {game.id}')
    except Exception as e:
        logger.error(f'Failed to emit WebSocket event: {e}')

    return await _build_game_response(game, db)


@router.delete("/{game_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_game(
    game_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Leave a game"""
    game = get_game_room_or_404(db, game_id)

    # Get player
    player = is_player(db, game, current_user.id)
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not in this game"
        )

    # Host can't leave, must delete game instead
    if player.is_host:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Host cannot leave. Delete the game instead."
        )

    # Remove player
    db.delete(player)
    db.commit()

    # Emit WebSocket event
    try:
        sio_instance = get_sio()
        await sio_instance.emit('player_left', {
            'game_id': game.id,
            'user_id': current_user.id,
        }, room=f'game_{game.id}')
        logger.info(f'Emitted player_left for user {current_user.id} in game {game.id}')
    except Exception as e:
        logger.error(f'Failed to emit WebSocket event: {e}')


@router.delete("/{game_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_game(
    game_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a game (host only)"""
    game = get_game_room_or_404(db, game_id)

    # Verify host
    if not is_host(db, game, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the host can delete this game"
        )

    # Delete game (cascades to players)
    db.delete(game)
    db.commit()


@router.post("/{game_id}/start", response_model=GameRoomResponse)
async def start_game(
    game_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start a game (host only)"""
    game = get_game_room_or_404(db, game_id)

    # Verify host
    if not is_host(db, game, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the host can start the game"
        )

    # Check if enough players
    accepted_players = db.query(GameRoomPlayer).filter(
        GameRoomPlayer.game_room_id == game.id,
        GameRoomPlayer.status == PlayerStatus.ACCEPTED
    ).all()

    if len(accepted_players) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Need at least 2 players to start"
        )

    # Check if all players have selected decks
    players_without_decks = [p for p in accepted_players if not p.deck_id]
    if players_without_decks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="All players must select their decks before starting"
        )

    # Start game
    game.status = GameStatus.IN_PROGRESS
    db.commit()

    # Emit WebSocket event
    try:
        sio_instance = get_sio()
        await sio_instance.emit('game_started', {
            'game_id': game.id,
        }, room=f'game_{game.id}')
        logger.info(f'Emitted game_started for game {game.id}')
    except Exception as e:
        logger.error(f'Failed to emit WebSocket event: {e}')

    return await _build_game_response(game, db)


@router.post("/{game_id}/stop", response_model=GameRoomResponse)
async def stop_game(
    game_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Stop a game and return to waiting state (host only)"""
    game = get_game_room_or_404(db, game_id)

    # Verify host
    if not is_host(db, game, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the host can stop the game"
        )

    # Check if game is in progress
    if game.status != GameStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Game is not in progress"
        )

    # Stop game - return to waiting
    game.status = GameStatus.WAITING
    db.commit()

    # Emit WebSocket event
    try:
        sio_instance = get_sio()
        await sio_instance.emit('game_stopped', {
            'game_id': game.id,
        }, room=f'game_{game.id}')
        logger.info(f'Emitted game_stopped for game {game.id}')
    except Exception as e:
        logger.error(f'Failed to emit WebSocket event: {e}')

    return await _build_game_response(game, db)


@router.post("/{game_id}/select-deck", response_model=GameRoomResponse)
async def select_deck(
    game_id: int,
    deck_selection: DeckSelectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Select a deck for the game"""
    game = get_game_room_or_404(db, game_id)

    # Verify user is in the game and accepted
    player = is_player(db, game, current_user.id)
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

    # Verify deck exists and belongs to user
    deck = db.query(Deck).filter(
        Deck.id == deck_selection.deck_id,
        Deck.owner_id == current_user.id
    ).first()

    if not deck:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found or does not belong to you"
        )

    # Update player's deck
    player.deck_id = deck_selection.deck_id
    db.commit()

    # Emit event to notify other players
    try:
        sio_instance = get_sio()
        await sio_instance.emit('deck_selected', {
            'game_id': game.id,
            'user_id': current_user.id,
            'deck_id': deck.id,
            'deck_name': deck.name,
        }, room=f'game_{game.id}')
    except Exception as e:
        logger.error(f'Failed to emit WebSocket event: {e}')

    return await _build_game_response(game, db)


async def _build_game_response(game: GameRoom, db: Session) -> GameRoomResponse:
    """Build a GameRoomResponse from a GameRoom model"""
    from app.services.scryfall import get_scryfall_service
    
    players = db.query(GameRoomPlayer, User).join(
        User, GameRoomPlayer.user_id == User.id
    ).filter(
        GameRoomPlayer.game_room_id == game.id
    ).all()

    scryfall_service = get_scryfall_service()
    
    player_responses = []
    for p, user in players:
        deck_info = None
        if p.deck_id:
            deck = db.query(Deck).filter(Deck.id == p.deck_id).first()
            if deck:
                # Get commander info from Scryfall
                commander_name = None
                commander_image_uris = None
                
                logger.info(f"Deck {deck.id}: commander_scryfall_id = '{deck.commander_scryfall_id}'")
                
                if deck.commander_scryfall_id:
                    card_data = await scryfall_service.get_card_by_scryfall_id(deck.commander_scryfall_id)
                    logger.info(f"Card data for {deck.commander_scryfall_id}: {card_data}")
                    if card_data:
                        commander_name = card_data.get('name', deck.name)
                        commander_image_uris = card_data.get('image_uris')
                        if not commander_image_uris and card_data.get('card_faces'):
                            commander_image_uris = card_data['card_faces'][0].get('image_uris')
                
                deck_info = DeckInfo(
                    id=deck.id,
                    name=deck.name,
                    commander_name=commander_name,
                    commander_image_uris=commander_image_uris
                )
        
        player_responses.append(GameRoomPlayerResponse(
            id=p.id,
            user_id=p.user_id,
            username=user.username,
            status=p.status,
            is_host=p.is_host,
            deck_id=p.deck_id,
            deck=deck_info,
            joined_at=p.joined_at
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
        created_at=game.created_at
    )
