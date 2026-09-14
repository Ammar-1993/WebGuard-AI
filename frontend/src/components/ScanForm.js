import { useState } from 'react';
import { startScan, isAuthenticated } from '@/utils/api';
import { useRouter } from 'next/router';

/**
 * WebGuard AI — نموذج بدء الفحص الأمني
 */
export default function ScanForm({ onScanStart }) {
  const router = useRouter();
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // ─── التحقق من تسجيل الدخول ───
    if (!isAuthenticated()) {
      router.push('/login');
      return;
    }

    // ─── التحقق من الرابط ───
    try {
      new URL(url);
    } catch {
      setError('الرابط غير صالح — أدخل رابطاً كاملاً يبدأ بـ http:// أو https://');
      return;
    }

    setLoading(true);
    try {
      const data = await startScan(url);
      onScanStart(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'فشل بدء الفحص — تأكد من أن الخادم يعمل');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-card p-8 max-w-2xl mx-auto">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-white mb-2">🔍 ابدأ فحصاً أمنياً</h2>
        <p className="text-gray-400">أدخل رابط الموقع المراد فحصه وسيقوم النظام بتحليله تلقائياً</p>
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
            dir="ltr"
            className="w-full px-5 py-4 bg-cyber-dark/50 border border-gray-700 rounded-xl text-white text-lg placeholder-gray-500 focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 transition-all"
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
              جاري إرسال الطلب...
            </>
          ) : (
            <>🚀 ابدأ الفحص الأمني</>
          )}
        </button>
      </form>

      <p className="text-xs text-gray-500 text-center mt-4">
        ⚠️ استخدم هذه الأداة فقط على المواقع التي تملك صلاحية فحصها
      </p>
    </div>
  );
}
