import React, { useState, useEffect } from 'react';
import {
  FileText, CheckCircle2, AlertTriangle, XCircle, Search, Filter,
  DollarSign, ShieldAlert, TrendingUp, RefreshCw, Eye, UserCheck, Clock, ExternalLink, Download
} from 'lucide-react';

export default function DashboardView({ onSelectRun, onOpenReviewModal }) {
  const [historyData, setHistoryData] = useState({ stats: {}, runs: [] });
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');

  const fetchHistory = () => {
    setLoading(true);
    fetch('/api/invoices/history')
      .then(res => res.json())
      .then(data => {
        setHistoryData(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching history:", err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const stats = historyData.stats || {};
  const runs = historyData.runs || [];

  const filteredRuns = runs.filter(r => {
    const matchesSearch =
      r.vendor_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.invoice_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.po_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.invoice_filename?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus = statusFilter === 'ALL' || r.decision_status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="space-y-6">
      {/* Top Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Card 1: Total Processed */}
        <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-xs font-semibold uppercase tracking-wider">Invoices Processed</span>
            <FileText className="w-4 h-4 text-blue-600" />
          </div>
          <div className="text-2xl font-extrabold text-slate-900">{stats.total_runs || 0}</div>
          <div className="text-[11px] text-slate-500 mt-1 flex items-center gap-1">
            <TrendingUp className="w-3 h-3 text-emerald-600" /> End-to-end ingestion
          </div>
        </div>

        {/* Card 2: Auto-Approval Rate */}
        <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-xs font-semibold uppercase tracking-wider">Auto-Approval Rate</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-extrabold text-slate-900">
            {stats.auto_approval_rate || 0}%
          </div>
          <div className="text-[11px] text-emerald-600 font-semibold mt-1">
            {stats.auto_approved || 0} zero-touch payments
          </div>
        </div>

        {/* Card 3: Spend Auto-Disbursed */}
        <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-xs font-semibold uppercase tracking-wider">Approved Spend</span>
            <DollarSign className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-extrabold text-slate-900 font-mono">
            ${stats.approved_dollar_volume?.toLocaleString('en-US', { minimumFractionDigits: 2 }) || '0.00'}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">
            Total volume: ${stats.total_dollar_volume?.toLocaleString('en-US', { minimumFractionDigits: 0 }) || '0'}
          </div>
        </div>

        {/* Card 4: Under Review */}
        <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-xs font-semibold uppercase tracking-wider">Review Queue</span>
            <AlertTriangle className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-2xl font-extrabold text-amber-600">
            {stats.review_required || 0}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">
            Tolerance breaches & unlinked
          </div>
        </div>

        {/* Card 5: Fraud / Duplicates Blocked */}
        <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-xs font-semibold uppercase tracking-wider">Fraud Blocked</span>
            <ShieldAlert className="w-4 h-4 text-rose-600" />
          </div>
          <div className="text-2xl font-extrabold text-rose-600 font-mono">
            ${stats.duplicate_prevented_volume?.toLocaleString('en-US', { minimumFractionDigits: 2 }) || '0.00'}
          </div>
          <div className="text-[11px] text-rose-600 font-semibold mt-1">
            {stats.rejected || 0} duplicates intercepted
          </div>
        </div>
      </div>

      {/* Runs Table Card */}
      <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm overflow-hidden">
        {/* Table Filters Bar */}
        <div className="p-4 border-b border-slate-200/80 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="relative w-full sm:w-72">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search vendor, invoice #, PO..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full text-xs pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
            <div className="flex items-center bg-slate-100 p-0.5 rounded-lg text-xs font-medium text-slate-600">
              <button
                onClick={() => setStatusFilter('ALL')}
                className={`px-3 py-1 rounded-md transition ${statusFilter === 'ALL' ? 'bg-white text-slate-900 shadow-sm font-bold' : ''}`}
              >
                All
              </button>
              <button
                onClick={() => setStatusFilter('AUTO_APPROVED')}
                className={`px-3 py-1 rounded-md transition ${statusFilter === 'AUTO_APPROVED' ? 'bg-white text-emerald-700 shadow-sm font-bold' : ''}`}
              >
                Approved
              </button>
              <button
                onClick={() => setStatusFilter('REVIEW_REQUIRED')}
                className={`px-3 py-1 rounded-md transition ${statusFilter === 'REVIEW_REQUIRED' ? 'bg-white text-amber-700 shadow-sm font-bold' : ''}`}
              >
                Review
              </button>
              <button
                onClick={() => setStatusFilter('REJECTED')}
                className={`px-3 py-1 rounded-md transition ${statusFilter === 'REJECTED' ? 'bg-white text-rose-700 shadow-sm font-bold' : ''}`}
              >
                Rejected
              </button>
            </div>

            <a
              href="/api/invoices/export/csv"
              download="zamp_ap_audit_trail.csv"
              title="Export Audit Trail to CSV"
              className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 text-xs font-semibold rounded-lg border border-blue-200 transition"
            >
              <Download className="w-3.5 h-3.5" />
              Export CSV
            </a>
            <button
              onClick={fetchHistory}
              title="Refresh History"
              className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg border border-slate-200 transition"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Table Content */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-[11px] font-bold text-slate-500 uppercase tracking-wider border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">Invoice / Vendor</th>
                <th className="py-3 px-3">PO Reference</th>
                <th className="py-3 px-3 text-right">Invoice Total</th>
                <th className="py-3 px-3 text-center">Status</th>
                <th className="py-3 px-3">Decision Rationale</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredRuns.length > 0 ? (
                filteredRuns.map((run) => (
                  <tr key={run.id} className="hover:bg-slate-50/70 transition">
                    <td className="py-3 px-4">
                      <div className="font-bold text-slate-900">{run.vendor_name}</div>
                      <div className="text-[11px] text-slate-500 font-mono flex items-center gap-2 mt-0.5">
                        <span>{run.invoice_number}</span>
                        <span>•</span>
                        <span className="truncate max-w-[120px]">{run.invoice_filename}</span>
                      </div>
                    </td>

                    <td className="py-3 px-3 font-mono">
                      {run.po_number ? (
                        <span className="font-semibold text-slate-700 bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200 text-[11px]">
                          {run.po_number}
                        </span>
                      ) : (
                        <span className="text-slate-400 italic">None</span>
                      )}
                    </td>

                    <td className="py-3 px-3 text-right font-mono font-bold text-slate-900">
                      ${run.invoice_total.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </td>

                    <td className="py-3 px-3 text-center">
                      {run.decision_status === 'AUTO_APPROVED' && (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
                          <CheckCircle2 className="w-3 h-3" /> Approved
                        </span>
                      )}
                      {run.decision_status === 'REVIEW_REQUIRED' && (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-200">
                          <AlertTriangle className="w-3 h-3" /> Under Review
                        </span>
                      )}
                      {run.decision_status === 'REJECTED' && (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-200">
                          <XCircle className="w-3 h-3" /> Rejected
                        </span>
                      )}
                      {run.is_manual_override && (
                        <span className="block text-[9px] text-blue-600 font-semibold mt-0.5">
                          Manual Override
                        </span>
                      )}
                    </td>

                    <td className="py-3 px-3 max-w-xs truncate text-slate-600" title={run.decision_reason}>
                      {run.decision_reason}
                    </td>

                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => onSelectRun(run)}
                          className="p-1.5 text-slate-600 hover:text-blue-600 hover:bg-blue-50 rounded border border-slate-200 transition"
                          title="View Live Stepper & Proof"
                        >
                          <Eye className="w-3.5 h-3.5" />
                        </button>
                        {run.decision_status === 'REVIEW_REQUIRED' && (
                          <button
                            onClick={() => onOpenReviewModal(run)}
                            className="px-2 py-1 bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-300 rounded font-semibold text-[11px] transition flex items-center gap-1"
                          >
                            <UserCheck className="w-3 h-3" /> Review
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-400">
                    <FileText className="w-8 h-8 mx-auto mb-2 text-slate-300" />
                    <div>No invoice runs recorded yet.</div>
                    <p className="text-xs text-slate-400 mt-1">
                      Go to the Live Processing Studio and trigger an invoice run to populate history.
                    </p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
