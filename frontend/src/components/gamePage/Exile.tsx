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
}> = ({ player, exileRef, hoveredZone, isCurrentUser, onMouseDownExile, onHoverCard, cardScale }) => {
    return (
        <div className="mt-2">
            <h4 className="text-xs text-gray-500 uppercase mb-1">Exile</h4>
            <div 
            ref={exileRef as any} 
            className={`flex justify-center gap-1 min-h-[100px] p-1 bg-gray-900/50 rounded transition-colors ${
                hoveredZone === 'exile' ? 'border-2 border-yellow-400 bg-yellow-900/30' : ''
            }`}
            >
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