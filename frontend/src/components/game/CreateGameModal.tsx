import React, { useState } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { apiClient } from '../../services/apiClient';
import type { PowerBracket, GameRoom, GameRoomCreate } from '../../types/game';
import { POWER_BRACKET_LABELS } from '../../types/game';

interface CreateGameModalProps {
  isOpen: boolean;
  onClose: () => void;
  onGameCreated: (game: GameRoom) => void;
}

const CreateGameModal: React.FC<CreateGameModalProps> = ({ isOpen, onClose, onGameCreated }) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [maxPlayers, setMaxPlayers] = useState(4);
  const [powerBracket, setPowerBracket] = useState<PowerBracket>('casual');
  const [isPublic, setIsPublic] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!name.trim()) {
      setError('Game name is required');
      return;
    }

    setIsSubmitting(true);
    setError('');

    try {
      const gameData: GameRoomCreate = {
        name: name.trim(),
        description: description.trim() || undefined,
        max_players: maxPlayers,
        power_bracket: powerBracket,
        is_public: isPublic,
      };

      const response = await apiClient.post('/games', gameData);
      onGameCreated(response);
      handleClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create game');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    setName('');
    setDescription('');
    setMaxPlayers(4);
    setPowerBracket('casual');
    setIsPublic(false);
    setError('');
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black bg-opacity-75 transition-opacity" onClick={handleClose} />
      
      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div className="relative bg-gray-800 rounded-xl shadow-xl max-w-md w-full">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-700">
            <h2 className="text-xl font-bold text-gray-100">Create Game</h2>
            <button
              onClick={handleClose}
              className="text-gray-400 hover:text-gray-200 transition-colors duration-200"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-6 space-y-5">
            {/* Error Message */}
            {error && (
              <div className="p-3 bg-red-500/20 border border-red-500/30 rounded-lg text-red-400 text-sm">
                {error}
              </div>
            )}

            {/* Game Name */}
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-100 mb-2">
                Game Name *
              </label>
              <input
                type="text"
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="bg-gray-700 text-gray-100 border border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:border-transparent w-full"
                placeholder="EDH Night"
                maxLength={100}
              />
            </div>

            {/* Description */}
            <div>
              <label htmlFor="description" className="block text-sm font-medium text-gray-100 mb-2">
                Description
              </label>
              <textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={2}
                className="bg-gray-700 text-gray-100 border border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:border-transparent w-full"
                placeholder="Brief description of the game..."
                maxLength={500}
              />
            </div>

            {/* Max Players */}
            <div>
              <label htmlFor="maxPlayers" className="block text-sm font-medium text-gray-100 mb-2">
                Number of Players
              </label>
              <select
                id="maxPlayers"
                value={maxPlayers}
                onChange={(e) => setMaxPlayers(Number(e.target.value))}
                className="bg-gray-700 text-gray-100 border border-gray-600 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:border-transparent w-full"
              >
                <option value={2}>2 Players</option>
                <option value={3}>3 Players</option>
                <option value={4}>4 Players</option>
              </select>
            </div>

            {/* Power Bracket */}
            <div>
              <label className="block text-sm font-medium text-gray-100 mb-2">
                Power Bracket
              </label>
              <div className="grid grid-cols-4 gap-2">
                {(['precon', 'casual', 'optimized', 'cedh'] as PowerBracket[]).map((bracket) => (
                  <button
                    key={bracket}
                    type="button"
                    onClick={() => setPowerBracket(bracket)}
                    className={`py-2 px-3 rounded-lg text-sm font-medium transition-all duration-200 ${
                      powerBracket === bracket
                        ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
                        : 'bg-gray-700 text-gray-300 border border-gray-600 hover:border-gray-500'
                    }`}
                  >
                    {POWER_BRACKET_LABELS[bracket]}
                  </button>
                ))}
              </div>
            </div>

            {/* Public/Private Toggle */}
            <div className="flex items-center justify-between p-4 bg-gray-700/50 rounded-lg">
              <div>
                <p className="text-gray-100 font-medium">Public Game</p>
                <p className="text-gray-400 text-sm">Anyone can see and join</p>
              </div>
              <button
                type="button"
                onClick={() => setIsPublic(!isPublic)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-200 ${
                  isPublic ? 'bg-yellow-500' : 'bg-gray-600'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform duration-200 ${
                    isPublic ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            {/* Submit Button */}
            <div className="flex items-center justify-end space-x-3 pt-2">
              <button
                type="button"
                onClick={handleClose}
                className="px-4 py-2 text-gray-300 hover:text-gray-100 transition-colors duration-200"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting || !name.trim()}
                className="bg-gradient-to-r from-yellow-500 to-amber-500 text-gray-900 font-semibold py-2 px-6 rounded-lg hover:from-yellow-400 hover:to-amber-400 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? 'Creating...' : 'Create Game'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default CreateGameModal;
