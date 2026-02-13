import React from 'react';
import { SparklesIcon, ArrowLeftOnRectangleIcon } from '@heroicons/react/24/outline';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

interface PageHeaderProps {
  title?: string;
  subtitle?: string;
}

const PageHeader: React.FC<PageHeaderProps> = ({ title = 'Deck Manager', subtitle }) => {
  const navigate = useNavigate();
  const { logout, user } = useAuth();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <header className="bg-gray-900/80 backdrop-blur-md border-b border-gray-800 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-3">
            <div className="bg-gradient-to-br from-yellow-500 to-amber-600 p-2 rounded-lg shadow-lg shadow-yellow-500/20">
              <SparklesIcon className="h-6 w-6 text-gray-900" />
            </div>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-yellow-400 to-amber-500 bg-clip-text text-transparent">
                MTG Commander
              </h1>
              <p className="text-xs text-gray-500">{title}</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-6">
            <div className="text-right hidden sm:block">
              <p className="text-sm text-gray-300">{user?.username || 'Player'}</p>
              <p className="text-xs text-gray-500">{user?.email}</p>
            </div>
            <button
              onClick={handleLogout}
              className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-gray-800 hover:bg-red-900/30 border border-gray-700 hover:border-red-500/50 transition-all duration-200 group"
            >
              <ArrowLeftOnRectangleIcon className="h-5 w-5 text-gray-400 group-hover:text-red-400 transition-colors" />
              <span className="text-sm text-gray-300 group-hover:text-red-400 transition-colors">Logout</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default PageHeader;
