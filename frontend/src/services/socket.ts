import { io, Socket } from 'socket.io-client';

class SocketService {
  private socket: Socket | null = null;
  private userId: number | null = null;

  connect(userId: number): Socket {
    if (this.socket?.connected) {
      return this.socket;
    }

    const wsUrl = 'http://localhost:8000';
    const socketPath = '/ws/socket.io';
    
    console.log('Connecting to WebSocket:', wsUrl, 'path:', socketPath);
    
    this.userId = userId;
    this.socket = io(wsUrl, {
      path: socketPath,
      transports: ['websocket', 'polling'],
      autoConnect: true,
    });

    this.socket.on('connect', () => {
      console.log('Socket connected:', this.socket?.id);
      this.authenticate();
    });

    this.socket.on('disconnect', () => {
      console.log('Socket disconnected');
    });

    this.socket.on('connect_error', (error) => {
      console.error('Socket connection error:', error);
    });

    return this.socket;
  }

  private authenticate() {
    if (this.socket && this.userId) {
      this.socket.emit('authenticate', { user_id: this.userId });
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.userId = null;
    }
  }

  getSocket(): Socket | null {
    return this.socket;
  }

  isConnected(): boolean {
    return this.socket?.connected ?? false;
  }

  joinGame(gameId: number) {
    if (this.socket && this.userId) {
      this.socket.emit('join_game', {
        game_id: gameId,
        user_id: this.userId,
      });
    }
  }

  leaveGame(gameId: number) {
    if (this.socket) {
      this.socket.emit('leave_game', { game_id: gameId });
    }
  }

  requestJoin(gameId: number, username: string) {
    if (this.socket && this.userId) {
      this.socket.emit('request_join', {
        game_id: gameId,
        user_id: this.userId,
        username,
      });
    }
  }

  playerAccepted(gameId: number, userId: number) {
    if (this.socket) {
      this.socket.emit('player_accepted', {
        game_id: gameId,
        user_id: userId,
      });
    }
  }

  playerRejected(gameId: number, userId: number) {
    if (this.socket) {
      this.socket.emit('player_rejected', {
        game_id: gameId,
        user_id: userId,
      });
    }
  }

  playerLeft(gameId: number) {
    if (this.socket && this.userId) {
      this.socket.emit('player_left', {
        game_id: gameId,
        user_id: this.userId,
      });
    }
  }

  gameStarted(gameId: number) {
    if (this.socket) {
      this.socket.emit('game_started', { game_id: gameId });
    }
  }

  onPlayerJoinRequest(callback: (data: { game_id: number; user_id: number; username: string }) => void) {
    if (this.socket) {
      this.socket.on('player_join_request', callback);
    }
  }

  onPlayerAccepted(callback: (data: { game_id: number; user_id: number }) => void) {
    if (this.socket) {
      this.socket.on('player_accepted', callback);
    }
  }

  onPlayerRejected(callback: (data: { game_id: number; user_id: number }) => void) {
    if (this.socket) {
      this.socket.on('player_rejected', callback);
    }
  }

  onPlayerLeft(callback: (data: { game_id: number; user_id: number }) => void) {
    if (this.socket) {
      this.socket.on('player_left', callback);
    }
  }

  onGameStarted(callback: (data: { game_id: number }) => void) {
    if (this.socket) {
      this.socket.on('game_started', callback);
    }
  }

  onGameStopped(callback: (data: { game_id: number }) => void) {
    if (this.socket) {
      this.socket.on('game_stopped', callback);
    }
  }

  onDeckSelected(callback: (data: { game_id: number; user_id: number; deck_id: number; deck_name: string; commander_name?: string }) => void) {
    if (this.socket) {
      this.socket.on('deck_selected', callback);
    }
  }

  onGameStateUpdated(callback: (data: { game_id: number }) => void) {
    if (this.socket) {
      this.socket.on('game_state_updated', callback);
    }
  }

  onCardPlayed(callback: (data: { game_id: number; user_id: number; card_id: number }) => void) {
    if (this.socket) {
      this.socket.on('card_played', callback);
    }
  }

  onCardMoved(callback: (data: { game_id: number; user_id: number; card_id: number; from_zone: string; to_zone: string }) => void) {
    if (this.socket) {
      this.socket.on('card_moved', callback);
    }
  }

  onCardTapped(callback: (data: { game_id: number; card_id: number; is_tapped: boolean }) => void) {
    if (this.socket) {
      this.socket.on('card_tapped', callback);
    }
  }

  removeAllListeners() {
    if (this.socket) {
      this.socket.removeAllListeners();
    }
  }
}

export const socketService = new SocketService();
