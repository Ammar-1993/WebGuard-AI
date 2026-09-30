import { useState, useEffect, useRef } from 'react';
import { getScanStatus, getReportDetail } from '@/utils/api';

/**
 * WebGuard AI — Scan Progress Tracker Component (v2 — Smooth Interpolation)
 *
 * يعرض شريط تقدم سلس وديناميكي أثناء استطلاع حالة الفحص كل 3 ثوانٍ.
 *
 * ─── آلية التحسين ───
 * بدلاً من عرض القيمة الفعلية من الـ Backend مباشرة (التي تقفز بين نقاط كبيرة)،
 * نُفصل بين:
 *   - targetProgress: القيمة الحقيقية القادمة من الـ Backend
 *   - displayProgress: القيمة المعروضة التي تتحرك تدريجياً نحو targetProgress
 *
 * ─── ما لم يتغير ───
 * - آلية الـ polling كل 3 ثوانٍ
 * - onComplete / onError callbacks
 * - stages (Queued, ZAP Scan, AI Analysis, Completed)
 * - CSS classes (glass-card, progress-bar)
 * - Backend API — لا تُمس أبداً
 */

// ─── ثوابت التحريك ───
const INTERPOLATION_MS  = 180;  // كل 180ms تتحرك displayProgress بخطوة
const BASE_STEP         = 0.15; // الحد الأدنى للخطوة
const EASE_FACTOR       = 0.05; // معامل التسارع (easing) — أسرع للبعيد، أبطأ للقريب

const STAGE_HINTS = {
  pending:   'Queuing scan pipeline...',
  scanning:  'ZAP active scan running — this may take a few minutes...',
  analyzing: 'AI analyzer processing vulnerabilities...',
  completed: 'Scan and analysis complete ✅',
  failed:    'Scan failed',
};

