'use client';

import React, { useEffect, useState } from 'react';
import { apiFetch } from '../lib/auth';
import { CheckCircleIcon, XCircleIcon } from '@heroicons/react/24/outline';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8001';

type ModelOption = { id: string; label: string; provider: string };

type AgentDef = {
  provider: string;
  name: string;
  description: string;
  models: string[];
  docsUrl: string;
};

const AGENT_DEFS: AgentDef[] = [
  {
    provider: 'ollama',
    name: 'Ollama (Local)',
    description: 'Locally-hosted open-source models via Ollama. No API key required — runs entirely on the VM.',
    models: [],
    docsUrl: 'https://ollama.com',
  },
  {
    provider: 'openai',
    name: 'OpenAI',
    description: 'GPT-4o and GPT-3.5 models via the OpenAI API. Set OPENAI_API_KEY in .env to enable.',
    models: ['gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo'],
    docsUrl: 'https://platform.openai.com',
  },
  {
    provider: 'anthropic',
    name: 'Anthropic',
    description: 'Claude 3.5 models via the Anthropic API. Set ANTHROPIC_API_KEY in .env to enable.',
    models: ['claude-3-5-haiku-20241022', 'claude-3-5-sonnet-20241022'],
    docsUrl: 'https://console.anthropic.com',
  },
  {
    provider: 'gemini',
    name: 'Google Gemini',
    description: 'Gemini 2.0 models via the Google GenAI API. Set GOOGLE_API_KEY in .env to enable.',
    models: ['gemini-2.0-flash', 'gemini-2.0-flash-lite'],
    docsUrl: 'https://aistudio.google.com',
  },
  {
    provider: 'groq',
    name: 'Groq',
    description: 'Fast inference for open-source models via the Groq API. Set GROQ_API_KEY in .env to enable.',
    models: ['llama-3.3-70b-versatile', 'llama-3.1-8b-instant'],
    docsUrl: 'https://console.groq.com',
  },
];

const PROVIDER_COLOURS: Record<string, string> = {
  ollama: 'border-cyan-500/30 bg-cyan-400/5',
  openai: 'border-green-500/30 bg-green-400/5',
  anthropic: 'border-purple-500/30 bg-purple-400/5',
  gemini: 'border-yellow-500/30 bg-yellow-400/5',
  groq: 'border-orange-500/30 bg-orange-400/5',
};

const PROVIDER_BADGE: Record<string, string> = {
  ollama: 'text-cyan-400 bg-cyan-400/10 border-cyan-500/30',
  openai: 'text-green-400 bg-green-400/10 border-green-500/30',
  anthropic: 'text-purple-400 bg-purple-400/10 border-purple-500/30',
  gemini: 'text-yellow-400 bg-yellow-400/10 border-yellow-500/30',
  groq: 'text-orange-400 bg-orange-400/10 border-orange-500/30',
};

export default function AIAgentsPanel() {
  const [activeProviders, setActiveProviders] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch(`${API_BASE}/ai/models`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d: { models: ModelOption[] } | null) => {
        if (d?.models) {
          setActiveProviders(new Set(d.models.map((m) => m.provider)));
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-slate-100">AI Agents</h2>
        <p className="text-sm text-slate-400 mt-0.5">
          Provider adapters registered in CyberOracle. All queries are routed through the DLP pipeline regardless of provider.
        </p>
      </div>

      {loading && <div className="text-sm text-slate-500">Loading…</div>}

      {!loading && (
        <div className="grid grid-cols-1 gap-4">
          {AGENT_DEFS.map((agent) => {
            const active = activeProviders.has(agent.provider);
            return (
              <div
                key={agent.provider}
                className={`rounded-xl border p-5 ${PROVIDER_COLOURS[agent.provider] ?? 'border-slate-700 bg-slate-800/50'}`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-sm font-semibold px-2 py-0.5 rounded border ${PROVIDER_BADGE[agent.provider] ?? 'text-slate-300 border-slate-700'}`}>
                        {agent.name}
                      </span>
                      {active ? (
                        <span className="flex items-center gap-1 text-xs text-green-400">
                          <CheckCircleIcon className="w-3.5 h-3.5" /> Active
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 text-xs text-slate-500">
                          <XCircleIcon className="w-3.5 h-3.5" /> Not configured
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-slate-400 mt-1">{agent.description}</p>
                    {agent.models.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mt-3">
                        {agent.models.map((m) => (
                          <span key={m} className="font-mono text-xs px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-400">
                            {m}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
