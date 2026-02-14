import logging
from typing import Dict
from socketio import AsyncServer

logger = logging.getLogger(__name__)

connected_users: Dict[str, int] = {}
user_sid_map: Dict[str, str] = {}


def register_handlers(sio: AsyncServer):
    """Register WebSocket event handlers"""
    
    @sio.on("connect")
    async def connect(sid, environ):
        logger.info(f"Client connected: {sid}")
    
    @sio.on("disconnect")
    async def disconnect(sid):
        logger.info(f"Client disconnected: {sid}")
        user_id = user_sid_map.pop(sid, None)
        if user_id:
            connected_users.pop(str(user_id), None)
    
    @sio.on("authenticate")
    async def authenticate(sid, data):
        """Client authenticates with user_id"""
        user_id = data.get("user_id")
        if user_id:
            connected_users[str(user_id)] = sid
            user_sid_map[sid] = str(user_id)
            logger.info(f"User {user_id} authenticated with sid {sid}")
            await sio.emit("authenticated", {"user_id": user_id}, room=sid)
    
    @sio.on("join_game")
    async def join_game(sid, data):
        """Client joins a game room"""
        game_id = data.get("game_id")
        user_id = data.get("user_id")
        
        if game_id and user_id:
            await sio.enter_room(sid, f"game_{game_id}")
            logger.info(f"User {user_id} joined game {game_id}")
    
    @sio.on("leave_game")
    async def leave_game(sid, data):
        """Client leaves a game room"""
        game_id = data.get("game_id")
        
        if game_id:
            await sio.leave_room(sid, f"game_{game_id}")
            logger.info(f"Client left game {game_id}")
    
    @sio.on("request_join")
    async def request_join(sid, data):
        """Player requests to join a game"""
        game_id = data.get("game_id")
        user_id = data.get("user_id")
        username = data.get("username")
        
        if game_id:
            await sio.emit("player_join_request", {
                "game_id": game_id,
                "user_id": user_id,
                "username": username
            }, room=f"game_{game_id}")
    
    @sio.on("player_accepted")
    async def player_accepted(sid, data):
        """Host accepts a player"""
        game_id = data.get("game_id")
        user_id = data.get("user_id")
        
        if game_id and user_id:
            await sio.emit("player_accepted", {
                "game_id": game_id,
                "user_id": user_id
            }, room=f"game_{game_id}")
    
    @sio.on("player_rejected")
    async def player_rejected(sid, data):
        """Host rejects a player"""
        game_id = data.get("game_id")
        user_id = data.get("user_id")
        
        if game_id and user_id:
            await sio.emit("player_rejected", {
                "game_id": game_id,
                "user_id": user_id
            }, room=f"game_{game_id}")
    
    @sio.on("player_left")
    async def player_left(sid, data):
        """Player leaves a game"""
        game_id = data.get("game_id")
        user_id = data.get("user_id")
        
        if game_id:
            await sio.emit("player_left", {
                "game_id": game_id,
                "user_id": user_id
            }, room=f"game_{game_id}")
    
    @sio.on("game_started")
    async def game_started(sid, data):
        """Game has started"""
        game_id = data.get("game_id")
        
        if game_id:
            await sio.emit("game_started", {
                "game_id": game_id
            }, room=f"game_{game_id}")
    
    logger.info("WebSocket handlers registered")
