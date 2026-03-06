import React from 'react';
import type { PlayerGameState } from '../../types/gameState';

const MANA_COLORS = [
  { key: 'white', label: 'W', color: '#F9F9F9', borderColor: '#A0A0A0' },
  { key: 'blue', label: 'U', color: '#2E5EAA', borderColor: '#1E3E6A' },
  { key: 'black', label: 'B', color: '#2E2E2E', borderColor: '#1A1A1A' },
  { key: 'red', label: 'R', color: '#C23B22', borderColor: '#8A2A16' },
  { key: 'green', label: 'G', color: '#00733E', borderColor: '#00522B' },
  { key: 'colorless', label: 'C', color: '#8B8B8B', borderColor: '#5B5B5B' },
] as const;

interface ManaPoolProps {
  player: PlayerGameState;
  isCurrentUser: boolean;
}

export const ManaPool: React.FC<ManaPoolProps> = ({ player, isCurrentUser }) => {
  const manaPool = player.mana_pool || {};
  
  const totalMana = Object.values(manaPool).reduce((sum, val) => sum + val, 0);
  
  if (!isCurrentUser) {
    return null;
  }

  return (
    <div className="absolute left-2 top-16 z-10 flex flex-col gap-1">
      {MANA_COLORS.map(({ key, color, borderColor }) => {
        const amount = manaPool[key] || 0;
        
        return (
          <div
            key={key}
            className={`
              flex items-center justify-center
              w-8 h-8 rounded-md font-bold text-sm
              transition-all duration-200
              ${amount > 0 
                ? 'ring-2 ring-white/50 shadow-lg' 
                : 'opacity-40'}
            `}
            style={{
              backgroundColor: color,
              border: `2px solid ${borderColor}`,
              boxShadow: amount > 0 ? `0 0 8px ${color}80` : undefined,
            }}
            title={`${key.charAt(0).toUpperCase() + key.slice(1)} mana: ${amount}`}
          >
            <span className={key === 'white' ? 'text-black' : 'text-white'}>
              {amount > 0 ? amount : ''}
            </span>
          </div>
        );
      })}
      
      {totalMana > 0 && (
        <div className="text-center text-xs text-gray-400 mt-1">
          {totalMana} total
        </div>
      )}
    </div>
  );
};
