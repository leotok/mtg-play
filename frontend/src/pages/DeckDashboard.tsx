import React, { useState, useEffect } from 'react';
import { PlusIcon, MagnifyingGlassIcon, LockClosedIcon, GlobeAltIcon, RectangleStackIcon } from '@heroicons/react/24/outline';
import DeckCard from '../components/deck/DeckCard';
import CreateDeckModal from '../components/deck/CreateDeckModal';
import PageHeader from '../components/common/PageHeader';
import type { Deck } from '../types/deck';
import { apiClient } from '../services/apiClient';

const DeckDashboard: React.FC = () => {
  const [decks, setDecks] = useState<Deck[]>([]);
  const [filteredDecks, setFilteredDecks] = useState<Deck[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  useEffect(() => {
    fetchDecks();
  }, []);

  useEffect(() => {
    if (searchQuery.trim() === '') {
      setFilteredDecks(decks);
    } else {
      const filtered = decks.filter(
        (deck) =>
          deck.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          deck.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
          deck.commander_name?.toLowerCase().includes(searchQuery.toLowerCase())
      );
      setFilteredDecks(filtered);
    }
  }, [searchQuery, decks]);

  const fetchDecks = async () => {
    setIsLoading(true);
    try {
      const response = await apiClient.get('/decks');
      setDecks(response || []);
      setFilteredDecks(response || []);
    } catch (error) {
      console.error('Failed to fetch decks:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleEditDeck = (deck: Deck) => {
    console.log('Edit deck:', deck);
  };

  const handleDeleteDeck = async (deck: Deck) => {
    if (!window.confirm(`Are you sure you want to delete "${deck.name}"?`)) {
      return;
    }

    try {
      await apiClient.delete(`/decks/${deck.id}`);
      await fetchDecks();
    } catch (error) {
      console.error('Failed to delete deck:', error);
      alert('Failed to delete deck');
    }
  };

  const handleExportDeck = (deck: Deck) => {
    console.log('Export deck:', deck);
  };

  const handleValidateDeck = (deck: Deck) => {
    console.log('Validate deck:', deck);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 flex items-center justify-center">
        <div className="text-center">
          <div className="relative">
            <div className="absolute inset-0 bg-yellow-500 blur-2xl opacity-20 rounded-full"></div>
            <svg className="animate-spin h-16 w-16 text-yellow-500 mx-auto relative" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>
          <p className="mt-6 text-gray-400 text-lg">Loading your decks...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950">
      <PageHeader title="My Decks" />

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-white mb-2">My Decks</h2>
          <p className="text-gray-400">Manage your Magic: The Gathering Commander decks</p>
        </div>

        {/* Stats Cards */}
        <div className="flex items-center gap-3 mb-6">
          <div className="flex items-center gap-2 bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-lg px-3 py-2">
            <RectangleStackIcon className="h-4 w-4 text-blue-400" />
            <span className="text-gray-400 text-sm">Total:</span>
            <span className="text-white font-bold">{decks.length}</span>
          </div>

          <div className="flex items-center gap-2 bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-lg px-3 py-2">
            <GlobeAltIcon className="h-4 w-4 text-green-400" />
            <span className="text-gray-400 text-sm">Public:</span>
            <span className="text-green-400 font-bold">{decks.filter(d => d.is_public).length}</span>
          </div>

          <div className="flex items-center gap-2 bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-lg px-3 py-2">
            <LockClosedIcon className="h-4 w-4 text-gray-400" />
            <span className="text-gray-400 text-sm">Private:</span>
            <span className="text-gray-300 font-bold">{decks.filter(d => !d.is_public).length}</span>
          </div>
        </div>

        {/* Actions Bar */}
        <div className="flex flex-col sm:flex-row items-center justify-between mb-8 gap-4">
          <div className="relative w-full sm:w-96">
            <MagnifyingGlassIcon className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-500" />
            <input
              type="text"
              placeholder="Search decks..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-gray-800/50 backdrop-blur-sm text-gray-100 border border-gray-700 rounded-xl pl-12 pr-4 py-3 focus:outline-none focus:ring-2 focus:ring-yellow-500/50 focus:border-yellow-500/50 transition-all placeholder-gray-500"
            />
          </div>

          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="flex items-center space-x-2 w-full sm:w-auto justify-center bg-gradient-to-r from-yellow-500 to-amber-500 text-gray-900 font-semibold py-3 px-6 rounded-xl hover:from-yellow-400 hover:to-amber-400 transition-all duration-200 shadow-lg shadow-yellow-500/20 hover:shadow-yellow-500/30"
          >
            <PlusIcon className="h-5 w-5" />
            <span>Create New Deck</span>
          </button>
        </div>

        {/* Decks Grid */}
        {filteredDecks.length === 0 ? (
          <div className="text-center py-20">
            <div className="bg-gray-800/30 border border-gray-700/50 rounded-2xl p-12 max-w-md mx-auto">
              <div className="bg-gradient-to-br from-yellow-500/20 to-amber-500/20 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6">
                <RectangleStackIcon className="h-10 w-10 text-yellow-500" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">
                {searchQuery ? 'No decks found' : 'No decks yet'}
              </h3>
              <p className="text-gray-400 mb-6">
                {searchQuery 
                  ? 'Try adjusting your search terms' 
                  : 'Create your first deck to get started with MTG Commander'}
              </p>
              {!searchQuery && (
                <button
                  onClick={() => setIsCreateModalOpen(true)}
                  className="bg-gradient-to-r from-yellow-500 to-amber-500 text-gray-900 font-semibold py-3 px-6 rounded-xl hover:from-yellow-400 hover:to-amber-400 transition-all duration-200"
                >
                  Create Your First Deck
                </button>
              )}
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredDecks.map((deck) => (
              <DeckCard
                key={deck.id}
                deck={deck}
                onDelete={handleDeleteDeck}
              />
            ))}
          </div>
        )}
      </main>

      <CreateDeckModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onDeckCreated={fetchDecks}
      />
    </div>
  );
};

export default DeckDashboard;
