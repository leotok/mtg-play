import React, { useEffect, useRef } from 'react';
import { useGameStateStore } from '../../store/gameStateStore';
import type { GameLog as GameLogType } from '../../types/gameState';

interface GameLogProps {
  currentPlayerId: number;
}

export const GameLog: React.FC<GameLogProps> = ({ currentPlayerId }) => {
  const { gameState } = useGameStateStore();
  const scrollRef = useRef<HTMLDivElement>(null);

  const gameLogs = gameState?.logs || [];

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [gameLogs]);

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
  };

  const getActionColor = (log: GameLogType) => {
    if (log.action_type === 'turn_change' || log.action_type === 'phase_change') {
      return 'text-yellow-400';
    }
    return 'text-white';
  };

  if (gameLogs.length === 0) {
    return (
      <div className="bg-gray-800 rounded p-2">
        <div className="text-gray-400 text-xs mb-1">Game Log</div>
        <div className="text-gray-500 text-xs">No actions yet</div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded p-2 flex flex-col">
      <div className="text-gray-400 text-xs mb-1">Game Log</div>
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto max-h-64 text-xs space-y-0.5"
      >
        {[...gameLogs].reverse().map((log) => (
          <div 
            key={log.id} 
            className={`${getActionColor(log)} leading-tight pt-3`}
          >
            <span className="text-gray-400 mr-1">[{formatTime(log.created_at)}]</span>
            {log.message}
          </div>
        ))}
      </div>
    </div>
  );
};
