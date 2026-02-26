import type React from "react";
import type { CardZone, GameCard, GameCardInBattlefield, PlayerGameState } from "../../types/gameState";
import { Card } from "./Card";


export const Battlefield: React.FC<{
    player: PlayerGameState;
    isCurrentUser: boolean;
    battlefieldRef?: React.RefObject<HTMLDivElement | null> | ((el: HTMLDivElement | null) => void);
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
    onTapCard?: (cardId: number) => void;
    onMouseDownCard?: (card: GameCard | GameCardInBattlefield, e: React.MouseEvent) => void;
    onHoverCard?: (card: GameCard | { id: number; card_name: string; image_uris?: { normal?: string }; card_faces?: Array<{ image_uris?: { normal?: string } }>; mana_cost?: string; type_line?: string } | null, position: { x: number; y: number }) => void;
}> = ({player, isCurrentUser, battlefieldRef, dragState, onTapCard, onMouseDownCard, onHoverCard}) => {

    return (
        <div className="h-[95%] min-h-0 pb-1">
            <h4 className="text-xs text-gray-500 uppercase mb-1">Battlefield ({player.battlefield.length})</h4>
            <div 
                ref={battlefieldRef}
                className={`h-[calc(100%-1.5rem)] p-1 border-2 rounded-lg relative select-none transition-colors border-none`}
            >
                {player.battlefield.map((card) => {
                const isDraggingThis = dragState?.isDragging && dragState?.cardId === card.id;
                if (isDraggingThis) return null;
                return (
                    <div
                    key={card.id}
                    className="absolute"
                    style={{ 
                        left: card.battlefield_x || 5, 
                        top: card.battlefield_y || 5,
                        transition: 'all 0.1s ease',
                        zIndex: 1,
                    }}
                    >
                    <Card 
                        card={card} 
                        size="sm"
                        onTap={() => onTapCard?.(card.id)}
                        onMouseDown={isCurrentUser ? (e) => onMouseDownCard?.(card, e) : undefined}
                        onHover={onHoverCard}
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
    )
};