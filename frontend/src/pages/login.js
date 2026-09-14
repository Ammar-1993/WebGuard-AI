import Head from 'next/head';
import { useState } from 'react';
import { useRouter } from 'next/router';
import { login, register } from '@/utils/api';

/**
 * WebGuard AI — صفحة تسجيل الدخول والتسجيل
 */
export default function Login() {
  const router = useRouter();
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      if (isLogin) {
        await login(formData.email, formData.password);
      } else {
        await register(formData.username, formData.email, formData.password);
      }
      router.push('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'حدث خطأ — حاول مرة أخرى');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Head>
        <title>{isLogin ? 'تسجيل الدخول' : 'إنشاء حساب'} — WebGuard AI</title>
      </Head>

      <div className="min-h-screen gradient-bg flex items-center justify-center px-4">
        <div className="glass-card w-full max-w-md p-8">
          {/* Logo */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-extrabold">
              <span className="bg-gradient-to-r from-primary-400 to-cyber-purple bg-clip-text text-transparent">
                🛡️ WebGuard AI
              </span>
            </h1>
            <p className="text-gray-400 mt-2">
              {isLogin ? 'سجّل دخولك للمتابعة' : 'أنشئ حساباً جديداً'}
            </p>
          </div>

          {/* رسالة خطأ */}
          {error && (
            <div className="bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-3 rounded-xl mb-6 text-sm text-center">
              {error}
            </div>
          )}

          {/* النموذج */}
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* اسم المستخدم (للتسجيل فقط) */}
            {!isLogin && (
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  اسم المستخدم
                </label>
                <input
                  type="text"
                  required
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  className="w-full px-4 py-3 bg-cyber-dark/50 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500 transition-colors"
                  placeholder="أدخل اسم المستخدم"
                />
              </div>
            )}

            {/* البريد الإلكتروني */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                البريد الإلكتروني
              </label>
              <input
                type="email"
                required
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full px-4 py-3 bg-cyber-dark/50 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500 transition-colors"
                placeholder="admin@webguard.ai"
              />
            </div>

            {/* كلمة المرور */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                كلمة المرور
              </label>
              <input
                type="password"
                required
                minLength={6}
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                className="w-full px-4 py-3 bg-cyber-dark/50 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-primary-500 focus:ring-1 focus:ring-primary-500 transition-colors"
                placeholder="••••••••"
              />
            </div>

            {/* زر الإرسال */}
            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {loading ? (
                <>
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  جاري المعالجة...
                </>
              ) : (
                isLogin ? '🔐 تسجيل الدخول' : '✨ إنشاء حساب'
              )}
            </button>
          </form>

          {/* التبديل بين تسجيل الدخول والتسجيل */}
          <div className="text-center mt-6">
            <button
              onClick={() => { setIsLogin(!isLogin); setError(''); }}
              className="text-primary-400 hover:text-primary-300 text-sm transition-colors"
            >
              {isLogin ? 'ليس لديك حساب؟ أنشئ حساباً جديداً' : 'لديك حساب بالفعل؟ سجّل دخولك'}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
