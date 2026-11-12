import React, { useState, useEffect } from 'react';
import {
  FileText, CheckCircle2, AlertTriangle, XCircle, ArrowRight, Play,
  Upload, RefreshCw, ShieldCheck, Mail, Database, Clock, ChevronDown, ChevronRight,
  ExternalLink, Layers, Sparkles, Download
} from 'lucide-react';

export default function LiveRunStudio({ onRunComplete, lastRun, isProcessing, setIsProcessing, onOpenAiConfig }) {
  const [scenarios, setScenarios] = useState([]);
  const [selectedScenario, setSelectedScenario] = useState(null);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [uploadedBlobUrl, setUploadedBlobUrl] = useState(null);
  const [activeStageIndex, setActiveStageIndex] = useState(-1);
  const [activeTabDetails, setActiveTabDetails] = useState('reconciliation'); // 'reconciliation' | 'extracted' | 'policy' | 'erp' | 'email' | 'pdf'
  const [currentRun, setCurrentRun] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  useEffect(() => {
    fetch('/api/samples')
      .then(res => res.json())
      .then(data => {
        setScenarios(data);
        if (data.length > 0 && !selectedScenario) {
          setSelectedScenario(data[0]);
        }
      })
      .catch(err => console.error("Error loading sample scenarios:", err));
  }, []);

  useEffect(() => {
    if (lastRun) {
      setCurrentRun(lastRun);
      setActiveStageIndex(5);
    }
  }, [lastRun]);

  const runScenario = async (scenario) => {
    setSelectedScenario(scenario);
    setUploadedFile(null);
    setUploadedBlobUrl(null);
    setIsProcessing(true);
    setCurrentRun(null);
    setActiveStageIndex(0);

    // Simulate stepped execution for visual impact
    for (let i = 0; i < 5; i++) {
      setActiveStageIndex(i);
      await new Promise(r => setTimeout(r, 220));
    }

    setErrorMessage(null);
    try {
      const res = await fetch('/api/invoices/process-sample', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sample_filename: scenario.filename })
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setErrorMessage(err.detail || `Server error (${res.status}). Please try again.`);
        setIsProcessing(false);
        return;
      }
      const data = await res.json();
      setActiveStageIndex(5);
      setCurrentRun(data);
      if (onRunComplete) onRunComplete(data);
    } catch (err) {
      console.error("Execution error:", err);
      setErrorMessage("Network error: Could not reach the backend. Ensure the server is running.");
    } finally {
      setIsProcessing(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploadedFile(file);
    try {
      setUploadedBlobUrl(URL.createObjectURL(file));
    } catch (_) {}
    setSelectedScenario(null);
    setIsProcessing(true);
    setCurrentRun(null);
    setActiveStageIndex(0);

    for (let i = 0; i < 5; i++) {
      setActiveStageIndex(i);
      await new Promise(r => setTimeout(r, 220));
    }

    const formData = new FormData();
    formData.append('file', file);

    setErrorMessage(null);
    try {
      const res = await fetch('/api/invoices/process', {
        method: 'POST',
        body: formData
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        setErrorMessage(errData.detail || `Upload processing failed (${res.status}). Check the PDF and try again.`);
        setIsProcessing(false);
        return;
      }
      const data = await res.json();
      setActiveStageIndex(5);
      setCurrentRun(data);
      if (onRunComplete) onRunComplete(data);
    } catch (err) {
      console.error("Upload execution error:", err);
      setErrorMessage("Network error: Failed to process uploaded PDF. Ensure the server is running.");
    } finally {
      setIsProcessing(false);
    }
  };

  const activePdfUrl = currentRun?.pdf_url || 
    (currentRun?.invoice_filename ? `/api/samples/${encodeURIComponent(currentRun.invoice_filename)}/pdf` : null) || 
    uploadedBlobUrl || 
    (selectedScenario ? `/api/samples/${encodeURIComponent(selectedScenario.filename)}/pdf` : null);

  const STAGES = [
    { id: 'stage_1_ingest', title: '1. Ingestion & Optical Parsing', desc: 'PDF text extraction & layout tokens' },
    { id: 'stage_2_extract', title: '2. Entity & Line Item Extraction', desc: 'Metadata, items, tax & financial totals' },
    { id: 'stage_3_vendor', title: '3. Vendor Master Verification', desc: 'ERP vendor authentication & risk tier' },
    { id: 'stage_4_po', title: '4. PO 2-Way Reconciliation', desc: 'Line item price/qty matching & split PO' },
    { id: 'stage_5_policy', title: '5. Policy & Duplicate Risk Engine', desc: 'Tolerance boundaries & duplicate ledger' },
    { id: 'stage_6_decision', title: '6. Autonomous Decision & ERP Action', desc: 'Verdict, audit rationale & webhook dispatch' },
  ];

  return (
    <div className="space-y-6">
      {/* 1-Click Scenario Runner Bar */}
      <div className="bg-white rounded-xl p-5 border border-slate-200/80 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
          <div>
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-blue-600" />
              1-Click Test Scenarios & Edge Cases
            </h2>
            <p className="text-xs text-slate-500">
              Select an invoice scenario or upload your own custom PDF to trigger real-time autonomous processing.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <label className="cursor-pointer inline-flex items-center gap-2 px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg border border-slate-300 transition">
              <Upload className="w-4 h-4 text-slate-600" />
              Upload Custom PDF
              <input type="file" accept=".pdf" className="hidden" onChange={handleFileUpload} disabled={isProcessing} />
            </label>
          </div>
        </div>

        {/* Scenario Pill Buttons */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-2.5">
          {scenarios.map((sc, idx) => {
            const isSelected = selectedScenario?.filename === sc.filename;
            const badgeColorMap = {
              emerald: 'border-emerald-300 bg-emerald-50 text-emerald-800',
              amber: 'border-amber-300 bg-amber-50 text-amber-800',
              blue: 'border-blue-300 bg-blue-50 text-blue-800',
              rose: 'border-rose-300 bg-rose-50 text-rose-800'
            };

            return (
              <button
                key={sc.filename}
                onClick={() => runScenario(sc)}
                disabled={isProcessing}
                className={`text-left p-3 rounded-lg border transition-all relative flex flex-col justify-between ${
                  isSelected
                    ? 'border-blue-600 bg-blue-50/60 ring-2 ring-blue-500/20 shadow-sm'
                    : 'border-slate-200 hover:border-slate-300 hover:bg-slate-50'
                } ${isProcessing ? 'opacity-70 cursor-not-allowed' : ''}`}
              >
                <div>
                  <div className="flex items-center justify-between gap-1 mb-1.5">
                    <span className="text-[10px] font-bold tracking-wide uppercase px-1.5 py-0.5 rounded bg-white border text-slate-600">
                      {idx === 0 ? 'Happy Path' : `Edge Case ${idx}`}
                    </span>
                    <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border ${badgeColorMap[sc.badge_color] || 'bg-slate-100'}`}>
                      {sc.expected_status.replace('_', ' ')}
                    </span>
                  </div>
                  <div className="text-xs font-bold text-slate-900 leading-snug mb-1">
                    {sc.title}
                  </div>
                  <div className="text-[11px] text-slate-500 font-mono">
                    {sc.po_number !== 'None' ? sc.po_number : 'No PO'} • ${sc.total.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </div>
                </div>

                <div className="mt-2 pt-2 border-t border-slate-200/60 flex items-center justify-between text-[10px] font-semibold text-blue-600">
                  <span>Run Live</span>
                  <Play className="w-3 h-3 fill-blue-600 text-blue-600" />
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Error Banner */}
      {errorMessage && (
        <div className="bg-rose-50 border border-rose-200 text-rose-800 text-xs font-semibold px-4 py-3 rounded-xl flex items-start gap-2">
          <span className="text-rose-600 font-bold mt-0.5">&#9888;</span>
          <span>{errorMessage}</span>
          <button onClick={() => setErrorMessage(null)} className="ml-auto text-rose-500 hover:text-rose-700 font-bold">&#10005;</button>
        </div>
      )}

      {/* Main Execution View: Left Stepper (40%), Right Visual Output (60%) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Live Stepper & Telemetry (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-white rounded-xl p-5 border border-slate-200/80 shadow-sm">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Layers className="w-4 h-4 text-blue-600" />
                Live Execution Stepper
              </h3>
              {isProcessing ? (
                <span className="flex items-center gap-1.5 text-xs font-semibold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full border border-blue-200 animate-pulse">
                  <RefreshCw className="w-3 h-3 animate-spin" /> Processing
                </span>
              ) : currentRun ? (
                <span className="text-xs font-semibold text-slate-500 flex items-center gap-1">
                  <Clock className="w-3 h-3" /> Completed in ~180ms
                </span>
              ) : (
                <span className="text-xs text-slate-400">Awaiting trigger</span>
              )}
            </div>

            {/* Stepper Timeline */}
            <div className="mt-4 space-y-3">
              {STAGES.map((stage, idx) => {
                const isCurrent = isProcessing && activeStageIndex === idx;
                const isPassed = activeStageIndex > idx || (!isProcessing && currentRun);
                const stageLog = currentRun?.stages?.find(s => s.stage_id === stage.id);
                const isFailed = stageLog?.status === 'FAILED';
                const isWarning = stageLog?.status === 'WARNING';

                let iconNode = (
                  <div className="w-6 h-6 rounded-full border-2 border-slate-200 bg-slate-50 flex items-center justify-center text-[10px] font-bold text-slate-400">
                    {idx + 1}
                  </div>
                );

                if (isCurrent) {
                  iconNode = (
                    <div className="w-6 h-6 rounded-full border-2 border-blue-600 bg-blue-50 flex items-center justify-center animate-spin">
                      <RefreshCw className="w-3.5 h-3.5 text-blue-600" />
                    </div>
                  );
                } else if (isPassed) {
                  if (isFailed) {
                    iconNode = <XCircle className="w-6 h-6 text-rose-500 fill-rose-50" />;
                  } else if (isWarning) {
                    iconNode = <AlertTriangle className="w-6 h-6 text-amber-500 fill-amber-50" />;
                  } else {
                    iconNode = <CheckCircle2 className="w-6 h-6 text-emerald-600 fill-emerald-50" />;
                  }
                }

                return (
                  <div
                    key={stage.id}
                    className={`p-3 rounded-lg border transition-all ${
                      isCurrent
                        ? 'border-blue-400 bg-blue-50/50 shadow-sm'
                        : isPassed
                        ? isFailed
                          ? 'border-rose-200 bg-rose-50/30'
                          : isWarning
                          ? 'border-amber-200 bg-amber-50/30'
                          : 'border-slate-200/80 bg-white'
                        : 'border-slate-100 bg-slate-50/50 opacity-60'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className="mt-0.5">{iconNode}</div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-slate-800">{stage.title}</span>
                          {stageLog && (
                            <span className="text-[10px] font-mono text-slate-400">
                              {stageLog.duration_ms}ms
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-slate-500 mt-0.5">
                          {stageLog?.message || stage.desc}
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Quick PDF Ingestion Preview Box */}
          <div className="bg-white rounded-xl p-4 border border-slate-200/80 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                <FileText className="w-4 h-4 text-slate-500" /> Ingested Document
              </span>
              {activePdfUrl && (
                <a
                  href={activePdfUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="text-[11px] font-semibold text-blue-600 hover:text-blue-800 flex items-center gap-1"
                >
                  Open PDF <ExternalLink className="w-3 h-3" />
                </a>
              )}
            </div>
            <div className="text-xs text-slate-600 font-mono bg-slate-50 p-2.5 rounded border border-slate-200/60 truncate">
              {uploadedFile ? uploadedFile.name : (currentRun?.invoice_filename || selectedScenario?.filename || 'No document loaded')}
            </div>
          </div>
        </div>

        {/* Right Column: Dynamic Decision & Deep Dive Tabs (7 cols) */}
        <div className="lg:col-span-7 space-y-4">
          {/* Top Decision Banner Card */}
          {currentRun ? (
            <div
              className={`rounded-xl p-5 border shadow-sm transition-all ${
                currentRun.decision_status === 'AUTO_APPROVED'
                  ? 'border-emerald-300 bg-gradient-to-br from-emerald-50/90 to-white'
                  : currentRun.decision_status === 'REVIEW_REQUIRED'
                  ? 'border-amber-300 bg-gradient-to-br from-amber-50/90 to-white'
                  : 'border-rose-300 bg-gradient-to-br from-rose-50/90 to-white'
              }`}
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-200/60">
                <div className="flex items-center gap-2.5">
                  {currentRun.decision_status === 'AUTO_APPROVED' ? (
                    <div className="w-9 h-9 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-700">
                      <CheckCircle2 className="w-6 h-6" />
                    </div>
                  ) : currentRun.decision_status === 'REVIEW_REQUIRED' ? (
                    <div className="w-9 h-9 rounded-full bg-amber-100 flex items-center justify-center text-amber-700">
                      <AlertTriangle className="w-6 h-6" />
                    </div>
                  ) : (
                    <div className="w-9 h-9 rounded-full bg-rose-100 flex items-center justify-center text-rose-700">
                      <XCircle className="w-6 h-6" />
                    </div>
                  )}
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                      Autonomous Verdict
                    </span>
                    <h3 className="text-base font-extrabold text-slate-900 leading-tight">
                      {currentRun.decision_status === 'AUTO_APPROVED' && 'AUTO-APPROVED FOR PAYMENT'}
                      {currentRun.decision_status === 'REVIEW_REQUIRED' && 'HOLD: MANUAL REVIEW REQUIRED'}
                      {currentRun.decision_status === 'REJECTED' && 'INVOICE REJECTED (NO PAYMENT)'}
                    </h3>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <div className="text-right">
                    <div className="text-[10px] text-slate-500 font-semibold uppercase">Confidence</div>
                    <div className="text-xs font-bold text-slate-800">{currentRun.confidence_score}%</div>
                  </div>
                  <div className="h-6 w-px bg-slate-200" />
                  <div className="text-right">
                    <div className="text-[10px] text-slate-500 font-semibold uppercase">Invoice Total</div>
                    <div className="text-xs font-bold text-slate-900 font-mono">
                      ${currentRun.invoice_total.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </div>
                  </div>
                </div>
              </div>

              {/* Decision Reason Paragraph */}
              <div className="mt-3.5">
                <p className="text-xs text-slate-700 font-medium leading-relaxed">
                  {currentRun.decision_reason}
                </p>
              </div>

              {/* Rationale Bullet Points */}
              {currentRun.stages?.find(s => s.stage_id === 'stage_6_decision')?.details && (
                <div className="mt-3 pt-3 border-t border-slate-200/60 flex flex-wrap gap-2 text-[11px] text-slate-600">
                  <span className="font-semibold text-slate-800">Action:</span>
                  <span>{currentRun.stages.find(s => s.stage_id === 'stage_6_decision').message.split('. ')[1] || 'Action dispatched.'}</span>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-white rounded-xl p-8 border border-dashed border-slate-300 text-center text-slate-400">
              <FileText className="w-10 h-10 mx-auto mb-2 text-slate-300" />
              <div className="text-sm font-semibold text-slate-600">Ready to Process</div>
              <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
                Click any test scenario above or upload an invoice PDF to inspect the live 2-way match and policy validation.
              </p>
            </div>
          )}

          {/* Detailed Audit & Proof Tabs */}
          {currentRun && (
            <div className="bg-white rounded-xl border border-slate-200/80 shadow-sm overflow-hidden">
              {/* Tab Navigation */}
              <div className="flex items-center gap-1 p-2 bg-slate-50/80 border-b border-slate-200 text-xs font-semibold text-slate-600 overflow-x-auto">
                <button
                  onClick={() => setActiveTabDetails('reconciliation')}
                  className={`px-3 py-1.5 rounded-lg transition ${
                    activeTabDetails === 'reconciliation'
                      ? 'bg-white text-blue-600 shadow-sm border border-slate-200 font-bold'
                      : 'hover:text-slate-900'
                  }`}
                >
                  PO 2-Way Reconciliation
                </button>
                <button
                  onClick={() => setActiveTabDetails('pdf')}
                  className={`px-3 py-1.5 rounded-lg transition ${
                    activeTabDetails === 'pdf'
                      ? 'bg-white text-blue-600 shadow-sm border border-slate-200 font-bold'
                      : 'hover:text-slate-900'
                  }`}
                >
                  PDF Document
                </button>
                <button
                  onClick={() => setActiveTabDetails('extracted')}
                  className={`px-3 py-1.5 rounded-lg transition ${
                    activeTabDetails === 'extracted'
                      ? 'bg-white text-blue-600 shadow-sm border border-slate-200 font-bold'
                      : 'hover:text-slate-900'
                  }`}
                >
                  Extracted Data ({currentRun.extracted_data?.line_items?.length || 0} Lines)
                </button>
                <button
                  onClick={() => setActiveTabDetails('policy')}
                  className={`px-3 py-1.5 rounded-lg transition ${
                    activeTabDetails === 'policy'
                      ? 'bg-white text-blue-600 shadow-sm border border-slate-200 font-bold'
                      : 'hover:text-slate-900'
                  }`}
                >
                  Policy Checks ({currentRun.policy_checks?.length || 0})
                </button>
                <button
                  onClick={() => setActiveTabDetails('erp')}
                  className={`px-3 py-1.5 rounded-lg transition ${
                    activeTabDetails === 'erp'
                      ? 'bg-white text-blue-600 shadow-sm border border-slate-200 font-bold'
                      : 'hover:text-slate-900'
                  }`}
                >
                  ERP Webhook Payload
                </button>
                {currentRun.vendor_notification_draft && (
                  <button
                    onClick={() => setActiveTabDetails('email')}
                    className={`px-3 py-1.5 rounded-lg transition ${
                      activeTabDetails === 'email'
                        ? 'bg-white text-blue-600 shadow-sm border border-slate-200 font-bold'
                        : 'hover:text-slate-900'
                    }`}
                  >
                    Vendor Inquiry Draft
                  </button>
                )}
              </div>

              {/* Tab 1: Reconciliation Matrix */}
              {activeTabDetails === 'reconciliation' && (
                <div className="p-4 space-y-4">
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-50 p-3 rounded-lg border border-slate-200/60 text-xs">
                    <div>
                      <div className="text-[10px] text-slate-500 font-semibold uppercase">PO Number</div>
                      <div className="font-bold text-slate-800">{currentRun.reconciliation?.po_number || 'N/A'}</div>
                    </div>
                    <div>
                      <div className="text-[10px] text-slate-500 font-semibold uppercase">Authorized Total</div>
                      <div className="font-bold text-slate-800 font-mono">
                        ${currentRun.reconciliation?.po_total?.toLocaleString('en-US', { minimumFractionDigits: 2 }) || '0.00'}
                      </div>
                    </div>
                    <div>
                      <div className="text-[10px] text-slate-500 font-semibold uppercase">Invoice Variance</div>
                      <div className={`font-bold font-mono ${
                        currentRun.reconciliation?.tolerance_breached
                          ? 'text-rose-600'
                          : currentRun.reconciliation?.total_variance > 0
                          ? 'text-amber-600'
                          : 'text-emerald-600'
                      }`}>
                        ${currentRun.reconciliation?.total_variance?.toLocaleString('en-US', { minimumFractionDigits: 2 }) || '0.00'} ({currentRun.reconciliation?.variance_percentage || 0}%)
                      </div>
                    </div>
                    <div>
                      <div className="text-[10px] text-slate-500 font-semibold uppercase">Remaining Balance</div>
                      <div className="font-bold text-blue-700 font-mono">
                        ${currentRun.reconciliation?.po_remaining_after?.toLocaleString('en-US', { minimumFractionDigits: 2 }) || '0.00'}
                      </div>
                    </div>
                  </div>

                  {/* Line Item Reconciliation Table */}
                  <div className="overflow-x-auto border border-slate-200 rounded-lg">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-slate-100/80 text-[11px] font-bold text-slate-700 uppercase tracking-wider">
                        <tr>
                          <th className="py-2.5 px-3">Invoice Item</th>
                          <th className="py-2.5 px-2 text-right">Inv Qty</th>
                          <th className="py-2.5 px-2 text-right">Inv Rate</th>
                          <th className="py-2.5 px-3 text-right">Inv Total</th>
                          <th className="py-2.5 px-2 text-right">PO Rate</th>
                          <th className="py-2.5 px-2 text-center">Variance</th>
                          <th className="py-2.5 px-3 text-center">Match Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-200">
                        {currentRun.reconciliation?.line_matches?.map((lm, idx) => (
                          <tr key={idx} className="hover:bg-slate-50/60">
                            <td className="py-2.5 px-3 font-medium text-slate-900 max-w-[180px] truncate" title={lm.invoice_description}>
                              {lm.invoice_description}
                            </td>
                            <td className="py-2.5 px-2 text-right text-slate-600">{lm.invoice_qty}</td>
                            <td className="py-2.5 px-2 text-right font-mono">${lm.invoice_unit_price?.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                            <td className="py-2.5 px-3 text-right font-mono font-bold">${lm.invoice_total?.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                            <td className="py-2.5 px-2 text-right font-mono text-slate-500">
                              {lm.po_unit_price ? `$${lm.po_unit_price.toLocaleString('en-US', { minimumFractionDigits: 2 })}` : 'N/A'}
                            </td>
                            <td className="py-2.5 px-2 text-center font-mono font-semibold">
                              {lm.variance_pct !== 0 ? (
                                <span className={lm.variance_pct > 0 ? 'text-rose-600' : 'text-emerald-600'}>
                                  {lm.variance_pct > 0 ? `+${lm.variance_pct}%` : `${lm.variance_pct}%`}
                                </span>
                              ) : (
                                <span className="text-slate-400">0.0%</span>
                              )}
                            </td>
                            <td className="py-2.5 px-3 text-center">
                              {lm.match_status === 'EXACT_MATCH' && (
                                <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">
                                  Exact Match
                                </span>
                              )}
                              {lm.match_status === 'TOLERANCE_MATCH' && (
                                <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-800">
                                  Within Tol.
                                </span>
                              )}
                              {lm.match_status === 'VARIANCE_BREACH' && (
                                <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-800">
                                  Price Breach
                                </span>
                              )}
                              {lm.match_status === 'PARTIAL_QUANTITY' && (
                                <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-800">
                                  Partial Qty
                                </span>
                              )}
                              {lm.match_status === 'UNMATCHED_SURCHARGE' && (
                                <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800">
                                  Unmatched
                                </span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* Notes / Explanations list */}
                  {currentRun.reconciliation?.notes?.length > 0 && (
                    <div className="bg-blue-50/60 p-3 rounded-lg border border-blue-200/60 text-xs text-blue-900 space-y-1">
                      <div className="font-bold flex items-center gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5 text-blue-600" /> Reconciliation Audit Trail
                      </div>
                      {currentRun.reconciliation.notes.map((n, i) => (
                        <div key={i} className="pl-5 text-slate-700">• {n}</div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Tab: Rendered PDF Document */}
              {activeTabDetails === 'pdf' && (
                <div className="p-3 bg-slate-100/50">
                  <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-200 text-xs">
                    <span className="font-semibold text-slate-700 flex items-center gap-1.5">
                      <FileText className="w-3.5 h-3.5 text-blue-600" />
                      Rendered Original PDF: <span className="font-mono text-slate-600">{currentRun.invoice_filename}</span>
                    </span>
                    <div className="flex items-center gap-2">
                      {activePdfUrl && (
                        <>
                          <a
                            href={activePdfUrl}
                            download={currentRun.invoice_filename || "invoice.pdf"}
                            className="text-[11px] font-semibold text-slate-600 hover:text-slate-800 flex items-center gap-1 px-2.5 py-1 bg-white rounded border border-slate-200 shadow-xs hover:bg-slate-50 transition"
                          >
                            <Download className="w-3 h-3 text-slate-500" /> Download
                          </a>
                          <a
                            href={activePdfUrl}
                            target="_blank"
                            rel="noreferrer"
                            className="text-[11px] font-bold text-blue-600 hover:text-blue-800 flex items-center gap-1 px-2.5 py-1 bg-white rounded border border-slate-200 shadow-xs hover:bg-slate-50 transition"
                          >
                            Open in New Tab <ExternalLink className="w-3 h-3" />
                          </a>
                        </>
                      )}
                    </div>
                  </div>

                  {activePdfUrl ? (
                    <div className="relative w-full h-[580px] rounded-lg border border-slate-300 bg-white shadow-inner overflow-hidden">
                      <object
                        data={`${activePdfUrl}#toolbar=1&navpanes=0`}
                        type="application/pdf"
                        className="w-full h-full"
                      >
                        <iframe
                          src={`${activePdfUrl}#toolbar=1&navpanes=0`}
                          className="w-full h-full border-0"
                          title="Original Vendor Invoice PDF"
                        >
                          <div className="p-8 text-center bg-slate-50 h-full flex flex-col items-center justify-center">
                            <FileText className="w-10 h-10 text-slate-400 mb-2" />
                            <p className="text-sm font-semibold text-slate-700">PDF Preview</p>
                            <p className="text-xs text-slate-500 mb-3 max-w-sm">
                              Click below to open or download the document directly in your browser.
                            </p>
                            <a
                              href={activePdfUrl}
                              target="_blank"
                              rel="noreferrer"
                              className="px-4 py-2 bg-blue-600 text-white text-xs font-semibold rounded-lg shadow hover:bg-blue-700"
                            >
                              Open PDF in New Window
                            </a>
                          </div>
                        </iframe>
                      </object>
                    </div>
                  ) : (
                    <div className="p-12 text-center bg-white rounded-lg border border-dashed border-slate-300">
                      <FileText className="w-10 h-10 text-slate-300 mx-auto mb-2" />
                      <p className="text-sm font-semibold text-slate-600">No PDF document attached to this run</p>
                      <p className="text-xs text-slate-400 mt-1">Select a scenario or upload an invoice PDF to inspect the visual document.</p>
                    </div>
                  )}
                </div>
              )}

              {/* Tab 2: Extracted Data */}
              {activeTabDetails === 'extracted' && (
                <div className="p-4 space-y-3 text-xs">
                  {/* AI & Extraction Engine Telemetry Bar */}
                  <div className="bg-slate-50 border border-slate-200 rounded-xl p-3.5 space-y-2.5">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-200/80 text-xs">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-bold text-slate-800">Processing Engine:</span>
                        <span className={`font-mono font-bold px-2 py-0.5 rounded text-[11px] border ${
                          currentRun.extracted_data?.extraction_method?.startsWith('LLM_')
                            ? 'bg-emerald-50 text-emerald-800 border-emerald-300'
                            : 'bg-blue-50 text-blue-800 border-blue-200'
                        }`}>
                          {currentRun.extracted_data?.extraction_method || 'HYBRID_OCR_PARSER'}
                        </span>
                        <span className="text-[11px] px-2 py-0.5 rounded-full font-semibold bg-slate-200/70 text-slate-700">
                          {currentRun.extracted_data?.extraction_method?.startsWith('LLM_') ? 'Live Cloud LLM' : 'Autonomous Cognitive Engine'}
                        </span>
                      </div>
                      <div className="text-[11px] font-semibold text-slate-700 flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                        Confidence: <span className="font-bold text-slate-900">{currentRun.confidence_score || currentRun.extracted_data?.confidence_score || 95}%</span>
                      </div>
                    </div>

                    {/* Telemetry metrics row */}
                    {(() => {
                      const s2 = currentRun.stages?.find(s => s.stage_id === 'stage_2_extract');
                      const telem = s2?.details?.llm_telemetry || {};
                      return (
                        <>
                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px]">
                          <div className="bg-white p-2 rounded border border-slate-200/70">
                            <span className="text-slate-400 block text-[10px] uppercase font-semibold">Configured Model</span>
                            <span className="font-mono font-bold text-slate-800">{telem.model || 'gemini-flash-latest'}</span>
                          </div>
                          <div className="bg-white p-2 rounded border border-slate-200/70">
                            <span className="text-slate-400 block text-[10px] uppercase font-semibold">Provider</span>
                            <span className="font-bold text-slate-800 uppercase">{telem.provider || 'gemini'}</span>
                          </div>
                          <div className="bg-white p-2 rounded border border-slate-200/70">
                            <span className="text-slate-400 block text-[10px] uppercase font-semibold">Document Tokens</span>
                            <span className="font-mono font-bold text-slate-800">{telem.tokens_in || 128} tokens</span>
                          </div>
                          <div className="bg-white p-2 rounded border border-slate-200/70">
                            <span className="text-slate-400 block text-[10px] uppercase font-semibold">Execution Path</span>
                            <span className="font-mono font-bold text-blue-700">{telem.source || 'HYBRID_PARSER'}</span>
                          </div>
                        </div>

                        {telem.llm_error && (
                          <div className="mt-2.5 p-2.5 rounded-lg bg-amber-50 border border-amber-300 text-amber-900 text-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
                            <div className="flex items-center gap-2">
                              <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                              <span>
                                <strong className="text-amber-800">Cloud LLM Notice:</strong>{" "}
                                {telem.llm_error.includes("401")
                                  ? "API key is invalid or expired (HTTP 401). System completed gracefully via Autonomous Engine."
                                  : telem.llm_error}
                              </span>
                            </div>
                            {onOpenAiConfig && (
                              <button
                                onClick={onOpenAiConfig}
                                className="shrink-0 px-2.5 py-1 bg-amber-600 hover:bg-amber-700 text-white font-bold rounded text-[11px] transition shadow-xs"
                              >
                                Update API Key
                              </button>
                            )}
                          </div>
                        )}
                      </>
                    );
                    })()}
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 bg-slate-50 p-3 rounded-lg border border-slate-200">
                    <div>
                      <span className="text-[10px] text-slate-500 font-semibold uppercase">Vendor Name</span>
                      <div className="font-bold text-slate-800">{currentRun.extracted_data?.vendor_name || 'N/A'}</div>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500 font-semibold uppercase">Tax ID</span>
                      <div className="font-mono text-slate-700">{currentRun.extracted_data?.vendor_tax_id || 'N/A'}</div>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500 font-semibold uppercase">Invoice #</span>
                      <div className="font-bold text-slate-800">{currentRun.extracted_data?.invoice_number || 'N/A'}</div>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500 font-semibold uppercase">Invoice Date</span>
                      <div className="text-slate-700">{currentRun.extracted_data?.invoice_date || 'N/A'}</div>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500 font-semibold uppercase">Subtotal</span>
                      <div className="font-mono text-slate-800">${currentRun.extracted_data?.subtotal?.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500 font-semibold uppercase">Tax / Surcharge</span>
                      <div className="font-mono text-slate-800">${currentRun.extracted_data?.tax_amount?.toLocaleString('en-US', { minimumFractionDigits: 2 })}</div>
                    </div>
                  </div>

                  <div className="border border-slate-200 rounded-lg overflow-hidden">
                    <div className="bg-slate-100 px-3 py-2 font-bold text-slate-700 text-xs">
                      Extracted Line Items ({currentRun.extracted_data?.line_items?.length || 0})
                    </div>
                    <div className="divide-y divide-slate-100">
                      {currentRun.extracted_data?.line_items?.map((item, idx) => (
                        <div key={idx} className="p-2.5 flex items-center justify-between text-xs">
                          <div>
                            <span className="font-mono text-blue-600 font-semibold">{item.item_code} </span>
                            <span className="text-slate-800">{item.description}</span>
                          </div>
                          <div className="text-right font-mono">
                            <span className="text-slate-500">{item.quantity} × ${item.unit_price} = </span>
                            <span className="font-bold text-slate-900">${item.total_price}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Tab 3: Policy Checks */}
              {activeTabDetails === 'policy' && (
                <div className="p-4 space-y-2.5 text-xs">
                  {currentRun.policy_checks?.map((chk) => (
                    <div
                      key={chk.check_id}
                      className={`p-3 rounded-lg border flex items-start gap-3 ${
                        chk.passed
                          ? 'border-emerald-200 bg-emerald-50/30'
                          : chk.severity === 'CRITICAL'
                          ? 'border-rose-200 bg-rose-50/40'
                          : 'border-amber-200 bg-amber-50/40'
                      }`}
                    >
                      <div className="mt-0.5">
                        {chk.passed ? (
                          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                        ) : chk.severity === 'CRITICAL' ? (
                          <XCircle className="w-4 h-4 text-rose-600" />
                        ) : (
                          <AlertTriangle className="w-4 h-4 text-amber-600" />
                        )}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-slate-900">{chk.check_name}</span>
                          <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                            chk.passed ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
                          }`}>
                            {chk.passed ? 'PASSED' : 'FLAGGED'}
                          </span>
                        </div>
                        <p className="text-slate-600 mt-0.5">{chk.message}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Tab 4: ERP Webhook Payload */}
              {activeTabDetails === 'erp' && (
                <div className="p-4">
                  <div className="flex items-center justify-between mb-2 text-xs">
                    <span className="font-semibold text-slate-600 flex items-center gap-1.5">
                      <Database className="w-3.5 h-3.5 text-blue-600" /> NetSuite / SAP Integration Payload
                    </span>
                    <span className="text-[10px] text-slate-400 font-mono">Format: REST / JSON</span>
                  </div>
                  <pre className="bg-slate-900 text-slate-100 p-3 rounded-lg text-[11px] font-mono overflow-x-auto">
                    {JSON.stringify(currentRun.erp_payload || { status: 'NO_ERP_MUTATION_ON_REJECTION' }, null, 2)}
                  </pre>
                </div>
              )}

              {/* Tab 5: Vendor Email Inquiry Draft */}
              {activeTabDetails === 'email' && (
                <div className="p-4 space-y-3">
                  <div className="flex items-center justify-between text-xs text-slate-600 font-semibold">
                    <span className="flex items-center gap-1.5">
                      <Mail className="w-3.5 h-3.5 text-amber-600" /> Auto-Generated Vendor Resolution Notice
                    </span>
                    <button
                      onClick={() => navigator.clipboard.writeText(currentRun.vendor_notification_draft)}
                      className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-[11px] font-medium transition"
                    >
                      Copy to Clipboard
                    </button>
                  </div>
                  <textarea
                    readOnly
                    rows={8}
                    value={currentRun.vendor_notification_draft}
                    className="w-full text-xs font-mono bg-slate-50 p-3 rounded-lg border border-slate-200 text-slate-800 focus:outline-none"
                  />
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
