import React from 'react';
import { useNavigate } from 'react-router-dom';
import type { DeckDetail } from '../../types/deck';
import { ArrowLeftIcon, PencilIcon, TrashIcon, CheckCircleIcon } from '@heroicons/react/24/outline';
import { ColorBadge } from '../../utils/colors';

interface DeckHeaderProps {
  deck: DeckDetail;
  onEdit: () => void;
  onDelete: () => void;
  onValidate: () => void;
  isValidating: boolean;
  validationResult: { valid: boolean; errors: string[] } | null;
}

const DeckHeader: React.FC<DeckHeaderProps> = ({
  deck,
  onEdit,
  onDelete,
  onValidate,
  isValidating,
  validationResult,
}) => {
  const navigate = useNavigate();

  return (
    <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-xl p-4 mb-4">
      {/* Breadcrumb */}
      <button
        onClick={() => navigate('/decks')}
        className="flex items-center space-x-2 text-gray-400 hover:text-gray-200 mb-4 transition-colors"
      >
        <ArrowLeftIcon className="h-4 w-4" />
        <span className="text-sm">Back to Decks</span>
      </button>

      <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
        {/* Left: Basic Info */}
        <div className="flex-1">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white mb-1">{deck.name}</h1>
              {deck.commander && (
                <p className="text-yellow-500 text-sm mb-2">
                  Commander: {deck.commander.name}
                </p>
              )}
            </div>
          </div>

          {deck.description && (
            <p className="text-gray-400 mb-3 max-w-xl text-sm">{deck.description}</p>
          )}

          <div className="flex flex-wrap items-center gap-2 mb-3">
            <ColorBadge colors={deck.commander?.color_identity || deck.commander?.colors || []} />
            
            <span className={`px-2 py-1 rounded-full text-xs ${deck.is_public ? 'bg-green-500/20 text-green-400' : 'bg-gray-600 text-gray-300'}`}>
              {deck.is_public ? 'Public' : 'Private'}
            </span>
          </div>

          {/* Validation Status */}
          {validationResult && (
            <div className={`flex items-center space-x-2 p-2 rounded-lg text-sm ${validationResult.valid ? 'bg-green-900/30 border border-green-500/30' : 'bg-yellow-900/30 border border-yellow-500/30'}`}>
              <CheckCircleIcon className={`h-4 w-4 ${validationResult.valid ? 'text-green-400' : 'text-yellow-400'}`} />
              <span className={`${validationResult.valid ? 'text-green-400' : 'text-yellow-400'}`}>
                {validationResult.valid 
                  ? 'Deck is valid!' 
                  : `Validation issues: ${validationResult.errors.length}`}
              </span>
            </div>
          )}
        </div>

        {/* Right: Actions */}
        <div className="flex flex-wrap gap-2">
          <button
            onClick={onEdit}
            className="flex items-center space-x-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-gray-200 transition-colors"
          >
            <PencilIcon className="h-4 w-4" />
            <span>Edit Info</span>
          </button>

          <button
            onClick={onValidate}
            disabled={isValidating}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 rounded-lg transition-colors disabled:opacity-50"
          >
            {isValidating ? (
              <>
                <div className="animate-spin h-4 w-4 border-2 border-current border-t-transparent rounded-full" />
                <span>Validating...</span>
              </>
            ) : (
              <>
                <CheckCircleIcon className="h-4 w-4" />
                <span>Validate</span>
              </>
            )}
          </button>

          <button
            onClick={onDelete}
            className="flex items-center space-x-2 px-4 py-2 bg-red-500/20 text-red-400 hover:bg-red-500/30 rounded-lg transition-colors"
          >
            <TrashIcon className="h-4 w-4" />
            <span>Delete</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default DeckHeader;
