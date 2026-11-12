import React, { useState, useEffect } from 'react';
import { Database, ShieldCheck, FileCheck, RefreshCw, History, CheckCircle2, Lock } from 'lucide-react';

export default function ErpExplorer({ onResetSystem }) {
  const [pos, setPos] = useState([]);
  const [vendors, setVendors] = useState([]);
  const [historyLedger, setHistoryLedger] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = () => {
    setLoading(true);
    Promise.all([
      fetch('/api/procurement/pos').then(res => res.json()),
      fetch('/api/procurement/vendors').then(res => res.json()),
      fetch('/api/procurement/history-ledger').then(res => res.json())
    ])
      .then(([posData, vendorsData, historyData]) => {
        setPos(posData);
        setVendors(vendorsData);
        setHistoryLedger(historyData);
        setLoading(false);
      })
      .catch(err => {
        console.error("Error loading ERP data:", err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Database className="w-5 h-5 text-blue-600" />
            Enterprise ERP Procurement & General Ledger (SQLite Persistent DB)
          </h2>
          <p className="text-xs text-slate-500">
            Simulates your company's core ERP system (Oracle NetSuite / SAP). Stores authorized purchase orders, approved vendor credentials, and the permanent historical payment ledger.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchData}
            className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg border border-slate-300 transition flex items-center gap-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} /> Refresh
          </button>
          <button
            onClick={onResetSystem}
            className="px-3.5 py-1.5 bg-rose-50 hover:bg-rose-100 text-rose-700 text-xs font-semibold rounded-lg border border-rose-200 transition"
          >
            Reset All Balances
          </button>
        </div>
      </div>

      {/* Grid: Left POs (60%), Right Vendors (40%) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Purchase Orders */}
        <div className="lg:col-span-7 bg-white rounded-xl border border-slate-200/80 shadow-sm overflow-hidden">
          <div className="p-4 border-b border-slate-200/80 flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <FileCheck className="w-4 h-4 text-blue-600" />
              Active Purchase Orders ({pos.length})
            </h3>
            <span className="text-[11px] text-slate-500">Dynamic 2-Way Match Targets</span>
          </div>

          <div className="divide-y divide-slate-100">
            {pos.map((po) => {
              const pctBilled = Math.min(100, Math.round((po.billed_amount / po.total_amount) * 100));

              return (
                <div key={po.po_number} className="p-4 hover:bg-slate-50/60 transition">
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-slate-900 text-sm">{po.po_number}</span>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          po.status === 'OPEN'
                            ? 'bg-blue-100 text-blue-800'
                            : po.status === 'PARTIALLY_BILLED'
                            ? 'bg-amber-100 text-amber-800'
                            : 'bg-emerald-100 text-emerald-800'
                        }`}>
                          {po.status}
                        </span>
                      </div>
                      <div className="text-xs text-slate-600 mt-0.5">{po.vendor_name}</div>
                    </div>

                    <div className="text-right">
                      <div className="text-xs font-bold text-slate-900 font-mono">
                        ${po.total_amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                      </div>
                      <div className="text-[11px] text-slate-400">Tolerance: +/-{po.tolerance_percentage}% (${po.tolerance_amount})</div>
                    </div>
                  </div>

                  {/* Drawdown Progress Bar */}
                  <div className="space-y-1 mt-3">
                    <div className="flex justify-between text-[11px] font-mono text-slate-500">
                      <span>Billed: ${po.billed_amount.toLocaleString('en-US', { minimumFractionDigits: 2 })} ({pctBilled}%)</span>
                      <span className="font-bold text-blue-700">Remaining: ${po.remaining_amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
                    </div>
                    <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden border border-slate-200/60">
                      <div
                        className={`h-full transition-all duration-500 ${
                          pctBilled === 100
                            ? 'bg-emerald-500'
                            : pctBilled > 0
                            ? 'bg-amber-500'
                            : 'bg-blue-500'
                        }`}
                        style={{ width: `${pctBilled}%` }}
                      />
                    </div>
                  </div>

                  {/* Line Items List preview */}
                  <div className="mt-3 pt-2 border-t border-slate-100 text-[11px] text-slate-500 flex flex-wrap gap-2">
                    {po.line_items.map((li, i) => (
                      <span key={i} className="bg-slate-100 px-2 py-0.5 rounded font-mono text-slate-700">
                        {li.item_code}: {li.quantity} @ ${li.unit_price}
                      </span>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: Vendor Master Directory */}
        <div className="lg:col-span-5 bg-white rounded-xl border border-slate-200/80 shadow-sm overflow-hidden">
          <div className="p-4 border-b border-slate-200/80 flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              Approved Vendor Master ({vendors.length})
            </h3>
            <span className="text-[11px] text-slate-500">Tax & Bank Verified</span>
          </div>

          <div className="divide-y divide-slate-100">
            {vendors.map((v) => (
              <div key={v.vendor_id} className="p-3.5 hover:bg-slate-50/60 transition">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <div className="flex items-center gap-1.5">
                      <span className="font-bold text-slate-900 text-xs">{v.vendor_name}</span>
                      {v.is_approved ? (
                        <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800">
                          APPROVED
                        </span>
                      ) : (
                        <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-rose-100 text-rose-800">
                          BLOCKED
                        </span>
                      )}
                    </div>
                    <div className="text-[11px] text-slate-500 font-mono mt-0.5">
                      ID: {v.vendor_id} • Tax: {v.tax_id || 'N/A'} • {v.payment_terms}
                    </div>
                    <div className="text-[10px] text-slate-400 mt-1">
                      Bank: {v.bank_account}
                    </div>
                  </div>

                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                    v.risk_rating === 'LOW'
                      ? 'bg-slate-100 text-slate-700'
                      : 'bg-rose-100 text-rose-800'
                  }`}>
                    {v.risk_rating} RISK
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Full Width: Historical Invoices Ledger */}
      <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-slate-200/80 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <History className="w-4 h-4 text-indigo-600" />
              ERP Historical Paid Invoices Ledger (Prior Accounting Periods & Settled Disbursements)
            </h3>
            <p className="text-[11px] text-slate-500 mt-0.5">
              The permanent historical ledger of invoices previously settled by the company. When an incoming invoice matches any record here (e.g., Edge Case 3), the duplicate detection engine immediately halts payment.
            </p>
          </div>
          <span className="text-xs font-mono font-bold text-indigo-700 bg-indigo-50 px-2.5 py-1 rounded-full border border-indigo-200">
            {historyLedger.length} Settled Records
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-[11px] font-bold text-slate-500 uppercase tracking-wider border-b border-slate-200">
              <tr>
                <th className="py-2.5 px-4">Invoice #</th>
                <th className="py-2.5 px-3">Vendor Name</th>
                <th className="py-2.5 px-3">PO Reference</th>
                <th className="py-2.5 px-3 text-right">Settled Amount</th>
                <th className="py-2.5 px-3">Date Paid</th>
                <th className="py-2.5 px-3">Bank ACH / Wire Reference</th>
                <th className="py-2.5 px-4 text-center">Ledger Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {historyLedger.map((item, idx) => (
                <tr key={idx} className="hover:bg-slate-50/70 transition">
                  <td className="py-2.5 px-4 font-mono font-bold text-slate-900">
                    {item.invoice_number}
                  </td>
                  <td className="py-2.5 px-3 font-medium text-slate-800">
                    {item.vendor_name}
                  </td>
                  <td className="py-2.5 px-3 font-mono text-slate-600">
                    {item.po_number || 'N/A'}
                  </td>
                  <td className="py-2.5 px-3 text-right font-mono font-bold text-slate-900">
                    ${item.total_amount.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </td>
                  <td className="py-2.5 px-3 text-slate-500 font-mono text-[11px]">
                    {item.paid_at || item.invoice_date}
                  </td>
                  <td className="py-2.5 px-3 font-mono text-slate-700 text-[11px]">
                    <span className="bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200">
                      {item.check_or_transfer_ref || 'ACH-DISBURSED'}
                    </span>
                  </td>
                  <td className="py-2.5 px-4 text-center">
                    <span className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200">
                      <Lock className="w-2.5 h-2.5" /> SETTLED
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
