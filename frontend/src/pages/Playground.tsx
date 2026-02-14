import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { PlusIcon, UserGroupIcon, GlobeAltIcon, LockClosedIcon } from '@heroicons/react/24/outline';
import PageHeader from '../components/common/PageHeader';
import CreateGameModal from '../components/game/CreateGameModal';
import { apiClient } from '../services/apiClient';
import { socketService } from '../services/socket';
import { useAuth } from '../context/AuthContext';
import type { GameRoomListItem, GameRoom, PowerBracket } from '../types/game';
import { POWER_BRACKET_LABELS, POWER_BRACKET_COLORS } from '../types/game';

const Playground: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [myGames, setMyGames] = useState<GameRoomListItem[]>([]);
  const [publicGames, setPublicGames] = useState<GameRoomListItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  const fetchGames = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await apiClient.get('/games');
      const games = response as GameRoomListItem[];
      
      // Filter games where user is host or player (including in_progress)
      const userGames = games.filter((g) => (g.is_host || g.is_in_game) && (g.status === 'waiting' || g.status === 'in_progress'));
      setMyGames(userGames);
      
      // Public games not hosted by current user and not already in (only waiting)
      const publicOnly = games.filter((g) => g.is_public && g.status === 'waiting' && !g.is_host && !g.is_in_game);
      setPublicGames(publicOnly);
    } catch (error) {
      console.error('Failed to fetch games:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchGames();
  }, [fetchGames]);

  useEffect(() => {
    if (!user?.id) return;

    socketService.connect(user.id);

    socketService.onPlayerJoinRequest(() => {
      fetchGames();
    });

    socketService.onPlayerAccepted(() => {
      fetchGames();
    });

    socketService.onPlayerRejected(() => {
      fetchGames();
    });

    socketService.onPlayerLeft(() => {
      fetchGames();
    });

    return () => {
      socketService.removeAllListeners();
    };
  }, [user?.id, fetchGames]);

  const handleCreateGame = async (game: GameRoom) => {
    setIsCreateModalOpen(false);
    navigate(`/playground/game/${game.id}`);
  };

  const handleJoinGame = async (game: GameRoomListItem) => {
    try {
      await apiClient.post(`/games/${game.id}/join`);
      navigate(`/playground/game/${game.id}`);
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to join game');
    }
  };

  const handleViewGame = (gameId: number) => {
    navigate(`/playground/game/${gameId}`);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'waiting':
        return 'bg-green-500/20 text-green-400 border-green-500/30';
      case 'in_progress':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      case 'completed':
        return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    }
  };

  const GameCard: React.FC<{ game: GameRoomListItem; isHost?: boolean }> = ({ game, isHost = false }) => {
    const isInGame = myGames.some((g) => g.id === game.id);
    const isFull = game.current_players >= game.max_players;
    const canJoin = !isHost && !isInGame && !isFull;

    const handleClick = () => {
      handleViewGame(game.id);
    };

    return (
      <div
        onClick={handleClick}
        className={`bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-xl p-5 transition-all duration-200 cursor-pointer ${
          canJoin || isHost || isInGame
            ? 'hover:border-yellow-500/30 hover:bg-gray-800/70'
            : isFull
            ? 'opacity-60 cursor-not-allowed'
            : ''
        }`}
      >
        <div className="flex items-start justify-between mb-3">
          <h3 className="text-lg font-semibold text-white truncate pr-2">{game.name}</h3>
          <span className={`text-xs px-2 py-1 rounded-full border ${getStatusColor(game.status)}`}>
            {game.status === 'waiting' ? 'Waiting' : game.status === 'in_progress' ? 'In Progress' : 'Completed'}
          </span>
        </div>
        
        <div className="flex items-center gap-4 text-sm text-gray-400 mb-3">
          <div className="flex items-center gap-1">
            <UserGroupIcon className="h-4 w-4" />
            <span>{game.current_players}/{game.max_players}</span>
          </div>
          <div className="flex items-center gap-1">
            {game.is_public ? (
              <GlobeAltIcon className="h-4 w-4 text-green-400" />
            ) : (
              <LockClosedIcon className="h-4 w-4 text-gray-500" />
            )}
          </div>
          <span className={`text-xs px-2 py-0.5 rounded border ${POWER_BRACKET_COLORS[game.power_bracket as PowerBracket]}`}>
            {POWER_BRACKET_LABELS[game.power_bracket as PowerBracket]}
          </span>
        </div>

        <p className="text-xs text-gray-500">Hosted by {game.host_username}</p>
      </div>
    );
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
          <p className="mt-6 text-gray-400 text-lg">Loading games...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950">
      <PageHeader title="Playground" />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Section */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-3xl font-bold text-white mb-2">Playground</h2>
            <p className="text-gray-400">Create or join Commander games</p>
          </div>
          
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="flex items-center space-x-2 bg-gradient-to-r from-yellow-500 to-amber-500 text-gray-900 font-semibold py-3 px-6 rounded-xl hover:from-yellow-400 hover:to-amber-400 transition-all duration-200 shadow-lg shadow-yellow-500/20 hover:shadow-yellow-500/30"
          >
            <PlusIcon className="h-5 w-5" />
            <span>Create Game</span>
          </button>
        </div>

        {/* My Games Section */}
        <section className="mb-12">
          <div className="flex items-center gap-2 mb-4">
            <UserGroupIcon className="h-5 w-5 text-yellow-400" />
            <h3 className="text-xl font-semibold text-white">My Games</h3>
            <span className="text-sm text-gray-500">({myGames.length})</span>
          </div>

          {myGames.length === 0 ? (
            <div className="bg-gray-800/30 border border-gray-700/50 rounded-xl p-8 text-center">
              <p className="text-gray-400">You haven't created or joined any games yet</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {myGames.map((game) => (
                <GameCard key={game.id} game={game} isHost />
              ))}
            </div>
          )}
        </section>

        {/* Public Games Section */}
        <section>
          <div className="flex items-center gap-2 mb-4">
            <GlobeAltIcon className="h-5 w-5 text-green-400" />
            <h3 className="text-xl font-semibold text-white">Public Games</h3>
            <span className="text-sm text-gray-500">({publicGames.length})</span>
          </div>

          {publicGames.length === 0 ? (
            <div className="bg-gray-800/30 border border-gray-700/50 rounded-xl p-8 text-center">
              <p className="text-gray-400">No public games available</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {publicGames.map((game) => (
                <GameCard key={game.id} game={game} />
              ))}
            </div>
          )}
        </section>
      </main>

      <CreateGameModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onGameCreated={handleCreateGame}
      />
    </div>
  );
};

export default Playground;
