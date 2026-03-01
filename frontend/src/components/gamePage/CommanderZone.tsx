import type { PlayerGameState } from "../../types/gameState";
import { Card } from "./Card";
import type { CardZone, GameCard } from "../../types/gameState";
import { useSettingsStore } from "../../store/settingsStore";


export const CommanderZone: React.FC<{ 
    player: PlayerGameState; 
    commanderRef?: React.RefObject<HTMLDivElement | null> | ((el: HTMLDivElement | null) => void);
    hoveredZone?: CardZone | null;
    isCurrentUser: boolean;
    onMouseDownCommander?: (card: GameCard, e: React.MouseEvent) => void;
    onHoverCard?: (card: GameCard | { id: number; card_name: string; image_uris?: { normal?: string }; card_faces?: Array<{ image_uris?: { normal?: string } }>; mana_cost?: string; type_line?: string } | null) => void;
    dragState?: {
        isDragging: boolean;
        cardId: number;
        sourceZone: CardZone;
    } | null;
    className?: string;
}> = ({ player, commanderRef, hoveredZone, isCurrentUser, onMouseDownCommander, onHoverCard, dragState, className = '' }) => {
    const cardHeight = useSettingsStore(state => state.getCardHeight());
    const cardWidth = useSettingsStore(state => state.getCardWidth());
    
    return (
        <div 
            ref={commanderRef as any}
            className={`w-auto relative flex flex-col justify-end items-end transition-colors ${className} ${
                hoveredZone === 'commander' ? 'bg-yellow-900/50 border-none' : ''
            }`}
            style={{top: 65, height: cardHeight}}
        >
            <span className="text-xs text-white absolute -top-5 right-2">
                Commander
            </span>
            <div className="flex -mt-8 justify-end">
                {player.commander.length > 0 && (
                    <>
                        {(() => {
                            const topCard = player.commander[0];
                            const isDraggingTop = dragState?.isDragging && dragState?.cardId === topCard.id;
                            
                            if (isDraggingTop && player.commander.length > 1) {
                                const cardBelow = player.commander[1];
                                return (
                                    <Card 
                                        key={cardBelow.id} 
                                        card={cardBelow} 
                                        size="sm"
                                        onMouseDown={isCurrentUser ? (e) => onMouseDownCommander?.(cardBelow, e) : undefined}
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
                                    onMouseDown={isCurrentUser ? (e) => onMouseDownCommander?.(topCard, e) : undefined}
                                    onHover={onHoverCard}
                                />
                            );
                        })()}
                    </>
                )}
                {player.commander.length === 0 && (
                    <div className="border-dashed border-2 border-gray-500 rounded" style={{width: cardWidth, height: cardHeight}}></div>
                )}
            </div>
        </div>
    );
};
