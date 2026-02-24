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
}> = ({ player, cardScale, graveyardRef, hoveredZone, isCurrentUser, onMouseDownGraveyard, onHoverCard }) => {
    return (
        
        <div className="mt-2">
            <h4 className="text-xs text-gray-500 uppercase mb-1">Grave</h4>
            <div 
            ref={graveyardRef as any} 
            className={`flex justify-center gap-1 min-h-[100px] p-1 bg-gray-900/50 rounded transition-colors ${
                hoveredZone === 'graveyard' ? 'border-2 border-yellow-400 bg-yellow-900/30' : ''
            }`}
            >
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