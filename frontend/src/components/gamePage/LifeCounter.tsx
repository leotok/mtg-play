import type { PlayerGameState } from "../../types/gameState";

export const LifeCounter: React.FC<{ player: PlayerGameState }> = ({ player }) => {
    return (
        <div>
            <div className="text-center text-xs text-gray-500 mb-1">
                Life
            </div>
            <div className="text-center text-lg font-bold mb-2">
                <span className={player.life_total <= 10 ? 'text-red-400' : 'text-white'}>
                {player.life_total}
                </span>
            </div>
        </div>
    );
};