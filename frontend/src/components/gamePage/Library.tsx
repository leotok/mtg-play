import type { PlayerGameState } from "../../types/gameState";

export const Library: React.FC<{ 
    player: PlayerGameState; 
    cardScale: number;
    className?: string;
}> = ({ player, cardScale, className = '' }) => {
    return (
        <div className={`w-24 h-36 relative overflow-hidden flex flex-col justify-end items-end ${className}`} style={{top: 65}}>
            <span className="text-xs text-gray-500 uppercase absolute top-0 right-2">
                Library ({player.library.length})
            </span>
            <div className="flex -mt-8 justify-end">
                <div 
                    className="h-36 w-24 rounded-lg overflow-hidden border border-gray-600"
                    style={{ transform: `scale(${cardScale / 100})` }}
                >
                    <img 
                        src="https://static.wikia.nocookie.net/mtgsalvation_gamepedia/images/f/f8/Magic_card_back.jpg" 
                        alt="Card Back"
                        className="w-full h-full object-cover"
                    />
                </div>
            </div>
        </div>
    );
};
