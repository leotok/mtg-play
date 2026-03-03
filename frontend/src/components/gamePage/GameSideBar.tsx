import React from "react";
import type { GameState, PlayerGameState, TurnPhase } from "../../types/gameState";
import { TURN_PHASE_LABELS } from "../../types/gameState";
import { ArrowRightIcon } from "@heroicons/react/24/outline";
import { useSettingsStore } from "../../store/settingsStore";
import { GameLog } from "./GameLog";

interface GameSideBarProps {
    gameState: GameState;
    gameMode?: string;
    isCurrentUserActive: boolean;
    currentPlayer?: PlayerGameState | null;
    currentPlayerId: number;
    handleDrawCard: () => void;
    handleUntapAll: () => void;
    handlePassPriority: () => void;
    isLoading: boolean;
}

const getDynamicButton = (
    phase: TurnPhase,
    handleUntapAll: () => void,
    handleDrawCard: () => void,
    handlePassPriority: () => void,
    isLoading: boolean
): { label: string; color: string; action: () => void } | null => {
    switch (phase) {
        case "untap":
            return { label: "Untap", color: "bg-green-600 hover:bg-green-500", action: () => {handleUntapAll(); handlePassPriority();} };
        case "upkeep":
            return { label: "Upkeep", color: "bg-yellow-600 hover:bg-yellow-500", action: handlePassPriority };
        case "draw":
            return { label: "Draw", color: "bg-blue-600 hover:bg-blue-500", action: () => {handleDrawCard(); handlePassPriority();} };
        case "cleanup":
            return { label: "End Turn", color: "bg-red-600 hover:bg-red-500", action: handlePassPriority };
        default:
            return { label: "Next", color: "bg-yellow-600 hover:bg-yellow-500", action: handlePassPriority };
    }
};

export const GameSideBar: React.FC<GameSideBarProps> = ({
    gameState,
    gameMode,
    isCurrentUserActive,
    currentPlayer,
    currentPlayerId,
    handleDrawCard,
    handleUntapAll,
    handlePassPriority,
    isLoading
}) => {
    const { cardScale, setCardScale } = useSettingsStore();
    
    const isRulesEnforced = gameMode === "rules_enforced";
    const dynamicButton = isRulesEnforced && isCurrentUserActive && currentPlayer
        ? getDynamicButton(gameState.current_phase, handleUntapAll, handleDrawCard, handlePassPriority, isLoading)
        : null;
    
    return (
        
            <div className="w-40 flex-shrink-0 flex flex-col gap-2">

                {/* Turn */}
                <div className="bg-gray-800 rounded p-2 text-center">
                    <div className="text-gray-400 text-xs">Turn</div>
                    <div className="text-white font-bold text-lg">{gameState.current_turn}</div>
                </div>

                {/* Phase */}
                <div className="bg-yellow-900/50 rounded p-2 text-center border border-yellow-700">
                    <div className="text-gray-400 text-xs">Phase</div>
                    <div className="text-yellow-400 text-xs font-semibold">
                    {TURN_PHASE_LABELS[gameState.current_phase]}
                    </div>
                </div>

                {/* Active Player */}
                <div className="bg-gray-800 rounded p-2 text-center">
                    <div className="text-gray-400 text-xs">Active Player</div>
                    <div className="text-white text-sm truncate">{gameState.active_player_username}</div>
                </div>

                {/* Card Scale */}
                <div className="bg-gray-800 rounded p-2 text-center">
                    <div className="text-gray-400 text-xs mb-1">Card Size</div>
                    <div className="flex items-center justify-center gap-2">
                    <button
                        onClick={() => setCardScale(Math.max(50, cardScale - 10))}
                        className="w-6 h-6 bg-gray-700 hover:bg-gray-600 rounded text-white text-sm font-bold"
                    >
                        -
                    </button>
                    <span className="text-white text-sm font-medium w-10">{cardScale}%</span>
                    <button
                        onClick={() => setCardScale(Math.min(150, cardScale + 10))}
                        className="w-6 h-6 bg-gray-700 hover:bg-gray-600 rounded text-white text-sm font-bold"
                    >
                        +
                    </button>
                    </div>
                </div>

                {/* Game Log */}
                <GameLog currentPlayerId={currentPlayerId} />

                <div className="flex-1" />

                {isCurrentUserActive && currentPlayer && (
                    <div className="flex flex-col gap-2">

                    {/* Rules Enforced: Single Dynamic Button */}
                    {isRulesEnforced && dynamicButton && (
                        <button
                            onClick={dynamicButton.action}
                            disabled={isLoading}
                            className={`flex items-center justify-center gap-1 px-2 py-2 ${dynamicButton.color} text-white rounded transition-colors text-sm disabled:opacity-50`}
                        >
                            {dynamicButton.label}
                        </button>
                    )}

                    {/* Manual Mode: Three Buttons */}
                    {!isRulesEnforced && (
                        <>
                        <button
                            onClick={handleUntapAll}
                            disabled={isLoading}
                            className="flex items-center justify-center gap-1 px-2 py-2 bg-green-600 hover:bg-green-500 text-white rounded transition-colors text-sm disabled:opacity-50"
                        >
                            Untap
                        </button>

                        <button
                            onClick={handleDrawCard}
                            disabled={isLoading}
                            className="flex items-center justify-center gap-1 px-2 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded transition-colors text-sm disabled:opacity-50"
                        >
                            <ArrowRightIcon className="h-4 w-4" />
                            Draw
                        </button>

                        <button
                            onClick={handlePassPriority}
                            disabled={isLoading}
                            className="flex items-center justify-center gap-1 px-2 py-2 bg-yellow-600 hover:bg-yellow-500 text-white rounded transition-colors text-sm disabled:opacity-50"
                        >
                            Pass Priority
                        </button>
                        </>
                    )}
                    </div>
                )}

            </div>
        
    );
};
