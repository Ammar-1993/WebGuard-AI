import { useState, useEffect } from 'react';
import { getScanStatus, getReportDetail } from '@/utils/api';

/**
 * WebGuard AI — مكوّن تتبع تقدم الفحص
 * يعرض شريط التقدم والرسائل أثناء الفحص ويستعلم عن الحالة كل 3 ثوانٍ.
 */
export default function ScanProgress({ scanId, targetUrl, onComplete, onError }) {
  const [status, setStatus] = useState('pending');
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState('تم استلام الطلب — في انتظار البدء...');

  useEffect(() => {
    if (!scanId) return;

    const interval = setInterval(async () => {
      try {
        const data = await getScanStatus(scanId);
        setStatus(data.status);
        setProgress(data.progress || 0);
        setMessage(data.message || '');

        // ─── اكتمل الفحص ───
        if (data.status === 'completed') {
          clearInterval(interval);
          // جلب التقرير الكامل
          try {
            const report = await getReportDetail(data.scan_id);
            onComplete(report);
          } catch {
            // إذا لم يُعثر على التقرير بـ scan_id، محاولة جلب جميع التقارير
            onComplete({
              scan_id: scanId,
              target_url: targetUrl,
              security_score: { score: 0, grade: 'N/A', color: '#6B7280', label: 'غير متاح' },
              vulnerabilities: [],
              ai_analysis: [],
              summary: 'اكتمل الفحص ولكن لم يتم العثور على تفاصيل التقرير.',
            });
          }
        }

        // ─── فشل الفحص ───
        if (data.status === 'failed') {
          clearInterval(interval);
          onError();
        }
      } catch (err) {
        console.error('خطأ في استعلام الحالة:', err);
      }
    }, 3000); // كل 3 ثوانٍ

    return () => clearInterval(interval);
  }, [scanId]);

  const stages = [
    { key: 'pending', label: 'استلام الطلب', icon: '📋' },
    { key: 'scanning', label: 'فحص ZAP', icon: '🔍' },
    { key: 'analyzing', label: 'تحليل AI', icon: '🧠' },
    { key: 'completed', label: 'مكتمل', icon: '✅' },
  ];

  const currentStageIndex = stages.findIndex(s => s.key === status);

  return (
    <div className="glass-card p-8 max-w-2xl mx-auto">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-white mb-2">⏳ جاري الفحص الأمني</h2>
        <p className="text-gray-400 text-sm" dir="ltr">{targetUrl}</p>
      </div>

      {/* مراحل الفحص */}
      <div className="flex items-center justify-between mb-8">
        {stages.map((stage, index) => (
          <div key={stage.key} className="flex items-center">
            <div className={`flex flex-col items-center ${index <= currentStageIndex ? 'opacity-100' : 'opacity-30'}`}>
              <div className={`w-12 h-12 rounded-full flex items-center justify-center text-xl mb-2 transition-all duration-500 ${
                index < currentStageIndex
                  ? 'bg-cyber-green/20 border-2 border-cyber-green'
                  : index === currentStageIndex
                  ? 'bg-primary-500/20 border-2 border-primary-500 animate-pulse'
                  : 'bg-gray-800 border-2 border-gray-700'
              }`}>
                {stage.icon}
              </div>
              <span className="text-xs text-gray-400 font-medium">{stage.label}</span>
            </div>
            {index < stages.length - 1 && (
              <div className={`w-12 h-0.5 mx-1 mb-6 transition-all duration-500 ${
                index < currentStageIndex ? 'bg-cyber-green' : 'bg-gray-700'
              }`} />
            )}
          </div>
        ))}
      </div>

      {/* شريط التقدم */}
      <div className="mb-4">
        <div className="flex justify-between text-sm mb-2">
          <span className="text-gray-400">التقدم</span>
          <span className="text-primary-300 font-bold">{progress}%</span>
        </div>
        <div className="w-full bg-gray-800 rounded-full h-3 overflow-hidden">
          <div
            className="progress-bar"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* الرسالة */}
      <div className="text-center">
        <p className="text-gray-300 text-sm">{message}</p>
      </div>

      {/* تحذير */}
      <div className="mt-6 bg-amber-500/5 border border-amber-500/20 rounded-xl p-4 text-center">
        <p className="text-amber-400/80 text-xs">
          💡 الفحص الأمني قد يستغرق عدة دقائق حسب حجم الموقع. لا تغلق هذه الصفحة.
        </p>
      </div>
    </div>
  );
}
