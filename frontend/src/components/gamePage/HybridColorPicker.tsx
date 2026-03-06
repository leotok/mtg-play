import React from 'react';

interface HybridColorPickerProps {
  isOpen: boolean;
  onSelect: (color: string) => void;
  onClose: () => void;
  position: { x: number; y: number };
  availableColors: string[];
}

const MANA_COLORS: Record<string, { color: string; borderColor: string; label: string }> = {
  white: { color: '#F9F9F9', borderColor: '#A0A0A0', label: 'W' },
  blue: { color: '#2E5EAA', borderColor: '#1E3E6A', label: 'U' },
  black: { color: '#2E2E2E', borderColor: '#1A1A1A', label: 'B' },
  red: { color: '#C23B22', borderColor: '#8A2A16', label: 'R' },
  green: { color: '#00733E', borderColor: '#00522B', label: 'G' },
  colorless: { color: '#8B8B8B', borderColor: '#5B5B5B', label: 'C' },
};

export const HybridColorPicker: React.FC<HybridColorPickerProps> = ({
  isOpen,
  onSelect,
  onClose,
  position,
  availableColors,
}) => {
  if (!isOpen) return null;

  return (
    <div
      className="fixed z-50"
      style={{
        left: position.x,
        top: position.y,
        transform: 'translate(-50%, -50%)',
      }}
    >
      <div className="bg-gray-900 border-2 border-gray-600 rounded-lg p-2 shadow-2xl">
        <div className="text-xs text-gray-300 text-center mb-2">
          Choose mana color
        </div>
        <div className="flex gap-1">
          {availableColors.map((color) => {
            const colorInfo = MANA_COLORS[color];
            if (!colorInfo) return null;
            
            return (
              <button
                key={color}
                onClick={() => onSelect(color)}
                className="w-10 h-10 rounded-md font-bold text-sm transition-transform hover:scale-110 focus:outline-none focus:ring-2 focus:ring-white"
                style={{
                  backgroundColor: colorInfo.color,
                  border: `2px solid ${colorInfo.borderColor}`,
                }}
                title={`${color} mana`}
              >
                <span className={color === 'white' ? 'text-black' : 'text-white'}>
                  {colorInfo.label}
                </span>
              </button>
            );
          })}
        </div>
        <button
          onClick={onClose}
          className="w-full mt-2 text-xs text-gray-400 hover:text-white"
        >
          Cancel
        </button>
      </div>
    </div>
  );
};
