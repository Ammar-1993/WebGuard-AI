import Head from 'next/head';
import { useState } from 'react';
import Navbar from '@/components/Navbar';
import ScanForm from '@/components/ScanForm';
import ScanProgress from '@/components/ScanProgress';
import Dashboard from '@/components/Dashboard';

/**
 * WebGuard AI — Home Page
 * Displays the scan form and results dashboard after completion.
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
        <title>WebGuard AI — Intelligent Vulnerability Scanner</title>
        <meta name="description" content="An intelligent platform for web vulnerability scanning powered by OWASP ZAP and AI analysis" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="min-h-screen gradient-bg">
        <Navbar />

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* ─── Idle State: Scan Form ─── */}
          {scanState === 'idle' && (
            <div className="space-y-12">
              {/* Hero Section */}
              <div className="text-center py-16">
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary-500/10 border border-primary-500/20 mb-6">
                  <span className="w-2 h-2 rounded-full bg-cyber-green animate-pulse"></span>
                  <span className="text-sm text-primary-300 font-medium">System Ready to Scan</span>
                </div>
                <h1 className="text-5xl md:text-6xl font-extrabold mb-6">
                  <span className="bg-gradient-to-r from-primary-400 via-cyber-purple to-cyber-blue bg-clip-text text-transparent">
                    WebGuard AI
                  </span>
                </h1>
                <p className="text-xl text-gray-400 max-w-3xl mx-auto leading-relaxed">
                  An intelligent vulnerability scanning platform — combining the power of
                  <span className="text-cyber-green font-semibold"> OWASP ZAP </span>
                  for vulnerability discovery with
                  <span className="text-cyber-purple font-semibold"> Artificial Intelligence </span>
                  for analysis and simplification
                </p>
              </div>

              {/* Scan Form */}
              <ScanForm onScanStart={handleScanStart} />

              {/* Features */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
                <div className="glass-card p-6 text-center">
                  <div className="text-4xl mb-4">🔍</div>
                  <h3 className="text-lg font-bold text-white mb-2">Comprehensive Scanning</h3>
                  <p className="text-gray-400 text-sm">Advanced security scan based on OWASP Top 10 global standards</p>
                </div>
                <div className="glass-card p-6 text-center">
                  <div className="text-4xl mb-4">🧠</div>
                  <h3 className="text-lg font-bold text-white mb-2">AI-Powered Analysis</h3>
                  <p className="text-gray-400 text-sm">Artificial intelligence analyzes results and eliminates false positives</p>
                </div>
                <div className="glass-card p-6 text-center">
                  <div className="text-4xl mb-4">💊</div>
                  <h3 className="text-lg font-bold text-white mb-2">Remediation Code</h3>
                  <p className="text-gray-400 text-sm">Ready-to-use recommendations and fix code for immediate application</p>
                </div>
              </div>
            </div>
          )}

          {/* ─── Scanning State: Progress Bar ─── */}
          {scanState === 'scanning' && scanData && (
            <ScanProgress
              scanId={scanData.scan_id}
              targetUrl={scanData.target_url}
              onComplete={handleScanComplete}
              onError={() => setScanState('idle')}
            />
          )}

          {/* ─── Completed State: Dashboard ─── */}
          {scanState === 'completed' && reportData && (
            <Dashboard
              report={reportData}
              onNewScan={handleNewScan}
            />
          )}
        </main>

        {/* Footer */}
        <footer className="text-center py-8 text-gray-500 text-sm border-t border-gray-800/50">
          <p>© 2026 WebGuard AI — University of Bisha</p>
        </footer>
      </div>
    </>
  );
}
