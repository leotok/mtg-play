import React from 'react';
import { Link } from 'react-router-dom';
import type { Deck } from '../../types/deck';
import { TrashIcon } from '@heroicons/react/24/outline';
import { ColorBadge } from '../../utils/colors';

interface DeckCardProps {
  deck: Deck;
  onDelete: (deck: Deck) => void;
}

const DeckCard: React.FC<DeckCardProps> = ({ deck, onDelete }) => {
  const commanderImage = deck.commander_image_uris?.art_crop || deck.commander_image_uris?.normal || deck.commander_image_uris?.large;

  return (
    <Link 
      to={`/decks/${deck.id}`}
      className="relative rounded-xl shadow-lg overflow-hidden hover:shadow-xl transition-all duration-200 group block"
      style={{
        backgroundImage: commanderImage ? `url(${commanderImage})` : undefined,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
      }}
    >
      {/* Dark overlay */}
      <div className="absolute inset-0 bg-gray-900/80 group-hover:bg-gray-900/70 transition-colors duration-200" />
      
      {/* Content */}
      <div className="relative p-6 cursor-pointer flex flex-col h-full">
        {/* Deck Header */}
        <div className="flex-1">
          <h3 className="text-xl font-bold text-white mb-1">{deck.name}</h3>
          {deck.commander_name && (
            <p className="text-sm text-yellow-500">
              Commander: {deck.commander_name}
            </p>
          )}
        </div>

        {/* Deck Description */}
        {deck.description && (
          <p className="text-gray-400 text-sm mb-4 line-clamp-2">
            {deck.description}
          </p>
        )}

        {/* Deck Stats */}
        <div className="flex items-center justify-between text-sm text-gray-400 mb-4">
          <span>{deck.total_cards || 0} cards</span>
          {deck.updated_at && (
            <span>Updated {new Date(deck.updated_at).toLocaleDateString()}</span>
          )}
        </div>

        {/* Badges */}
        <div className="flex items-center justify-between mt-auto">
          <div className="flex items-center space-x-2">
            <ColorBadge colors={deck.color_identity} />
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
              deck.is_public 
                ? 'bg-green-600 text-white' 
                : 'bg-gray-600 text-gray-300'
            }`}>
              {deck.is_public ? 'Public' : 'Private'}
            </span>
          </div>
          <button
            onClick={(e) => { e.preventDefault(); onDelete(deck); }}
            className="p-2 text-gray-400 hover:text-red-400 transition-colors duration-200"
            title="Delete Deck"
          >
            <TrashIcon className="h-5 w-5" />
          </button>
        </div>
      </div>
    </Link>
  );
};

export default DeckCard;
