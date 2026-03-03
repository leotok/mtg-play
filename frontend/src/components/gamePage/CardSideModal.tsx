import React from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import type { CardSideOption } from '../../types/gameState';

interface CardSideModalProps {
  cardName: string;
  sides: CardSideOption[];
  onSelect: (sideIndex: number) => void;
  onClose: () => void;
}

const CardSideModal: React.FC<CardSideModalProps> = ({ cardName, sides, onSelect, onClose }) => {
  if (!sides || sides.length === 0) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black bg-opacity-75 transition-opacity" onClick={onClose} />
      
      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-gray-800 rounded-xl shadow-xl max-w-4xl w-full">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-700">
            <h2 className="text-xl font-bold text-gray-100">
              Choose Which Side to Play
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-200 transition-colors duration-200"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>

          {/* Card Sides */}
          <div className="p-6">
            <p className="text-gray-400 text-sm mb-6 text-center">
              {cardName} has multiple faces. Choose which side to play:
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {sides.map((side) => (
                <button
                  key={side.side_index}
                  onClick={() => onSelect(side.side_index)}
                  className="group relative bg-gray-700 rounded-lg overflow-hidden border-2 border-gray-600 hover:border-yellow-500 hover:ring-2 hover:ring-yellow-500/30 transition-all duration-200 transform hover:scale-[1.02]"
                >
                  {/* Card Image */}
                  <div className="aspect-[5/7] relative">
                    {side.image_url ? (
                      <img
                        src={side.image_url}
                        alt={side.name}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center bg-gray-600">
                        <span className="text-gray-400">No image available</span>
                      </div>
                    )}
                  </div>
                  
                  {/* Card Info Overlay */}
                  <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 via-black/70 to-transparent p-4">
                    <h3 className="text-lg font-bold text-gray-100 mb-1">
                      {side.name}
                    </h3>
                    {side.type_line && (
                      <p className="text-xs text-gray-300 mb-2">
                        {side.type_line}
                      </p>
                    )}
                    {side.mana_cost && (
                      <div className="flex items-center">
                        <span className="text-sm text-yellow-400 font-medium">
                          Mana Cost: {side.mana_cost}
                        </span>
                      </div>
                    )}
                  </div>
                  
                  {/* Selection indicator */}
                  <div className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity">
                    <span className="bg-yellow-500 text-gray-900 text-xs font-bold px-3 py-1 rounded-full">
                      Click to Select
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </div>
          
          {/* Footer */}
          <div className="p-6 border-t border-gray-700">
            <p className="text-gray-400 text-sm text-center">
              Select a side to play this the battlefield
            card onto </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CardSideModal;
