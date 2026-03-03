import React, { useState, useRef, useEffect } from 'react';
import { type GameCard } from '../../types/gameState';
import { useSettingsStore } from '../../store/settingsStore';
import { CARD_SIZES, type CardSizeKey } from '../../config';

export const Card: React.FC<{
  card: GameCard | { id: number; card_name: string; image_uris?: { normal?: string }; card_faces?: Array<{ image_uris?: { normal?: string } }>; mana_cost?: string; type_line?: string; is_tapped?: boolean; battlefield_x?: number; battlefield_y?: number; is_attacking?: boolean; is_blocking?: boolean; is_face_up?: boolean };
  onTap?: () => void;
  onMouseDown?: (e: React.MouseEvent) => void;
  onHover?: (card: GameCard | { id: number; card_name: string; image_uris?: { normal?: string }; card_faces?: Array<{ image_uris?: { normal?: string } }>; mana_cost?: string; type_line?: string } | null) => void;
  size?: CardSizeKey;
  hidden?: boolean;
  isDragging?: boolean;
  isSelected?: boolean;
  style?: React.CSSProperties;
  scale?: number;
  handIndex?: number; // Position in hand for angles (e.g., -2, -1, 0, 1, 2)
  idx?: number; // Index in hand array for z-index (e.g., 0, 1, 2, 3, 4)
  horizontalOffset?: number;
  inHand?: boolean;
  rotation?: number;
  top?: number;
}> = ({ card, onTap, onMouseDown, onHover, size, hidden = false, isDragging = false, isSelected = false, style, scale, handIndex = 0, idx = 0, horizontalOffset = -40, inHand = false, rotation = 0, top = 0 }) => {
  const { baseCardSize, cardScale } = useSettingsStore();
  const cardHeight = CARD_SIZES[size || baseCardSize].height * (cardScale / 100);
  const cardWidth = CARD_SIZES[size || baseCardSize].width * (cardScale / 100);

  const [isHovered, setIsHovered] = useState(false);
  const isHoveredRef = useRef(false);
  const isPreviewShownRef = useRef(false);
  const wasDraggingRef = useRef(false);
  const cardRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (wasDraggingRef.current && !isDragging && isPreviewShownRef.current && onHover) {
      onHover(card);
    }
    wasDraggingRef.current = isDragging;
  }, [isDragging, card, onHover]);

  useEffect(() => {
    if (!isDragging && !isHoveredRef.current && cardRef.current) {
      const checkHover = () => {
        if (cardRef.current && cardRef.current.matches(':hover')) {
          isHoveredRef.current = true;
          setIsHovered(true);
        }
      };
      setTimeout(checkHover, 50);
    }
  }, [card.id, isDragging]);

  const imageUrl = card.image_uris?.normal || card.card_faces?.[0]?.image_uris?.normal;
  const cardName = hidden ? 'Unknown Card' : card.card_name;

  const handleMouseEnter = () => {
    isHoveredRef.current = true;
    if (!hidden && onHover) {
      onHover(card);
      isPreviewShownRef.current = true;
    }
    setIsHovered(true);
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    if (onMouseDown) {
      onMouseDown(e);
    }
  };

  const handleMouseMove = () => {
    // Position tracking removed - no longer needed
  };

  const handleDoubleClick = () => {
    if (onTap) {
      onTap();
    }
  };

  const handleClick = () => {
    // TODO: Implement card click behavior
  };

  const handleMouseLeave = () => {
    isHoveredRef.current = false;
    isPreviewShownRef.current = false;
    if (onHover) {
      onHover(null);
    }
    setIsHovered(false);
  };

  const left = handIndex * horizontalOffset;

  let cardTop = top;
  let zIndex = idx;

  if (isHovered && inHand) {
    cardTop = -15;
  }

  const cardRotation = card.is_tapped ? 90 : rotation;
  const hoverScale = isHovered && inHand ? 1.05 : 1;
  const scaleTransform = scale !== undefined && scale !== 100 ? `scale(${scale / 100})` : '';
  const hoverScaleTransform = isHovered ? `scale(${hoverScale})` : '';
  const rotationTransform = cardRotation !== 0 ? `rotate(${cardRotation}deg)` : '';
  const combinedTransform = [scaleTransform, hoverScaleTransform, rotationTransform].filter(Boolean).join(' ');
  const getBorderStyle = () => {
    if (isSelected) {
      return { boxShadow: '0 0 0 2px #22d3ee, 0 0 10px #22d3ee' };
    }
    if (isHovered || isDragging) {
      return { boxShadow: '0 0 0 2px #fbbf24, 0 0 10px #fbbf24' };
    }
    return {};
  };
  const hoverBorder = getBorderStyle();
  const scaleStyle = combinedTransform ? { ...style, transform: combinedTransform, ...hoverBorder } : { ...style, ...hoverBorder };

  return (
    <div
      ref={cardRef}
      onMouseDown={handleMouseDown}
      onClick={handleClick}
      onDoubleClick={handleDoubleClick}
      onMouseEnter={handleMouseEnter}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className={`
        flex items-center justify-center select-none min-w-fit
        transition-all duration-200
        ${isDragging ? 'z-500' : ''}
        ${hidden ? 'display-none' : ''}
      `}
      style={{...scaleStyle, zIndex: zIndex, position: 'relative', left, top: cardTop, width: cardWidth, height: cardHeight, pointerEvents: 'all', borderRadius: '8px'}}
    >
      {hidden ? (
        <img 
          src="https://backs.scryfall.io/small/2/2/222b7a3b-2321-4d4c-af19-19338b134971.jpg"
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