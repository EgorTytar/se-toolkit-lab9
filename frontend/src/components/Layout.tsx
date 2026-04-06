import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function Layout() {
  const { user, isAuthenticated, logout } = useAuth();
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  return (
    <div className="min-h-screen flex flex-col bg-gray-900 text-gray-100">
      {/* Header */}
      <header className="bg-red-800 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link to="/" className="flex items-center space-x-2">
              <span className="text-2xl">🏎️</span>
              <h1 className="text-xl font-bold">F1 Assistant</h1>
            </Link>
            
            <nav className="hidden md:flex space-x-4">
              <Link
                to="/"
                className={`px-3 py-2 rounded-md text-sm font-medium transition ${
                  isActive('/') ? 'bg-red-900' : 'hover:bg-red-700'
                }`}
              >
                Dashboard
              </Link>
              {isAuthenticated && (
                <Link
                  to="/account"
                  className={`px-3 py-2 rounded-md text-sm font-medium transition ${
                    isActive('/account') ? 'bg-red-900' : 'hover:bg-red-700'
                  }`}
                >
                  Account
                </Link>
              )}
            </nav>

            <div className="flex items-center space-x-4">
              {isAuthenticated ? (
                <div className="flex items-center space-x-3">
                  <span className="text-sm">{user?.display_name}</span>
                  <button
                    onClick={logout}
                    className="px-3 py-1 text-sm bg-gray-100 text-red-800 rounded hover:bg-white transition"
                  >
                    Logout
                  </button>
                </div>
              ) : (
                <div className="flex items-center space-x-2">
                  <Link
                    to="/login"
                    className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-white hover:text-red-800 transition"
                  >
                    Login
                  </Link>
                  <Link
                    to="/register"
                    className="px-3 py-1 text-sm bg-white text-red-800 rounded hover:bg-gray-100 transition"
                  >
                    Register
                  </Link>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content - flex-1 pushes footer down */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>

      {/* Footer - always at bottom */}
      <footer className="bg-gray-800 text-gray-400 py-6 mt-auto">
        <div className="max-w-7xl mx-auto px-4 text-center text-sm">
          F1 Assistant • Data from{' '}
          <a href="https://api.jolpi.ca" className="text-red-400 hover:underline" target="_blank">
            Jolpica-F1
          </a>{' '}
          • Powered by Qwen AI
        </div>
      </footer>
    </div>
  );
}
