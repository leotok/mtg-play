import type { GameCard, GameCardInBattlefield, CardZone } from "../../types/gameState";
import { Card } from "./Card";

export const DraggingCard: React.FC<{ 
    dragState?: {
        isDragging: boolean;
        cardId: number;
        sourceZone: CardZone;
        card: GameCard | GameCardInBattlefield | null;
        currentX: number;
        currentY: number;
    } | null;
    isCurrentUser: boolean;
}> = ({ dragState, isCurrentUser }) => {
    if (dragState && dragState.isDragging && isCurrentUser && dragState.card) {
        return (
                <div
                  className="fixed pointer-events-none z-50"
                  style={{
                    left: dragState.currentX - 20,
                    top: dragState.currentY - 28,
                  }}
                >
                  <Card card={dragState.card} size="sm" isDragging />
                </div>
        )}
    return null;
};