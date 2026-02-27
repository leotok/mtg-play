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
    className?: string;
}> = ({ player, exileRef, hoveredZone, isCurrentUser, onMouseDownExile, onHoverCard, className = '' }) => {
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
                {player.exile.length == 0 && (
                    <div className="border-dashed border-2 border-gray-500 rounded" style={{width: cardWidth, height: cardHeight}}></div>
                )}
                {player.exile.slice(-1).map((card) => (
                    <Card 
                        key={card.id} 
                        card={card} 
                        size="sm"
                        onMouseDown={isCurrentUser ? (e) => onMouseDownExile?.(card, e) : undefined}
                        onHover={onHoverCard}
                    />
                ))}
            </div>
        </div>
    );
};
