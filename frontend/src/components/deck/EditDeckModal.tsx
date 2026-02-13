import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { XMarkIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import { apiClient } from '../../services/apiClient';
import type { DeckDetail } from '../../types/deck';

const editDeckSchema = z.object({
  name: z.string().min(1, 'Deck name is required').max(100, 'Deck name must be less than 100 characters'),
  description: z.string().max(500, 'Description must be less than 500 characters').optional(),
  is_public: z.boolean(),
});

type EditDeckFormData = z.infer<typeof editDeckSchema>;

interface EditDeckModalProps {
  isOpen: boolean;
  onClose: () => void;
  deck: DeckDetail;
  onDeckUpdated: () => void;
}

const EditDeckModal: React.FC<EditDeckModalProps> = ({ isOpen, onClose, deck, onDeckUpdated }) => {
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [selectedCommander, setSelectedCommander] = useState<any>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
    reset,
  } = useForm<EditDeckFormData>({
    resolver: zodResolver(editDeckSchema),
    defaultValues: {
      name: deck.name,
      description: deck.description || '',
      is_public: deck.is_public,
    },
  });

  useEffect(() => {
    if (deck.commander) {
      setSelectedCommander({
        id: deck.commander_scryfall_id,
        name: deck.commander.name,
        image_uris: deck.commander.image_uris,
      });
    }
  }, [deck]);

  const searchCommander = async (query: string) => {
    if (!query || query.length < 2) return;
    
    setIsSearching(true);
    try {
      const results = await apiClient.get(`/search?q=${encodeURIComponent(query)}&type=legendary&type=creature`);
      setSearchResults(results || []);
    } catch (error) {
      console.error('Failed to search commander:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const selectCommander = (card: any) => {
    setSelectedCommander(card);
    setSearchQuery(card.name);
    setSearchResults([]);
  };

  const clearCommander = () => {
    setSelectedCommander(null);
    setSearchQuery('');
    setSearchResults([]);
  };

  const onSubmit = async (data: EditDeckFormData) => {
    setIsSubmitting(true);
    try {
      await apiClient.put(`/decks/${deck.id}`, {
        name: data.name,
        description: data.description,
        commander_scryfall_id: selectedCommander?.id,
        is_public: data.is_public,
      });
      
      onDeckUpdated();
      onClose();
    } catch (error) {
      console.error('Failed to update deck:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    reset();
    setSelectedCommander(null);
    setSearchQuery('');
    setSearchResults([]);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="fixed inset-0 bg-black bg-opacity-75 transition-opacity" onClick={handleClose} />
      
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-gray-800 rounded-xl shadow-xl max-w-md w-full">
          <div className="flex items-center justify-between p-6 border-b border-gray-700">
            <h2 className="text-xl font-bold text-gray-100">Edit Deck</h2>
            <button
              onClick={handleClose}
              className="text-gray-400 hover:text-gray-200 transition-colors duration-200"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-6">
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-100 mb-2">
                Deck Name *
              </label>
              <input
                {...register('name')}
                type="text"
                id="name"
                className="bg-gray-700 text-gray-100 border border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:border-transparent w-full"
              />
              {errors.name && (
                <p className="mt-1 text-sm text-red-400">{errors.name.message}</p>
              )}
            </div>

            <div>
              <label htmlFor="description" className="block text-sm font-medium text-gray-100 mb-2">
                Description
              </label>
              <textarea
                {...register('description')}
                id="description"
                rows={3}
                className="bg-gray-700 text-gray-100 border border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:border-transparent w-full"
              />
              {errors.description && (
                <p className="mt-1 text-sm text-red-400">{errors.description.message}</p>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-100 mb-2">
                Commander
              </label>
              <div className="relative">
                <input
                  type="text"
                  value={selectedCommander ? selectedCommander.name : searchQuery}
                  onChange={(e) => {
                    setSelectedCommander(null);
                    setSearchQuery(e.target.value);
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      searchCommander(searchQuery);
                    }
                  }}
                  className="bg-gray-700 text-gray-100 border border-gray-600 rounded-lg px-4 py-2 pr-10 focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:border-transparent w-full"
                  placeholder="Search for a legendary creature..."
                />
                <button
                  type="button"
                  onClick={() => searchCommander(searchQuery)}
                  disabled={isSearching || searchQuery.length < 2}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-200 disabled:opacity-50"
                >
                  {isSearching ? (
                    <div className="animate-spin h-5 w-5 border-2 border-current border-t-transparent rounded-full" />
                  ) : (
                    <MagnifyingGlassIcon className="h-5 w-5" />
                  )}
                </button>
              </div>

              {searchResults.length > 0 && (
                <div className="mt-2 bg-gray-700 rounded-lg max-h-48 overflow-y-auto">
                  {searchResults.map((card) => (
                    <button
                      key={card.id}
                      type="button"
                      onClick={() => selectCommander(card)}
                      className="w-full text-left px-4 py-2 hover:bg-gray-600 transition-colors duration-200 flex items-center space-x-3"
                    >
                      {card.image_uris?.small && (
                        <img
                          src={card.image_uris.small}
                          alt={card.name}
                          className="w-8 h-11 object-cover rounded"
                        />
                      )}
                      <div>
                        <p className="text-gray-100 font-medium">{card.name}</p>
                        <p className="text-gray-400 text-sm">{card.type_line}</p>
                      </div>
                    </button>
                  ))}
                </div>
              )}

              {selectedCommander && (
                <div className="mt-2 p-3 bg-gray-700 rounded-lg flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {selectedCommander.image_uris?.small && (
                      <img
                        src={selectedCommander.image_uris.small}
                        alt={selectedCommander.name}
                        className="w-12 h-16 object-cover rounded"
                      />
                    )}
                    <div>
                      <p className="text-yellow-500 font-medium">{selectedCommander.name}</p>
                      <p className="text-gray-400 text-sm">Commander</p>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={clearCommander}
                    className="text-gray-400 hover:text-red-400"
                  >
                    <XMarkIcon className="h-5 w-5" />
                  </button>
                </div>
              )}
            </div>

            <div className="flex items-center">
              <input
                {...register('is_public')}
                type="checkbox"
                id="is_public"
                className="h-4 w-4 text-yellow-500 focus:ring-yellow-500 border-gray-600 rounded"
              />
              <label htmlFor="is_public" className="ml-2 block text-sm text-gray-300">
                Make this deck public
              </label>
            </div>

            <div className="flex items-center justify-end space-x-3 pt-4">
              <button
                type="button"
                onClick={handleClose}
                className="px-4 py-2 text-gray-300 hover:text-gray-100 transition-colors duration-200"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting || !selectedCommander}
                className="bg-yellow-500 text-gray-900 font-semibold py-2 px-4 rounded-lg hover:bg-yellow-400 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default EditDeckModal;
