import type { PlayerGameState } from "../../types/gameState";
import type { CardZone } from "../../types/gameState";
import type { GameCard } from "../../types/gameState";
import { Card } from "./Card";

export const Exile: React.FC<{ 
    player: PlayerGameState; 
    exileRef?: React.RefObject<HTMLDivElement | null> | ((el: HTMLDivElement | null) => void);
    hoveredZone?: CardZone | null;
    isCurrentUser: boolean;
    onMouseDownExile?: (card: GameCard, e: React.MouseEvent) => void;
    onHoverCard?: (card: GameCard | { id: number; card_name: string; image_uris?: { normal?: string }; card_faces?: Array<{ image_uris?: { normal?: string } }>; mana_cost?: string; type_line?: string } | null, position: { x: number; y: number }) => void;
    cardScale: number;
    className?: string;
}> = ({ player, exileRef, hoveredZone, isCurrentUser, onMouseDownExile, onHoverCard, cardScale, className = '' }) => {
    return (
        <div 
            ref={exileRef as any}
            className={`w-auto h-36 relative flex flex-col justify-end items-end transition-colors ${className} ${
                hoveredZone === 'exile' ? 'bg-yellow-900/50 border-2 border-yellow-400' : ''
            }`}
            style={{top: 65}}
        >
            <span className="text-xs text-gray-500 uppercase absolute -top-5 right-2">
                Exile ({player.exile.length})
            </span>
            <div className="flex -mt-8 justify-end">
                {player.exile.length == 0 && (
                    <div className="w-24 h-36 border-dashed border-2 border-gray-500 rounded"></div>
                )}
                {player.exile.slice(0, 3).map((card) => (
                    <Card 
                        key={card.id} 
                        card={card} 
                        size="sm"
                        scale={cardScale}
                        onMouseDown={isCurrentUser ? (e) => onMouseDownExile?.(card, e) : undefined}
                        onHover={onHoverCard}
                    />
                ))}
            </div>
        </div>
    );
};
