import React from 'react';

interface ManaCostProps {
  cost?: string;
  className?: string;
  showLabel?: boolean;
}

const MANA_COLORS: Record<string, string> = {
  'W': '#F9F9B5',
  'U': '#2A6FDB',
  'B': '#000000',
  'R': '#E03C31',
  'G': '#509E2F',
  'C': '#B3B3B3',
};

const getManaColor = (symbol: string): string => {
  const upper = symbol.toUpperCase();
  if (upper.includes('W')) return MANA_COLORS['W'];
  if (upper.includes('U')) return MANA_COLORS['U'];
  if (upper.includes('B')) return MANA_COLORS['B'];
  if (upper.includes('R')) return MANA_COLORS['R'];
  if (upper.includes('G')) return MANA_COLORS['G'];
  if (upper === '{C}' || upper === '{S}') return MANA_COLORS['C'];
  return '#888888';
};

const getManaText = (symbol: string): string => {
  const upper = symbol.toUpperCase();
  
  if (upper === '{W}') return 'W';
  if (upper === '{U}') return 'U';
  if (upper === '{B}') return 'B';
  if (upper === '{R}') return 'R';
  if (upper === '{G}') return 'G';
  if (upper === '{C}') return 'C';
  if (upper === '{X}') return 'X';
  if (upper === '{S}') return 'S';
  if (upper === '{P}') return 'P';
  
  if (upper.match(/^\{\d+\}$/)) {
    return upper.replace(/[{}]/g, '');
  }
  
  if (upper.match(/^\{2\/[WUBRG]\}$/)) {
    return '2' + upper[3];
  }
  
  if (upper.match(/^\{[WUBRG]\/[WUBRG]\}$/)) {
    return upper[1] + '/' + upper[3];
  }
  
  if (upper.match(/^\{[WUBRG]\/P\}$/)) {
    return upper[1] + '/P';
  }
  
  return symbol;
};

const parseManaCost = (cost: string): string[] => {
  if (!cost) return [];
  
  const regex = /\{[^}]+\}/g;
  const matches = cost.match(regex);
  return matches || [];
};

const ManaCost: React.FC<ManaCostProps> = ({ cost, className = '', showLabel = false }) => {
  if (!cost) return null;

  const symbols = parseManaCost(cost);

  return (
    <span className={`inline-flex items-center gap-1 ${className}`}>
      {showLabel && <span className="text-gray-500 text-xs">Cost</span>}
      {symbols.map((symbol, index) => {
        const color = getManaColor(symbol);
        const text = getManaText(symbol);
        
        return (
          <span
            key={index}
            className="inline-flex items-center justify-center w-4 h-4 text-[10px] font-bold rounded-sm"
            style={{
              backgroundColor: color,
              color: color === '#000000' || color === '#2A6FDB' || color === '#509E2F' || color === '#E03C31' ? '#FFFFFF' : '#000000',
              textShadow: color === '#F9F9B5' || color === '#F19F1E' || color === '#509E2F' ? '0 0 1px #000' : 'none',
            }}
            title={symbol}
          >
            {text}
          </span>
        );
      })}
    </span>
  );
};

export default ManaCost;
