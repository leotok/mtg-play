import type { PlayerGameState } from "../../types/gameState";

export const LifeCounter: React.FC<{ player: PlayerGameState }> = ({ player }) => {
    return (
        <div className="absolute top-2 right-2 z-10 bg-gray-900/80 rounded-lg px-3 py-1">
            <span className={player.life_total <= 10 ? 'text-red-400' : 'text-white'}>
                {player.life_total}
            </span>
        </div>
    );
};
