import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeftIcon,
  UserGroupIcon,
  GlobeAltIcon,
  LockClosedIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClipboardIcon,
  PlayIcon,
  StopIcon,
  TrashIcon,
  ArrowRightIcon,
  ChevronDownIcon,
} from '@heroicons/react/24/outline';
import PageHeader from '../components/common/PageHeader';
import { apiClient } from '../services/apiClient';
import { socketService } from '../services/socket';
import { useAuth } from '../context/AuthContext';
import type { GameRoom, PowerBracket, PlayerStatus, DeckInfo } from '../types/game';
import type { Deck } from '../types/deck';
import { POWER_BRACKET_LABELS, POWER_BRACKET_COLORS } from '../types/game';

const GameRoomPage: React.FC = () => {
  const { gameId } = useParams<{ gameId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [game, setGame] = useState<GameRoom | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);
  const [userDecks, setUserDecks] = useState<Deck[]>([]);
  const [selectedDeckId, setSelectedDeckId] = useState<number | null>(null);
  const [isSelectingDeck, setIsSelectingDeck] = useState(false);

  const fetchGame = useCallback(async () => {
    if (!gameId) return;
    try {
      const response = await apiClient.get(`/games/${gameId}`);
      setGame(response);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load game');
    } finally {
      setIsLoading(false);
    }
  }, [gameId]);

  useEffect(() => {
    fetchGame();
  }, [fetchGame]);

  const fetchUserDecks = useCallback(async () => {
    if (!user?.id) return;
    try {
      const response = await apiClient.get('/decks');
      setUserDecks(Array.isArray(response) ? response : []);
    } catch (err) {
      console.error('Failed to fetch decks:', err);
    }
  }, [user?.id]);

  useEffect(() => {
    fetchUserDecks();
  }, [fetchUserDecks]);

  useEffect(() => {
    if (!gameId || !user?.id) return;

    socketService.connect(user.id);
    socketService.joinGame(Number(gameId));

    socketService.onPlayerJoinRequest(() => {
      fetchGame();
    });

    socketService.onPlayerAccepted(() => {
      fetchGame();
    });

    socketService.onPlayerRejected(() => {
      fetchGame();
    });

    socketService.onPlayerLeft(() => {
      fetchGame();
    });

    socketService.onGameStarted(() => {
      fetchGame();
    });

    socketService.onGameStopped(() => {
      fetchGame();
    });

    socketService.onDeckSelected(() => {
      fetchGame();
    });

    return () => {
      socketService.leaveGame(Number(gameId));
    };
  }, [gameId, user?.id, fetchGame]);

  const handleAccept = async (playerId: number) => {
    try {
      await apiClient.post(`/games/${gameId}/accept/${playerId}`);
      socketService.playerAccepted(Number(gameId), playerId);
      fetchGame();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to accept player');
    }
  };

  const handleReject = async (playerId: number) => {
    try {
      await apiClient.post(`/games/${gameId}/reject/${playerId}`);
      socketService.playerRejected(Number(gameId), playerId);
      fetchGame();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to reject player');
    }
  };

  const handleStartGame = async () => {
    // Check if all players have selected decks
    const allHaveDecks = acceptedPlayers.every(p => p.deck_id);
    if (!allHaveDecks) {
      alert('All players must select their decks before starting the game');
      return;
    }
    try {
      await apiClient.post(`/games/${gameId}/start`);
      socketService.gameStarted(Number(gameId));
      fetchGame();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to start game');
    }
  };

  const handleStopGame = async () => {
    if (!window.confirm('Are you sure you want to stop the game? Players will be able to change their decks.')) return;
    try {
      await apiClient.post(`/games/${gameId}/stop`);
      fetchGame();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to stop game');
    }
  };

  const handleLeaveGame = async () => {
    if (!window.confirm('Are you sure you want to leave this game?')) return;
    try {
      await apiClient.delete(`/games/${gameId}/leave`);
      navigate('/playground');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to leave game');
    }
  };

  const handleDeleteGame = async () => {
    if (!window.confirm('Are you sure you want to delete this game? This cannot be undone.')) return;
    try {
      await apiClient.delete(`/games/${gameId}`);
      navigate('/playground');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete game');
    }
  };

  const handleCopyInvite = () => {
    if (game) {
      const inviteLink = `${window.location.origin}/playground/join/${game.invite_code}`;
      navigator.clipboard.writeText(inviteLink);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleSelectDeck = async (deckId: number) => {
    try {
      await apiClient.post(`/games/${gameId}/select-deck`, { deck_id: deckId });
      setSelectedDeckId(deckId);
      setIsSelectingDeck(false);
      fetchGame();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to select deck');
    }
  };

  const isHost = game?.players.some((p) => p.user_id === user?.id && p.is_host);
  const currentUser = game?.players.find((p) => p.user_id === user?.id);
  const isInGame = !!currentUser;
  const isAccepted = currentUser?.status === 'accepted';
  const isPending = currentUser?.status === 'pending';
  const acceptedPlayers = game?.players.filter((p) => p.status === 'accepted') || [];
  const pendingPlayers = game?.players.filter((p) => p.status === 'pending') || [];

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
      <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 text-lg mb-4">{error || 'Game not found'}</p>
          <button
            onClick={() => navigate('/playground')}
            className="text-yellow-400 hover:text-yellow-300"
          >
            Back to Playground
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950">
      <PageHeader title={game.name} />

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Back Button */}
        <button
          onClick={() => navigate('/playground')}
          className="flex items-center text-gray-400 hover:text-gray-200 mb-6 transition-colors"
        >
          <ArrowLeftIcon className="h-5 w-5 mr-2" />
          Back to Playground
        </button>

        {/* Game Header */}
        <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-xl p-6 mb-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h1 className="text-2xl font-bold text-white mb-1">{game.name}</h1>
              <p className="text-gray-400">Hosted by {game.host_username}</p>
            </div>
            <span className={`px-3 py-1 rounded-full text-sm font-medium border ${
              game.status === 'waiting' ? 'bg-green-500/20 text-green-400 border-green-500/30' :
              game.status === 'in_progress' ? 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30' :
              'bg-gray-500/20 text-gray-400 border-gray-500/30'
            }`}>
              {game.status === 'waiting' ? 'Waiting' : game.status === 'in_progress' ? 'In Progress' : 'Completed'}
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
              <UserGroupIcon className="h-4 w-4" />
              <span>{acceptedPlayers.length}/{game.max_players}</span>
            </div>
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

        {/* Pending Status (for non-host players with pending request) */}
        {!isHost && isPending && game.status === 'waiting' && (
          <div className="bg-yellow-500/20 border border-yellow-500/30 rounded-xl p-6 mb-6 text-center">
            <p className="text-yellow-400 font-medium">Waiting for host to accept your join request...</p>
          </div>
        )}

        {/* Invite Friends Button (for host) */}
        {isHost && game.status === 'waiting' && (
          <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-4 mb-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Invite Friends</p>
                <p className="text-gray-500 text-xs">Share this link to invite players</p>
              </div>
              <button
                onClick={handleCopyInvite}
                className="flex items-center gap-2 px-4 py-2 bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-400 border border-yellow-500/30 rounded-lg transition-colors"
              >
                <ClipboardIcon className="h-4 w-4" />
                {copied ? 'Copied!' : 'Copy Link'}
              </button>
            </div>
            <input
              type="text"
              readOnly
              value={`${window.location.origin}/playground/join/${game.invite_code}`}
              className="mt-3 w-full bg-gray-700 text-gray-300 border border-gray-600 rounded-lg px-3 py-2 text-sm"
            />
          </div>
        )}

        {/* Deck Selection (for accepted players) */}
        {isAccepted && game.status === 'waiting' && (
          <div className="bg-gray-800/50 border border-gray-700/50 rounded-xl p-4 mb-6">
            <div className="flex items-center justify-between mb-3">
              <p className="text-gray-400 text-sm">Your Commander Deck</p>
            </div>
            
            {!isSelectingDeck ? (
              <button
                onClick={() => setIsSelectingDeck(true)}
                className="w-full flex items-center justify-between px-4 py-3 bg-gray-700 hover:bg-gray-600 border border-gray-600 rounded-lg transition-colors"
              >
                <span className="text-gray-300">
                  {currentUser?.deck ? (
                    <div className="flex items-center gap-2">
                      {currentUser.deck.commander_image_uris?.art_crop && (
                        <img 
                          src={currentUser.deck.commander_image_uris.art_crop} 
                          alt={currentUser.deck.commander_name || currentUser.deck.name}
                          className="w-6 h-6 rounded object-cover"
                        />
                      )}
                      <span>{currentUser.deck.name}</span>
                      <span className="text-gray-400 text-xs">({currentUser.deck.commander_name})</span>
                    </div>
                  ) : (
                    'Choose a deck...'
                  )}
                </span>
                <div className="flex items-center gap-2">
                  {currentUser?.deck && (
                    <span className="text-xs text-gray-400">Change</span>
                  )}
                  <ChevronDownIcon className="h-5 w-5 text-gray-400" />
                </div>
              </button>
            ) : (
              <div className="space-y-2">
                {userDecks.length === 0 ? (
                  <p className="text-gray-400 text-sm text-center py-2">No decks found. Create a deck first.</p>
                ) : (
                  userDecks.map((deck) => (
                    <button
                      key={deck.id}
                      onClick={() => handleSelectDeck(deck.id)}
                      className="w-full flex items-center gap-3 px-4 py-3 bg-gray-700 hover:bg-gray-600 border border-gray-600 rounded-lg transition-colors"
                    >
                      {deck.commander_image_uris?.art_crop && (
                        <img 
                          src={deck.commander_image_uris.art_crop} 
                          alt={deck.commander_name}
                          className="w-10 h-10 rounded object-cover"
                        />
                      )}
                      <div className="text-left">
                        <p className="text-gray-100 font-medium">{deck.name}</p>
                        {deck.commander_name && (
                          <p className="text-gray-400 text-sm">Commander: {deck.commander_name}</p>
                        )}
                      </div>
                    </button>
                  ))
                )}
                <button
                  onClick={() => setIsSelectingDeck(false)}
                  className="w-full text-center text-gray-400 text-sm py-2 hover:text-gray-300"
                >
                  Cancel
                </button>
              </div>
            )}
          </div>
        )}

        {/* Players List */}
        <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-xl p-6 mb-6">
          <h2 className="text-lg font-semibold text-white mb-4">Players</h2>
          
          {acceptedPlayers.length === 0 ? (
            <p className="text-gray-400 text-center py-4">No players yet</p>
          ) : (
            <div className="space-y-3">
              {acceptedPlayers.map((player) => (
                <div
                  key={player.id}
                  className="flex items-center justify-between p-3 bg-gray-700/50 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-yellow-500 to-amber-600 flex items-center justify-center text-gray-900 font-bold">
                      {player.username.charAt(0).toUpperCase()}
                    </div>
                    <div className="flex items-center gap-2">
                      <p className="text-white font-medium">
                        {player.username}
                        {player.is_host && (
                          <span className="ml-2 text-xs px-2 py-0.5 bg-yellow-500/20 text-yellow-400 rounded">
                            Host
                          </span>
                        )}
                      </p>
                      {player.deck && (
                        <div className="flex items-center gap-2">
                          <div className="flex items-center gap-1 text-xs">
                            <span className="text-gray-300">{player.deck.name}</span>
                            {player.deck.commander_name && player.deck.commander_name !== player.deck.name && (
                              <span className="text-gray-400">({player.deck.commander_name})</span>
                            )}
                          </div>
                          {player.deck.commander_image_uris?.art_crop && (
                            <img 
                              src={player.deck.commander_image_uris.art_crop} 
                              alt={player.deck.commander_name}
                              className="w-10 h-10 rounded object-cover"
                            />
                          )}
                        </div>
                      )}
                      {!player.deck && (
                        <span className="text-gray-500 text-xs">
                          {player.user_id === user?.id ? 'Select a deck' : 'No deck selected'}
                        </span>
                      )}
                    </div>
                  </div>
                  {player.deck ? (
                    <CheckCircleIcon className="h-5 w-5 text-green-400" />
                  ) : (
                    <div className="h-5 w-5 rounded-full border-2 border-gray-500" />
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Empty Slots */}
          {acceptedPlayers.length < game.max_players && game.status === 'waiting' && (
            <div className="mt-4 pt-4 border-t border-gray-700">
              <p className="text-gray-500 text-sm">
                Waiting for {game.max_players - acceptedPlayers.length} more player{game.max_players - acceptedPlayers.length > 1 ? 's' : ''}...
              </p>
            </div>
          )}
        </div>

        {/* Pending Requests (for host) */}
        {isHost && pendingPlayers.length > 0 && (
          <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700/50 rounded-xl p-6 mb-6">
            <h2 className="text-lg font-semibold text-white mb-4">Join Requests</h2>
            <div className="space-y-3">
              {pendingPlayers.map((player) => (
                <div
                  key={player.id}
                  className="flex items-center justify-between p-3 bg-gray-700/50 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold">
                      {player.username.charAt(0).toUpperCase()}
                    </div>
                    <p className="text-white font-medium">{player.username}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleAccept(player.id)}
                      className="p-2 bg-green-500/20 hover:bg-green-500/30 text-green-400 rounded-lg transition-colors"
                    >
                      <CheckCircleIcon className="h-5 w-5" />
                    </button>
                    <button
                      onClick={() => handleReject(player.id)}
                      className="p-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg transition-colors"
                    >
                      <XCircleIcon className="h-5 w-5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-between">
          {isHost ? (
            <button
              onClick={handleDeleteGame}
              className="flex items-center gap-2 px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg transition-colors"
            >
              <TrashIcon className="h-5 w-5" />
              Delete Game
            </button>
          ) : isInGame ? (
            <button
              onClick={handleLeaveGame}
              className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-lg transition-colors"
            >
              Leave Game
            </button>
          ) : (
            <button
              onClick={async () => {
                try {
                  await apiClient.post(`/games/${gameId}/join`);
                  fetchGame();
                } catch (err: any) {
                  alert(err.response?.data?.detail || 'Failed to join game');
                }
              }}
              disabled={game.status !== 'waiting'}
              className="flex items-center gap-2 px-4 py-2 bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-400 border border-yellow-500/30 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Join Game
            </button>
          )}

          {isHost && game.status === 'waiting' && acceptedPlayers.length >= 2 && (
            <button
              onClick={handleStartGame}
              disabled={!acceptedPlayers.every(p => p.deck_id)}
              className="flex items-center gap-2 bg-gradient-to-r from-yellow-500 to-amber-500 text-gray-900 font-semibold py-2 px-6 rounded-xl hover:from-yellow-400 hover:to-amber-400 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              title={!acceptedPlayers.every(p => p.deck_id) ? 'All players must select their decks first' : 'Start the game'}
            >
              <PlayIcon className="h-5 w-5" />
              Start Game
            </button>
          )}

          {isHost && game.status === 'in_progress' && (
            <button
              onClick={handleStopGame}
              className="flex items-center gap-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 border border-red-500/30 font-semibold py-2 px-6 rounded-xl transition-all duration-200"
            >
              <StopIcon className="h-5 w-5" />
              Stop Game
            </button>
          )}

          {isAccepted && game.status === 'in_progress' && (
            <button
              onClick={() => navigate(`/playground/game/${gameId}/play`)}
              className="flex items-center gap-2 bg-gradient-to-r from-green-500 to-emerald-500 text-white font-semibold py-2 px-6 rounded-xl hover:from-green-400 hover:to-emerald-400 transition-all duration-200"
            >
              <PlayIcon className="h-5 w-5" />
              Enter Game
            </button>
          )}
        </div>
      </main>
    </div>
  );
};

export default GameRoomPage;
