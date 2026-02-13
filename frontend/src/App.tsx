import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/auth/ProtectedRoute';
import LoginForm from './components/auth/LoginForm';
import RegisterForm from './components/auth/RegisterForm';
import DeckDashboard from './pages/DeckDashboard';
import DeckEditor from './pages/DeckEditor';

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen bg-gray-900">
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<LoginForm />} />
            <Route path="/register" element={<RegisterForm />} />
            
            {/* Redirect root to login */}
            <Route path="/" element={<Navigate to="/login" replace />} />
            
            {/* Protected routes */}
            <Route
              path="/decks"
              element={
                <ProtectedRoute>
                  <DeckDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/decks/:deckId"
              element={
                <ProtectedRoute>
                  <DeckEditor />
                </ProtectedRoute>
              }
            />
            
            {/* Catch all route - redirect to login */}
            <Route path="*" element={<Navigate to="/login" replace />} />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
