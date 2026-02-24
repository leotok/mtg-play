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
}> = ({ player, commanderRef, cardScale, hoveredZone, isCurrentUser, onMouseDownCommander, onHoverCard }) => {
    return (
        <div>
           
            <h4 className="text-xs text-gray-500 uppercase mb-1 mt-2 text-center">Cmd</h4>
            <div 
                ref={commanderRef as any} 
                className={`flex justify-center gap-1 min-h-[100px] p-1 bg-gray-900/50 rounded transition-colors ${
                hoveredZone === 'commander' ? 'border-2 border-yellow-400 bg-yellow-900/30' : ''
                }`}
            >
                {player.commander.map((card) => (
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