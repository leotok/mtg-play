import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeftIcon, CheckCircleIcon, GlobeAltIcon, LockClosedIcon } from '@heroicons/react/24/outline';
import PageHeader from '../components/common/PageHeader';
import { apiClient } from '../services/apiClient';
import { socketService } from '../services/socket';
import { useAuth } from '../context/AuthContext';
import type { GameRoom, PowerBracket } from '../types/game';
import { POWER_BRACKET_LABELS, POWER_BRACKET_COLORS } from '../types/game';

const JoinGamePage: React.FC = () => {
  const { inviteCode } = useParams<{ inviteCode: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [game, setGame] = useState<GameRoom | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isJoining, setIsJoining] = useState(false);
  const [error, setError] = useState('');
  const [joinMessage, setJoinMessage] = useState('');
  const [hasJoined, setHasJoined] = useState(false);

  useEffect(() => {
    const fetchGame = async () => {
      if (!inviteCode) return;
      try {
        const response = await apiClient.get(`/games/invite/${inviteCode}`);
        setGame(response);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Game not found');
      } finally {
        setIsLoading(false);
      }
    };
    fetchGame();
  }, [inviteCode]);

  useEffect(() => {
    if (!hasJoined || !user?.id || !game) return;

    socketService.connect(user.id);
    socketService.joinGame(game.id);

    socketService.onPlayerAccepted((data) => {
      if (data.game_id === game.id && data.user_id === user.id) {
        navigate(`/playground/game/${game.id}`);
      }
    });

    return () => {
      socketService.leaveGame(game.id);
    };
  }, [hasJoined, user?.id, game, navigate]);

  const handleJoin = async () => {
    if (!game) return;
    setIsJoining(true);
    setError('');
    try {
      await apiClient.post(`/games/${game.id}/join`);
      setJoinMessage('Join request sent to host!');
      setHasJoined(true);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to join game');
    } finally {
      setIsJoining(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 flex items-center justify-center">
        <div className="text-center">
          <svg className="animate-spin h-16 w-16 text-yellow-500 mx-auto" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <p className="mt-6 text-gray-400 text-lg">Loading game...</p>
        </div>
      </div>
    );
  }

  if (error || !game) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950">
        <PageHeader title="Join Game" />
        <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <button
            onClick={() => navigate('/playground')}
            className="flex items-center text-gray-400 hover:text-gray-200 mb-6 transition-colors"
          >
            <ArrowLeftIcon className="h-5 w-5 mr-2" />
            Back to Playground
          </button>
          <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-8 text-center">
            <p className="text-red-400 text-lg mb-4">{error || 'Game not found'}</p>
            <p className="text-gray-400">This invite link may be invalid or expired.</p>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950">
      <PageHeader title="Join Game" />

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <button
          onClick={() => navigate('/playground')}
          className="flex items-center text-gray-400 hover:text-gray-200 mb-6 transition-colors"
        >
          <ArrowLeftIcon className="h-5 w-5 mr-2" />
          Back to Playground
        </button>

        {joinMessage && !error && (
          <div className="bg-green-500/20 border border-green-500/30 rounded-xl p-6 mb-6 text-center">
            <CheckCircleIcon className="h-12 w-12 text-green-400 mx-auto mb-2" />
            <p className="text-green-400 font-medium text-lg">{joinMessage}</p>
            {joinMessage.includes('request') && (
              <p className="text-gray-400 mt-2">Waiting for the host to accept your request...</p>
            )}
          </div>
        )}

        {/* Game Info */}
        <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-xl p-6 mb-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h1 className="text-2xl font-bold text-white mb-1">{game.name}</h1>
              <p className="text-gray-400">Hosted by {game.host_username}</p>
            </div>
            <span className={`px-3 py-1 rounded-full text-sm font-medium border ${
              game.status === 'waiting' ? 'bg-green-500/20 text-green-400 border-green-500/30' :
              'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
            }`}>
              {game.status === 'waiting' ? 'Waiting for Players' : 'In Progress'}
            </span>
          </div>

          {game.description && (
            <p className="text-gray-300 mb-4">{game.description}</p>
          )}

          <div className="flex items-center gap-4 text-sm">
            <span className={`px-2 py-1 rounded border ${POWER_BRACKET_COLORS[game.power_bracket as PowerBracket]}`}>
              {POWER_BRACKET_LABELS[game.power_bracket as PowerBracket]}
            </span>
            <div className="flex items-center gap-1 text-gray-400">
              {game.is_public ? (
                <GlobeAltIcon className="h-4 w-4 text-green-400" />
              ) : (
                <LockClosedIcon className="h-4 w-4 text-gray-500" />
              )}
              <span>{game.is_public ? 'Public' : 'Private'}</span>
            </div>
          </div>
        </div>

        {/* Join Button */}
        <div className="flex justify-center">
          <button
            onClick={handleJoin}
            disabled={isJoining || game.status !== 'waiting'}
            className="flex items-center gap-2 bg-gradient-to-r from-yellow-500 to-amber-500 text-gray-900 font-semibold py-3 px-8 rounded-xl hover:from-yellow-400 hover:to-amber-400 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isJoining ? 'Joining...' : game.status !== 'waiting' ? 'Game Already Started' : 'Join Game'}
          </button>
        </div>

        {error && (
          <p className="text-center text-red-400 mt-4">{error}</p>
        )}
      </main>
    </div>
  );
};

export default JoinGamePage;
