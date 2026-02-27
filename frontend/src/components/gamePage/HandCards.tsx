import { useState, useEffect, useRef } from 'react';
import { Card } from './Card';
import { type PlayerGameState } from '../../types/gameState';
import { type CardZone } from '../../types/gameState';
import { type GameCard, type GameCardInBattlefield } from '../../types/gameState';
import { useSettingsStore } from '../../store/settingsStore';
import { CARD_SIZES } from '../../config';


export const HandCards: React.FC<{
    player: PlayerGameState;
    isCurrentUser: boolean;
    handRef?: React.RefObject<HTMLDivElement | null> | ((el: HTMLDivElement | null) => void);
    hoveredZone?: CardZone | null;
    dragState?: {
        isDragging: boolean;
        cardId: number;
        sourceZone: CardZone;
        card: GameCard | GameCardInBattlefield | null;
        currentX: number;
        currentY: number;
        cardPosition: { x: number; y: number };
        mouseOffset: { x: number; y: number };
    } | null;
    onMouseDownHand?: (card: GameCard, e: React.MouseEvent) => void;
    onHoverCard?: (card: GameCard | { id: number; card_name: string; image_uris?: { normal?: string }; card_faces?: Array<{ image_uris?: { normal?: string } }>; mana_cost?: string; type_line?: string } | null, position: { x: number; y: number }) => void;
}> = ({player, isCurrentUser, handRef, hoveredZone, dragState, onMouseDownHand, onHoverCard }) => {
    const cardHeight = useSettingsStore(state => state.getCardHeight());
    const cardScale = useSettingsStore(state => state.cardScale);
    const handHeight = cardHeight * 0.7;
    const opponentHandHeight = cardHeight * 0.45;

    const opponentContainerRef = useRef<HTMLDivElement>(null);
    
    
    const cardWidth = CARD_SIZES.sm.width * (cardScale / 100);
    const handCardCount = player.hand.length;
    const minOffset = 10;
    const maxOffset = 50;
    const maxHandWidth = 500;

    const availableWidthPerCard = maxHandWidth / handCardCount
    const cardOffset = Math.min(maxOffset, Math.max(minOffset, availableWidthPerCard));
    console.log('cardOffset', isCurrentUser, cardOffset);


    const handIndexArray = player.hand.map((_, idx) => {
        return (idx - (player.hand.length/2));
    });
    
    if (isCurrentUser) {
        return (
            <div 
                className={`flex justify-center gap-1 p-1 rounded transition-colors overflow-hidden flex-auto max-w-[58%] ${
                    hoveredZone === 'hand' ? 'bg-yellow-900/50 border-none' : ''
                }`}

                ref={handRef} 
                style={{height: handHeight}}
            >
            {player.hand.map((card, idx) => {
                const isDraggingThis = dragState?.isDragging && dragState?.cardId === card.id;
                if (isDraggingThis) return null;
                return (
                <Card 
                    key={card.id} 
                    card={card} 
                    size="sm"
                    onMouseDown={(e) => onMouseDownHand?.(card, e)}
                    onHover={onHoverCard}
                    handIndex={handIndexArray[idx]}
                    zIndex={idx}
                    inHand={true}
                    horizontalOffset={-cardOffset}
                />
                );
            })}
            </div>
        )
    }
    return (
        <div className="overflow-hidden flex-auto max-w-[58%]">
            <div 
                ref={opponentContainerRef}
                className="flex justify-center gap-1 p-1 rounded transition-colors" 
                style={{height: opponentHandHeight}}
            >
                {player.hand.map((card, idx) => {
                const isDraggingThis = dragState?.isDragging && dragState?.cardId === card.id;
                if (isDraggingThis) return null;
                return (
                    <Card 
                        key={card.id} 
                        card={card} 
                        size="sm"
                        hidden={true}
                        onHover={onHoverCard}
                        handIndex={handIndexArray[idx]}
                        zIndex={idx}
                        inHand={true}
                    />
                );
                })}
            </div>
        </div>
    )
};