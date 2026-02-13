import React, { useState, useEffect, useCallback } from 'react';
import { XMarkIcon, MagnifyingGlassIcon, PlusIcon, MinusIcon } from '@heroicons/react/24/outline';
import { apiClient } from '../../services/apiClient';
import ManaCost from '../common/ManaCost';

interface AddCardModalProps {
  isOpen: boolean;
  onClose: () => void;
  deckId: number;
  onCardAdded: () => void;
}

interface CardResult {
  id: string;
  name: string;
  type_line: string;
  mana_cost?: string;
  image_uris?: {
    small?: string;
    normal?: string;
  };
}

const AddCardModal: React.FC<AddCardModalProps> = ({ isOpen, onClose, deckId, onCardAdded }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<CardResult[]>([]);
  const [selectedCard, setSelectedCard] = useState<CardResult | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [isAdding, setIsAdding] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchTerm.length >= 2) {
        searchCards(searchTerm);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [searchTerm]);

  const searchCards = useCallback(async (query: string) => {
    if (!query || query.length < 2) return;
    
    setIsSearching(true);
    setError(null);
    
    try {
      const results = await apiClient.get(`/search?q=${encodeURIComponent(query)}&limit=20`);
      setSearchResults(results || []);
    } catch (err) {
      console.error('Search failed:', err);
      setError('Failed to search cards');
    } finally {
      setIsSearching(false);
    }
  }, []);

  const selectCard = (card: CardResult) => {
    setSelectedCard(card);
    setQuantity(1);
    setError(null);
  };

  const addCard = async () => {
    if (!selectedCard) return;
    
    setIsAdding(true);
    setError(null);
    
    try {
      await apiClient.post(`/decks/${deckId}/cards`, {
        card_scryfall_id: selectedCard.id,
        quantity: quantity,
        is_commander: false,
      });
      
      onCardAdded();
      setSelectedCard(null);
      setSearchTerm('');
      setSearchResults([]);
      setQuantity(1);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to add card');
    } finally {
      setIsAdding(false);
    }
  };

  const handleClose = () => {
    setSearchTerm('');
    setSearchResults([]);
    setSelectedCard(null);
    setQuantity(1);
    setError(null);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="fixed inset-0 bg-black bg-opacity-75 transition-opacity" onClick={handleClose} />
      
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-gray-800 rounded-xl shadow-xl max-w-2xl w-full border border-gray-700">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-700">
            <h2 className="text-xl font-bold text-gray-100">Add Card</h2>
            <button
              onClick={handleClose}
              className="text-gray-400 hover:text-gray-200 transition-colors duration-200"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>

          <div className="p-6">
            {/* Search */}
            {!selectedCard ? (
              <div className="space-y-4">
                <div className="relative">
                  <MagnifyingGlassIcon className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-500" />
                  <input
                    type="text"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    placeholder="Search for cards..."
                    className="w-full bg-gray-700 text-gray-100 border border-gray-600 rounded-lg pl-12 pr-4 py-3 focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:border-transparent"
                    autoFocus
                  />
                </div>

                {isSearching && (
                  <div className="text-center py-8">
                    <div className="animate-spin h-8 w-8 border-2 border-yellow-500 border-t-transparent rounded-full mx-auto"></div>
                    <p className="text-gray-500 mt-2">Searching...</p>
                  </div>
                )}

                {error && (
                  <div className="bg-red-900/30 border border-red-500/30 rounded-lg p-3 text-red-400 text-sm">
                    {error}
                  </div>
                )}

                {/* Search Results */}
                {searchResults.length > 0 && (
                  <div className="bg-gray-700 rounded-lg max-h-80 overflow-y-auto border border-gray-600">
                    <div className="px-3 py-2 bg-gray-750 border-b border-gray-600 text-xs text-gray-400">
                      Click a card to add it:
                    </div>
                    {searchResults.map((card) => (
                      <button
                        key={card.id}
                        onClick={() => selectCard(card)}
                        className="w-full text-left px-4 py-3 hover:bg-gray-600 transition-colors duration-200 flex items-center space-x-3 border-b border-gray-600 last:border-0"
                      >
                        {card.image_uris?.small ? (
                          <img
                            src={card.image_uris.small}
                            alt={card.name}
                            className="w-10 h-14 object-cover rounded shadow-md"
                          />
                        ) : (
                          <div className="w-10 h-14 bg-gray-600 rounded flex items-center justify-center">
                            <span className="text-xs text-gray-500">?</span>
                          </div>
                        )}
                        <div className="flex-1 min-w-0">
                          <p className="text-gray-100 font-medium truncate">{card.name}</p>
                          <p className="text-gray-400 text-xs truncate">{card.type_line}</p>
                          {card.mana_cost && (
                            <ManaCost cost={card.mana_cost} className="mt-1" />
                          )}
                        </div>
                      </button>
                    ))}
                  </div>
                )}

                {searchTerm.length >= 2 && !isSearching && searchResults.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    <p>No cards found</p>
                    <p className="text-sm mt-1">Try a different search term</p>
                  </div>
                )}
              </div>
            ) : (
              /* Selected Card Details */
              <div className="space-y-6">
                <div className="flex items-start space-x-4">
                  {selectedCard.image_uris?.normal ? (
                    <img
                      src={selectedCard.image_uris.normal}
                      alt={selectedCard.name}
                      className="w-32 h-44 object-cover rounded-lg shadow-xl"
                    />
                  ) : (
                    <div className="w-32 h-44 bg-gray-700 rounded-lg flex items-center justify-center">
                      <span className="text-gray-500">No Image</span>
                    </div>
                  )}
                  
                  <div className="flex-1">
                    <h3 className="text-xl font-bold text-white">{selectedCard.name}</h3>
                    <p className="text-gray-400">{selectedCard.type_line}</p>
                    {selectedCard.mana_cost && (
                      <ManaCost cost={selectedCard.mana_cost} className="mt-1" />
                    )}
                    
                    <button
                      onClick={() => {
                        setSelectedCard(null);
                        setError(null);
                      }}
                      className="text-sm text-yellow-500 hover:text-yellow-400 mt-4 underline"
                    >
                      ← Back to search
                    </button>
                  </div>
                </div>

                {/* Quantity Selector */}
                <div className="bg-gray-700/50 rounded-lg p-4">
                  <label className="block text-sm font-medium text-gray-300 mb-3">
                    Quantity
                  </label>
                  <div className="flex items-center space-x-4">
                    <button
                      onClick={() => setQuantity(Math.max(1, quantity - 1))}
                      className="p-2 rounded-lg bg-gray-700 hover:bg-gray-600 text-gray-300"
                    >
                      <MinusIcon className="h-5 w-5" />
                    </button>
                    
                    <span className="text-2xl font-bold text-white w-12 text-center">
                      {quantity}
                    </span>
                    
                    <button
                      onClick={() => setQuantity(Math.min(99, quantity + 1))}
                      className="p-2 rounded-lg bg-gray-700 hover:bg-gray-600 text-gray-300"
                    >
                      <PlusIcon className="h-5 w-5" />
                    </button>
                  </div>
                </div>

                {error && (
                  <div className="bg-red-900/30 border border-red-500/30 rounded-lg p-3 text-red-400 text-sm">
                    {error}
                  </div>
                )}

                <div className="flex items-center justify-end space-x-3">
                  <button
                    onClick={() => {
                      setSelectedCard(null);
                      setError(null);
                    }}
                    className="px-4 py-2 text-gray-300 hover:text-gray-100 transition-colors duration-200"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={addCard}
                    disabled={isAdding}
                    className="bg-gradient-to-r from-yellow-500 to-amber-500 text-gray-900 font-semibold py-2 px-6 rounded-lg hover:from-yellow-400 hover:to-amber-400 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isAdding ? (
                      <span className="flex items-center space-x-2">
                        <div className="animate-spin h-4 w-4 border-2 border-gray-900 border-t-transparent rounded-full" />
                        <span>Adding...</span>
                      </span>
                    ) : (
                      `Add ${quantity} to Deck`
                    )}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AddCardModal;
