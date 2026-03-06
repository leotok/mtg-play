import { useState, useEffect } from "react";
import type { PlayerGameState } from "../../types/gameState";
import { useGameStateStore } from "../../store/gameStateStore";

interface LifeCounterProps {
    player: PlayerGameState;
    gameMode?: string;
}

export const LifeCounter: React.FC<LifeCounterProps> = ({ player, gameMode }) => {
    const { gameId, adjustLife } = useGameStateStore();
    const [inputValue, setInputValue] = useState(player.life_total.toString());
    const [isEditing, setIsEditing] = useState(false);

    const isManualMode = gameMode === 'manual';

    useEffect(() => {
        if (!isEditing) {
            setInputValue(player.life_total.toString());
        }
    }, [player.life_total, isEditing]);

    const handleAdjustLife = (amount: number) => {
        if (gameId && isManualMode) {
            adjustLife(gameId, amount);
        }
    };

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value.replace(/[^0-9-]/g, '');
        setInputValue(value);
    };

    const handleInputBlur = () => {
        const newLife = parseInt(inputValue, 10);
        if (!isNaN(newLife) && newLife >= 0 && newLife !== player.life_total) {
            const diff = newLife - player.life_total;
            if (gameId && isManualMode) {
                adjustLife(gameId, diff);
            }
        } else {
            setInputValue(player.life_total.toString());
        }
        setIsEditing(false);
    };

    const handleInputKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            handleInputBlur();
        }
    };

    if (!isManualMode) {
        return (
            <div className="absolute top-2 right-2 z-10 bg-gray-900/80 rounded-lg px-2 py-1">
                <span className={`font-bold text-sm px-1 ${player.life_total <= 10 ? 'text-red-400' : 'text-white'}`}>
                    {player.life_total}
                </span>
            </div>
        );
    }

    return (
        <div className="absolute top-2 right-2 z-10 bg-gray-900/80 rounded-lg px-2 py-1 flex items-center">
            <button
                onClick={() => handleAdjustLife(-5)}
                className="w-5 h-5 rounded text-gray-400 hover:text-white hover:bg-gray-700 text-xs flex items-center justify-center transition-colors"
            >
                -5
            </button>
            <button
                onClick={() => handleAdjustLife(-1)}
                className="w-5 h-5 rounded text-gray-400 hover:text-white hover:bg-gray-700 text-sm flex items-center justify-center transition-colors mx-0.5"
            >
                -
            </button>
            {isEditing ? (
                <input
                    type="text"
                    inputMode="numeric"
                    value={inputValue}
                    onChange={handleInputChange}
                    onBlur={handleInputBlur}
                    onKeyDown={handleInputKeyDown}
                    autoFocus
                    className="w-8 text-center font-bold text-sm bg-transparent text-white border-none outline-none"
                />
            ) : (
                <span
                    onClick={() => setIsEditing(true)}
                    className={`w-8 min-w-[3ch] text-center font-bold text-sm cursor-pointer hover:text-yellow-300 px-1 ${player.life_total <= 10 ? 'text-red-400' : 'text-white'}`}
                >
                    {player.life_total}
                </span>
            )}
            <button
                onClick={() => handleAdjustLife(1)}
                className="w-5 h-5 rounded text-gray-400 hover:text-white hover:bg-gray-700 text-sm flex items-center justify-center transition-colors mx-0.5"
            >
                +
            </button>
            <button
                onClick={() => handleAdjustLife(5)}
                className="w-5 h-5 rounded text-gray-400 hover:text-white hover:bg-gray-700 text-xs flex items-center justify-center transition-colors"
            >
                +5
            </button>
        </div>
    );
};
