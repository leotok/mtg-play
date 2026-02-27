import type React from "react";
import type { GameCard, GameCardInBattlefield, CardZone } from "../../types/gameState";
import { Card } from "./Card";
import { useEffect, useState } from "react";

export const DraggingCard: React.FC<{ 
    dragState?: {
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
        selectedCards?: Array<{ id: number; originalX: number; originalY: number; isTapped: boolean; cardData: GameCardInBattlefield }>;
    } | null;
    isCurrentUser: boolean;
    battlefieldRef?: React.RefObject<HTMLDivElement | null>;
}> = ({ dragState, isCurrentUser, battlefieldRef }) => {
    
    const [battlefieldRect, setBattlefieldRect] = useState<DOMRect | null>(null);
    
    useEffect(() => {
        if (battlefieldRef?.current) {
            setBattlefieldRect(battlefieldRef.current.getBoundingClientRect());
        }
    }, [battlefieldRef, dragState]);
    
    if (!dragState || !dragState.isDragging || !isCurrentUser || !dragState.card) {
        return null;
    }

    const renderDragCard = (card: GameCard | GameCardInBattlefield, offsetX: number, offsetY: number): React.ReactNode => {
        let left: number;
        let top: number;
        
        if (card.is_tapped && battlefieldRect && dragState.sourceZone === 'battlefield' && dragState.originalLogicalPosition) {
            const screenDeltaX = dragState.currentX - dragState.initialMouseX;
            const screenDeltaY = dragState.currentY - dragState.initialMouseY;
            const originalX = dragState.originalLogicalPosition.x;
            const originalY = dragState.originalLogicalPosition.y;
            const logicalX = originalX + screenDeltaX + offsetX;
            const logicalY = originalY + screenDeltaY + offsetY;
            left = battlefieldRect.left + logicalX;
            top = battlefieldRect.top + logicalY;
        } else if (dragState.sourceZone === 'battlefield' && dragState.originalLogicalPosition) {
            const screenDeltaX = dragState.currentX - dragState.initialMouseX;
            const screenDeltaY = dragState.currentY - dragState.initialMouseY;
            const originalX = dragState.originalLogicalPosition.x;
            const originalY = dragState.originalLogicalPosition.y;
            const logicalX = originalX + screenDeltaX + offsetX;
            const logicalY = originalY + screenDeltaY + offsetY;
            left = battlefieldRect ? battlefieldRect.left + logicalX : dragState.currentX - dragState.mouseOffset.x + offsetX;
            top = battlefieldRect ? battlefieldRect.top + logicalY : dragState.currentY - dragState.mouseOffset.y + offsetY;
        } else {
            left = dragState.currentX - dragState.mouseOffset.x + offsetX;
            top = dragState.currentY - dragState.mouseOffset.y + offsetY;
        }
        
        return (
            <div
                key={card.id}
                className="fixed pointer-events-none z-50"
                style={{
                    left: left,
                    top: top,
                }}
            >
                <Card card={card} size="sm" isDragging />
            </div>
        );
    };

    const cards: Array<{ card: GameCard | GameCardInBattlefield; offsetX: number; offsetY: number }> = [];
    
    if (dragState.selectedCards && dragState.selectedCards.length > 0) {
        const mainOriginalX = dragState.originalLogicalPosition?.x || 0;
        const mainOriginalY = dragState.originalLogicalPosition?.y || 0;
        
        dragState.selectedCards.forEach(selected => {
            if (selected.id === dragState.cardId) {
                cards.push({ card: dragState.card!, offsetX: 0, offsetY: 0 });
            } else {
                const offsetX = selected.originalX - mainOriginalX;
                const offsetY = selected.originalY - mainOriginalY;
                cards.push({ card: selected.cardData, offsetX, offsetY });
            }
        });
    } else {
        cards.push({ card: dragState.card, offsetX: 0, offsetY: 0 });
    }
    
    return (
        <>
            {cards.map(({ card, offsetX, offsetY }) => renderDragCard(card, offsetX, offsetY))}
        </>
    );
};
