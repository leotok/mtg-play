import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useGameStateStore } from '../store/gameStateStore';
import { socketService } from '../services/socket';
import { type GameCard, type CardZone, type GameCardInBattlefield } from '../types/gameState';
import { CardPreview } from '../components/gamePage/CardPreview';
import { PlayerZone } from '../components/gamePage/PlayerZone';
import { GameSideBar } from '../components/gamePage/GameSideBar';


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
    sourceZone: CardZone;
    card: GameCard | GameCardInBattlefield | null;
    currentX: number;
    currentY: number;
    cardPosition: { x: number; y: number };
    mouseOffset: { x: number; y: number };
  } | null>(null);

  const [hoveredZone, setHoveredZone] = useState<CardZone | null>(null);

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
  const isCurrentUser = !!currentPlayer;

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
    
    const rect = e.currentTarget.getBoundingClientRect();
    
    setDragState({
      isDragging: true,
      cardId: card.id,
      sourceZone: 'battlefield',
      card,
      currentX: e.clientX,
      currentY: e.clientY,
      cardPosition: { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 },
      mouseOffset: { x: e.clientX - rect.left, y: e.clientY - rect.top },
    });
  };

  const handleMouseDownHand = (card: GameCard, e: React.MouseEvent) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setDragState({
      isDragging: true,
      cardId: card.id,
      sourceZone: 'hand',
      card,
      currentX: e.clientX,
      currentY: e.clientY,
      cardPosition: { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 },
      mouseOffset: { x: e.clientX - rect.left, y: e.clientY - rect.top },
    });
  };

  const handleMouseDownCommander = (card: GameCard, e: React.MouseEvent) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setDragState({
      isDragging: true,
      cardId: card.id,
      sourceZone: 'commander',
      card,
      currentX: e.clientX,
      currentY: e.clientY,
      cardPosition: { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 },
      mouseOffset: { x: e.clientX - rect.left, y: e.clientY - rect.top },
    });
  };

  const handleMouseDownGraveyard = (card: GameCard, e: React.MouseEvent) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setDragState({
      isDragging: true,
      cardId: card.id,
      sourceZone: 'graveyard',
      card,
      currentX: e.clientX,
      currentY: e.clientY,
      cardPosition: { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 },
      mouseOffset: { x: e.clientX - rect.left, y: e.clientY - rect.top },
    });
  };

  const handleMouseDownExile = (card: GameCard, e: React.MouseEvent) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setDragState({
      isDragging: true,
      cardId: card.id,
      sourceZone: 'exile',
      card,
      currentX: e.clientX,
      currentY: e.clientY,
      cardPosition: { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 },
      mouseOffset: { x: e.clientX - rect.left, y: e.clientY - rect.top },
    });
  };

  const isOverElement = (x: number, y: number, ref: React.RefObject<HTMLDivElement | null>) => {
    if (!ref.current) return false;
    const rect = ref.current.getBoundingClientRect();
    return x >= rect.left && x <= rect.right && y >= rect.top && y <= rect.bottom;
  };

  useEffect(() => {
    if (!dragState) {
      setHoveredZone(null);
      return;
    }

    const handleMouseMove = (e: MouseEvent) => {
      const x = e.clientX;
      const y = e.clientY;

      // Update drag position (always viewport coords)
      setDragState(prev => prev ? { ...prev, currentX: x, currentY: y } : null);

      // Check which zone we're hovering over
      if (battlefieldRef.current) {
        const bfRect = battlefieldRef.current.getBoundingClientRect();
        if (x >= bfRect.left && x <= bfRect.right && y >= bfRect.top && y <= bfRect.bottom) {
          setHoveredZone('battlefield');
          return;
        }
      }

      if (isCurrentUser && isOverElement(x, y, handRef)) {
        setHoveredZone('hand');
        return;
      }
      if (isCurrentUser && isOverElement(x, y, commanderRef)) {
        setHoveredZone('commander');
        return;
      }
      if (isCurrentUser && isOverElement(x, y, graveyardRef)) {
        setHoveredZone('graveyard');
        return;
      }
      if (isCurrentUser && isOverElement(x, y, exileRef)) {
        setHoveredZone('exile');
        return;
      }

      setHoveredZone(null);
    };

    const handleMouseUp = async (e: MouseEvent) => {
      if (!dragState || !gameId) {
        setDragState(null);
        return;
      }

      const gameIdNum = parseInt(gameId);
      const x = e.clientX;
      const y = e.clientY;

      // Check battlefield first
      if (battlefieldRef.current) {
        const bfRect = battlefieldRef.current.getBoundingClientRect();
        const isInsideBf = x >= bfRect.left && x <= bfRect.right && y >= bfRect.top && y <= bfRect.bottom;

        if (isInsideBf) {
          if (dragState.sourceZone === 'hand' || dragState.sourceZone === 'commander') {
            const localX = x - bfRect.left - dragState.mouseOffset.x;
            const localY = y - bfRect.top - dragState.mouseOffset.y;
            setDragState(null);
            await playCard(gameIdNum, dragState.cardId, localX, localY);
            return;
          }

          if (dragState.sourceZone === 'battlefield') {
            const localX = x - bfRect.left - dragState.mouseOffset.x;
            const localY = y - bfRect.top - dragState.mouseOffset.y;
            const isValidPosition = localX >= 0 && localX <= bfRect.width - 64 && localY >= 0 && localY <= bfRect.height - 96;

            if (isValidPosition) {
              await updateBattlefieldPosition(gameIdNum, dragState.cardId, localX, localY);
              setDragState(null);
              return;
            }
          }

          // Handle cards from graveyard, exile, etc. to battlefield
          if (dragState.sourceZone === 'graveyard' || dragState.sourceZone === 'exile') {
            const localX = x - bfRect.left - dragState.mouseOffset.x;
            const localY = y - bfRect.top - dragState.mouseOffset.y;
            setDragState(null);
            await moveCard(gameIdNum, dragState.cardId, 'battlefield', 0);
            // Position will be set at a default location; precise placement would require additional logic
            return;
          }
        }
      }

      // Check other zones (snap to position)
      if (isCurrentUser && isOverElement(x, y, handRef)) {
        setDragState(null);
        await moveCard(gameIdNum, dragState.cardId, 'hand', 0);
        return;
      }
      if (isCurrentUser && isOverElement(x, y, commanderRef)) {
        setDragState(null);
        await moveCard(gameIdNum, dragState.cardId, 'commander', 0);
        return;
      }
      if (isCurrentUser && isOverElement(x, y, graveyardRef)) {
        setDragState(null);
        await moveCard(gameIdNum, dragState.cardId, 'graveyard', 0);
        return;
      }
      if (isCurrentUser && isOverElement(x, y, exileRef)) {
        setDragState(null);
        await moveCard(gameIdNum, dragState.cardId, 'exile', 0);
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
  }, [dragState, gameId, isCurrentUser]);

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

      {/* Card Preview */}

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

      {/* Game Board */}
      
      <div className="w-full h-full flex">
        <div className="flex-1 flex flex-col min-h-0 pr-2">

          {/* Player Zones */}

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
                  hoveredZone={isCurrentUserPlayer ? hoveredZone : null}
                />
              );
            })}
        </div>
        
        <GameSideBar
          gameState={gameState}
          isCurrentUserActive={isCurrentUserActive}
          currentPlayer={currentPlayer}
          handleDrawCard={handleDrawCard}
          handleUntapAll={handleUntapAll}
          handlePassPriority={handlePassPriority}
          isLoading={isLoading}
        />
        
      </div>
    </div>
  );
};

export default GamePage;
