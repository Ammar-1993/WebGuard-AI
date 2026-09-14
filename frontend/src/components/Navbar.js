import Link from 'next/link';
import { useState, useEffect } from 'react';
import { getCurrentUser, logout, isAuthenticated } from '@/utils/api';

/**
 * WebGuard AI — Top Navigation Bar (Navbar)
 */
export default function Navbar() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    if (isAuthenticated()) {
      setUser(getCurrentUser());
    }
  }, []);

  return (
    <nav className="border-b border-gray-800/50 backdrop-blur-md bg-cyber-darker/50 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3 group">
            <span className="text-2xl">🛡️</span>
            <span className="text-xl font-bold bg-gradient-to-r from-primary-400 to-cyber-purple bg-clip-text text-transparent group-hover:from-primary-300 group-hover:to-cyber-blue transition-all">
              WebGuard AI
            </span>
          </Link>

          {/* Menu */}
          <div className="flex items-center gap-4">
            {user ? (
              <>
                <span className="text-gray-400 text-sm hidden sm:block">
                  Welcome, <span className="text-primary-300 font-medium">{user.username}</span>
                </span>
                <button
                  onClick={logout}
                  className="text-gray-400 hover:text-red-400 text-sm font-medium transition-colors px-3 py-2 rounded-lg hover:bg-red-500/10"
                >
                  Sign Out
                </button>
              </>
            ) : (
              <Link
                href="/login"
                className="btn-secondary text-sm py-2 px-4"
              >
                🔐 Sign In
              </Link>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
