import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeftIcon,
  ArrowRightIcon,
} from '@heroicons/react/24/outline';
import { useAuth } from '../context/AuthContext';
import { useGameStateStore } from '../store/gameStateStore';
import { socketService } from '../services/socket';
import { TURN_PHASE_LABELS, type GameCard, type GameCardInBattlefield, type PlayerGameState } from '../types/gameState';

const CardPreview: React.FC<{
  card: GameCard | { id: number; card_name: string; image_uris?: { normal?: string }; card_faces?: Array<{ image_uris?: { normal?: string } }>; mana_cost?: string; type_line?: string };
  position: { x: number; y: number };
  isOpponent?: boolean;
  isCommander?: boolean;
}> = ({ card, position, isOpponent = false, isCommander = false }) => {
  const imageUrl = card.image_uris?.normal || card.card_faces?.[0]?.image_uris?.normal;
  if (!imageUrl) return null;

  const previewWidth = 256;
  const aspectRatio = 1.4;
  const previewHeight = previewWidth * aspectRatio;

  return (
    <div
      className="fixed pointer-events-none z-50"
      style={{
        left: isCommander ? position.x - previewWidth : position.x,
        top: isOpponent ? position.y : position.y - previewHeight - 10,
      }}
    >
      <img
        src={imageUrl}
        alt={card.card_name}
        className="w-64 h-auto rounded-lg shadow-2xl border-2 border-gray-600"
      />
    </div>
  );
};

const Card: React.FC<{
  card: GameCard | { id: number; card_name: string; image_uris?: { normal?: string }; card_faces?: Array<{ image_uris?: { normal?: string } }>; mana_cost?: string; type_line?: string; is_tapped?: boolean; battlefield_x?: number; battlefield_y?: number; is_attacking?: boolean; is_blocking?: boolean; is_face_up?: boolean };
  onTap?: () => void;
  onMouseDown?: (e: React.MouseEvent) => void;
  onHover?: (card: GameCard | { id: number; card_name: string; image_uris?: { normal?: string }; card_faces?: Array<{ image_uris?: { normal?: string } }>; mana_cost?: string; type_line?: string } | null, position: { x: number; y: number }) => void;
  size?: 'xs' | 'sm' | 'md' | 'lg';
  hidden?: boolean;
  isDragging?: boolean;
  style?: React.CSSProperties;
}> = ({ card, onTap, onMouseDown, onHover, size = 'md', hidden = false, isDragging = false, style }) => {
  const sizeClasses = {
    xs: 'w-10 h-14',
    sm: 'w-16 h-24',
    md: 'w-24 h-36',
    lg: 'w-32 h-48',
  };

  const imageUrl = card.image_uris?.normal || card.card_faces?.[0]?.image_uris?.normal;
  const cardName = hidden ? 'Unknown Card' : card.card_name;

  const handleMouseEnter = (e: React.MouseEvent) => {
    if (!hidden && onHover) {
      onHover(card, { x: e.clientX, y: e.clientY });
    }
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    if (onMouseDown) {
      onMouseDown(e);
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!hidden && onHover) {
      onHover(card, { x: e.clientX, y: e.clientY });
    }
  };

  const handleDoubleClick = () => {
    if (onTap) {
      onTap();
    }
  };

  const handleMouseLeave = () => {
    if (onHover) {
      onHover(null, { x: 0, y: 0 });
    }
  };

  return (
    <div
      onMouseDown={handleMouseDown}
      onDoubleClick={handleDoubleClick}
      onMouseEnter={handleMouseEnter}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className={`
        ${sizeClasses[size]} 
        rounded-lg border-2 border-gray-600 bg-gray-800 
        flex items-center justify-center cursor-grab select-none
        transition-all duration-200
        ${card.is_tapped ? 'rotate-90' : ''}
        ${isDragging ? 'opacity-80 scale-105 cursor-grabbing z-50' : 'hover:scale-105 hover:border-yellow-500'}
        ${hidden ? 'bg-gray-900 border-dashed' : ''}
      `}
      style={style}
      title={hidden ? cardName : `${cardName}\n${card.mana_cost || ''}\n${card.type_line || ''}`}
    >
      {hidden ? (
        <div className="text-gray-500 text-xs text-center p-1">Hidden</div>
      ) : imageUrl ? (
        <img 
          src={imageUrl} 
          alt={cardName}
          className="w-full h-full object-cover rounded-md pointer-events-none"
        />
      ) : (
        <div className="text-white text-xs text-center p-1 pointer-events-none">
          <div className="font-bold">{cardName}</div>
          {card.mana_cost && <div>{card.mana_cost}</div>}
        </div>
      )}
    </div>
  );
};

