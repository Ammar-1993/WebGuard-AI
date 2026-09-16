import SecurityGauge from './SecurityGauge';
import VulnerabilityTable from './VulnerabilityTable';
import RiskChart from './RiskChart';

/**
 * WebGuard AI — Main Dashboard Component
 * Displays scan results visually and interactively.
 */
export default function Dashboard({ report, onNewScan }) {
  const score = report?.security_score || { score: 0, grade: 'F', color: '#DC2626', label: 'Unavailable' };
  const vulnerabilities = report?.vulnerabilities || [];
  const aiAnalysis = report?.ai_analysis || [];
  const summary = report?.summary || '';
  const falsePositives = report?.false_positives_count || 0;
  const totalVulns = report?.total_vulnerabilities || vulnerabilities.length;

  // ─── Count vulnerabilities by risk level ───
  const riskCounts = { High: 0, Medium: 0, Low: 0, Informational: 0 };
  vulnerabilities.forEach((v) => {
    const risk = v.risk || 'Informational';
    if (riskCounts[risk] !== undefined) riskCounts[risk]++;
  });

  return (
    <div className="space-y-8">
      {/* ─── Page Header ─── */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold text-white">📊 Security Scan Results</h2>
          <p className="text-gray-400 mt-1">{report?.target_url}</p>
        </div>
        <div className="flex gap-2 print:hidden">
          <button onClick={() => window.print()} className="btn-secondary text-sm">
            📄 Export PDF
          </button>
          <button onClick={() => {
            const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(report, null, 2));
            const dlAnchorElem = document.createElement('a');
            dlAnchorElem.setAttribute("href", dataStr);
            dlAnchorElem.setAttribute("download", `webguard-report-${report?.scan_id || report?.id || 'export'}.json`);
            dlAnchorElem.click();
          }} className="btn-secondary text-sm">
            💾 Export JSON
          </button>
          <button onClick={onNewScan} className="btn-primary text-sm">
            🔄 New Scan
          </button>
        </div>
      </div>

      {/* ─── Row 1: Security Gauge + Summary ─── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Security Gauge */}
        <div className="glass-card p-6 flex flex-col items-center justify-center">
          <SecurityGauge score={score.score} grade={score.grade} color={score.color} label={score.label} />
        </div>

        {/* Quick Stats */}
        <div className="glass-card p-6 space-y-4">
          <h3 className="text-lg font-bold text-white mb-4">📈 Scan Statistics</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Total Alerts</span>
              <span className="text-white font-bold text-xl">{totalVulns}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">False Positives Excluded</span>
              <span className="text-cyber-green font-bold text-xl">{falsePositives}</span>
            </div>
            <hr className="border-gray-700/50" />
            <div className="flex justify-between items-center">
              <span className="text-red-400 font-medium">🔴 High Risk</span>
              <span className="text-red-400 font-bold">{riskCounts.High}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-amber-400 font-medium">🟠 Medium Risk</span>
              <span className="text-amber-400 font-bold">{riskCounts.Medium}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-blue-400 font-medium">🔵 Low Risk</span>
              <span className="text-blue-400 font-bold">{riskCounts.Low}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400 font-medium">⚪ Informational</span>
              <span className="text-gray-400 font-bold">{riskCounts.Informational}</span>
            </div>
          </div>
        </div>

        {/* Chart */}
        <div className="glass-card p-6">
          <h3 className="text-lg font-bold text-white mb-4">📊 Vulnerability Distribution</h3>
          <RiskChart counts={riskCounts} />
        </div>
      </div>

      {/* ─── AI Summary ─── */}
      {summary && (
        <div className="glass-card p-6">
          <h3 className="text-lg font-bold text-white mb-3">🧠 AI Analysis Summary</h3>
          <p className="text-gray-300 leading-relaxed">{summary}</p>
        </div>
      )}

      {/* ─── Detailed Vulnerability Table ─── */}
      <VulnerabilityTable vulnerabilities={vulnerabilities} aiAnalysis={aiAnalysis} />
    </div>
  );
}
