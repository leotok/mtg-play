import React from 'react';
import { type GameCard } from '../../types/gameState';
import { useSettingsStore } from '../../store/settingsStore';
import { CARD_SIZES, type CardSizeKey } from '../../config';

export const Card: React.FC<{
  card: GameCard | { id: number; card_name: string; image_uris?: { normal?: string }; card_faces?: Array<{ image_uris?: { normal?: string } }>; mana_cost?: string; type_line?: string; is_tapped?: boolean; battlefield_x?: number; battlefield_y?: number; is_attacking?: boolean; is_blocking?: boolean; is_face_up?: boolean };
  onTap?: () => void;
  onMouseDown?: (e: React.MouseEvent) => void;
  onHover?: (card: GameCard | { id: number; card_name: string; image_uris?: { normal?: string }; card_faces?: Array<{ image_uris?: { normal?: string } }>; mana_cost?: string; type_line?: string } | null, position: { x: number; y: number }) => void;
  size?: CardSizeKey;
  hidden?: boolean;
  isDragging?: boolean;
  style?: React.CSSProperties;
  scale?: number;
  handIndex?: number;
  zIndex?: number;
}> = ({ card, onTap, onMouseDown, onHover, size, hidden = false, isDragging = false, style, scale, handIndex = 0, zIndex = 0 }) => {
  const { baseCardSize, cardScale } = useSettingsStore();
  const cardHeight = CARD_SIZES[size || baseCardSize].height * (cardScale / 100);
  const cardWidth = CARD_SIZES[size || baseCardSize].width * (cardScale / 100);

  const imageUrl = card.image_uris?.normal || card.card_faces?.[0]?.image_uris?.normal;
  const cardName = hidden ? 'Unknown Card' : card.card_name;

  const handleMouseEnter = (e: React.MouseEvent) => {
    if (!hidden && onHover) {
      onHover(card, { x: e.clientX, y: e.clientY });
    }
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    if (onMouseDown) {
      onMouseDown(e);
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!hidden && onHover) {
      onHover(card, { x: e.clientX, y: e.clientY });
    }
  };

  const handleDoubleClick = () => {
    if (onTap) {
      onTap();
    }
  };

  const handleMouseLeave = () => {
    if (onHover) {
      onHover(null, { x: 0, y: 0 });
    }
  };

  const left = handIndex * -40;
  const top = Math.abs(handIndex * 8 );

  const rotation = card.is_tapped ? 90 : (handIndex * 4);
  const scaleTransform = scale !== undefined && scale !== 100 ? `scale(${scale / 100})` : '';
  const rotationTransform = rotation !== 0 ? `rotate(${rotation}deg)` : '';
  const combinedTransform = [scaleTransform, rotationTransform].filter(Boolean).join(' ');
  const scaleStyle = combinedTransform ? { ...style, transform: combinedTransform } : style;

  return (
    <div
      onMouseDown={handleMouseDown}
      onDoubleClick={handleDoubleClick}
      onMouseEnter={handleMouseEnter}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className={`
        flex items-center justify-center cursor-grab select-none
        transition-all duration-200
        ${isDragging ? 'opacity-80 scale-105 cursor-grabbing z-50' : 'hover:scale-105 hover:border-yellow-500'}
        ${hidden ? 'bg-gray-900 border-dashed' : ''}
      `}
      style={{...scaleStyle, zIndex, position: 'relative', left, top, width: cardWidth, height: cardHeight}}
      title={hidden ? cardName : `${cardName}\n${card.mana_cost || ''}\n${card.type_line || ''}`}
    >
      {hidden ? (
        <img 
          src="https://static.wikia.nocookie.net/mtgsalvation_gamepedia/images/f/f8/Magic_card_back.jpg"
          alt="Card Back"
          className="w-full h-full object-cover rounded-md pointer-events-none"
        />
      ) : imageUrl ? (
        <img 
          src={imageUrl} 
          alt={cardName}
          className="w-full h-full object-cover rounded-md pointer-events-none"
        />
      ) : (
        <div className="text-white text-xs text-center p-1 pointer-events-none">
          <div className="font-bold">{cardName}</div>
          {card.mana_cost && <div>{card.mana_cost}</div>}
        </div>
      )}
    </div>
  );
};