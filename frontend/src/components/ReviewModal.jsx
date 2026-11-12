import React, { useState } from 'react';
import { X, CheckCircle2, XCircle, Mail, AlertTriangle } from 'lucide-react';

export default function ReviewModal({ run, onClose, onReviewComplete }) {
  const [action, setAction] = useState('APPROVE_OVERRIDE');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  if (!run) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!notes.trim()) {
      alert("Please provide audit notes for your review decision.");
      return;
    }
    setSubmitting(true);
    try {
      const res = await fetch(`/api/invoices/${run.id}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action,
          notes,
          reviewer: 'AP Operations Specialist'
        })
      });
      const data = await res.json();
      onReviewComplete(data.updated_record);
      onClose();
    } catch (err) {
      console.error("Review submit error:", err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-lg w-full overflow-hidden border border-slate-200">
        <div className="flex items-center justify-between p-4 border-b border-slate-200 bg-slate-50">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-600" />
            <h3 className="text-sm font-bold text-slate-900">
              Human-in-the-Loop AP Review
            </h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4 text-xs">
          {/* Invoice Summary */}
          <div className="bg-amber-50/70 p-3 rounded-lg border border-amber-200/80 space-y-1">
            <div className="font-bold text-amber-900">Hold Reason:</div>
            <p className="text-amber-800 leading-relaxed">{run.decision_reason}</p>
            <div className="pt-2 flex justify-between font-mono text-[11px] text-amber-900/80 border-t border-amber-200/60">
              <span>Invoice: {run.invoice_number} ({run.vendor_name})</span>
              <span className="font-bold">${run.invoice_total.toLocaleString('en-US', { minimumFractionDigits: 2 })}</span>
            </div>
          </div>

          {/* Action Selector */}
          <div>
            <label className="block font-bold text-slate-700 mb-2">Select Resolution Action:</label>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => setAction('APPROVE_OVERRIDE')}
                className={`p-2.5 rounded-lg border text-center transition ${
                  action === 'APPROVE_OVERRIDE'
                    ? 'border-emerald-500 bg-emerald-50 text-emerald-800 font-bold'
                    : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                }`}
              >
                <CheckCircle2 className="w-4 h-4 mx-auto mb-1 text-emerald-600" />
                Approve Override
              </button>
              <button
                type="button"
                onClick={() => setAction('REJECT')}
                className={`p-2.5 rounded-lg border text-center transition ${
                  action === 'REJECT'
                    ? 'border-rose-500 bg-rose-50 text-rose-800 font-bold'
                    : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                }`}
              >
                <XCircle className="w-4 h-4 mx-auto mb-1 text-rose-600" />
                Reject Invoice
              </button>
              <button
                type="button"
                onClick={() => setAction('REQUEST_CORRECTION')}
                className={`p-2.5 rounded-lg border text-center transition ${
                  action === 'REQUEST_CORRECTION'
                    ? 'border-blue-500 bg-blue-50 text-blue-800 font-bold'
                    : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                }`}
              >
                <Mail className="w-4 h-4 mx-auto mb-1 text-blue-600" />
                Request Revision
              </button>
            </div>
          </div>

          {/* Reviewer Audit Notes */}
          <div>
            <label className="block font-bold text-slate-700 mb-1">
              Audit Notes & Approval Rationale <span className="text-rose-500">*</span>
            </label>
            <textarea
              rows={3}
              required
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g. Surcharge approved by VP of Engineering per emergency cloud maintenance clause..."
              className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          {/* Submit Buttons */}
          <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              className="px-3.5 py-2 text-slate-600 hover:bg-slate-100 rounded-lg transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg shadow-sm transition disabled:opacity-50"
            >
              {submitting ? 'Recording...' : 'Commit Decision to ERP'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
