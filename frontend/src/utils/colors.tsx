import React from 'react';

export interface ColorInfo {
  name: string;
  bg: string;
  text: string;
  gradient?: string;
}

export const COLOR_MAP: Record<string, ColorInfo> = {
  'W': { bg: 'bg-yellow-100', text: 'text-yellow-800', name: 'White' },
  'U': { bg: 'bg-blue-500', text: 'text-white', name: 'Blue' },
  'B': { bg: 'bg-gray-800', text: 'text-white', name: 'Black' },
  'R': { bg: 'bg-red-500', text: 'text-white', name: 'Red' },
  'G': { bg: 'bg-green-500', text: 'text-white', name: 'Green' },
};

export const COLOR_GROUPS: Record<string, string> = {
  'W': 'Mono White',
  'U': 'Mono Blue',
  'B': 'Mono Black',
  'R': 'Mono Red',
  'G': 'Mono Green',
  'WU': 'Azorius',
  'UB': 'Dimir',
  'BR': 'Rakdos',
  'RG': 'Gruul',
  'GW': 'Selesnya',
  'WB': 'Orzhov',
  'UG': 'Simic',
  'UR': 'Izzet',
  'BG': 'Golgari',
  'RW': 'Boros',
  'WBG': 'Abzan',
  'WUB': 'Esper',
  'WUR': 'Jeskai',
  'BRU': 'Grixis',
  'BRW': 'Mardu',
  'RWG': 'Naya',
  'GWU': 'Bant',
  'WUBRG': 'Five Color',
};

const SHARD_GROUPS: Record<string, string> = {
  'Abzan': ['WBG', 'WGB', 'BWG', 'GWB', 'GBW', 'BGW', 'G W B', 'W B G', 'B W G', 'G B W'],
  'Esper': ['WUB', 'WBU', 'UWB', 'UBW', 'BWU', 'BUW'],
  'Jeskai': ['WUR', 'WRU', 'UWR', 'URW', 'RWU', 'RUW', 'W R U', 'U R W'],
  'Grixis': ['UBR', 'URB', 'BUR', 'BRU', 'RUB', 'RBU', 'U B R', 'B U R', 'R U B', 'B R U'],
  'Mardu': ['BRW', 'BWR', 'R B W', 'RWB', 'WBR', 'WRB', 'B R W', 'R W B', 'W R B', 'B W R'],
  'Naya': ['RWG', 'RW G', 'WRG', 'WGR', 'GWR', 'GRW', 'R W G', 'W R G'],
  'Bant': ['GWU', 'G UW', 'WGU', 'W G U', 'UGW', 'UGW', 'G W U'],
};

const COLOR_ORDER = ['W', 'U', 'B', 'R', 'G'];

const sortColors = (colors: string[]): string[] => {
  return colors.sort();
};

const findShardGroup = (sortedColors: string): string | undefined => {
  for (const [groupName, permutations] of Object.entries(SHARD_GROUPS)) {
    if (permutations.includes(sortedColors)) {
      return groupName;
    }
  }
  return undefined;
};

const GUILD_GRADIENTS: Record<string, string> = {
  'Azorius': 'from-blue-500 to-white',
  'Dimir': 'from-gray-700 to-blue-600',
  'Rakdos': 'from-red-700 to-gray-800',
  'Gruul': 'from-green-600 to-red-600',
  'Selesnya': 'from-green-500 to-white',
  'Orzhov': 'from-gray-600 to-white',
  'Izzet': 'from-red-500 to-blue-500',
  'Golgari': 'from-green-700 to-gray-800',
  'Boros': 'from-red-600 to-yellow-500',
  'Simic': 'from-green-500 to-blue-500',
};

const SHARD_GRADIENTS: Record<string, string> = {
  'Abzan': 'from-gray-700 via-black to-green-600',
  'Esper': 'from-gray-400 via-blue-500 to-gray-600',
  'Jeskai': 'from-blue-400 via-red-500 to-yellow-400',
  'Grixis': 'from-blue-600 via-red-600 to-gray-800',
  'Mardu': 'from-red-600 via-gray-400 to-yellow-100',
  'Naya': 'from-green-600 via-yellow-400 to-red-500',
  'Bant': 'from-green-400 via-blue-400 to-white',
};

export const getColorGroupName = (colors: string[]): string => {
  if (!colors || colors.length === 0) return 'Colorless';
  
  const uniqueColors = [...new Set(colors.map(c => c.trim()).filter(c => c && COLOR_ORDER.includes(c)))];
  if (uniqueColors.length === 0) return 'Colorless';
  
  const sortedColors = sortColors(uniqueColors).join('');
  
  return COLOR_GROUPS[sortedColors] || uniqueColors.join(', ');
};

interface ColorBadgeProps {
  colors?: string[];
  className?: string;
}

export const ColorBadge: React.FC<ColorBadgeProps> = ({ colors, className = '' }) => {
  if (!colors || colors.length === 0) {
    return <span className={`px-2 py-1 bg-gray-600 text-gray-300 rounded-full text-xs ${className}`}>Colorless</span>;
  }
  
  const uniqueColors = [...new Set(colors.map(c => c.trim()).filter(c => c && COLOR_ORDER.includes(c)))];
  if (uniqueColors.length === 0) {
    return <span className={`px-2 py-1 bg-gray-600 text-gray-300 rounded-full text-xs ${className}`}>Colorless</span>;
  }
  
  const sortedColors = sortColors(uniqueColors).join('');

  
  if (uniqueColors.length === 1) {
    const color = uniqueColors[0];
    const colorInfo = COLOR_MAP[color];
    return (
      <span className={`px-2 py-1 ${colorInfo?.bg || 'bg-gray-600'} ${colorInfo?.text || 'text-white'} rounded-full text-xs font-medium ${className}`}>
        {colorInfo?.name || color}
      </span>
    );
  }
  
  const groupName = COLOR_GROUPS[sortedColors] || uniqueColors.join(', ');
  
  if (uniqueColors.length === 2) {
    const gradient = GUILD_GRADIENTS[groupName];
    return (
      <span className={`px-2 py-1 bg-gradient-to-r ${gradient || 'from-purple-500 to-blue-500'} text-white rounded-full text-xs font-semibold ${className}`}>
        {groupName}
      </span>
    );
  }
  
  const gradient = SHARD_GRADIENTS[groupName];
  
  console.log('ColorBadge - colors:', colors, 'uniqueColors:', uniqueColors, 'sortedColors:', sortedColors, 'groupName:', groupName, 'gradient:', gradient);
  return (
    <span className={`px-2 py-1 bg-gradient-to-r ${gradient || 'from-purple-500 to-blue-500'} text-white rounded-full text-xs font-semibold ${className}`}>
      {groupName}
    </span>
  );
};
