import React from 'react';
import { type GameCard } from '../../types/gameState';


export const CardPreview: React.FC<{
  card: GameCard | { id: number; card_name: string; image_uris?: { normal?: string }; card_faces?: Array<{ image_uris?: { normal?: string } }>; mana_cost?: string; type_line?: string };
  position: { x: number; y: number };
  isOpponent?: boolean;
  isCommander?: boolean;
}> = ({ card, position, isOpponent = false, isCommander = false }) => {
  const imageUrl = card.image_uris?.normal || card.card_faces?.[0]?.image_uris?.normal;
  if (!imageUrl) return null;

  const previewWidth = 256;
  const aspectRatio = 1.4;
  const previewHeight = previewWidth * aspectRatio;

  return (
    <div
      className="fixed pointer-events-none z-50"
      style={{
        left: isCommander ? position.x - previewWidth : position.x,
        top: isOpponent ? position.y : position.y - previewHeight - 10,
      }}
    >
      <img
        src={imageUrl}
        alt={card.card_name}
        className="w-64 h-auto rounded-lg shadow-2xl border-2 border-gray-600"
      />
    </div>
  );
};