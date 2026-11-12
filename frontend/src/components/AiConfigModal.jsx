import React, { useState, useEffect } from 'react';
import { X, Sparkles, Key, Check, ShieldCheck, Cpu } from 'lucide-react';

export default function AiConfigModal({ isOpen, onClose, onConfigSaved }) {
  const [provider, setProvider] = useState('gemini');
  const [apiKey, setApiKey] = useState('');
  const [modelName, setModelName] = useState('gemini-1.5-flash');
  const [currentConfig, setCurrentConfig] = useState(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (isOpen) {
      fetch('/api/llm/config')
        .then(res => res.json())
        .then(data => {
          setCurrentConfig(data);
          setProvider(data.provider || 'gemini');
          setModelName(data.model_name || 'gemini-1.5-flash');
        })
        .catch(err => console.error("Error loading LLM config:", err));
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setMessage('');
    try {
      const res = await fetch('/api/llm/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider,
          api_key: apiKey,
          model_name: modelName
        })
      });
      const data = await res.json();
      setCurrentConfig(data);
      setMessage("AI configuration updated successfully!");
      if (onConfigSaved) onConfigSaved(data);
      setTimeout(() => {
        setMessage('');
        onClose();
      }, 1200);
    } catch (err) {
      console.error("Save config error:", err);
      setMessage("Error saving AI configuration.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-md w-full overflow-hidden border border-slate-200">
        <div className="flex items-center justify-between p-4 border-b border-slate-200 bg-slate-50">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-blue-600" />
            <h3 className="text-sm font-bold text-slate-900">
              AI Cognitive Engine Configuration
            </h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSave} className="p-5 space-y-4 text-xs">
          {/* Active status info */}
          <div className="bg-blue-50/70 p-3 rounded-lg border border-blue-200/80 space-y-1">
            <div className="flex items-center justify-between">
              <span className="font-bold text-blue-900 flex items-center gap-1.5">
                <Cpu className="w-4 h-4 text-blue-600" /> Active AI Mode:
              </span>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-100 text-blue-800">
                {currentConfig?.status || 'AUTONOMOUS'}
              </span>
            </div>
            <p className="text-[11px] text-blue-800/90 leading-relaxed mt-1">
              The engine combines optical OCR tokenization with LLM semantic reasoning. Connect your own Google Gemini or OpenAI API key, or use the zero-config Autonomous mode.
            </p>
          </div>

          {/* Provider Selector */}
          <div>
            <label className="block font-bold text-slate-700 mb-1.5">Select AI Model Provider:</label>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => { setProvider('gemini'); setModelName('gemini-1.5-flash'); }}
                className={`p-2.5 rounded-lg border text-center transition ${
                  provider === 'gemini'
                    ? 'border-blue-600 bg-blue-50/60 font-bold text-blue-700 ring-1 ring-blue-500'
                    : 'border-slate-200 hover:bg-slate-50 text-slate-600'
                }`}
              >
                Google Gemini
              </button>
              <button
                type="button"
                onClick={() => { setProvider('openai'); setModelName('gpt-4o'); }}
                className={`p-2.5 rounded-lg border text-center transition ${
                  provider === 'openai'
                    ? 'border-blue-600 bg-blue-50/60 font-bold text-blue-700 ring-1 ring-blue-500'
                    : 'border-slate-200 hover:bg-slate-50 text-slate-600'
                }`}
              >
                OpenAI
              </button>
              <button
                type="button"
                onClick={() => { setProvider('autonomous'); setModelName('autonomous-agent'); setApiKey(''); }}
                className={`p-2.5 rounded-lg border text-center transition ${
                  provider === 'autonomous'
                    ? 'border-emerald-600 bg-emerald-50/60 font-bold text-emerald-800 ring-1 ring-emerald-500'
                    : 'border-slate-200 hover:bg-slate-50 text-slate-600'
                }`}
              >
                Autonomous
              </button>
            </div>
          </div>

          {/* Model Name */}
          {provider !== 'autonomous' && (
            <div>
              <label className="block font-bold text-slate-700 mb-1">Model Name:</label>
              <select
                value={modelName}
                onChange={(e) => setModelName(e.target.value)}
                className="w-full text-xs p-2 border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                {provider === 'gemini' ? (
                  <>
                    <option value="gemini-flash-lite-latest">Gemini Flash Lite (Fastest, High Throughput)</option>
                    <option value="gemini-flash-latest">Gemini Flash (Standard)</option>
                    <option value="gemini-1.5-flash">Gemini 1.5 Flash</option>
                    <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
                  </>
                ) : (
                  <>
                    <option value="gpt-4o">GPT-4o (Flagship Multimodal)</option>
                    <option value="gpt-4o-mini">GPT-4o Mini (Fast & Cost-Efficient)</option>
                  </>
                )}
              </select>
            </div>
          )}

          {/* API Key Input */}
          {provider !== 'autonomous' && (
            <div>
              <label className="block font-bold text-slate-700 mb-1 flex items-center justify-between">
                <span>API Key:</span>
                {currentConfig?.masked_key && currentConfig.masked_key !== 'None' && (
                  <span className="text-[10px] text-emerald-600 font-mono font-semibold">
                    Current: {currentConfig.masked_key}
                  </span>
                )}
              </label>
              <div className="relative">
                <Key className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
                <input
                  type="password"
                  placeholder={provider === 'gemini' ? "AIzaSy..." : "sk-..."}
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  className="w-full text-xs pl-8 pr-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500 font-mono"
                />
              </div>
              <div className="text-[10px] text-slate-500 mt-1.5 flex items-center justify-between">
                <span>Credentials persist in your local <code className="font-mono text-blue-700 bg-blue-50 px-1 py-0.5 rounded">.env</code> file across all sessions.</span>
                <span className="text-[10px] text-emerald-600 font-semibold flex items-center gap-1">
                  <ShieldCheck className="w-3 h-3" /> Auto-persisted
                </span>
              </div>
            </div>
          )}

          {message && (
            <div className="p-2 bg-emerald-50 text-emerald-800 rounded text-center text-xs font-semibold flex items-center justify-center gap-1.5">
              <Check className="w-3.5 h-3.5" /> {message}
            </div>
          )}

          {/* Buttons */}
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
              disabled={saving}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg shadow-sm transition disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save AI Configuration'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
