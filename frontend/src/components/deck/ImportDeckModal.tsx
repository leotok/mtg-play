import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { XMarkIcon, DocumentArrowUpIcon, CheckCircleIcon, ExclamationCircleIcon } from '@heroicons/react/24/outline';
import { apiClient } from '../../services/apiClient';

const importSchema = z.object({
  deck_list: z.string().min(1, 'Deck list is required'),
});

type ImportFormData = z.infer<typeof importSchema>;

interface ImportDeckModalProps {
  isOpen: boolean;
  onClose: () => void;
  deckId: number;
  onCardsImported: () => void;
}

interface ImportResult {
  success: boolean;
  imported_count: number;
  failed_cards: string[];
  errors: string[];
}

const ImportDeckModal: React.FC<ImportDeckModalProps> = ({ isOpen, onClose, deckId, onCardsImported }) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [showHelp, setShowHelp] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<ImportFormData>({
    resolver: zodResolver(importSchema),
  });

  const onSubmit = async (data: ImportFormData) => {
    setIsSubmitting(true);
    setImportResult(null);
    
    try {
      const result = await apiClient.post(`/decks/${deckId}/import/text`, {
        deck_text: data.deck_list,
      });
      
      setImportResult({
        success: result.success,
        imported_count: result.imported_count || 0,
        failed_cards: result.failed_cards || [],
        errors: result.errors || [],
      });
      
      if (result.success && result.imported_count > 0) {
        onCardsImported();
      }
    } catch (error: any) {
      setImportResult({
        success: false,
        imported_count: 0,
        failed_cards: [],
        errors: [error.response?.data?.detail || 'Import failed. Please try again.'],
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    reset();
    setImportResult(null);
    setShowHelp(false);
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
            <div className="flex items-center space-x-3">
              <div className="bg-gradient-to-br from-green-500 to-emerald-600 p-2 rounded-lg">
                <DocumentArrowUpIcon className="h-5 w-5 text-white" />
              </div>
              <h2 className="text-xl font-bold text-gray-100">Import Deck List</h2>
            </div>
            <button
              onClick={handleClose}
              className="text-gray-400 hover:text-gray-200 transition-colors duration-200"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>

          <div className="p-6">
            {/* Help Toggle */}
            <button
              onClick={() => setShowHelp(!showHelp)}
              className="text-sm text-yellow-500 hover:text-yellow-400 mb-4 underline"
            >
              {showHelp ? 'Hide Help' : 'Show Format Help'}
            </button>

            {/* Help Panel */}
            {showHelp && (
              <div className="bg-gray-700/50 rounded-lg p-4 mb-4 text-sm space-y-3">
                <p className="text-gray-300">
                  Paste your deck list below. Supported formats:
                </p>
                <div className="space-y-2 text-gray-400">
                  <p><strong className="text-yellow-500">Simple format:</strong></p>
                  <pre className="bg-gray-800 p-2 rounded text-xs">
{`1 Sol Ring
1 Command Tower
1 Arcane Signet
20 Plains
20 Island`}</pre>
                  
                  <p><strong className="text-yellow-500">MTGO/MTGA format:</strong></p>
                  <pre className="bg-gray-800 p-2 rounded text-xs">
{`1 Sol Ring (CMR) 247
1 Command Tower (C19) 239
1 Arcane Signet (CMR) 222`}</pre>
                  
                  <p><strong className="text-yellow-500">With set codes (optional):</strong></p>
                  <pre className="bg-gray-800 p-2 rounded text-xs">
{`1 Sol Ring [CMR]
1 Command Tower [C19]`}</pre>
                </div>
                <p className="text-gray-500 text-xs">
                  The import will match card names against Scryfall's database. Set codes help find the correct version.
                </p>
              </div>
            )}

            {/* Import Form */}
            {!importResult ? (
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-100 mb-2">
                    Deck List <span className="text-red-400">*</span>
                  </label>
                  <textarea
                    {...register('deck_list')}
                    rows={15}
                    className="w-full bg-gray-700 text-gray-100 border border-gray-600 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent font-mono text-sm"
                    placeholder={`Paste your deck list here...\n\nExample:\n1 Sol Ring\n1 Command Tower\n1 Arcane Signet\n1 Brainstorm\n1 Ponder\n20 Island\n20 Swamp`}
                  />
                  {errors.deck_list && (
                    <p className="mt-1 text-sm text-red-400">{errors.deck_list.message}</p>
                  )}
                </div>

                <div className="flex items-center justify-end space-x-3 pt-4 border-t border-gray-700">
                  <button
                    type="button"
                    onClick={handleClose}
                    className="px-4 py-2 text-gray-300 hover:text-gray-100 transition-colors duration-200"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="bg-gradient-to-r from-green-500 to-emerald-500 text-white font-semibold py-2 px-6 rounded-lg hover:from-green-400 hover:to-emerald-400 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-green-500/20"
                  >
                    {isSubmitting ? (
                      <span className="flex items-center space-x-2">
                        <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
                        <span>Importing...</span>
                      </span>
                    ) : (
                      'Import Cards'
                    )}
                  </button>
                </div>
              </form>
            ) : (
              /* Import Results */
              <div className="space-y-4">
                <div className={`p-4 rounded-lg ${importResult.success ? 'bg-green-900/30 border border-green-500/30' : 'bg-red-900/30 border border-red-500/30'}`}>
                  <div className="flex items-center space-x-3">
                    {importResult.success ? (
                      <CheckCircleIcon className="h-8 w-8 text-green-400" />
                    ) : (
                      <ExclamationCircleIcon className="h-8 w-8 text-red-400" />
                    )}
                    <div>
                      <h3 className={`text-lg font-semibold ${importResult.success ? 'text-green-400' : 'text-red-400'}`}>
                        {importResult.success ? 'Import Successful!' : 'Import Completed with Issues'}
                      </h3>
                      <p className="text-gray-300">
                        {importResult.imported_count} cards imported successfully
                      </p>
                    </div>
                  </div>
                </div>

                {/* Failed Cards */}
                {importResult.failed_cards.length > 0 && (
                  <div className="bg-gray-700/50 rounded-lg p-4">
                    <h4 className="text-sm font-semibold text-red-400 mb-2">
                      Failed to import ({importResult.failed_cards.length} cards):
                    </h4>
                    <ul className="text-sm text-gray-400 space-y-1 max-h-32 overflow-y-auto">
                      {importResult.failed_cards.map((card, index) => (
                        <li key={index} className="flex items-center space-x-2">
                          <span className="text-red-500">•</span>
                          <span>{card}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Errors */}
                {importResult.errors.length > 0 && (
                  <div className="bg-gray-700/50 rounded-lg p-4">
                    <h4 className="text-sm font-semibold text-red-400 mb-2">Errors:</h4>
                    <ul className="text-sm text-gray-400 space-y-1">
                      {importResult.errors.map((error, index) => (
                        <li key={index} className="flex items-center space-x-2">
                          <span className="text-red-500">•</span>
                          <span>{error}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="flex items-center justify-end space-x-3 pt-4 border-t border-gray-700">
                  <button
                    onClick={() => {
                      setImportResult(null);
                      reset();
                    }}
                    className="px-4 py-2 text-gray-300 hover:text-gray-100 transition-colors duration-200"
                  >
                    Import Another List
                  </button>
                  <button
                    onClick={handleClose}
                    className="bg-gradient-to-r from-green-500 to-emerald-500 text-white font-semibold py-2 px-6 rounded-lg hover:from-green-400 hover:to-emerald-400 transition-all duration-200"
                  >
                    Done
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

export default ImportDeckModal;
