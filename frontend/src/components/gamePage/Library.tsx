import type { PlayerGameState } from "../../types/gameState";

export const Library: React.FC<{ 
    player: PlayerGameState; 
    cardScale: number 
}> = ({ player, cardScale }) => {
    return (
        <div>
            <div className="text-center text-xs text-gray-500 mb-1">
                Library
            </div>
            <div className="text-center text-lg font-bold mb-1">
                <span className="text-gray-400">
                {player.library.length}
                </span>
            </div>
            <div 
                className="w-16 h-24 mx-auto rounded-lg overflow-hidden cursor-pointer hover:scale-105 transition-transform border border-gray-600"
                style={{ transform: `scale(${cardScale / 100})` }}
            >
                <img 
                src="https://static.wikia.nocookie.net/mtgsalvation_gamepedia/images/f/f8/Magic_card_back.jpg" 
                alt="Card Back"
                className="w-full h-full object-cover"
                />
            </div>
        </div>
    );
};