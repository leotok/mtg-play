import type { GameCard, GameCardInBattlefield, PlayerGameState } from "../../types/gameState";
import type { CardZone } from "../../types/gameState";
import { Battlefield } from "./Battlefield";
import { CommanderZone } from "./CommanderZone";
import { DraggingCard } from "./DraggingCard";
import { Exile } from "./Exile";
import { Graveyard } from "./Graveyard";
import { HandCards } from "./HandCards";
import { Library } from "./Library";
import { LifeCounter } from "./LifeCounter";


export const PlayerZone: React.FC<{
  player: PlayerGameState;
  isCurrentUser: boolean;
  isActive: boolean;
  onTapCard?: (cardId: number) => void;
  onHoverCard?: (card: GameCard | { id: number; card_name: string; image_uris?: { normal?: string }; card_faces?: Array<{ image_uris?: { normal?: string } }>; mana_cost?: string; type_line?: string } | null) => void;
  onMouseDownCard?: (card: GameCardInBattlefield, e: React.MouseEvent) => void;
  onMouseDownHand?: (card: GameCard, e: React.MouseEvent) => void;
  onMouseDownCommander?: (card: GameCard, e: React.MouseEvent) => void;
  onMouseDownGraveyard?: (card: GameCard, e: React.MouseEvent) => void;
  onMouseDownExile?: (card: GameCard, e: React.MouseEvent) => void;
  onMouseDownEmptyBattlefield?: (e: React.MouseEvent) => void;
  battlefieldRef?: React.RefObject<HTMLDivElement | null>;
  handRef?: React.RefObject<HTMLDivElement | null> | ((el: HTMLDivElement | null) => void);
  commanderRef?: React.RefObject<HTMLDivElement | null> | ((el: HTMLDivElement | null) => void);
  graveyardRef?: React.RefObject<HTMLDivElement | null> | ((el: HTMLDivElement | null) => void);
  exileRef?: React.RefObject<HTMLDivElement | null> | ((el: HTMLDivElement | null) => void);
  dragState?: {
    isDragging: boolean;
    cardId: number;
    sourceZone: CardZone;
    card: GameCard | GameCardInBattlefield | null;
    currentX: number;
    currentY: number;
    initialMouseX: number;
    initialMouseY: number;
    cardPosition: { x: number; y: number };
    mouseOffset: { x: number; y: number };
    originalLogicalPosition?: { x: number; y: number };
  } | null;
  hoveredZone?: CardZone | null;
  selectedCardIds?: Set<number>;
}> = ({ player, isCurrentUser, isActive, onTapCard, onHoverCard, onMouseDownCard, onMouseDownHand, onMouseDownCommander, onMouseDownGraveyard, onMouseDownExile, onMouseDownEmptyBattlefield, battlefieldRef, handRef, commanderRef, graveyardRef, exileRef, dragState, hoveredZone, selectedCardIds }) => {
  const backgroundColor = isCurrentUser ? 'darkslateblue' : 'darkslategray';

  return (
    <div 
      className={`p-2 pb-0 overflow-hidden rounded-lg flex-1 flex flex-col relative ${isActive ? 'bg-yellow-900/30 border-2 border-yellow-500' : 'bg-gray-800/50 border border-gray-700'}`} 
      style={{backgroundColor}}
    >
      
      <LifeCounter player={player} />

      <Battlefield
        player={player}
        isCurrentUser={isCurrentUser}
        battlefieldRef={battlefieldRef}
        dragState={dragState}
        onTapCard={onTapCard}
        onMouseDownCard={onMouseDownCard}
        onHoverCard={onHoverCard}
        onMouseDownEmptyBattlefield={onMouseDownEmptyBattlefield}
        selectedCardIds={selectedCardIds}
      />

      <div className="h-auto flex gap-2 items-end w-full min-w-0 overflow-y-visible">
        <HandCards
          player={player}
          isCurrentUser={isCurrentUser}
          handRef={handRef}
          hoveredZone={hoveredZone}
          dragState={dragState}
          onMouseDownHand={onMouseDownHand}
          onHoverCard={onHoverCard}
        />
        
        <div className="ml-auto flex gap-2 items-end">
          {/* Hand size */}
          <div className={`flex items-end`}
          >
            <span className="text-xs text-white whitespace-nowrap">
              Hand ({player.hand.length})
            </span>
          </div>
          
          <CommanderZone
            player={player}
            commanderRef={commanderRef}
            hoveredZone={hoveredZone}
            isCurrentUser={isCurrentUser}
            onMouseDownCommander={onMouseDownCommander}
            onHoverCard={onHoverCard}
            dragState={dragState ?? null}
          />

          <Graveyard
            player={player}
            graveyardRef={graveyardRef}
            hoveredZone={hoveredZone}
            isCurrentUser={isCurrentUser}
            onMouseDownGraveyard={onMouseDownGraveyard}
            onHoverCard={onHoverCard}
            dragState={dragState ?? null}
          />

          <Exile 
            player={player}
            exileRef={exileRef}
            hoveredZone={hoveredZone}
            isCurrentUser={isCurrentUser}
            onMouseDownExile={onMouseDownExile}
            onHoverCard={onHoverCard}
            dragState={dragState ?? null}
          />

          <Library player={player} />
        </div>
      </div>

      <DraggingCard dragState={dragState} isCurrentUser={isCurrentUser} battlefieldRef={battlefieldRef} />
  
    </div>
  );
};
