import { Card } from './Card';
import { type PlayerGameState } from '../../types/gameState';
import { type CardZone } from '../../types/gameState';
import { type GameCard, type GameCardInBattlefield } from '../../types/gameState';


export const HandCards: React.FC<{
    player: PlayerGameState;
    isCurrentUser: boolean;
    handRef?: React.RefObject<HTMLDivElement | null> | ((el: HTMLDivElement | null) => void);
    hoveredZone?: CardZone | null;
    cardScale?: number;
    dragState?: {
        isDragging: boolean;
        cardId: number;
        sourceZone: CardZone;
        card: GameCard | GameCardInBattlefield | null;
        currentX: number;
        currentY: number;
    } | null;
    onMouseDownHand?: (card: GameCard, e: React.MouseEvent) => void;
    onHoverCard?: (card: GameCard | { id: number; card_name: string; image_uris?: { normal?: string }; card_faces?: Array<{ image_uris?: { normal?: string } }>; mana_cost?: string; type_line?: string } | null, position: { x: number; y: number }) => void;
}> = ({player, isCurrentUser, handRef, hoveredZone, cardScale = 100, dragState, onMouseDownHand, onHoverCard }) => {

    const handIndexArray = player.hand.map((_, idx) => {
        return (idx - (player.hand.length/2));
    });
    
    if (isCurrentUser) {
        return (
            <div 
            ref={handRef as any} 
            className={`h-[5%] min-h-[20px] flex justify-center gap-1 p-1 rounded transition-colors ${
                hoveredZone === 'hand' ? 'bg-yellow-900/50 border-2 border-yellow-400' : ''
            }`}
            >
            {player.hand.map((card, idx) => {
                const isDraggingThis = dragState?.isDragging && dragState?.cardId === card.id;
                if (isDraggingThis) return null;
                return (
                <Card 
                    key={card.id} 
                    card={card} 
                    size="sm"
                    scale={cardScale}
                    onMouseDown={(e) => onMouseDownHand?.(card, e)}
                    onHover={onHoverCard}
                    handIndex={handIndexArray[idx]}
                    zIndex={idx}
                />
                );
            })}
            </div>
        )
    }
    return (
        <div className="flex-shrink-0 h-1 overflow-visible">
            <div className="flex justify-center -mt-2" style={{transform: 'translateY(-40%)'}}>
                {player.hand.map((card, idx) => {
                const isDraggingThis = dragState?.isDragging && dragState?.cardId === card.id;
                if (isDraggingThis) return null;
                return (
                    <div key={card.id} className="-ml-4 first:ml-0">
                    <Card 
                        card={card} 
                        size="sm"
                        scale={cardScale}
                        hidden={true}
                        onHover={onHoverCard}
                        handIndex={handIndexArray[idx]}
                        zIndex={idx}
                    />
                    </div>
                );
                })}
            </div>
        </div>
    )
};