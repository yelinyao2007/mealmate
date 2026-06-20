import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './context/AuthContext';
import { LanguageProvider } from './context/LanguageContext';
import Navbar from './components/Navbar';
import Landing from './pages/Landing';
import Login from './pages/Login';
import Register from './pages/Register';
import Profile from './pages/Profile';
import AIChef from './pages/AIChef';
import RecipeFeed from './pages/RecipeFeed';
import RecipeDetail from './pages/RecipeDetail';
import CreateRecipe from './pages/CreateRecipe';
import Bookmarks from './pages/Bookmarks';
import Notifications from './pages/Notifications';
import WorkflowDashboard from './pages/WorkflowDashboard';
import ImageRecognitionPage from './pages/ImageRecognitionPage';
import { Loader2 } from 'lucide-react';

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 size={32} className="animate-spin text-terracotta" />
      </div>
    );
  }
  return user ? children : <Navigate to="/login" />;
}

export default function App() {
  return (
    <LanguageProvider>
      <div className="min-h-screen bg-cream">
        <Navbar />
        <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/feed" element={<RecipeFeed />} />
        <Route
          path="/recipes/new"
          element={<ProtectedRoute><CreateRecipe /></ProtectedRoute>}
        />
        <Route path="/recipes/:id" element={<RecipeDetail />} />
        <Route
          path="/profile"
          element={<ProtectedRoute><Profile /></ProtectedRoute>}
        />
        <Route
          path="/ai"
          element={<ProtectedRoute><AIChef /></ProtectedRoute>}
        />
        <Route
          path="/image"
          element={<ProtectedRoute><ImageRecognitionPage /></ProtectedRoute>}
        />
        <Route
          path="/workflow"
          element={<ProtectedRoute><WorkflowDashboard /></ProtectedRoute>}
        />
        <Route
          path="/bookmarks"
          element={<ProtectedRoute><Bookmarks /></ProtectedRoute>}
        />
        <Route
          path="/notifications"
          element={<ProtectedRoute><Notifications /></ProtectedRoute>}
        />
      </Routes>
    </div>
    </LanguageProvider>
  );
}
