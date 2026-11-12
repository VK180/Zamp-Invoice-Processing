import React from 'react';
import { Video, Award, CheckCircle, ShieldAlert, BookOpen, HelpCircle, Sparkles } from 'lucide-react';

export default function DemoGuideView() {
  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-blue-900 to-indigo-950 text-white p-6 rounded-xl shadow-md">
        <div className="flex items-center gap-2.5 text-blue-300 text-xs font-bold uppercase tracking-wider mb-1">
          <Award className="w-4 h-4" /> AI Solutions Analyst — Placement Showcase
        </div>
        <h2 className="text-xl font-extrabold text-white">
          Zamp Problem Statement 1: Complete Operational Guide & Video Script
        </h2>
        <p className="text-xs text-blue-100/90 mt-1 max-w-2xl leading-relaxed">
          Everything you need to deliver a top-tier 5-minute Loom demo and ace the live interview with Zamp hiring partners.
        </p>
      </div>

      {/* Script Timeline Section (Deliverable 2) */}
      <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <Video className="w-5 h-5 text-blue-600" />
            <h3 className="text-sm font-bold text-slate-900">
              5-Minute Demo Video Script (Second-by-Second Playbook)
            </h3>
          </div>
          <span className="text-xs font-bold text-blue-600 bg-blue-50 px-2.5 py-0.5 rounded-full border border-blue-200">
            Target Duration: 4m 45s
          </span>
        </div>

        <div className="space-y-4 text-xs">
          {/* 0:00 - 0:45 */}
          <div className="p-3.5 rounded-lg border border-slate-200 bg-slate-50/70">
            <div className="flex items-center justify-between font-bold text-slate-800 mb-1">
              <span className="text-blue-700">0:00 – 0:45 | The Problem & Architecture Overview</span>
              <span className="text-slate-400 font-mono">Intro</span>
            </div>
            <p className="text-slate-600 leading-relaxed mb-2">
              <b>What to say:</b> "Hi everyone! I’m presenting my solution for Zamp’s PS-1: Accounts Payable Invoice Intelligence. Mid-sized companies receive hundreds of PDF invoices monthly. Tired AP staff waste hours comparing numbers against purchase orders in spreadsheets, leading to expensive mistakes: overpaying price increases, duplicate disbursements, or paying unapproved vendors."
            </p>
            <p className="text-slate-600 leading-relaxed">
              <b>What to show:</b> Show the Live Run Studio interface with the 6-stage telemetry stepper and the 1-click test scenarios bar.
            </p>
          </div>

          {/* 0:45 - 1:45 */}
          <div className="p-3.5 rounded-lg border border-slate-200 bg-slate-50/70">
            <div className="flex items-center justify-between font-bold text-slate-800 mb-1">
              <span className="text-blue-700">0:45 – 1:45 | Happy Path Run (Clean 2-Way Match)</span>
              <span className="text-slate-400 font-mono">Scenario 1</span>
            </div>
            <p className="text-slate-600 leading-relaxed mb-2">
              <b>What to say:</b> "Let’s start with the happy path. I click 'Happy Path: Apex Software'. Watch the live stepper: it ingests the PDF, extracts the line items and metadata, authenticates the vendor in our ERP Vendor Master, reconciles the line items against PO-2026-101, validates tolerance and duplicate checks, and outputs an AUTO-APPROVED verdict with confidence 99%."
            </p>
            <p className="text-slate-600 leading-relaxed">
              <b>What to show:</b> Point to the green decision badge, the Line Item Reconciliation table showing exact matches, and the ERP JSON webhook payload generated for NetSuite.
            </p>
          </div>

          {/* 1:45 - 2:45 */}
          <div className="p-3.5 rounded-lg border border-slate-200 bg-slate-50/70">
            <div className="flex items-center justify-between font-bold text-slate-800 mb-1">
              <span className="text-blue-700">1:45 – 2:45 | Edge Case 1: Unit Price Inflation & Tolerance Breach</span>
              <span className="text-slate-400 font-mono">Scenario 2</span>
            </div>
            <p className="text-slate-600 leading-relaxed mb-2">
              <b>What to say:</b> "Now, what happens on a Friday afternoon when a vendor quietly hikes prices? I run Edge Case 1: CloudScale. The vendor billed compute instances at $1,400 instead of our contracted $1,200—a +16.7% hike resulting in a $800 breach over our PO’s 2% tolerance limit. Notice the system doesn’t crash or blindly pay: it halts, flags REVIEW REQUIRED, highlights the exact line variance in red, and auto-generates a ready-to-send dispute email to the vendor."
            </p>
            <p className="text-slate-600 leading-relaxed">
              <b>What to show:</b> Show the red 'Price Breach' tag in the line item table and switch to the 'Vendor Inquiry Draft' tab showing the auto-generated email.
            </p>
          </div>

          {/* 2:45 - 3:30 */}
          <div className="p-3.5 rounded-lg border border-slate-200 bg-slate-50/70">
            <div className="flex items-center justify-between font-bold text-slate-800 mb-1">
              <span className="text-blue-700">2:45 – 3:30 | Edge Case 2 & 3: Split POs & Duplicate Fraud Detection</span>
              <span className="text-slate-400 font-mono">Scenarios 3 & 4</span>
            </div>
            <p className="text-slate-600 leading-relaxed mb-2">
              <b>What to say:</b> "In real operations, vendors split POs across multiple shipments. I trigger Edge Case 2: Global Freight. The invoice is $5,000 against a $15,000 master PO. The engine auto-approves and updates the remaining balance in ERP to $10,000. Next, I trigger Edge Case 3: CyberGuard. This vendor resubmitted an invoice that was already settled last month. Our historical ledger catches it instantly, rejecting the $6,000 duplicate before a penny leaves the account."
            </p>
            <p className="text-slate-600 leading-relaxed">
              <b>What to show:</b> Show the updated remaining balance, then run Scenario 4 to show the immediate REJECTED banner with duplicate transaction ID reference.
            </p>
          </div>

          {/* 3:30 - 4:45 */}
          <div className="p-3.5 rounded-lg border border-slate-200 bg-slate-50/70">
            <div className="flex items-center justify-between font-bold text-slate-800 mb-1">
              <span className="text-blue-700">3:30 – 4:45 | Dashboard & Human-in-the-Loop Override</span>
              <span className="text-slate-400 font-mono">Conclusion</span>
            </div>
            <p className="text-slate-600 leading-relaxed mb-2">
              <b>What to say:</b> "Finally, switching to our AP Operations Dashboard: CFOs and controllers get real-time visibility into auto-approval rates, total spend disbursed, and fraud prevented. If an AP Specialist receives manager sign-off for that CloudScale price hike, they simply click 'Review', enter the audit authorization, and commit the override directly to ERP. Thank you!"
            </p>
            <p className="text-slate-600 leading-relaxed">
              <b>What to show:</b> Switch to DashboardView, show the metrics cards, open the ReviewModal, type an override note, and show the status change to Approved.
            </p>
          </div>
        </div>
      </div>

      {/* Edge Cases Deep Dive Table */}
      <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-sm space-y-3">
        <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-blue-600" />
          The Edge Case Matrix Built Into This System
        </h3>
        <p className="text-xs text-slate-500">
          The case study notes: <i>"The edge cases you choose tell us how well you understand the problem."</i> Here is how our architecture addresses realistic operational friction:
        </p>

        <div className="overflow-x-auto border border-slate-200 rounded-lg text-xs mt-3">
          <table className="w-full text-left">
            <thead className="bg-slate-50 text-[11px] font-bold text-slate-600 uppercase border-b border-slate-200">
              <tr>
                <th className="py-2.5 px-3">Scenario</th>
                <th className="py-2.5 px-3">Operational Complexity</th>
                <th className="py-2.5 px-3">Technical Handling</th>
                <th className="py-2.5 px-3">Outcome</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              <tr>
                <td className="py-2.5 px-3 font-bold text-slate-900">1. Happy Path</td>
                <td className="py-2.5 px-3 text-slate-600">Standard clean invoice matching agreed PO contract.</td>
                <td className="py-2.5 px-3 text-slate-600">2-way matching on unit price and line totals.</td>
                <td className="py-2.5 px-3 font-semibold text-emerald-700">AUTO-APPROVED (100% Match)</td>
              </tr>
              <tr>
                <td className="py-2.5 px-3 font-bold text-slate-900">2. Price Breach</td>
                <td className="py-2.5 px-3 text-slate-600">Vendor raised unit rate by 16.7%, invoice +$800 over PO.</td>
                <td className="py-2.5 px-3 text-slate-600">Tolerance threshold check: breaches 2.0% limit. Red flags item.</td>
                <td className="py-2.5 px-3 font-semibold text-amber-700">REVIEW REQUIRED + Dispute Email</td>
              </tr>
              <tr>
                <td className="py-2.5 px-3 font-bold text-slate-900">3. Split PO / Partial</td>
                <td className="py-2.5 px-3 text-slate-600">Vendor bills partial shipment ($5k of $15k PO).</td>
                <td className="py-2.5 px-3 text-slate-600">Dynamic balance tracking. PO remaining balance decremented.</td>
                <td className="py-2.5 px-3 font-semibold text-blue-700">AUTO-APPROVED ($10k PO Remaining)</td>
              </tr>
              <tr>
                <td className="py-2.5 px-3 font-bold text-slate-900">4. Duplicate Resubmission</td>
                <td className="py-2.5 px-3 text-slate-600">Vendor resubmits previously settled invoice #INV-CG-9942.</td>
                <td className="py-2.5 px-3 text-slate-600">Duplicate detection registry queries invoice #, vendor, and amount.</td>
                <td className="py-2.5 px-3 font-semibold text-rose-700">REJECTED (Saves $6,000 double payout)</td>
              </tr>
              <tr>
                <td className="py-2.5 px-3 font-bold text-slate-900">5. Rogue Spend</td>
                <td className="py-2.5 px-3 text-slate-600">Unknown vendor, missing PO reference, unapproved spend.</td>
                <td className="py-2.5 px-3 text-slate-600">ERP Vendor Master check fails; halts unbudgeted disbursement.</td>
                <td className="py-2.5 px-3 font-semibold text-rose-700">REJECTED (Compliance Hold)</td>
              </tr>
              <tr>
                <td className="py-2.5 px-3 font-bold text-slate-900">6. Tolerance Absorption</td>
                <td className="py-2.5 px-3 text-slate-600">Minor ground shipping surcharge of $18.50 on $3,250 order.</td>
                <td className="py-2.5 px-3 text-slate-600">Variance of 0.57% is &lt; 2.0% tolerance limit.</td>
                <td className="py-2.5 px-3 font-semibold text-emerald-700">AUTO-APPROVED (Audit Note Logged)</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Interview Q&A Section */}
      <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-sm space-y-3">
        <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
          <HelpCircle className="w-4 h-4 text-blue-600" />
          Zamp Interview Q&A Cheatsheet
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs pt-1">
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
            <div className="font-bold text-slate-900 mb-1">Q: Why not let the LLM make the financial decision directly?</div>
            <p className="text-slate-600 leading-relaxed">
              <b>A:</b> In enterprise finance, LLMs should be used for <i>unstructured perception</i> (extracting messy text, handling differing layouts), but never for <i>deterministic execution</i>. Dollar math, duplicate checks, and tolerance bounds must be enforced by verified deterministic rules to eliminate hallucinations and ensure 100% audit compliance.
            </p>
          </div>

          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
            <div className="font-bold text-slate-900 mb-1">Q: How does this scale to 50,000 invoices/month?</div>
            <p className="text-slate-600 leading-relaxed">
              <b>A:</b> The ingestion and OCR extraction are asynchronous worker tasks (e.g. Celery / SQS). Rule evaluation runs in &lt;10ms per invoice in memory. High-confidence happy paths (~70-80%) auto-disburse straight to ERP, while human AP analysts only touch the 20% exception queue.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
