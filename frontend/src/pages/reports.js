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

  // ─── Modern Delete Modal & Toast State ───
  const [reportToDelete, setReportToDelete] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [toast, setToast] = useState(null); // { message, type: 'success' | 'error' }

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/login');
      return;
    }
    fetchReports();
  }, []);

  // Auto-dismiss toast after 3.5s
  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 3500);
      return () => clearTimeout(timer);
    }
  }, [toast]);

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

  const openDeleteModal = (report) => {
    setReportToDelete(report);
  };

  const confirmDelete = async () => {
    if (!reportToDelete) return;
    const targetId = reportToDelete.id || reportToDelete._id;
    try {
      setIsDeleting(true);
      await deleteReport(targetId);
      setReports((prev) => (Array.isArray(prev) ? prev.filter((r) => (r.id || r._id) !== targetId) : []));
      setToast({
        type: 'success',
        message: `Report for "${reportToDelete.target_url || 'Target'}" was deleted successfully.`
      });
      setReportToDelete(null);
    } catch (err) {
      console.error('Error deleting report:', err);
      setToast({
        type: 'error',
        message: 'Failed to delete report. Please try again.'
      });
    } finally {
      setIsDeleting(false);
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

      <div className="min-h-screen gradient-bg relative">
        <Navbar />

        {/* ─── Floating Toast Notification ─── */}
        {toast && (
          <div className="fixed top-20 right-6 z-50 animate-bounce transition-all">
            <div className={`px-5 py-3 rounded-xl shadow-2xl backdrop-blur-md border flex items-center gap-3 ${
              toast.type === 'success'
                ? 'bg-cyber-darker/90 border-cyber-green/40 text-cyber-green shadow-emerald-950/50'
                : 'bg-cyber-darker/90 border-red-500/40 text-red-400 shadow-red-950/50'
            }`}>
              <span className="text-xl">{toast.type === 'success' ? '✅' : '⚠️'}</span>
              <p className="text-sm font-medium text-white">{toast.message}</p>
              <button
                onClick={() => setToast(null)}
                className="text-gray-400 hover:text-white text-sm ml-2"
              >
                ✕
              </button>
            </div>
          </div>
        )}

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
            <div className="glass-card overflow-hidden shadow-xl">
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
                              onClick={() => openDeleteModal(report)}
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

        {/* ─── Modern Cyber Confirmation Modal ─── */}
        {reportToDelete && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm transition-all animate-fadeIn">
            <div className="glass-card border border-red-500/30 shadow-2xl shadow-red-950/50 max-w-lg w-full p-6 text-left relative overflow-hidden">
              {/* Glowing accent border top */}
              <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-red-500/20 via-red-500 to-red-500/20"></div>

              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-xl bg-red-500/15 border border-red-500/30 flex items-center justify-center text-red-400 text-2xl flex-shrink-0 shadow-inner">
                  ⚠️
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-white mb-1">Delete Security Report?</h3>
                  <p className="text-gray-400 text-sm leading-relaxed">
                    Are you sure you want to permanently delete this report? This action cannot be undone and will purge all scan findings and AI remediation data.
                  </p>
                </div>
              </div>

              {/* Target info preview */}
              <div className="mt-5 p-3.5 rounded-xl bg-gray-900/80 border border-gray-800 space-y-2">
                <div className="flex items-center justify-between text-xs text-gray-400">
                  <span>Target URL</span>
                  <span className="text-gray-500">{reportToDelete.scan_date ? new Date(reportToDelete.scan_date).toLocaleDateString() : ''}</span>
                </div>
                <div className="font-mono text-sm text-primary-300 truncate font-semibold">
                  {reportToDelete.target_url || 'Unknown Target'}
                </div>
                <div className="flex gap-4 pt-1 text-xs border-t border-gray-800/80">
                  <span className="text-gray-400">
                    Score: <span className="font-bold text-white">{reportToDelete.score ?? 0}/100 ({reportToDelete.grade || 'N/A'})</span>
                  </span>
                  <span className="text-gray-400">
                    Alerts: <span className="font-bold text-white">{reportToDelete.total_vulnerabilities ?? 0}</span>
                  </span>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="mt-6 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setReportToDelete(null)}
                  disabled={isDeleting}
                  className="px-4 py-2.5 rounded-xl border border-gray-700 hover:border-gray-600 text-gray-300 hover:text-white hover:bg-gray-800/50 text-sm font-medium transition-colors disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={confirmDelete}
                  disabled={isDeleting}
                  className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-red-600 to-red-700 hover:from-red-500 hover:to-red-600 text-white text-sm font-semibold shadow-lg shadow-red-600/30 hover:shadow-red-600/50 transition-all active:scale-95 disabled:opacity-50 flex items-center gap-2"
                >
                  {isDeleting ? (
                    <>
                      <span className="animate-spin text-sm">⏳</span>
                      <span>Deleting...</span>
                    </>
                  ) : (
                    <>
                      <span>🗑️</span>
                      <span>Delete Report</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
