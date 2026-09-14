import SecurityGauge from './SecurityGauge';
import VulnerabilityTable from './VulnerabilityTable';
import RiskChart from './RiskChart';

/**
 * WebGuard AI — لوحة التحكم الرئيسية (Dashboard)
 * تعرض نتائج الفحص الأمني بشكل مرئي وتفاعلي.
 */
export default function Dashboard({ report, onNewScan }) {
  const score = report?.security_score || { score: 0, grade: 'F', color: '#DC2626', label: 'غير متاح' };
  const vulnerabilities = report?.vulnerabilities || [];
  const aiAnalysis = report?.ai_analysis || [];
  const summary = report?.summary || '';
  const falsePositives = report?.false_positives_count || 0;
  const totalVulns = report?.total_vulnerabilities || vulnerabilities.length;

  // ─── حساب عدد الثغرات حسب المستوى ───
  const riskCounts = { High: 0, Medium: 0, Low: 0, Informational: 0 };
  vulnerabilities.forEach((v) => {
    const risk = v.risk || 'Informational';
    if (riskCounts[risk] !== undefined) riskCounts[risk]++;
  });

  return (
    <div className="space-y-8">
      {/* ─── رأس الصفحة ─── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold text-white">📊 نتائج الفحص الأمني</h2>
          <p className="text-gray-400 mt-1" dir="ltr">{report?.target_url}</p>
        </div>
        <button onClick={onNewScan} className="btn-secondary text-sm">
          🔄 فحص جديد
        </button>
      </div>

      {/* ─── الصف الأول: مؤشر الأمان + ملخص ─── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* مؤشر الأمان */}
        <div className="glass-card p-6 flex flex-col items-center justify-center">
          <SecurityGauge score={score.score} grade={score.grade} color={score.color} label={score.label} />
        </div>

        {/* إحصائيات سريعة */}
        <div className="glass-card p-6 space-y-4">
          <h3 className="text-lg font-bold text-white mb-4">📈 إحصائيات الفحص</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-400">إجمالي التنبيهات</span>
              <span className="text-white font-bold text-xl">{totalVulns}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">إنذارات خاطئة مُستبعدة</span>
              <span className="text-cyber-green font-bold text-xl">{falsePositives}</span>
            </div>
            <hr className="border-gray-700/50" />
            <div className="flex justify-between items-center">
              <span className="text-red-400 font-medium">🔴 عالية الخطورة</span>
              <span className="text-red-400 font-bold">{riskCounts.High}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-amber-400 font-medium">🟠 متوسطة</span>
              <span className="text-amber-400 font-bold">{riskCounts.Medium}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-blue-400 font-medium">🔵 منخفضة</span>
              <span className="text-blue-400 font-bold">{riskCounts.Low}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400 font-medium">⚪ معلوماتية</span>
              <span className="text-gray-400 font-bold">{riskCounts.Informational}</span>
            </div>
          </div>
        </div>

        {/* الرسم البياني */}
        <div className="glass-card p-6">
          <h3 className="text-lg font-bold text-white mb-4">📊 توزيع الثغرات</h3>
          <RiskChart counts={riskCounts} />
        </div>
      </div>

      {/* ─── ملخص الذكاء الاصطناعي ─── */}
      {summary && (
        <div className="glass-card p-6">
          <h3 className="text-lg font-bold text-white mb-3">🧠 ملخص تحليل الذكاء الاصطناعي</h3>
          <p className="text-gray-300 leading-relaxed">{summary}</p>
        </div>
      )}

      {/* ─── جدول الثغرات التفصيلي ─── */}
      <VulnerabilityTable vulnerabilities={vulnerabilities} aiAnalysis={aiAnalysis} />
    </div>
  );
}
