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
    } | null;
    isCurrentUser: boolean;
    battlefieldRef?: React.RefObject<HTMLDivElement | null>;
}> = ({ dragState, isCurrentUser, battlefieldRef }) => {
    const [battlefieldRect, setBattlefieldRect] = useState<DOMRect | null>(null);
    
    useEffect(() => {
        if (battlefieldRef?.current) {
            setBattlefieldRect(battlefieldRef.current.getBoundingClientRect());
        }
    }, [battlefieldRef]);
    
    if (dragState && dragState.isDragging && isCurrentUser && dragState.card) {
        let left, top;
        
        if (dragState.card.is_tapped && dragState.originalLogicalPosition && dragState.sourceZone === 'battlefield' && battlefieldRect) {
            // Use same logic as mouse up: apply screen delta to original logical position
            const screenDeltaX = dragState.currentX - dragState.initialMouseX;
            const screenDeltaY = dragState.currentY - dragState.initialMouseY;
            
            const originalX = dragState.originalLogicalPosition.x;
            const originalY = dragState.originalLogicalPosition.y;
            
            // Calculate the logical position
            const logicalX = originalX + screenDeltaX;
            const logicalY = originalY + screenDeltaY;
            
            // Convert logical coordinates (relative to battlefield) to screen coordinates
            left = battlefieldRect.left + logicalX;
            top = battlefieldRect.top + logicalY;
        } else {
            // Use original logic for non-tapped cards or other zones
            left = dragState.currentX - dragState.mouseOffset.x;
            top = dragState.currentY - dragState.mouseOffset.y;
        }
        
        return (
                <div
                  className="fixed pointer-events-none z-50"
                  style={{
                    left: left,
                    top: top,
                  }}
                >
                  <Card card={dragState.card} size="sm" isDragging />
                </div>
        )}
    return null;
};