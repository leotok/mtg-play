import type { PlayerGameState } from "../../types/gameState";
import { useSettingsStore } from "../../store/settingsStore";

export const Library: React.FC<{ 
    player: PlayerGameState; 
    className?: string;
}> = ({ player, className = '' }) => {
    const cardHeight = useSettingsStore(state => state.getCardHeight());
    
    return (
        <div className={`w-auto relative flex flex-col justify-end items-end ${className}`} style={{top: 65, height: cardHeight}}>
            <span className="text-xs text-gray-500 uppercase absolute -top-5 right-2">
                Library ({player.library.length})
            </span>
            <div className="flex -mt-8 justify-end">
                <div 
                    className="w-auto rounded-lg overflow-hidden border border-gray-600"
                    style={{ height: cardHeight }}
                >
                    <img 
                        src="https://backs.scryfall.io/small/2/2/222b7a3b-2321-4d4c-af19-19338b134971.jpg" 
                        alt="Card Back"
                        className="w-full h-full object-cover"
                    />
                </div>
            </div>
        </div>
    );
};
