import type { PlayerGameState } from "../../types/gameState";
import type { CardZone } from "../../types/gameState";
import type { GameCard } from "../../types/gameState";
import { Card } from "./Card";
import { useSettingsStore } from "../../store/settingsStore";

export const Exile: React.FC<{ 
    player: PlayerGameState; 
    exileRef?: React.RefObject<HTMLDivElement | null> | ((el: HTMLDivElement | null) => void);
    hoveredZone?: CardZone | null;
    isCurrentUser: boolean;
    onMouseDownExile?: (card: GameCard, e: React.MouseEvent) => void;
    onHoverCard?: (card: GameCard | { id: number; card_name: string; image_uris?: { normal?: string }; card_faces?: Array<{ image_uris?: { normal?: string } }>; mana_cost?: string; type_line?: string } | null) => void;
    dragState?: {
        isDragging: boolean;
        cardId: number;
        sourceZone: CardZone;
    } | null;
    className?: string;
}> = ({ player, exileRef, hoveredZone, isCurrentUser, onMouseDownExile, onHoverCard, dragState, className = '' }) => {
    const cardHeight = useSettingsStore(state => state.getCardHeight());
    const cardWidth = useSettingsStore(state => state.getCardWidth());
    
    return (
        <div 
            ref={exileRef as any}
            className={`w-auto relative flex flex-col justify-end items-end transition-colors ${className} ${
                hoveredZone === 'exile' ? 'bg-yellow-900/50 border-none' : ''
            }`}
            style={{top: 65, height: cardHeight}}
        >
            <span className="text-xs text-white absolute -top-5 right-2">
                Exile ({player.exile.length})
            </span>
            <div className="flex -mt-8 justify-end">
                {player.exile.length > 0 && (
                    <>
                        {(() => {
                            const topCard = player.exile[player.exile.length - 1];
                            const isDraggingTop = dragState?.isDragging && dragState?.cardId === topCard.id;
                            
                            if (isDraggingTop && player.exile.length > 1) {
                                const cardBelow = player.exile[player.exile.length - 2];
                                return (
                                    <Card 
                                        key={cardBelow.id} 
                                        card={cardBelow} 
                                        size="sm"
                                        onMouseDown={isCurrentUser ? (e) => onMouseDownExile?.(cardBelow, e) : undefined}
                                        onHover={onHoverCard}
                                    />
                                );
                            }
                            
                            if (isDraggingTop) {
                                return (
                                    <div className="border-dashed border-2 border-gray-500 rounded" style={{width: cardWidth, height: cardHeight}}></div>
                                );
                            }
                            
                            return (
                                <Card 
                                    key={topCard.id} 
                                    card={topCard} 
                                    size="sm"
                                    onMouseDown={isCurrentUser ? (e) => onMouseDownExile?.(topCard, e) : undefined}
                                    onHover={onHoverCard}
                                />
                            );
                        })()}
                    </>
                )}
                {player.exile.length === 0 && (
                    <div className="border-dashed border-2 border-gray-500 rounded" style={{width: cardWidth, height: cardHeight}}></div>
                )}
            </div>
        </div>
    );
};
