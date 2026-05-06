'use client';

import React, { useEffect, useState } from 'react';
import { apiFetch } from '../lib/auth';
import { ArrowPathIcon, CpuChipIcon } from '@heroicons/react/24/outline';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8001';

type ModelOption = {
  id: string;
  label: string;
  provider: string;
};

const PROVIDER_COLOURS: Record<string, string> = {
  ollama: 'text-cyan-400 bg-cyan-400/10 border-cyan-500/30',
  openai: 'text-green-400 bg-green-400/10 border-green-500/30',
  anthropic: 'text-purple-400 bg-purple-400/10 border-purple-500/30',
  gemini: 'text-yellow-400 bg-yellow-400/10 border-yellow-500/30',
  groq: 'text-orange-400 bg-orange-400/10 border-orange-500/30',
};

const PROVIDER_LABELS: Record<string, string> = {
  ollama: 'Ollama',
  openai: 'OpenAI',
  anthropic: 'Anthropic',
  gemini: 'Google Gemini',
  groq: 'Groq',
};

export default function AIModelsPanel() {
  const [models, setModels] = useState<ModelOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  function fetchModels() {
    setLoading(true);
    setError(null);
    apiFetch(`${API_BASE}/ai/models`)
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d) => setModels(d.models ?? []))
      .catch(() => setError('Failed to load models.'))
      .finally(() => setLoading(false));
  }

  useEffect(() => { fetchModels(); }, []);

  const byProvider = models.reduce<Record<string, ModelOption[]>>((acc, m) => {
    if (!acc[m.provider]) acc[m.provider] = [];
    acc[m.provider].push(m);
    return acc;
  }, {});

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-100">AI Models</h2>
          <p className="text-sm text-slate-400 mt-0.5">
            Models available in this deployment. Add an API key to <code className="text-cyan-400 bg-slate-800 px-1 rounded text-xs">.env</code> to enable a provider.
          </p>
        </div>
        <button
          onClick={fetchModels}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm transition"
        >
          <ArrowPathIcon className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {loading && !error && (
        <div className="text-sm text-slate-500">Loading models…</div>
      )}

      {!loading && !error && models.length === 0 && (
        <div className="rounded-lg border border-slate-700 bg-slate-800/50 px-6 py-10 text-center">
          <CpuChipIcon className="w-10 h-10 text-slate-600 mx-auto mb-3" />
          <p className="text-slate-400 text-sm">No models configured.</p>
        </div>
      )}

      {!loading && Object.entries(byProvider).map(([provider, providerModels]) => (
        <div key={provider} className="rounded-xl border border-slate-700 bg-slate-900 overflow-hidden">
          <div className={`px-5 py-3 border-b border-slate-700 flex items-center gap-2 ${PROVIDER_COLOURS[provider] ?? 'text-slate-300'}`}>
            <span className="text-xs font-bold uppercase tracking-widest">
              {PROVIDER_LABELS[provider] ?? provider}
            </span>
            <span className="ml-auto text-xs font-medium px-2 py-0.5 rounded-full bg-green-500/10 text-green-400 border border-green-500/20">
              Active
            </span>
          </div>
          <div className="divide-y divide-slate-800">
            {providerModels.map((m) => (
              <div key={m.id} className="flex items-center justify-between px-5 py-3">
                <div>
                  <p className="text-sm font-medium text-slate-100">{m.label}</p>
                  <p className="text-xs text-slate-500 font-mono mt-0.5">{m.id}</p>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded border ${PROVIDER_COLOURS[provider] ?? 'text-slate-400 border-slate-700'}`}>
                  {provider}
                </span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
