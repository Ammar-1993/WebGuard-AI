import Head from 'next/head';
import { useState } from 'react';
import Navbar from '@/components/Navbar';
import ScanForm from '@/components/ScanForm';
import ScanProgress from '@/components/ScanProgress';
import Dashboard from '@/components/Dashboard';

/**
 * WebGuard AI — الصفحة الرئيسية
 * تعرض نموذج الفحص ونتائج الفحص (Dashboard) بعد الاكتمال.
 */
export default function Home() {
  const [scanState, setScanState] = useState('idle'); // idle | scanning | completed
  const [scanData, setScanData] = useState(null);
  const [reportData, setReportData] = useState(null);

  const handleScanStart = (data) => {
    setScanState('scanning');
    setScanData(data);
  };

  const handleScanComplete = (report) => {
    setScanState('completed');
    setReportData(report);
  };

  const handleNewScan = () => {
    setScanState('idle');
    setScanData(null);
    setReportData(null);
  };

  return (
    <>
      <Head>
        <title>WebGuard AI — فاحص الثغرات الأمنية الذكي</title>
        <meta name="description" content="منصة ذكية لفحص الثغرات الأمنية باستخدام OWASP ZAP والذكاء الاصطناعي" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="min-h-screen gradient-bg">
        <Navbar />

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* ─── حالة الخمول: نموذج الفحص ─── */}
          {scanState === 'idle' && (
            <div className="space-y-12">
              {/* Hero Section */}
              <div className="text-center py-16">
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary-500/10 border border-primary-500/20 mb-6">
                  <span className="w-2 h-2 rounded-full bg-cyber-green animate-pulse"></span>
                  <span className="text-sm text-primary-300 font-medium">نظام جاهز للفحص</span>
                </div>
                <h1 className="text-5xl md:text-6xl font-extrabold mb-6">
                  <span className="bg-gradient-to-r from-primary-400 via-cyber-purple to-cyber-blue bg-clip-text text-transparent">
                    WebGuard AI
                  </span>
                </h1>
                <p className="text-xl text-gray-400 max-w-3xl mx-auto leading-relaxed">
                  منصة ذكية لفحص الثغرات الأمنية — تجمع بين قوة محرك
                  <span className="text-cyber-green font-semibold"> OWASP ZAP </span>
                  لاكتشاف الثغرات والذكاء الاصطناعي
                  <span className="text-cyber-purple font-semibold"> (AI) </span>
                  لتحليلها وتبسيطها
                </p>
              </div>

              {/* نموذج الفحص */}
              <ScanForm onScanStart={handleScanStart} />

              {/* المميزات */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
                <div className="glass-card p-6 text-center">
                  <div className="text-4xl mb-4">🔍</div>
                  <h3 className="text-lg font-bold text-white mb-2">فحص شامل</h3>
                  <p className="text-gray-400 text-sm">فحص أمني متقدم يعتمد على معايير OWASP Top 10 العالمية</p>
                </div>
                <div className="glass-card p-6 text-center">
                  <div className="text-4xl mb-4">🧠</div>
                  <h3 className="text-lg font-bold text-white mb-2">تحليل ذكي</h3>
                  <p className="text-gray-400 text-sm">ذكاء اصطناعي يحلل النتائج ويستبعد الإنذارات الخاطئة</p>
                </div>
                <div className="glass-card p-6 text-center">
                  <div className="text-4xl mb-4">💊</div>
                  <h3 className="text-lg font-bold text-white mb-2">أكواد إصلاح</h3>
                  <p className="text-gray-400 text-sm">توصيات وأكواد إصلاح جاهزة لتطبيقها فوراً</p>
                </div>
              </div>
            </div>
          )}

          {/* ─── حالة الفحص: شريط التقدم ─── */}
          {scanState === 'scanning' && scanData && (
            <ScanProgress
              scanId={scanData.scan_id}
              targetUrl={scanData.target_url}
              onComplete={handleScanComplete}
              onError={() => setScanState('idle')}
            />
          )}

          {/* ─── حالة الاكتمال: لوحة التحكم ─── */}
          {scanState === 'completed' && reportData && (
            <Dashboard
              report={reportData}
              onNewScan={handleNewScan}
            />
          )}
        </main>

        {/* Footer */}
        <footer className="text-center py-8 text-gray-500 text-sm border-t border-gray-800/50">
          <p>© 2024 WebGuard AI — مشروع تخرج جامعي</p>
        </footer>
      </div>
    </>
  );
}