const PlayerZone: React.FC<{
  player: PlayerGameState;
  isCurrentUser: boolean;
  isActive: boolean;
  onTapCard?: (cardId: number) => void;
  onHoverCard?: (card: GameCard | { id: number; card_name: string; image_uris?: { normal?: string }; card_faces?: Array<{ image_uris?: { normal?: string } }>; mana_cost?: string; type_line?: string } | null, position: { x: number; y: number }) => void;
  onMouseDownCard?: (card: GameCardInBattlefield, e: React.MouseEvent) => void;
  onMouseDownHand?: (card: GameCard, e: React.MouseEvent) => void;
  battlefieldRef?: React.RefObject<HTMLDivElement | null>;
  dragState?: {
    isDragging: boolean;
    cardId: number;
    source: 'battlefield' | 'hand';
    cardX: number;
    cardY: number;
  } | null;
}> = ({ player, isCurrentUser, isActive, onTapCard, onHoverCard, onMouseDownCard, onMouseDownHand, battlefieldRef, dragState }) => {
  return (
    <div className={`p-2 rounded-lg flex-1 flex flex-col ${isActive ? 'bg-yellow-900/30 border-2 border-yellow-500' : 'bg-gray-800/50 border border-gray-700'}`}>
      <div className="flex gap-2 flex-1 min-h-0">
        <div className="flex-1 flex flex-col min-h-0">
          <div className="flex-1 min-h-0">
            <div className="h-full min-h-0 pb-2">
              <h4 className="text-xs text-gray-500 uppercase mb-1">Battlefield ({player.battlefield.length})</h4>
              <div 
                ref={battlefieldRef}
                className="h-[calc(100%-1.5rem)] p-1 bg-green-900/20 border-2 border-dashed border-green-800 rounded-lg relative select-none"
              >
                {player.battlefield.map((card) => {
                  const isDraggingThis = dragState?.isDragging && dragState?.cardId === card.id;
                  return (
                    <div
                      key={card.id}
                      className="absolute"
                      style={{ 
                        left: isDraggingThis ? dragState.cardX : (card.battlefield_x || 5), 
                        top: isDraggingThis ? dragState.cardY : (card.battlefield_y || 5),
                        transition: isDraggingThis ? 'none' : 'all 0.1s ease',
                        zIndex: isDraggingThis ? 50 : 1,
                      }}
                    >
                      <Card 
                        card={card} 
                        size="sm"
                        onTap={() => onTapCard?.(card.id)}
                        onMouseDown={isCurrentUser ? (e) => onMouseDownCard?.(card, e) : undefined}
                        onHover={onHoverCard}
                        isDragging={isDraggingThis}
                      />
                    </div>
                  );
                })}
                {player.battlefield.length === 0 && (
                  <div className="absolute inset-0 flex items-center justify-center text-gray-600 text-xs">
                    Drop cards here
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="flex-shrink-0">
            <h4 className="text-xs text-gray-500 uppercase mb-1 text-center">Hand ({player.hand.length})</h4>
            <div className="flex flex-wrap justify-center gap-1 min-h-[40px] p-1 bg-gray-900/50 rounded">
              {player.hand.map((card) => {
                const isDraggingThis = dragState?.isDragging && dragState?.cardId === card.id;
                if (isDraggingThis) return null;
                return (
                  <Card 
                    key={card.id} 
                    card={card} 
                    size="xs"
                    hidden={!isCurrentUser}
                    onMouseDown={isCurrentUser ? (e) => onMouseDownHand?.(card, e) : undefined}
                    onHover={onHoverCard}
                  />
                );
              })}
            </div>
              </div>
              {dragState?.isDragging && dragState?.source === 'hand' && (() => {
                const draggedCard = player.hand.find(c => c.id === dragState.cardId);
                if (!draggedCard) return null;
                return (
                  <div
                    className="absolute pointer-events-none z-50"
                    style={{
                      left: dragState.cardX - 20,
                      top: dragState.cardY - 28,
                    }}
                  >
                    <Card card={draggedCard} size="sm" isDragging />
                  </div>
                );
              })()}
            </div>

          <div className="w-20 flex-shrink-0">
            <h4 className="text-xs text-gray-500 uppercase mb-1">Cmd</h4>
            <div className="flex flex-col gap-1 min-h-[40px] p-1 bg-gray-900/50 rounded">
              {player.commander.map((card) => (
                <Card 
                  key={card.id} 
                  card={card} 
                  size="xs"
                  onHover={onHoverCard}
                />
              ))}
            </div>

            <div className="mt-2">
              <h4 className="text-xs text-gray-500 uppercase mb-1">Grave</h4>
              <div className="flex flex-wrap gap-0.5 min-h-[20px] p-1 bg-gray-900/50 rounded overflow-x-auto">
                {player.graveyard.slice(0, 3).map((card) => (
                  <Card key={card.id} card={card} size="xs" onHover={onHoverCard} />
                ))}
              </div>
            </div>

            <div className="mt-2">
              <h4 className="text-xs text-gray-500 uppercase mb-1">Exile</h4>
              <div className="flex flex-wrap gap-0.5 min-h-[20px] p-1 bg-gray-900/50 rounded overflow-x-auto">
                {player.exile.slice(0, 3).map((card) => (
                  <Card key={card.id} card={card} size="xs" onHover={onHoverCard} />
                ))}
              </div>
            </div>
          </div>
      </div>
    </div>
  );
};

const GamePage: React.FC = () => {
  const { gameId } = useParams<{ gameId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { 
    gameState, 
    isLoading, 
    error, 
    fetchGameState, 
    drawCard, 
    untapAll,
    playCard, 
    tapCard,
    updateBattlefieldPosition,
  } = useGameStateStore();

  const [hoveredCard, setHoveredCard] = useState<{
    card: GameCard | { id: number; card_name: string; image_uris?: { normal?: string }; card_faces?: Array<{ image_uris?: { normal?: string } }>; mana_cost?: string; type_line?: string };
    position: { x: number; y: number };
  } | null>(null);

  const [dragState, setDragState] = useState<{
    isDragging: boolean;
    cardId: number;
    source: 'battlefield' | 'hand';
    cardX: number;
    cardY: number;
    clickOffsetX: number;
    clickOffsetY: number;
  } | null>(null);

  const battlefieldRef = React.useRef<HTMLDivElement>(null);

  const currentPlayer = gameState?.players.find(p => p.user_id === user?.id);

  useEffect(() => {
    if (!gameId || !user?.id) return;
    
    const id = parseInt(gameId);
    fetchGameState(id);

    socketService.connect(user.id);
    socketService.joinGame(id);

    socketService.onGameStateUpdated(() => {
      fetchGameState(id);
    });

    return () => {
      socketService.leaveGame(id);
    };
  }, [gameId, user?.id]);

  const handleDrawCard = async () => {
    if (!gameId) return;
    await drawCard(parseInt(gameId));
  };

  const handleUntapAll = async () => {
    if (!gameId) return;
    await untapAll(parseInt(gameId));
  };

  const handleTapCard = async (cardId: number) => {
    if (!gameId) return;
    await tapCard(parseInt(gameId), cardId);
  };

  const handleMouseDownBattlefield = (card: GameCardInBattlefield, e: React.MouseEvent) => {
    if (!battlefieldRef.current) return;
    
    const rect = battlefieldRef.current.getBoundingClientRect();
    const cardX = card.battlefield_x || 0;
    const cardY = card.battlefield_y || 0;
    
    const clickOffsetX = e.clientX - rect.left - cardX;
    const clickOffsetY = e.clientY - rect.top - cardY;
    
    setDragState({
      isDragging: true,
      cardId: card.id,
      source: 'battlefield',
      cardX,
      cardY,
      clickOffsetX,
      clickOffsetY,
    });
  };

  const handleMouseDownHand = (card: GameCard, e: React.MouseEvent) => {
    setDragState({
      isDragging: true,
      cardId: card.id,
      source: 'hand',
      cardX: e.clientX,
      cardY: e.clientY,
      clickOffsetX: 0,
      clickOffsetY: 0,
    });
  };

  useEffect(() => {
    if (!dragState) return;

    const handleMouseMove = (e: MouseEvent) => {
      if (!battlefieldRef.current) return;
      
      const rect = battlefieldRef.current.getBoundingClientRect();
      
      if (dragState.source === 'hand') {
        setDragState(prev => prev ? { ...prev, cardX: e.clientX, cardY: e.clientY } : null);
      } else {
        const x = e.clientX - rect.left - dragState.clickOffsetX;
        const y = e.clientY - rect.top - dragState.clickOffsetY;
        setDragState(prev => prev ? { ...prev, cardX: x, cardY: y } : null);
      }
    };

    const handleMouseUp = async () => {
      if (!dragState || !battlefieldRef.current || !gameId) {
        setDragState(null);
        return;
      }

      const rect = battlefieldRef.current.getBoundingClientRect();
      const x = dragState.cardX;
      const y = dragState.cardY;

      const isInside = 
        x >= rect.left && 
        x <= rect.right && 
        y >= rect.top && 
        y <= rect.bottom;

      if (dragState.source === 'hand' && isInside) {
        const localX = dragState.cardX - rect.left - 32;
        const localY = dragState.cardY - rect.top - 48;
        await playCard(parseInt(gameId), dragState.cardId, localX, localY);
      } else if (dragState.source === 'battlefield') {
        const localX = dragState.cardX;
        const localY = dragState.cardY;
        const isValidPosition = 
          localX >= 0 && 
          localX <= rect.width - 64 && 
          localY >= 0 && 
          localY <= rect.height - 96;

        if (isValidPosition) {
          await updateBattlefieldPosition(parseInt(gameId), dragState.cardId, localX, localY);
        }
      }

      setDragState(null);
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [dragState, gameId]);

  if (isLoading && !gameState) {
    return (
      <div className="w-screen h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 flex items-center justify-center overflow-hidden">
        <div className="text-center">
          <svg className="animate-spin h-12 w-12 text-yellow-500 mx-auto" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <p className="mt-4 text-gray-400">Loading game...</p>
        </div>
      </div>
    );
  }

  if (error || !gameState) {
    return (
      <div className="w-screen h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 flex items-center justify-center overflow-hidden">
        <div className="text-center">
          <p className="text-red-400 mb-4">{error || 'Game not found'}</p>
          <button
            onClick={() => navigate('/playground')}
            className="text-yellow-400 hover:text-yellow-300"
          >
            Back to Playground
          </button>
        </div>
      </div>
    );
  }

  const isCurrentUserActive = currentPlayer?.is_active || false;

  return (
    <div className="w-screen h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 overflow-hidden select-none">
      <div className="absolute top-2 left-2 z-10">
        <button
          onClick={() => navigate(`/playground/game/${gameId}`)}
          className="flex items-center text-gray-400 hover:text-gray-200 transition-colors text-sm"
        >
          <ArrowLeftIcon className="h-4 w-4 mr-1" />
          Back
        </button>
      </div>
      {hoveredCard && !dragState?.isDragging && (() => {
        const currentUser = gameState.players.find(p => p.user_id === user?.id);
        const isCommander = gameState.players.some(p => p.commander.some(c => c.id === hoveredCard.card.id));
        const isOpponent = currentUser && !(
          currentUser.hand.some(c => c.id === hoveredCard.card.id) ||
          currentUser.battlefield.some(c => c.id === hoveredCard.card.id) ||
          currentUser.commander.some(c => c.id === hoveredCard.card.id) ||
          currentUser.graveyard.some(c => c.id === hoveredCard.card.id) ||
          currentUser.exile.some(c => c.id === hoveredCard.card.id) ||
          currentUser.library.some(c => c.id === hoveredCard.card.id)
        );
        return <CardPreview card={hoveredCard.card} position={hoveredCard.position} isOpponent={isOpponent} isCommander={isCommander} />;
      })()}
      <div className="w-full h-full p-2 flex">
        <div className="flex-1 flex flex-col min-h-0 pr-2">
          {gameState.players
            .sort((a, b) => {
              if (a.user_id === user?.id) return 1;
              if (b.user_id === user?.id) return -1;
              return a.player_order - b.player_order;
            })
            .map((player) => (
              <PlayerZone
                key={player.id}
                player={player}
                isCurrentUser={player.user_id === user?.id}
                isActive={player.is_active}
                onTapCard={player.user_id === user?.id ? handleTapCard : undefined}
                onHoverCard={(card, position) => setHoveredCard(card ? { card, position } : null)}
                onMouseDownCard={player.user_id === user?.id ? handleMouseDownBattlefield : undefined}
                onMouseDownHand={player.user_id === user?.id ? handleMouseDownHand : undefined}
                battlefieldRef={battlefieldRef}
                dragState={player.user_id === user?.id ? dragState : null}
              />
            ))}
        </div>

        <div className="w-40 flex-shrink-0 flex flex-col gap-2">
          <div className="bg-gray-800 rounded p-2 text-center">
            <div className="text-gray-400 text-xs">Turn</div>
            <div className="text-white font-bold text-lg">{gameState.current_turn}</div>
          </div>

          <div className="bg-yellow-900/50 rounded p-2 text-center border border-yellow-700">
            <div className="text-yellow-400 text-xs font-semibold">
              {TURN_PHASE_LABELS[gameState.current_phase]}
            </div>
          </div>

          <div className="bg-gray-800 rounded p-2 text-center">
            <div className="text-gray-400 text-xs">Active</div>
            <div className="text-white text-sm truncate">{gameState.active_player_username}</div>
          </div>

          <div className="flex-1" />

          <div className="bg-gray-800 rounded p-2">
            <div className="text-gray-400 text-xs uppercase mb-2 text-center">Players</div>
            <div className="flex flex-col gap-2">
              {gameState.players
                .sort((a, b) => a.player_order - b.player_order)
                .map((player) => (
                  <div 
                    key={player.id} 
                    className={`flex items-center justify-between p-1 rounded ${player.is_active ? 'bg-yellow-900/50 border border-yellow-600' : 'bg-gray-900/50'}`}
                  >
                    <div className="flex items-center gap-1">
                      <div className="w-6 h-6 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold text-xs">
                        {player.username.charAt(0).toUpperCase()}
                      </div>
                      <span className={`text-xs truncate max-w-[80px] ${player.user_id === user?.id ? 'text-yellow-400' : 'text-gray-300'}`}>
                        {player.username}
                      </span>
                    </div>
                    <div className="flex items-center gap-1">
                      <span className={`text-sm font-bold ${player.life_total <= 10 ? 'text-red-400' : 'text-white'}`}>
                        {player.life_total}
                      </span>
                      {player.poison_counters > 0 && (
                        <span className="text-green-400 text-xs">({player.poison_counters})</span>
                      )}
                    </div>
                  </div>
                ))}
            </div>
          </div>

          {currentPlayer && (
            <div className="bg-gray-800 rounded p-2 text-center">
              <div className="text-gray-400 text-xs">Your Library</div>
              <div className="text-white font-bold">{currentPlayer.library.length}</div>
            </div>
          )}

          {isCurrentUserActive && currentPlayer && (
            <div className="flex flex-col gap-2">
              <button
                onClick={handleUntapAll}
                disabled={isLoading}
                className="flex items-center justify-center gap-1 px-2 py-2 bg-green-600 hover:bg-green-500 text-white rounded transition-colors text-sm disabled:opacity-50"
              >
                Untap
              </button>
              <button
                onClick={handleDrawCard}
                disabled={isLoading}
                className="flex items-center justify-center gap-1 px-2 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded transition-colors text-sm disabled:opacity-50"
              >
                <ArrowRightIcon className="h-4 w-4" />
                Draw
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default GamePage;
