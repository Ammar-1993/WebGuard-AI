import { useState } from 'react';
import { startScan, isAuthenticated } from '@/utils/api';
import { useRouter } from 'next/router';

/**
 * WebGuard AI — Security Scan Form Component
 */
export default function ScanForm({ onScanStart }) {
  const router = useRouter();
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // ─── Check authentication ───
    if (!isAuthenticated()) {
      router.push('/login');
      return;
    }

    // ─── Validate URL ───
    try {
      new URL(url);
    } catch {
      setError('Invalid URL — please enter a full URL starting with http:// or https://');
      return;
    }

    setLoading(true);
    try {
      const data = await startScan(url);
      onScanStart(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start scan — make sure the server is running');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-card p-8 max-w-2xl mx-auto">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-white mb-2">🔍 Start a Security Scan</h2>
        <p className="text-gray-400">Enter the target website URL and the system will analyze it automatically</p>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-3 rounded-xl mb-4 text-sm text-center">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="relative">
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com"
            required
            className="w-full px-5 py-4 pl-12 bg-cyber-dark/50 border border-gray-700 rounded-xl text-white text-lg placeholder-gray-500 focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 transition-all"
          />
          <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500">🌐</span>
        </div>

        <button
          type="submit"
          disabled={loading || !url}
          className="btn-primary w-full text-lg py-4 flex items-center justify-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <>
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Submitting request...
            </>
          ) : (
            <>🚀 Start Security Scan</>
          )}
        </button>
      </form>

      <p className="text-xs text-gray-500 text-center mt-4">
        ⚠️ Only use this tool on websites you have permission to scan
      </p>
    </div>
  );
}
