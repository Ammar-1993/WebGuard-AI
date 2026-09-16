import Head from 'next/head';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import Navbar from '@/components/Navbar';
import { getReports, getReportDetail, deleteReport, isAuthenticated } from '@/utils/api';

export default function Reports() {
  const router = useRouter();
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [downloadingId, setDownloadingId] = useState(null);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/login');
      return;
    }
    fetchReports();
  }, []);

  const fetchReports = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await getReports();
      // Handle array or object response safely
      const list = Array.isArray(data)
        ? data
        : Array.isArray(data?.reports)
          ? data.reports
          : [];
      setReports(list);
    } catch (err) {
      console.error('Error fetching reports:', err);
      setError('Failed to fetch reports. Please make sure you are logged in and the server is running.');
      setReports([]);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this report?')) return;
    try {
      await deleteReport(id);
      setReports((prev) => (Array.isArray(prev) ? prev.filter((r) => (r.id || r._id) !== id) : []));
    } catch (err) {
      console.error('Error deleting report:', err);
      alert('Failed to delete report.');
    }
  };

  const handleDownloadJson = async (report) => {
    const reportId = report.id || report._id;
    try {
      setDownloadingId(reportId);
      // Fetch full report details to include vulnerabilities and AI analysis
      const fullReport = await getReportDetail(reportId);
      const dataToExport = fullReport || report;
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(dataToExport, null, 2));
      const dlAnchorElem = document.createElement('a');
      dlAnchorElem.setAttribute("href", dataStr);
      dlAnchorElem.setAttribute("download", `webguard-report-${report.scan_id || reportId}.json`);
      dlAnchorElem.click();
    } catch (err) {
      console.error('Error fetching full report, falling back to summary:', err);
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(report, null, 2));
      const dlAnchorElem = document.createElement('a');
      dlAnchorElem.setAttribute("href", dataStr);
      dlAnchorElem.setAttribute("download", `webguard-report-${report.scan_id || reportId}.json`);
      dlAnchorElem.click();
    } finally {
      setDownloadingId(null);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 90) return 'text-cyber-green';
    if (score >= 70) return 'text-amber-400';
    return 'text-red-500';
  };

  const reportList = Array.isArray(reports) ? reports : [];

  return (
    <>
      <Head>
        <title>Reports History — WebGuard AI</title>
      </Head>

      <div className="min-h-screen gradient-bg">
        <Navbar />

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-8">
            <div>
              <h1 className="text-3xl font-bold text-white">📄 Security Reports History</h1>
              <p className="text-gray-400 text-sm mt-1">View, download, and manage your past vulnerability assessment reports</p>
            </div>
            <div className="flex gap-3">
              <button onClick={fetchReports} className="btn-secondary text-sm">
                🔄 Refresh
              </button>
              <Link href="/" className="btn-primary text-sm">
                ➕ New Scan
              </Link>
            </div>
          </div>

          {error && (
            <div className="bg-red-500/10 border border-red-500/20 text-red-400 px-4 py-3 rounded-xl mb-6 flex justify-between items-center">
              <span>{error}</span>
              <button onClick={fetchReports} className="underline text-sm ml-4">Try Again</button>
            </div>
          )}

          {loading ? (
            <div className="glass-card p-16 flex flex-col justify-center items-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mb-4"></div>
              <p className="text-gray-400 text-sm">Loading security reports...</p>
            </div>
          ) : reportList.length === 0 ? (
            <div className="glass-card p-12 text-center">
              <div className="text-5xl mb-4">📭</div>
              <h3 className="text-xl font-bold text-white mb-2">No Reports Found</h3>
              <p className="text-gray-400 max-w-md mx-auto mb-6">
                You haven't run any security scans yet, or no past scan reports are stored in the database.
              </p>
              <Link href="/" className="btn-primary inline-block">
                Start a New Scan
              </Link>
            </div>
          ) : (
            <div className="glass-card overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-gray-800/60 text-gray-300 text-xs uppercase tracking-wider border-b border-gray-700/50">
                      <th className="p-4 font-semibold">Target URL</th>
                      <th className="p-4 font-semibold">Scan Date</th>
                      <th className="p-4 font-semibold">Security Score</th>
                      <th className="p-4 font-semibold">Vulnerabilities</th>
                      <th className="p-4 font-semibold text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-700/40">
                    {reportList.map((report) => {
                      const reportId = report.id || report._id;
                      const dateStr = report.scan_date ? new Date(report.scan_date).toLocaleString() : 'N/A';
                      const isDownloading = downloadingId === reportId;

                      return (
                        <tr key={reportId} className="hover:bg-white/5 transition-colors">
                          <td className="p-4 font-medium text-white max-w-xs truncate">
                            <span title={report.target_url}>{report.target_url || 'N/A'}</span>
                          </td>
                          <td className="p-4 text-gray-400 text-sm whitespace-nowrap">
                            {dateStr}
                          </td>
                          <td className="p-4 font-bold whitespace-nowrap">
                            <span className={getScoreColor(report.score ?? 0)}>
                              {report.grade || 'N/A'} ({report.score ?? 0}/100)
                            </span>
                          </td>
                          <td className="p-4 text-gray-300 text-sm whitespace-nowrap">
                            <span className="font-semibold text-white">{report.total_vulnerabilities ?? 0}</span> alerts
                            {report.false_positives_count > 0 && (
                              <span className="text-cyber-green text-xs ml-2">
                                ({report.false_positives_count} filtered)
                              </span>
                            )}
                          </td>
                          <td className="p-4 text-right space-x-2 whitespace-nowrap">
                            <Link
                              href={`/?report_id=${reportId}`}
                              className="text-primary-400 hover:text-primary-300 text-sm font-medium transition-colors px-3 py-1.5 rounded-lg hover:bg-primary-500/10 inline-flex items-center gap-1"
                            >
                              👁️ View
                            </Link>
                            <button
                              onClick={() => handleDownloadJson(report)}
                              disabled={isDownloading}
                              className="text-cyber-blue hover:text-blue-300 text-sm font-medium transition-colors px-3 py-1.5 rounded-lg hover:bg-blue-500/10 inline-flex items-center gap-1 disabled:opacity-50"
                            >
                              {isDownloading ? '⏳ Downloading...' : '💾 JSON'}
                            </button>
                            <button
                              onClick={() => handleDelete(reportId)}
                              className="text-red-400 hover:text-red-300 text-sm font-medium transition-colors px-3 py-1.5 rounded-lg hover:bg-red-500/10 inline-flex items-center gap-1"
                            >
                              🗑️ Delete
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </main>
      </div>
    </>
  );
}
