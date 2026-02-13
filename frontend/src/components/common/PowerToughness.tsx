import React from 'react';

interface PowerToughnessProps {
  power?: string;
  toughness?: string;
  className?: string;
  showLabel?: boolean;
}

const PowerToughness: React.FC<PowerToughnessProps> = ({ power, toughness, className = '', showLabel = false }) => {
  if (!power || !toughness) return null;

  return (
    <span 
      className={`inline-flex items-center gap-1 ${className}`}
      title={`${power}/${toughness}`}
    >
      {showLabel && <span className="text-gray-500 text-xs">P/T</span>}
      <span className="text-xs font-bold text-red-400">{power}</span>
      <span className="text-xs text-gray-500">/</span>
      <span className="text-xs font-bold text-green-400">{toughness}</span>
    </span>
  );
};

export default PowerToughness;
