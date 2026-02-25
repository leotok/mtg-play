import type { PlayerGameState } from "../../types/gameState";
import { Card } from "./Card";
import type { CardZone, GameCard } from "../../types/gameState";


export const CommanderZone: React.FC<{ 
    player: PlayerGameState; 
    commanderRef?: React.RefObject<HTMLDivElement | null> | ((el: HTMLDivElement | null) => void);
    cardScale: number 
    hoveredZone?: CardZone | null;
    isCurrentUser: boolean;
    onMouseDownCommander?: (card: GameCard, e: React.MouseEvent) => void;
    onHoverCard?: (card: GameCard | { id: number; card_name: string; image_uris?: { normal?: string }; card_faces?: Array<{ image_uris?: { normal?: string } }>; mana_cost?: string; type_line?: string } | null, position: { x: number; y: number }) => void;
    className?: string;
}> = ({ player, commanderRef, cardScale, hoveredZone, isCurrentUser, onMouseDownCommander, onHoverCard, className = '' }) => {
    return (
        <div 
            ref={commanderRef as any}
            className={`w-auto h-36 relative flex flex-col justify-end items-end transition-colors ${className} ${
                hoveredZone === 'commander' ? 'bg-yellow-900/50 border-2 border-yellow-400' : ''
            }`}
            style={{top: 65}}
        >
            <span className="text-xs text-gray-500 uppercase absolute -top-5 right-2">
                Commander
            </span>
            <div className="flex -mt-8 justify-end">
                {player.commander.length == 0 && (
                    <div className="w-24 h-36 border-dashed border-2 border-gray-500 rounded"></div>
                )}
                {player.commander.slice(0, 1).map((card) => (
                    <Card 
                        key={card.id} 
                        card={card} 
                        size="sm"
                        scale={cardScale}
                        onMouseDown={isCurrentUser ? (e) => onMouseDownCommander?.(card, e) : undefined}
                        onHover={onHoverCard}
                    />
                ))}
            </div>
        </div>
    );
};
