import type { PlayerGameState } from "../../types/gameState";
import type { CardZone } from "../../types/gameState";
import type { GameCard } from "../../types/gameState";
import { Card } from "./Card";

export const Graveyard: React.FC<{ 
    player: PlayerGameState; 
    cardScale: number 
    graveyardRef?: React.RefObject<HTMLDivElement | null> | ((el: HTMLDivElement | null) => void);
    hoveredZone?: CardZone | null;
    isCurrentUser: boolean;
    onMouseDownGraveyard?: (card: GameCard, e: React.MouseEvent) => void;
    onHoverCard?: (card: GameCard | { id: number; card_name: string; image_uris?: { normal?: string }; card_faces?: Array<{ image_uris?: { normal?: string } }>; mana_cost?: string; type_line?: string } | null, position: { x: number; y: number }) => void;
    className?: string;
}> = ({ player, cardScale, graveyardRef, hoveredZone, isCurrentUser, onMouseDownGraveyard, onHoverCard, className = '' }) => {
    return (
        <div 
            ref={graveyardRef as any}
            className={`w-24 h-36 relative overflow-hidden flex flex-col justify-end items-end transition-colors ${className} ${
                hoveredZone === 'graveyard' ? 'bg-yellow-900/50 border-2 border-yellow-400' : ''
            }`}
            style={{top: 65}}
        >
            <span className="text-xs text-gray-500 uppercase absolute top-0 right-2">
                Grave ({player.graveyard.length})
            </span>
            <div className="flex -mt-8 justify-end">
                {player.graveyard.slice(0, 3).map((card) => (
                    <Card 
                        key={card.id} 
                        card={card} 
                        size="sm"
                        scale={cardScale}
                        onMouseDown={isCurrentUser ? (e) => onMouseDownGraveyard?.(card, e) : undefined}
                        onHover={onHoverCard}
                    />
                ))}
            </div>
        </div>
    );
};
