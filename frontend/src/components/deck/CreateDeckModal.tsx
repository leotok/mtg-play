import React, { useState, useEffect, useCallback } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { XMarkIcon, MagnifyingGlassIcon, CheckCircleIcon, SparklesIcon } from '@heroicons/react/24/outline';
import { apiClient } from '../../services/apiClient';

const createDeckSchema = z.object({
  name: z.string().min(1, 'Deck name is required').max(100, 'Deck name must be less than 100 characters'),
  description: z.string().max(500, 'Description must be less than 500 characters').optional(),
  commander_name: z.string().min(1, 'Commander is required'),
  is_public: z.boolean().default(false),
});

type CreateDeckFormData = z.infer<typeof createDeckSchema>;

interface CreateDeckModalProps {
  isOpen: boolean;
  onClose: () => void;
  onDeckCreated: () => void;
}

// Debounce hook
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);
  
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  
  return debouncedValue;
}

const CreateDeckModal: React.FC<CreateDeckModalProps> = ({ isOpen, onClose, onDeckCreated }) => {
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [selectedCommander, setSelectedCommander] = useState<any>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isValid },
    reset,
  } = useForm<CreateDeckFormData>({
    resolver: zodResolver(createDeckSchema),
    defaultValues: {
      is_public: false,
    },
    mode: 'onChange',
  });

  const commanderName = watch('commander_name');
  // Ensure we always have a string value
  const safeCommanderName = typeof commanderName === 'string' ? commanderName : '';
  const debouncedCommanderName = useDebounce(safeCommanderName, 500);

  // Auto-search when typing
  useEffect(() => {
    if (debouncedCommanderName && debouncedCommanderName.length >= 2 && !selectedCommander) {
      searchCommander(debouncedCommanderName);
    }
  }, [debouncedCommanderName, selectedCommander]);

  const searchCommander = useCallback(async (searchTerm: string) => {
    if (!searchTerm || searchTerm.length < 2) return;
    
    setIsSearching(true);
    setHasSearched(true);
    try {
      const results = await apiClient.get(`/search?q=${encodeURIComponent(searchTerm)}&type=legendary&type=creature`);
      setSearchResults(results || []);
    } catch (error) {
      console.error('Failed to search commander:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  }, []);

  const selectCommander = (card: any) => {
    setSelectedCommander(card);
    setValue('commander_name', card.name, { shouldValidate: true });
    setSearchResults([]);
  };

  const clearCommander = () => {
    setSelectedCommander(null);
    setValue('commander_name', '', { shouldValidate: true });
    setSearchResults([]);
    setHasSearched(false);
  };

  const onSubmit = async (data: CreateDeckFormData) => {
    if (!selectedCommander) {
      return;
    }

    setIsSubmitting(true);
    try {
      await apiClient.post('/decks', {
        name: data.name,
        description: data.description,
        commander_scryfall_id: selectedCommander.id,
        is_public: data.is_public,
      });
      
      reset();
      setSelectedCommander(null);
      setHasSearched(false);
      onDeckCreated();
      onClose();
    } catch (error) {
      console.error('Failed to create deck:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    reset();
    setSelectedCommander(null);
    setSearchResults([]);
    setHasSearched(false);
    onClose();
  };

  if (!isOpen) return null;

  // Determine button disabled state
  let buttonDisabledReason = '';
  if (isSubmitting) {
    buttonDisabledReason = 'Creating deck...';
  } else if (!selectedCommander) {
    buttonDisabledReason = 'Select a commander first';
  } else if (!isValid) {
    buttonDisabledReason = 'Fill in deck name';
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black bg-opacity-75 transition-opacity" onClick={handleClose} />
      
      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-gray-800 rounded-xl shadow-xl max-w-md w-full">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-700">
            <h2 className="text-xl font-bold text-gray-100">Create New Deck</h2>
            <button
              onClick={handleClose}
              className="text-gray-400 hover:text-gray-200 transition-colors duration-200"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>

          {/* Progress Steps */}
          <div className="px-6 pt-4">
            <div className="flex items-center space-x-2 text-sm">
              <div className={`flex items-center space-x-1 ${selectedCommander ? 'text-green-400' : 'text-yellow-500'}`}>
                <span className="flex items-center justify-center w-6 h-6 rounded-full bg-current bg-opacity-20 font-semibold">
                  {selectedCommander ? '✓' : '1'}
                </span>
                <span>Select Commander</span>
              </div>
              <span className="text-gray-600">→</span>
              <div className={`flex items-center space-x-1 ${isValid && selectedCommander ? 'text-green-400' : 'text-gray-500'}`}>
                <span className="flex items-center justify-center w-6 h-6 rounded-full bg-current bg-opacity-20 font-semibold">
                  {isValid && selectedCommander ? '✓' : '2'}
                </span>
                <span>Fill Details</span>
              </div>
            </div>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-6">
            {/* Deck Name */}
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-100 mb-2">
                Deck Name *
              </label>
              <input
                {...register('name')}
                type="text"
                id="name"
                className="bg-gray-700 text-gray-100 border border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:border-transparent w-full"
                placeholder="My Awesome Deck"
              />
              {errors.name && (
                <p className="mt-1 text-sm text-red-400">{errors.name.message}</p>
              )}
            </div>

            {/* Description */}
            <div>
              <label htmlFor="description" className="block text-sm font-medium text-gray-100 mb-2">
                Description
              </label>
              <textarea
                {...register('description')}
                id="description"
                rows={3}
                className="bg-gray-700 text-gray-100 border border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:border-transparent w-full"
                placeholder="Brief description of your deck..."
              />
              {errors.description && (
                <p className="mt-1 text-sm text-red-400">{errors.description.message}</p>
              )}
            </div>

            {/* Commander Search */}
            <div>
              <label htmlFor="commander_name" className="block text-sm font-medium text-gray-100 mb-2">
                Commander *
              </label>
              <div className="relative">
                <input
                  {...register('commander_name')}
                  type="text"
                  id="commander_name"
                  className="bg-gray-700 text-gray-100 border border-gray-600 rounded-lg px-4 py-2 pr-10 focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:border-transparent w-full"
                  placeholder="Search for a legendary creature..."
                />
                <button
                  type="button"
                  onClick={() => searchCommander(safeCommanderName)}
                  disabled={isSearching || safeCommanderName.length < 2}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-200 disabled:opacity-50"
                >
                  <MagnifyingGlassIcon className="h-5 w-5" />
                </button>
              </div>
              {errors.commander_name && (
                <p className="mt-1 text-sm text-red-400">{errors.commander_name.message}</p>
              )}

              {/* Search Results */}
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

              {/* Selected Commander */}
              {selectedCommander && (
                <div className="mt-2 p-3 bg-gray-700 rounded-lg flex items-center space-x-3">
                  {selectedCommander.image_uris?.small && (
                    <img
                      src={selectedCommander.image_uris.small}
                      alt={selectedCommander.name}
                      className="w-12 h-16 object-cover rounded"
                    />
                  )}
                  <div>
                    <p className="text-yellow-500 font-medium">{selectedCommander.name}</p>
                    <p className="text-gray-400 text-sm">Selected as Commander</p>
                  </div>
                </div>
              )}
            </div>

            {/* Public/Private */}
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

            {/* Submit Button */}
            <div className="flex items-center justify-end space-x-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-gray-300 hover:text-gray-100 transition-colors duration-200"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting || !selectedCommander}
                className="bg-yellow-500 text-gray-900 font-semibold py-2 px-4 rounded-lg hover:bg-yellow-400 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? 'Creating...' : 'Create Deck'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default CreateDeckModal;
