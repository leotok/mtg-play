import React, { useState } from 'react';
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
  horizontalOffset?: number;
  inHand?: boolean;
}> = ({ card, onTap, onMouseDown, onHover, size, hidden = false, isDragging = false, style, scale, handIndex = 0, zIndex = 0, horizontalOffset = -40, inHand = false }) => {
  const { baseCardSize, cardScale } = useSettingsStore();
  const cardHeight = CARD_SIZES[size || baseCardSize].height * (cardScale / 100);
  const cardWidth = CARD_SIZES[size || baseCardSize].width * (cardScale / 100);

  const [isHovered, setIsHovered] = useState(false);

  const imageUrl = card.image_uris?.normal || card.card_faces?.[0]?.image_uris?.normal;
  const cardName = hidden ? 'Unknown Card' : card.card_name;

  const handleMouseEnter = (e: React.MouseEvent) => {
    if (!hidden && onHover) {
      onHover(card, { x: e.clientX, y: e.clientY });
    }
    setIsHovered(true);
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
    setIsHovered(false);
  };

  const left = handIndex * horizontalOffset;
  const top = Math.abs(handIndex * 8 );

  const rotation = card.is_tapped ? 90 : (handIndex * 4);
  const hoverScale = isHovered && inHand ? 1.05 : 1;
  const scaleTransform = scale !== undefined && scale !== 100 ? `scale(${scale / 100})` : '';
  const hoverScaleTransform = isHovered ? `scale(${hoverScale})` : '';
  const rotationTransform = rotation !== 0 ? `rotate(${rotation}deg)` : '';
  const combinedTransform = [scaleTransform, hoverScaleTransform, rotationTransform].filter(Boolean).join(' ');
  const scaleStyle = combinedTransform ? { ...style, transform: combinedTransform } : style;

  return (
    <div
      onMouseDown={handleMouseDown}
      onDoubleClick={handleDoubleClick}
      onMouseEnter={handleMouseEnter}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className={`
        flex items-center justify-center select-none 
        transition-all duration-200
        ${isDragging ? 'z-50' : ''}
        ${hidden ? 'display-none' : ''}
      `}
      style={{...scaleStyle, zIndex, position: 'relative', left, top, width: cardWidth, height: cardHeight}}
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