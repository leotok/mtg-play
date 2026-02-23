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
  scale?: number;
  handIndex?: number;
  zIndex?: number;
}> = ({ card, onTap, onMouseDown, onHover, size = 'md', hidden = false, isDragging = false, style, scale = 100, handIndex = 0, zIndex = 0 }) => {
  const sizeClasses = {
    xs: 'h-24',
    sm: 'h-36',
    md: 'h-80',
    lg: 'h-112',
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

  const left = handIndex * -40;
  const top = Math.abs(handIndex * 8 );

  const rotation = card.is_tapped ? 90 : (handIndex * 4);
  const scaleTransform = scale !== 100 ? `scale(${scale / 100})` : '';
  const rotationTransform = rotation !== 0 ? `rotate(${rotation}deg)` : '';
  const combinedTransform = [scaleTransform, rotationTransform].filter(Boolean).join(' ');
  const scaleStyle = combinedTransform ? { ...style, transform: combinedTransform } : style;

  return (
    <div
      onMouseDown={handleMouseDown}
      onDoubleClick={handleDoubleClick}
      onMouseEnter={handleMouseEnter}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className={`
        ${sizeClasses[size]} 
        
        flex items-center justify-center cursor-grab select-none
        transition-all duration-200
        ${isDragging ? 'opacity-80 scale-105 cursor-grabbing z-50' : 'hover:scale-105 hover:border-yellow-500'}
        ${hidden ? 'bg-gray-900 border-dashed' : ''}
      `}
      style={{...scaleStyle, zIndex, position: 'relative', left, top}}
      title={hidden ? cardName : `${cardName}\n${card.mana_cost || ''}\n${card.type_line || ''}`}
    >
      {hidden ? (
        <img 
          src="https://static.wikia.nocookie.net/mtgsalvation_gamepedia/images/f/f8/Magic_card_back.jpg"
          alt="Card Back"
          className="w-full h-full object-cover rounded-md pointer-events-none"
        />
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
  onMouseDownCommander?: (card: GameCard, e: React.MouseEvent) => void;
  onMouseDownGraveyard?: (card: GameCard, e: React.MouseEvent) => void;
  onMouseDownExile?: (card: GameCard, e: React.MouseEvent) => void;
  battlefieldRef?: React.RefObject<HTMLDivElement | null>;
  handRef?: React.RefObject<HTMLDivElement | null> | ((el: HTMLDivElement | null) => void);
  commanderRef?: React.RefObject<HTMLDivElement | null> | ((el: HTMLDivElement | null) => void);
  graveyardRef?: React.RefObject<HTMLDivElement | null> | ((el: HTMLDivElement | null) => void);
  exileRef?: React.RefObject<HTMLDivElement | null> | ((el: HTMLDivElement | null) => void);
  dragState?: {
    isDragging: boolean;
    cardId: number;
    source: 'battlefield' | 'hand' | 'commander' | 'graveyard' | 'exile';
    cardX: number;
    cardY: number;
  } | null;
  cardScale?: number;
}> = ({ player, isCurrentUser, isActive, onTapCard, onHoverCard, onMouseDownCard, onMouseDownHand, onMouseDownCommander, onMouseDownGraveyard, onMouseDownExile, battlefieldRef, handRef, commanderRef, graveyardRef, exileRef, dragState, cardScale = 100 }) => {
  const backgroundColor = isCurrentUser ? 'darkslateblue' : 'darkslategray';


  const handIndexArray = player.hand.map((_, idx) => {
    return (idx - (player.hand.length/2));
  });

  return (
    <div className={`p-2 rounded-lg flex-1 flex flex-col relative ${isActive ? 'bg-yellow-900/30 border-2 border-yellow-500' : 'bg-gray-800/50 border border-gray-700'}`} style={{backgroundColor}}>
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
                        scale={cardScale}
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

          {isCurrentUser && (
            <div className="fixed bottom-0 left-0 right-40 z-20 pointer-events-none" style={{transform: 'translateY(40%)'}}>
              <div ref={handRef as any} className="flex justify-center gap-1 p-2 pointer-events-auto">
                {player.hand.map((card, idx) => {
                  const isDraggingThis = dragState?.isDragging && dragState?.cardId === card.id;
                  if (isDraggingThis) return null;
                  return (
                    <Card 
                      key={card.id} 
                      card={card} 
                      size="sm"
                      scale={cardScale}
                      onMouseDown={(e) => onMouseDownHand?.(card, e)}
                      onHover={onHoverCard}
                      handIndex={handIndexArray[idx]}
                      zIndex={idx}
                    />
                  );
                })}
              </div>
            </div>
          )}
          {!isCurrentUser && (
            <div className="flex-shrink-0 h-1 overflow-visible">
              <div className="flex justify-center -mt-2" style={{transform: 'translateY(-40%)'}}>
                {player.hand.map((card, idx) => {
                  const isDraggingThis = dragState?.isDragging && dragState?.cardId === card.id;
                  if (isDraggingThis) return null;
                  return (
                    <div key={card.id} className="-ml-4 first:ml-0">
                      <Card 
                        card={card} 
                        size="sm"
                        scale={cardScale}
                        hidden={true}
                        onHover={onHoverCard}
                        handIndex={handIndexArray[idx]}
                        zIndex={idx}
                      />
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        <div className="w-20 flex-shrink-0">
            <div className="text-center text-xs text-gray-500 mb-1">
              Life
            </div>
            <div className="text-center text-lg font-bold mb-2">
              <span className={player.life_total <= 10 ? 'text-red-400' : 'text-white'}>
                {player.life_total}
              </span>
            </div>
            <div className="text-center text-xs text-gray-500 mb-1">
              Library
            </div>
            <div className="text-center text-lg font-bold mb-1">
              <span className="text-gray-400">
                {player.library.length}
              </span>
            </div>
            <div 
              className="w-16 h-24 mx-auto rounded-lg overflow-hidden cursor-pointer hover:scale-105 transition-transform border border-gray-600"
              style={{ transform: `scale(${cardScale / 100})` }}
            >
              <img 
                src="https://static.wikia.nocookie.net/mtgsalvation_gamepedia/images/f/f8/Magic_card_back.jpg" 
                alt="Card Back"
                className="w-full h-full object-cover"
              />
            </div>
            <h4 className="text-xs text-gray-500 uppercase mb-1 mt-2 text-center">Cmd</h4>
            <div ref={commanderRef as any} className="flex justify-center gap-1 min-h-[100px] p-1 bg-gray-900/50 rounded">
              {player.commander.map((card) => (
                <Card 
                  key={card.id} 
                  card={card} 
                  size="sm"
                  scale={cardScale}
                  onMouseDown={isCurrentUser ? (e) => onMouseDownCommander?.(card, e) : undefined}
                  onHover={onHoverCard}
                />
              ))}
            </div>

            <div className="mt-2">
              <h4 className="text-xs text-gray-500 uppercase mb-1">Grave</h4>
              <div ref={graveyardRef as any} className="flex flex-wrap gap-0.5 min-h-[20px] p-1 bg-gray-900/50 rounded overflow-x-auto">
                {player.graveyard.slice(0, 3).map((card) => (
                  <Card 
                    key={card.id} 
                    card={card} 
                    size="xs" 
                    scale={cardScale} 
                    onMouseDown={isCurrentUser ? (e) => onMouseDownGraveyard?.(card, e) : undefined}
                    onHover={onHoverCard} 
                  />
                ))}
              </div>
            </div>

            <div className="mt-2">
              <h4 className="text-xs text-gray-500 uppercase mb-1">Exile</h4>
              <div ref={exileRef as any} className="flex flex-wrap gap-0.5 min-h-[20px] p-1 bg-gray-900/50 rounded overflow-x-auto">
                {player.exile.slice(0, 3).map((card) => (
                  <Card 
                    key={card.id} 
                    card={card} 
                    size="xs" 
                    scale={cardScale} 
                    onMouseDown={isCurrentUser ? (e) => onMouseDownExile?.(card, e) : undefined}
                    onHover={onHoverCard} 
                  />
                ))}
              </div>
            </div>
          </div>
      </div>
      {dragState?.isDragging && isCurrentUser && (() => {
        let draggedCard;
        if (dragState.source === 'hand') {
          draggedCard = player.hand.find(c => c.id === dragState.cardId);
        } else if (dragState.source === 'commander') {
          draggedCard = player.commander.find(c => c.id === dragState.cardId);
        } else if (dragState.source === 'graveyard') {
          draggedCard = player.graveyard.find(c => c.id === dragState.cardId);
        } else if (dragState.source === 'exile') {
          draggedCard = player.exile.find(c => c.id === dragState.cardId);
        }
        if (!draggedCard) return null;
        return (
          <div
            className="fixed pointer-events-none z-50"
            style={{
              left: dragState.cardX - 20,
              top: dragState.cardY - 28,
            }}
          >
            <Card card={draggedCard} size="sm" scale={cardScale} isDragging />
          </div>
        );
      })()}
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
    passPriority,
    moveCard,
  } = useGameStateStore();

  const [hoveredCard, setHoveredCard] = useState<{
    card: GameCard | { id: number; card_name: string; image_uris?: { normal?: string }; card_faces?: Array<{ image_uris?: { normal?: string } }>; mana_cost?: string; type_line?: string };
    position: { x: number; y: number };
  } | null>(null);

  const [dragState, setDragState] = useState<{
    isDragging: boolean;
    cardId: number;
    source: 'battlefield' | 'hand' | 'commander' | 'graveyard' | 'exile';
    cardX: number;
    cardY: number;
    clickOffsetX: number;
    clickOffsetY: number;
  } | null>(null);

  const [cardScale, setCardScale] = useState(100);

  const battlefieldRef = React.useRef<HTMLDivElement>(null);
  const handRef = React.useRef<HTMLDivElement>(null);
  const commanderRef = React.useRef<HTMLDivElement>(null);
  const graveyardRef = React.useRef<HTMLDivElement>(null);
  const exileRef = React.useRef<HTMLDivElement>(null);

  const setHandRef = React.useCallback((el: HTMLDivElement | null) => {
    handRef.current = el;
  }, []);

  const setCommanderRef = React.useCallback((el: HTMLDivElement | null) => {
    commanderRef.current = el;
  }, []);

  const setGraveyardRef = React.useCallback((el: HTMLDivElement | null) => {
    graveyardRef.current = el;
  }, []);

  const setExileRef = React.useCallback((el: HTMLDivElement | null) => {
    exileRef.current = el;
  }, []);

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

  const handlePassPriority = async () => {
    if (!gameId) return;
    await passPriority(parseInt(gameId));
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

  const handleMouseDownCommander = (card: GameCard, e: React.MouseEvent) => {
    setDragState({
      isDragging: true,
      cardId: card.id,
      source: 'commander',
      cardX: e.clientX,
      cardY: e.clientY,
      clickOffsetX: 0,
      clickOffsetY: 0,
    });
  };

  const handleMouseDownGraveyard = (card: GameCard, e: React.MouseEvent) => {
    setDragState({
      isDragging: true,
      cardId: card.id,
      source: 'graveyard',
      cardX: e.clientX,
      cardY: e.clientY,
      clickOffsetX: 0,
      clickOffsetY: 0,
    });
  };

  const handleMouseDownExile = (card: GameCard, e: React.MouseEvent) => {
    setDragState({
      isDragging: true,
      cardId: card.id,
      source: 'exile',
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
      
      if (dragState.source === 'hand' || dragState.source === 'commander' || dragState.source === 'graveyard' || dragState.source === 'exile') {
        setDragState(prev => prev ? { ...prev, cardX: e.clientX, cardY: e.clientY } : null);
      } else {
        const x = e.clientX - rect.left - dragState.clickOffsetX;
        const y = e.clientY - rect.top - dragState.clickOffsetY;
        setDragState(prev => prev ? { ...prev, cardX: x, cardY: y } : null);
      }
    };

    const isOverElement = (e: MouseEvent, ref: React.RefObject<HTMLDivElement | null>) => {
      if (!ref.current) return false;
      const rect = ref.current.getBoundingClientRect();
      return e.clientX >= rect.left && e.clientX <= rect.right && e.clientY >= rect.top && e.clientY <= rect.bottom;
    };

    const handleMouseUp = async (e: MouseEvent) => {
      if (!dragState || !gameId) {
        setDragState(null);
        return;
      }

      const gameIdNum = parseInt(gameId);
      const x = dragState.cardX;
      const y = dragState.cardY;

      // Check if dropping on battlefield
      if (battlefieldRef.current) {
        const bfRect = battlefieldRef.current.getBoundingClientRect();
        const isInsideBf = x >= bfRect.left && x <= bfRect.right && y >= bfRect.top && y <= bfRect.bottom;

        if ((dragState.source === 'hand' || dragState.source === 'commander') && isInsideBf) {
          const localX = x - bfRect.left - 32;
          const localY = y - bfRect.top - 48;
          await playCard(gameIdNum, dragState.cardId, localX, localY);
          setDragState(null);
          return;
        }

        if (dragState.source === 'battlefield') {
          const localX = x;
          const localY = y;
          const isValidPosition = localX >= 0 && localX <= bfRect.width - 64 && localY >= 0 && localY <= bfRect.height - 96;

          if (isValidPosition) {
            await updateBattlefieldPosition(gameIdNum, dragState.cardId, localX, localY);
            setDragState(null);
            return;
          }
        }
      }

      // Check if dropping on hand
      if (isCurrentUser && isOverElement(e, handRef)) {
        await moveCard(gameIdNum, dragState.cardId, 'hand', 0);
        setDragState(null);
        return;
      }

      // Check if dropping on commander
      if (isCurrentUser && isOverElement(e, commanderRef)) {
        await moveCard(gameIdNum, dragState.cardId, 'commander', 0);
        setDragState(null);
        return;
      }

      // Check if dropping on graveyard
      if (isCurrentUser && isOverElement(e, graveyardRef)) {
        await moveCard(gameIdNum, dragState.cardId, 'graveyard', 0);
        setDragState(null);
        return;
      }

      // Check if dropping on exile
      if (isCurrentUser && isOverElement(e, exileRef)) {
        await moveCard(gameIdNum, dragState.cardId, 'exile', 0);
        setDragState(null);
        return;
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
    <div className="w-screen h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 overflow-x-hidden select-none">
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
            .map((player) => {
              const isCurrentUserPlayer = player.user_id === user?.id;
              return (
                <PlayerZone
                  key={player.id}
                  player={player}
                  isCurrentUser={isCurrentUserPlayer}
                  isActive={player.is_active}
                  onTapCard={isCurrentUserPlayer ? handleTapCard : undefined}
                  onHoverCard={(card, position) => setHoveredCard(card ? { card, position } : null)}
                  onMouseDownCard={isCurrentUserPlayer ? handleMouseDownBattlefield : undefined}
                  onMouseDownHand={isCurrentUserPlayer ? handleMouseDownHand : undefined}
                  onMouseDownCommander={isCurrentUserPlayer ? handleMouseDownCommander : undefined}
                  onMouseDownGraveyard={isCurrentUserPlayer ? handleMouseDownGraveyard : undefined}
                  onMouseDownExile={isCurrentUserPlayer ? handleMouseDownExile : undefined}
                  battlefieldRef={battlefieldRef}
                  handRef={isCurrentUserPlayer ? (el: any) => { handRef.current = el; } : undefined}
                  commanderRef={isCurrentUserPlayer ? (el: any) => { commanderRef.current = el; } : undefined}
                  graveyardRef={isCurrentUserPlayer ? (el: any) => { graveyardRef.current = el; } : undefined}
                  exileRef={isCurrentUserPlayer ? (el: any) => { exileRef.current = el; } : undefined}
                  dragState={isCurrentUserPlayer ? dragState : null}
                  cardScale={cardScale}
                />
              );
            })}
        </div>

        <div className="w-40 flex-shrink-0 flex flex-col gap-2">
          <div className="bg-gray-800 rounded p-2 text-center">
            <div className="text-gray-400 text-xs">Turn</div>
            <div className="text-white font-bold text-lg">{gameState.current_turn}</div>
          </div>

          <div className="bg-yellow-900/50 rounded p-2 text-center border border-yellow-700">
            <div className="text-gray-400 text-xs">Phase</div>
            <div className="text-yellow-400 text-xs font-semibold">
              {TURN_PHASE_LABELS[gameState.current_phase]}
            </div>
          </div>

          <div className="bg-gray-800 rounded p-2 text-center">
            <div className="text-gray-400 text-xs">Active</div>
            <div className="text-white text-sm truncate">{gameState.active_player_username}</div>
          </div>

          <div className="bg-gray-800 rounded p-2 text-center">
            <div className="text-gray-400 text-xs mb-1">Card Size</div>
            <div className="flex items-center justify-center gap-2">
              <button
                onClick={() => setCardScale(s => Math.max(50, s - 10))}
                className="w-6 h-6 bg-gray-700 hover:bg-gray-600 rounded text-white text-sm font-bold"
              >
                -
              </button>
              <span className="text-white text-sm font-medium w-10">{cardScale}%</span>
              <button
                onClick={() => setCardScale(s => Math.min(150, s + 10))}
                className="w-6 h-6 bg-gray-700 hover:bg-gray-600 rounded text-white text-sm font-bold"
              >
                +
              </button>
            </div>
          </div>

          <div className="flex-1" />

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
              <button
                onClick={handlePassPriority}
                disabled={isLoading}
                className="flex items-center justify-center gap-1 px-2 py-2 bg-yellow-600 hover:bg-yellow-500 text-white rounded transition-colors text-sm disabled:opacity-50"
              >
                Pass Priority
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default GamePage;