export default function ScanProgress({ scanId, targetUrl, onComplete, onError }) {
  const [status,          setStatus]          = useState('pending');
  const [targetProgress,  setTargetProgress]  = useState(0);
  const [displayProgress, setDisplayProgress] = useState(0);
  const [message,         setMessage]         = useState('Request received — waiting to start...');
  const [pulseKey,        setPulseKey]        = useState(0);

  // refs لتجنب stale closure داخل الـ setInterval
  const targetRef = useRef(0);
  const statusRef = useRef('pending');

  // ─── 1. Polling: استطلاع الـ Backend كل 3 ثوانٍ ───
  useEffect(() => {
    if (!scanId) return;

    const pollInterval = setInterval(async () => {
      try {
        const data = await getScanStatus(scanId);

        setStatus(data.status);
        statusRef.current = data.status;
        setMessage(data.message || '');

        const newProgress = data.progress || 0;
        if (newProgress !== targetRef.current) {
          targetRef.current = newProgress;
          setTargetProgress(newProgress);
          setPulseKey(k => k + 1); // نبضة بصرية عند كل تحديث حقيقي
        }

        // ─── اكتمل الفحص ───
        if (data.status === 'completed') {
          clearInterval(pollInterval);
          // نعطي الأنيميشن 1.2 ثانية ليُكمل الوصول إلى 100% قبل عرض النتائج
          setTimeout(async () => {
            try {
              const report = await getReportDetail(data.scan_id);
              onComplete(report);
            } catch {
              onComplete({
                scan_id: scanId,
                target_url: targetUrl,
                security_score: { score: 0, grade: 'N/A', color: '#6B7280', label: 'Unavailable' },
                vulnerabilities: [],
                ai_analysis: [],
                summary: 'Scan completed but report details could not be retrieved.',
              });
            }
          }, 1200);
        }

        // ─── فشل الفحص ───
        if (data.status === 'failed') {
          clearInterval(pollInterval);
          onError();
        }
      } catch (err) {
        console.error('Status polling error:', err);
      }
    }, 3000);

    return () => clearInterval(pollInterval);
  }, [scanId]); // eslint-disable-line react-hooks/exhaustive-deps

  // ─── 2. Interpolation Loop: تحريك displayProgress نحو targetProgress بخطوات صغيرة ───
  useEffect(() => {
    const loop = setInterval(() => {
      setDisplayProgress(prev => {
        const target = targetRef.current;

        // عند الاكتمال: نُكمل مباشرة إلى 100%
        if (statusRef.current === 'completed' && prev >= 99.5) return 100;

        // Safety cap: لا تتجاوز الـ target (إلا عند completed)
        const cap = statusRef.current === 'completed' ? 100 : target;
        if (prev >= cap) return prev;

        // Easing: الخطوة تصغر كلما اقتربنا من الـ cap
        const gap  = cap - prev;
        const step = Math.min(gap, gap * EASE_FACTOR + BASE_STEP);
        return Math.min(prev + step, cap);
      });
    }, INTERPOLATION_MS);

    return () => clearInterval(loop);
  }, []); // يعمل طوال حياة الـ component

  // ─── مراحل الفحص ───
  const stages = [
    { key: 'pending',   label: 'Queued',      icon: '📋' },
    { key: 'scanning',  label: 'ZAP Scan',    icon: '🔍' },
    { key: 'analyzing', label: 'AI Analysis', icon: '🧠' },
    { key: 'completed', label: 'Completed',   icon: '✅' },
  ];

  const currentStageIndex = stages.findIndex(s => s.key === status);
  const displayInt = Math.min(100, Math.floor(displayProgress));

  // لون الشريط حسب المرحلة
  const barStyle =
    status === 'completed'
      ? { background: 'linear-gradient(90deg, #10B981, #34D399, #6EE7B7)' }
      : status === 'analyzing'
      ? { background: 'linear-gradient(90deg, #8B5CF6, #A78BFA, #C4B5FD)' }
      : { background: 'linear-gradient(90deg, #6366F1, #8B5CF6, #A78BFA)' };

  return (
    <div className="glass-card p-8 max-w-2xl mx-auto">
      {/* ─── العنوان ─── */}
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-white mb-2">⏳ Security Scan in Progress</h2>
        <p className="text-gray-400 text-sm">{targetUrl}</p>
      </div>

      {/* ─── مراحل الفحص ─── */}
      <div className="flex items-center justify-between mb-8">
        {stages.map((stage, index) => (
          <div key={stage.key} className="flex items-center">
            <div className={`flex flex-col items-center ${index <= currentStageIndex ? 'opacity-100' : 'opacity-30'}`}>
              <div
                className={`w-12 h-12 rounded-full flex items-center justify-center text-xl mb-2 transition-all duration-500 ${
                  index < currentStageIndex
                    ? 'bg-cyber-green/20 border-2 border-cyber-green'
                    : index === currentStageIndex
                    ? 'bg-primary-500/20 border-2 border-primary-500 animate-pulse'
                    : 'bg-gray-800 border-2 border-gray-700'
                }`}
              >
                {stage.icon}
              </div>
              <span className="text-xs text-gray-400 font-medium">{stage.label}</span>
            </div>
            {index < stages.length - 1 && (
              <div
                className={`w-12 h-0.5 mx-1 mb-6 transition-all duration-500 ${
                  index < currentStageIndex ? 'bg-cyber-green' : 'bg-gray-700'
                }`}
              />
            )}
          </div>
        ))}
      </div>

      {/* ─── شريط التقدم السلس ─── */}
      <div className="mb-4">
        {/* رأس الشريط */}
        <div className="flex justify-between text-sm mb-2">
          <span className="text-gray-400">Progress</span>
          {/* النسبة تومض لحظياً عند كل تحديث من الـ Backend */}
          <span
            key={pulseKey}
            className="text-primary-300 font-bold tabular-nums"
            style={{ animation: pulseKey > 0 ? 'progressPctFlash 0.6s ease-out' : 'none' }}
          >
            {displayInt}%
          </span>
        </div>

        {/* Track */}
        <div className="w-full bg-gray-800 rounded-full h-3 overflow-hidden">
          {/* شريط التقدم — يتحرك عبر displayProgress (interpolated) */}
          <div
            className="progress-bar"
            style={{
              width: `${displayProgress}%`,
              transition: 'none', // الـ interpolation loop يتولى التحريك، لا نريد CSS transition
              ...barStyle,
            }}
          />
        </div>

        {/* نص مساعد صغير أسفل الشريط */}
        <div className="flex justify-end mt-1">
          <span className="text-xs text-gray-600">
            {displayInt < 50 && status === 'scanning'  ? 'ZAP crawling & scanning...' :
             displayInt < 85 && status === 'analyzing' ? 'AI processing results...'  :
             displayInt >= 85 && displayInt < 100       ? 'Finalizing report...'      : ''}
          </span>
        </div>
      </div>

      {/* ─── رسالة الحالة ─── */}
      <div className="text-center mt-2">
        <p className="text-gray-300 text-sm">{message}</p>
      </div>

      {/* ─── تنبيه ─── */}
      <div className="mt-6 bg-amber-500/5 border border-amber-500/20 rounded-xl p-4 text-center">
        <p className="text-amber-400/80 text-xs">
          💡 The security scan may take several minutes depending on the website size. Please do not close this page.
        </p>
      </div>
    </div>
  );
}
