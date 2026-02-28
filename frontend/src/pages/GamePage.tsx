import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useGameStateStore } from '../store/gameStateStore';
import { socketService } from '../services/socket';
import { type GameCard, type CardZone, type GameCardInBattlefield } from '../types/gameState';
import { CardPreview } from '../components/gamePage/CardPreview';
import { PlayerZone } from '../components/gamePage/PlayerZone';
import { GameSideBar } from '../components/gamePage/GameSideBar';
import { CARD_SIZES } from '../config';


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
    moveCards,
  } = useGameStateStore();

  const [hoveredCard, setHoveredCard] = useState<GameCard | { id: number; card_name: string; image_uris?: { normal?: string }; card_faces?: Array<{ image_uris?: { normal?: string } }>; mana_cost?: string; type_line?: string } | null>(null);

  const [dragState, setDragState] = useState<{
    isDown: boolean
    isDragging: boolean;
    cardId: number;
    sourceZone: CardZone;
    card: GameCard | GameCardInBattlefield | null;
    currentX: number;
    currentY: number;
    initialMouseX: number;
    initialMouseY: number;
    cardPosition: { x: number; y: number };
    mouseOffset: { x: number; y: number };
    originalLogicalPosition?: { x: number; y: number };
    selectedCards?: Array<{ id: number; originalX: number; originalY: number; isTapped: boolean }>;
  } | null>(null);

  const [hoveredZone, setHoveredZone] = useState<CardZone | null>(null);

  const [selectedCardIds, setSelectedCardIds] = useState<Set<number>>(new Set());
  const [selectionBox, setSelectionBox] = useState<{ startX: number; startY: number; currentX: number; currentY: number } | null>(null);
  const [isSelecting, setIsSelecting] = useState(false);

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
    
    if (e.shiftKey && isCurrentUser) {
      if (selectedCardIds.has(card.id)) {
        const newSelection = new Set(selectedCardIds);
        newSelection.delete(card.id);
        setSelectedCardIds(newSelection);
      } else {
        const newSelection = new Set(selectedCardIds);
        newSelection.add(card.id);
        setSelectedCardIds(newSelection);
      }
      return;
    }

    if (selectedCardIds.size > 0 && !selectedCardIds.has(card.id)) {
      setSelectedCardIds(new Set());
    }

    const currentUserPlayer = gameState?.players.find(p => p.user_id === user?.id);
    let selectedCards: Array<{ id: number; originalX: number; originalY: number; isTapped: boolean; cardData: GameCardInBattlefield }> = [];
    
    if (selectedCardIds.has(card.id) && selectedCardIds.size > 1 && currentUserPlayer) {
      selectedCards = currentUserPlayer.battlefield
        .filter(c => selectedCardIds.has(c.id))
        .map(c => ({
          id: c.id,
          originalX: c.battlefield_x || 0,
          originalY: c.battlefield_y || 0,
          isTapped: c.is_tapped || false,
          cardData: c,
        }));
    }
    
    setDragState({
      isDown: true,
      isDragging: false,
      cardId: card.id,
      sourceZone: 'battlefield',
      card,
      currentX: e.clientX,
      currentY: e.clientY,
      initialMouseX: e.clientX,
      initialMouseY: e.clientY,
      cardPosition: { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 },
      mouseOffset: { x: e.clientX - rect.left, y: e.clientY - rect.top },
      originalLogicalPosition: { x: card.battlefield_x || 0, y: card.battlefield_y || 0 },
      selectedCards: selectedCards.length > 0 ? selectedCards : undefined,
    });
  };

  const handleMouseDownEmptyBattlefield = (e: React.MouseEvent) => {
    if (!battlefieldRef.current) return;
    
    if (e.shiftKey) return;

    const target = e.target as HTMLElement;
    if (target.closest('[data-card-id]')) return;
    
    setSelectedCardIds(new Set());
    setSelectionBox({
      startX: e.clientX,
      startY: e.clientY,
      currentX: e.clientX,
      currentY: e.clientY,
    });
    setIsSelecting(true);
  };

  const handleMouseDownHand = (card: GameCard, e: React.MouseEvent) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setDragState({
      isDown: true,
      isDragging: true,
      cardId: card.id,
      sourceZone: 'hand',
      card,
      currentX: e.clientX,
      currentY: e.clientY,
      initialMouseX: e.clientX,
      initialMouseY: e.clientY,
      cardPosition: { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 },
      mouseOffset: { x: e.clientX - rect.left, y: e.clientY - rect.top },
    });
  };

  const handleMouseDownCommander = (card: GameCard, e: React.MouseEvent) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setDragState({
      isDown: true,
      isDragging: true,
      cardId: card.id,
      sourceZone: 'commander',
      card,
      currentX: e.clientX,
      currentY: e.clientY,
      initialMouseX: e.clientX,
      initialMouseY: e.clientY,
      cardPosition: { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 },
      mouseOffset: { x: e.clientX - rect.left, y: e.clientY - rect.top },
    });
  };

  const handleMouseDownGraveyard = (card: GameCard, e: React.MouseEvent) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setDragState({
      isDown: true,
      isDragging: true,
      cardId: card.id,
      sourceZone: 'graveyard',
      card,
      currentX: e.clientX,
      currentY: e.clientY,
      initialMouseX: e.clientX,
      initialMouseY: e.clientY,
      cardPosition: { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 },
      mouseOffset: { x: e.clientX - rect.left, y: e.clientY - rect.top },
    });
  };

  const handleMouseDownExile = (card: GameCard, e: React.MouseEvent) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setDragState({
      isDown: true,
      isDragging: true,
      cardId: card.id,
      sourceZone: 'exile',
      card,
      currentX: e.clientX,
      currentY: e.clientY,
      initialMouseX: e.clientX,
      initialMouseY: e.clientY,
      cardPosition: { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 },
      mouseOffset: { x: e.clientX - rect.left, y: e.clientY - rect.top },
    });
  };

  const isOverElement = (x: number, y: number, ref: React.RefObject<HTMLDivElement | null>) => {
    if (!ref.current) return false;
    const rect = ref.current.getBoundingClientRect();
    return x >= rect.left && x <= rect.right && y >= rect.top && y <= rect.bottom;
  };

  // Selection box handling
  useEffect(() => {
    if (!isSelecting || !selectionBox) return;

    const handleSelectionMouseMove = (e: MouseEvent) => {
      setSelectionBox(prev => prev ? { ...prev, currentX: e.clientX, currentY: e.clientY } : null);
    };

    const handleSelectionMouseUp = () => {
      if (!battlefieldRef.current || !selectionBox) {
        setIsSelecting(false);
        setSelectionBox(null);
        return;
      }

      const bfRect = battlefieldRef.current.getBoundingClientRect();
      const minX = Math.min(selectionBox.startX, selectionBox.currentX);
      const maxX = Math.max(selectionBox.startX, selectionBox.currentX);
      const minY = Math.min(selectionBox.startY, selectionBox.currentY);
      const maxY = Math.max(selectionBox.startY, selectionBox.currentY);

      const currentUserPlayer = gameState?.players.find(p => p.user_id === user?.id);
      if (currentUserPlayer) {
        const newSelection = new Set<number>();
        currentUserPlayer.battlefield.forEach(card => {
          const cardEl = battlefieldRef.current?.querySelector(`[data-card-id="${card.id}"]`);
          if (cardEl) {
            const cardRect = cardEl.getBoundingClientRect();
            const cardCenterX = cardRect.left + cardRect.width / 2;
            const cardCenterY = cardRect.top + cardRect.height / 2;
            
            if (cardCenterX >= minX && cardCenterX <= maxX && cardCenterY >= minY && cardCenterY <= maxY) {
              newSelection.add(card.id);
            }
          }
        });
        setSelectedCardIds(newSelection);
      }

      setIsSelecting(false);
      setSelectionBox(null);
    };

    window.addEventListener('mousemove', handleSelectionMouseMove);
    window.addEventListener('mouseup', handleSelectionMouseUp);

    return () => {
      window.removeEventListener('mousemove', handleSelectionMouseMove);
      window.removeEventListener('mouseup', handleSelectionMouseUp);
    };
  }, [isSelecting, selectionBox, gameState, user?.id]);

  useEffect(() => {
    if (!dragState) {
      setHoveredZone(null);
      return;
    }

    const handleMouseMove = (e: MouseEvent) => {
      const x = e.clientX;
      const y = e.clientY;

      const isDragging = dragState.isDown;
      setDragState(prev => prev ? { ...prev, currentX: x, currentY: y, isDragging } : null);

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
            await playCard(gameIdNum, dragState.cardId, localX, localY);
            setDragState(null);
            return;
          }

          if (dragState.sourceZone === 'battlefield') {

            // Calculate movement delta in screen coordinates
            const screenDeltaX = x - dragState.initialMouseX;
            const screenDeltaY = y - dragState.initialMouseY;
            
            // Calculate new position by applying delta to original logical position
            const originalX = dragState.originalLogicalPosition?.x || 0;
            const originalY = dragState.originalLogicalPosition?.y || 0;
            
            let localX = originalX + screenDeltaX;
            let localY = originalY + screenDeltaY;
            
            var cardWidth = Number(CARD_SIZES['sm'].width);
            var cardHeight = Number(CARD_SIZES['sm'].height);

            if (dragState.card?.is_tapped) {              
              const temp = cardHeight;
              cardHeight = cardWidth;
              cardWidth = temp;
            }

            let isValidPosition = (
              0 <= localX && 
              localX <= bfRect.width - cardWidth + 16 && 
              localY >= 0 - 32 && 
              localY <= bfRect.height + cardHeight
            );
            
            if (isValidPosition) {
              if (dragState.selectedCards && dragState.selectedCards.length > 1) {
                const screenDeltaX = x - dragState.initialMouseX;
                const screenDeltaY = y - dragState.initialMouseY;
                
                for (const selected of dragState.selectedCards) {
                  const origX = selected.originalX;
                  const origY = selected.originalY;
                  const newX = origX + screenDeltaX;
                  const newY = origY + screenDeltaY;
                  await updateBattlefieldPosition(gameIdNum, selected.id, newX, newY);
                }
              } else {
                await updateBattlefieldPosition(gameIdNum, dragState.cardId, localX, localY);
              }
              setDragState(null);
              return;
            }
          }

          // Handle cards from graveyard, exile, etc. to battlefield
          if (dragState.sourceZone === 'graveyard' || dragState.sourceZone === 'exile') {
            const localX = x - bfRect.left - dragState.mouseOffset.x;
            const localY = y - bfRect.top - dragState.mouseOffset.y;
            await moveCard(gameIdNum, dragState.cardId, 'battlefield', 0);
            await updateBattlefieldPosition(gameIdNum, dragState.cardId, localX, localY);
            setDragState(null);
            return;
          }
        }
      }

      // Check other zones (snap to position)
      if (isCurrentUser && isOverElement(x, y, handRef)) {
        if (dragState.sourceZone === 'battlefield' && selectedCardIds.size > 1) {
          const moves = Array.from(selectedCardIds).map(cardId => ({
            card_id: cardId,
            target_zone: 'hand',
            position: 0
          }));
          await moveCards(gameIdNum, moves);
          setSelectedCardIds(new Set());
        } else {
          await moveCard(gameIdNum, dragState.cardId, 'hand', 0);
        }
        setDragState(null);
        return;
      }
      if (isCurrentUser && isOverElement(x, y, commanderRef)) {
        if (dragState.sourceZone === 'battlefield' && selectedCardIds.size > 1) {
          const moves = Array.from(selectedCardIds).map(cardId => ({
            card_id: cardId,
            target_zone: 'commander',
            position: 0
          }));
          await moveCards(gameIdNum, moves);
          setSelectedCardIds(new Set());
        } else {
          await moveCard(gameIdNum, dragState.cardId, 'commander', 0);
        }
        setDragState(null);
        return;
      }
      if (isCurrentUser && isOverElement(x, y, graveyardRef)) {
        if (dragState.sourceZone === 'battlefield' && selectedCardIds.size > 1) {
          const moves = Array.from(selectedCardIds).map(cardId => ({
            card_id: cardId,
            target_zone: 'graveyard',
            position: 0
          }));
          await moveCards(gameIdNum, moves);
          setSelectedCardIds(new Set());
        } else {
          await moveCard(gameIdNum, dragState.cardId, 'graveyard', 0);
        }
        setDragState(null);
        return;
      }
      if (isCurrentUser && isOverElement(x, y, exileRef)) {
        if (dragState.sourceZone === 'battlefield' && selectedCardIds.size > 1) {
          const moves = Array.from(selectedCardIds).map(cardId => ({
            card_id: cardId,
            target_zone: 'exile',
            position: 0
          }));
          await moveCards(gameIdNum, moves);
          setSelectedCardIds(new Set());
        } else {
          await moveCard(gameIdNum, dragState.cardId, 'exile', 0);
        }
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
  }, [dragState, gameId, isCurrentUser, selectedCardIds]);

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
        const isCommander = gameState.players.some(p => p.commander.some(c => c.id === hoveredCard.id));
        const isCurrentUserCard = currentUser && (
          currentUser.hand.some(c => c.id === hoveredCard.id) ||
          currentUser.battlefield.some(c => c.id === hoveredCard.id) ||
          currentUser.commander.some(c => c.id === hoveredCard.id) ||
          currentUser.graveyard.some(c => c.id === hoveredCard.id) ||
          currentUser.exile.some(c => c.id === hoveredCard.id) ||
          currentUser.library.some(c => c.id === hoveredCard.id)
        );
        return <CardPreview card={hoveredCard} isCurrentUserCard={isCurrentUserCard} isCommander={isCommander} />;
      })()}

      {/* Game Board */}
      
      <div className="w-full h-full flex">
        <div className="max-w-[90%] flex-1 flex flex-col min-h-0 pr-2">

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
                  onHoverCard={(card) => setHoveredCard(card)}
                  onMouseDownCard={isCurrentUserPlayer ? handleMouseDownBattlefield : undefined}
                  onMouseDownEmptyBattlefield={isCurrentUserPlayer ? handleMouseDownEmptyBattlefield : undefined}
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
                  selectedCardIds={isCurrentUserPlayer ? selectedCardIds : new Set()}
                />
              );
            })}
        </div>
        
        <GameSideBar
          gameState={gameState}
          isCurrentUserActive={isCurrentUserActive}
          currentPlayer={currentPlayer}
          currentPlayerId={user?.id || 0}
          handleDrawCard={handleDrawCard}
          handleUntapAll={handleUntapAll}
          handlePassPriority={handlePassPriority}
          isLoading={isLoading}
        />
        
      </div>

      {/* Selection Box Overlay */}
      {selectionBox && isSelecting && (
        <div
          className="fixed pointer-events-none border-2 border-cyan-400 bg-cyan-400/20 z-[9999]"
          style={{
            left: Math.min(selectionBox.startX, selectionBox.currentX),
            top: Math.min(selectionBox.startY, selectionBox.currentY),
            width: Math.abs(selectionBox.currentX - selectionBox.startX),
            height: Math.abs(selectionBox.currentY - selectionBox.startY),
          }}
        />
      )}
    </div>
  );
};

export default GamePage;
