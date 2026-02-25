import { Card } from './Card';
import { type PlayerGameState } from '../../types/gameState';
import { type CardZone } from '../../types/gameState';
import { type GameCard, type GameCardInBattlefield } from '../../types/gameState';
import { useSettingsStore } from '../../store/settingsStore';


export const HandCards: React.FC<{
    player: PlayerGameState;
    isCurrentUser: boolean;
    handRef?: React.RefObject<HTMLDivElement | null> | ((el: HTMLDivElement | null) => void);
    hoveredZone?: CardZone | null;
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
}> = ({player, isCurrentUser, handRef, hoveredZone, dragState, onMouseDownHand, onHoverCard }) => {
    const cardHeight = useSettingsStore(state => state.getCardHeight());
    const handHeight = cardHeight * 0.37;

    const handIndexArray = player.hand.map((_, idx) => {
        return (idx - (player.hand.length/2));
    });
    
    if (isCurrentUser) {
        return (
            <div 
            ref={handRef as any} 
            className={`flex justify-center gap-1 p-1 rounded transition-colors flex-auto ${
                hoveredZone === 'hand' ? 'bg-yellow-900/50 border-none' : ''
            }`}
            style={{height: handHeight}}
            >
            {player.hand.map((card, idx) => {
                const isDraggingThis = dragState?.isDragging && dragState?.cardId === card.id;
                if (isDraggingThis) return null;
                return (
                <Card 
                    key={card.id} 
                    card={card} 
                    size="sm"
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
        <div className="flex-shrink-0 overflow-visible">
            <div className="flex justify-center -mt-2" style={{transform: 'translateY(-40%)'}}>
                {player.hand.map((card, idx) => {
                const isDraggingThis = dragState?.isDragging && dragState?.cardId === card.id;
                if (isDraggingThis) return null;
                return (
                    <div key={card.id} className="-ml-4 first:ml-0">
                    <Card 
                        card={card} 
                        size="sm"
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