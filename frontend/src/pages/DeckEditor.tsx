import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import DeckHeader from '../components/deck/DeckHeader';
import CardList from '../components/deck/CardList';
import AddCardModal from '../components/deck/AddCardModal';
import ImportDeckModal from '../components/deck/ImportDeckModal';
import EditDeckModal from '../components/deck/EditDeckModal';
import PageHeader from '../components/common/PageHeader';
import type { DeckDetail, DeckCard } from '../types/deck';
import { apiClient } from '../services/apiClient';
import { useAuth } from '../context/AuthContext';
import { PlusIcon, ArrowLeftIcon } from '@heroicons/react/24/outline';

const DeckEditor: React.FC = () => {
  const { deckId } = useParams<{ deckId: string }>();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  
  const [deck, setDeck] = useState<DeckDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Modals
  const [isAddCardModalOpen, setIsAddCardModalOpen] = useState(false);
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  
  // Validation
  const [isValidating, setIsValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<{ valid: boolean; errors: string[] } | null>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
    
    if (deckId) {
      fetchDeck(parseInt(deckId));
    }
  }, [deckId, isAuthenticated, navigate]);

  const fetchDeck = async (id: number) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await apiClient.get(`/decks/${id}`);
      setDeck(response);
    } catch (err: any) {
      console.error('Failed to fetch deck:', err);
      setError(err.response?.data?.detail || 'Failed to load deck');
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdateCardQuantity = async (cardId: number, newQuantity: number) => {
    if (!deck) return;
    
    try {
      await apiClient.put(`/decks/${deck.id}/cards/${cardId}`, {
        quantity: newQuantity,
      });
      
      // Update local state
      setDeck(prev => {
        if (!prev) return null;
        return {
          ...prev,
          cards: prev.cards.map(card =>
            card.id === cardId ? { ...card, quantity: newQuantity } : card
          ),
        };
      });
    } catch (err) {
      console.error('Failed to update quantity:', err);
      alert('Failed to update card quantity');
    }
  };

  const handleRemoveCard = async (cardId: number) => {
    if (!deck) return;
    
    if (!window.confirm('Are you sure you want to remove this card?')) {
      return;
    }
    
    try {
      await apiClient.delete(`/decks/${deck.id}/cards/${cardId}`);
      
      // Update local state
      setDeck(prev => {
        if (!prev) return null;
        return {
          ...prev,
          cards: prev.cards.filter(card => card.id !== cardId),
          total_cards: (prev.total_cards || prev.cards.length) - 1,
        };
      });
    } catch (err) {
      console.error('Failed to remove card:', err);
      alert('Failed to remove card');
    }
  };

  const handleValidateDeck = async () => {
    if (!deck) return;
    
    setIsValidating(true);
    setValidationResult(null);
    
    try {
      const result = await apiClient.post(`/decks/${deck.id}/validate`, {});
      setValidationResult({
        valid: result.valid,
        errors: result.errors || [],
      });
    } catch (err) {
      console.error('Validation failed:', err);
      setValidationResult({
        valid: false,
        errors: ['Validation failed'],
      });
    } finally {
      setIsValidating(false);
    }
  };

  const handleDeleteDeck = async () => {
    if (!deck) return;
    
    if (!window.confirm(`Are you sure you want to delete "${deck.name}"? This cannot be undone.`)) {
      return;
    }
    
    try {
      await apiClient.delete(`/decks/${deck.id}`);
      navigate('/decks');
    } catch (err) {
      console.error('Failed to delete deck:', err);
      alert('Failed to delete deck');
    }
  };

  const handleCardsChanged = () => {
    if (deckId) {
      fetchDeck(parseInt(deckId));
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin h-12 w-12 border-2 border-yellow-500 border-t-transparent rounded-full mx-auto"></div>
          <p className="mt-4 text-gray-400">Loading deck...</p>
        </div>
      </div>
    );
  }

  if (error || !deck) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 text-lg mb-4">{error || 'Deck not found'}</p>
          <button
            onClick={() => navigate('/decks')}
            className="flex items-center space-x-2 text-gray-400 hover:text-gray-200 mx-auto"
          >
            <ArrowLeftIcon className="h-5 w-5" />
            <span>Back to Decks</span>
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950">
      <PageHeader title="Deck Editor" />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Deck Header */}
        <DeckHeader
          deck={deck}
          onEdit={() => setIsEditModalOpen(true)}
          onImport={() => setIsImportModalOpen(true)}
          onDelete={handleDeleteDeck}
          onValidate={handleValidateDeck}
          isValidating={isValidating}
          validationResult={validationResult}
        />

        {/* Action Bar */}
        <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
          <h2 className="text-2xl font-bold text-white">Cards</h2>
          <div className="flex space-x-3">
            <button
              onClick={() => setIsImportModalOpen(true)}
              className="flex items-center space-x-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg text-gray-200 transition-colors"
            >
              <span>Import List</span>
            </button>
            <button
              onClick={() => setIsAddCardModalOpen(true)}
              className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-yellow-500 to-amber-500 text-gray-900 font-semibold rounded-lg hover:from-yellow-400 hover:to-amber-400 transition-all"
            >
              <PlusIcon className="h-5 w-5" />
              <span>Add Card</span>
            </button>
          </div>
        </div>

        {/* Card List */}
        <CardList
          cards={deck.cards}
          onUpdateQuantity={handleUpdateCardQuantity}
          onRemoveCard={handleRemoveCard}
          commander={deck.cards.find(c => c.is_commander)}
        />
      </div>

      {/* Modals */}
      <AddCardModal
        isOpen={isAddCardModalOpen}
        onClose={() => setIsAddCardModalOpen(false)}
        deckId={deck.id}
        onCardAdded={handleCardsChanged}
      />

      <ImportDeckModal
        isOpen={isImportModalOpen}
        onClose={() => setIsImportModalOpen(false)}
        deckId={deck.id}
        onCardsImported={handleCardsChanged}
      />

      <EditDeckModal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        deck={deck}
        onDeckUpdated={handleCardsChanged}
      />
    </div>
  );
};

export default DeckEditor;
