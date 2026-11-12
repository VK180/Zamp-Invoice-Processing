import React, { useState } from 'react';
import {
  Layers, BarChart3, Database, RotateCcw, ShieldCheck, Sparkles
} from 'lucide-react';
import LiveRunStudio from './components/LiveRunStudio';
import DashboardView from './components/DashboardView';
import ErpExplorer from './components/ErpExplorer';
import ReviewModal from './components/ReviewModal';
import AiConfigModal from './components/AiConfigModal';

export default function App() {
  const [activeTab, setActiveTab] = useState('studio'); // 'studio' | 'dashboard' | 'erp'
  const [lastRun, setLastRun] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [reviewModalRun, setReviewModalRun] = useState(null);
  const [isAiModalOpen, setIsAiModalOpen] = useState(false);
  const [toastMessage, setToastMessage] = useState('');

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(''), 3500);
  };

  const handleReset = async () => {
    if (!window.confirm("Are you sure you want to reset all ERP purchase order balances and run history back to baseline?")) {
      return;
    }
    try {
      const res = await fetch('/api/reset', { method: 'POST' });
      const data = await res.json();
      setLastRun(null);
      showToast(data.message || "ERP and Run History reset successfully!");
    } catch (err) {
      console.error("Reset error:", err);
      showToast("Error resetting system state.");
    }
  };

  const handleSelectRunFromDashboard = (run) => {
    setLastRun(run);
    setActiveTab('studio');
  };

  const handleReviewComplete = (updatedRecord) => {
    setLastRun(updatedRecord);
    showToast(`Invoice #${updatedRecord.invoice_number} decision updated to ${updatedRecord.decision_status}!`);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Top Navigation Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Brand Logo & Name */}
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center text-white font-extrabold text-lg shadow-sm shadow-blue-500/20">
                z
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-extrabold text-slate-900 tracking-tight text-base">
                    zamp
                  </span>
                  <span className="text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                    PS-1 AP Engine
                  </span>
                </div>
                <div className="text-[11px] text-slate-500">
                  Invoice Processing & Autonomous 2-Way Match
                </div>
              </div>
            </div>

            {/* Navigation Tabs */}
            <nav className="hidden md:flex items-center gap-1 bg-slate-100 p-1 rounded-xl text-xs font-semibold text-slate-600">
              <button
                onClick={() => setActiveTab('studio')}
                className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg transition ${
                  activeTab === 'studio'
                    ? 'bg-white text-blue-600 shadow-sm font-bold'
                    : 'hover:text-slate-900'
                }`}
              >
                <Layers className="w-3.5 h-3.5" />
                Live Run Studio
              </button>

              <button
                onClick={() => setActiveTab('dashboard')}
                className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg transition ${
                  activeTab === 'dashboard'
                    ? 'bg-white text-blue-600 shadow-sm font-bold'
                    : 'hover:text-slate-900'
                }`}
              >
                <BarChart3 className="w-3.5 h-3.5" />
                AP Dashboard
              </button>

              <button
                onClick={() => setActiveTab('erp')}
                className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg transition ${
                  activeTab === 'erp'
                    ? 'bg-white text-blue-600 shadow-sm font-bold'
                    : 'hover:text-slate-900'
                }`}
              >
                <Database className="w-3.5 h-3.5" />
                ERP Master Explorer
              </button>
            </nav>

            {/* Actions: Reset & Status */}
            <div className="flex items-center gap-2.5">
              <button
                onClick={() => setIsAiModalOpen(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-lg border border-blue-200 transition shadow-xs"
                title="Configure Google Gemini or OpenAI LLM API Keys"
              >
                <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                <span>LLM Settings</span>
              </button>

              <div className="hidden sm:flex items-center gap-1.5 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                Engine Active
              </div>

              <button
                onClick={handleReset}
                title="Reset demo ERP balances and history"
                className="p-2 text-slate-500 hover:text-rose-600 hover:bg-rose-50 rounded-lg border border-slate-200 transition"
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Navigation Tabs */}
        <div className="md:hidden flex items-center justify-around border-t border-slate-200 bg-slate-50 py-1.5 text-xs font-semibold text-slate-600">
          <button
            onClick={() => setActiveTab('studio')}
            className={`px-2 py-1 ${activeTab === 'studio' ? 'text-blue-600 font-bold' : ''}`}
          >
            Studio
          </button>
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`px-2 py-1 ${activeTab === 'dashboard' ? 'text-blue-600 font-bold' : ''}`}
          >
            Dashboard
          </button>
          <button
            onClick={() => setActiveTab('erp')}
            className={`px-2 py-1 ${activeTab === 'erp' ? 'text-blue-600 font-bold' : ''}`}
          >
            ERP
          </button>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'studio' && (
          <LiveRunStudio
            onRunComplete={(run) => setLastRun(run)}
            lastRun={lastRun}
            isProcessing={isProcessing}
            setIsProcessing={setIsProcessing}
            onOpenAiConfig={() => setIsAiModalOpen(true)}
          />
        )}

        {activeTab === 'dashboard' && (
          <DashboardView
            onSelectRun={handleSelectRunFromDashboard}
            onOpenReviewModal={(run) => setReviewModalRun(run)}
          />
        )}

        {activeTab === 'erp' && (
          <ErpExplorer onResetSystem={handleReset} />
        )}
      </main>

      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-5 right-5 z-50 bg-slate-900 text-white text-xs font-semibold px-4 py-2.5 rounded-lg shadow-lg border border-slate-800 flex items-center gap-2 animate-bounce">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          {toastMessage}
        </div>
      )}

      {/* Human In The Loop Review Modal */}
      {reviewModalRun && (
        <ReviewModal
          run={reviewModalRun}
          onClose={() => setReviewModalRun(null)}
          onReviewComplete={handleReviewComplete}
        />
      )}

      {/* AI Cognitive Engine Configuration Modal */}
      <AiConfigModal
        isOpen={isAiModalOpen}
        onClose={() => setIsAiModalOpen(false)}
        onConfigSaved={(cfg) => showToast(`AI configured: ${cfg.provider?.toUpperCase()} (${cfg.model_name})`)}
      />

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-4 text-center text-xs text-slate-400">
        Zamp AI Solutions Analyst Case Study • Problem Statement 1 (Finance / AP) • 2026 Candidate Submission
      </footer>
    </div>
  );
}
