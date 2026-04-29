'use client';

import React, { useEffect, useMemo, useRef, useState } from 'react';
import { ArrowPathIcon, XMarkIcon } from '@heroicons/react/24/outline';

type PolicyDecision = 'allow' | 'redact' | 'block';

type BackendSecurity = {
  risk_score?: number;
  policy_decision?: PolicyDecision;
  rules_triggered?: string[];
  redactions?: { type: string; count: number }[];
  blocked_reason?: string | null;
  phase?: 'input' | 'output';
};

type BackendOutput = {
  text?: string;
  redacted?: boolean;
  blocked?: boolean;
};

type QueryResponse = {
  request_id?: string;
  model?: string;
  output?: BackendOutput;
  security?: BackendSecurity;
  meta?: {
    latency_ms?: number;
    timestamp?: string;
  };
};

type ChatMessage = {
  id: string;
  role: 'user' | 'assistant';
  text: string;
  timestamp: string;
  security?: BackendSecurity;
};

type Conversation = {
  id: string;
  title: string;
  modelId: string;
  hideSensitive: boolean;
  createdAt: string;
  updatedAt: string;
  messages: ChatMessage[];
};

type ModelOption = {
  id: string;
  label: string;
  provider: string;
};

// Provider badge colours
const PROVIDER_COLOURS: Record<string, string> = {
  ollama: 'text-cyan-400',
  openai: 'text-green-400',
  anthropic: 'text-purple-400',
  gemini: 'text-yellow-400',
  groq: 'text-orange-400',
};

import { apiFetch } from '../lib/auth';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8001';
const STORAGE_KEY = 'cyberoracle_secure_chat_conversations_v2';
const RATE_LIMIT_WINDOW_SECONDS = 60;
const MAX_PROMPT_LENGTH = 8000;

const FALLBACK_MODEL: ModelOption = {
  id: 'ollama:llama3.2:1b',
  label: 'Ollama (llama3.2:1b)',
  provider: 'ollama',
};

function Spinner({ className }: { className?: string }) {
  return <ArrowPathIcon className={`animate-spin text-cyan-400 ${className ?? 'w-5 h-5'}`} />;
}

function maskSensitiveUI(text: string): string {
  if (!text) return text;
  text = text.replace(
    /[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}/g,
    '[EMAIL_REDACTED]'
  );
  text = text.replace(/\b\d{3}[- ]?\d{2}[- ]?\d{4}\b/g, '[SSN_REDACTED]');
  text = text.replace(/\b(?:\d[ -]*?){13,16}\b/g, '[CARD_REDACTED]');
  text = text.replace(/(?:sk-|AKIA)[0-9A-Za-z]{10,}/g, '[API_KEY_REDACTED]');
  return text;
}

function formatTime(tsIso: string) {
  try {
    const d = new Date(tsIso);
    return d.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
  } catch {
    return '';
  }
}

function makeTitleFromFirstUserMessage(messages: ChatMessage[]) {
  const firstUser = messages.find((m) => m.role === 'user');
  if (!firstUser?.text) return 'New chat';
  const t = firstUser.text.trim().replace(/\s+/g, ' ');
  return t.length > 32 ? t.slice(0, 32) + '…' : t;
}

function createEmptyConversation(id?: string, modelId?: string): Conversation {
  const now = new Date().toISOString();
  return {
    id: id ?? crypto.randomUUID(),
    title: 'New chat',
    modelId: modelId ?? FALLBACK_MODEL.id,
    hideSensitive: true,
    createdAt: now,
    updatedAt: now,
    messages: [],
  };
}

function providerLabel(provider: string): string {
  const map: Record<string, string> = {
    ollama: 'Ollama',
    openai: 'OpenAI',
    anthropic: 'Anthropic',
    gemini: 'Google',
    groq: 'Groq',
  };
  return map[provider] ?? provider;
}

export default function SecureChatPanel() {
  const [availableModels, setAvailableModels] = useState<ModelOption[]>([FALLBACK_MODEL]);
  const [selectedModelId, setSelectedModelId] = useState<string>(FALLBACK_MODEL.id);

  const [prompt, setPrompt] = useState('');
  const [hideSensitive, setHideSensitive] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [rateLimited, setRateLimited] = useState(false);
  const [retryAfter, setRetryAfter] = useState(0);

  const [conversations, setConversations] = useState<Conversation[]>(() => [
    createEmptyConversation(undefined, FALLBACK_MODEL.id),
  ]);
  const [activeConvId, setActiveConvId] = useState<string>(() => crypto.randomUUID());
  const [historyOpen, setHistoryOpen] = useState(false);

  const scrollRef = useRef<HTMLDivElement | null>(null);

  // Fetch available models from the backend on mount
  useEffect(() => {
    apiFetch(`${API_BASE}/ai/models`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data?.models?.length) {
          setAvailableModels(data.models as ModelOption[]);
          setSelectedModelId((prev) => {
            const stillValid = data.models.some((m: ModelOption) => m.id === prev);
            return stillValid ? prev : data.models[0].id;
          });
        }
      })
      .catch(() => {
        // Keep fallback model list on network error
      });
  }, []);

  useEffect(() => {
    setConversations((prev) => {
      if (prev.some((c) => c.id === activeConvId)) return prev;
      return [createEmptyConversation(activeConvId, selectedModelId)];
    });
  }, [activeConvId]); // eslint-disable-line

  const activeConversation = useMemo(
    () => conversations.find((c) => c.id === activeConvId) ?? null,
    [conversations, activeConvId]
  );

  const messages = activeConversation?.messages ?? [];

  const lastAssistant = useMemo(
    () => [...messages].reverse().find((m) => m.role === 'assistant'),
    [messages]
  );

  const decision: PolicyDecision = lastAssistant?.security?.policy_decision ?? 'allow';
  const risk = lastAssistant?.security?.risk_score ?? 0;

  // Restore conversations from localStorage
  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as Conversation[];
        if (Array.isArray(parsed) && parsed.length > 0) {
          setConversations(parsed);
          setActiveConvId(parsed[0].id);
          setHideSensitive(!!parsed[0].hideSensitive);
          setSelectedModelId(parsed[0].modelId ?? FALLBACK_MODEL.id);
          return;
        }
      }
    } catch {
      // ignore
    }
    setConversations((prev) =>
      prev.length > 0 ? prev : [createEmptyConversation(activeConvId, selectedModelId)]
    );
  }, []); // eslint-disable-line

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
    } catch {
      // ignore
    }
  }, [conversations]);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
  }, [messages.length, historyOpen]);

  function updateActiveConversation(patch: Partial<Conversation>) {
    setConversations((prev) =>
      prev.map((c) => {
        if (c.id !== activeConvId) return c;
        const updated: Conversation = {
          ...c,
          ...patch,
          updatedAt: new Date().toISOString(),
        };
        if (updated.messages.length > 0) {
          updated.title = makeTitleFromFirstUserMessage(updated.messages);
        }
        return updated;
      })
    );
  }

  function ensureActiveConversationExists() {
    setConversations((prev) => {
      if (prev.some((c) => c.id === activeConvId)) return prev;
      return [createEmptyConversation(activeConvId, selectedModelId), ...prev];
    });
  }

  function newChat() {
    const conv = createEmptyConversation(undefined, selectedModelId);
    conv.hideSensitive = hideSensitive;
    setConversations((prev) => [conv, ...prev]);
    setActiveConvId(conv.id);
    setHistoryOpen(false);
    setPrompt('');
    setError(null);
  }

  function loadConversation(id: string) {
    const conv = conversations.find((c) => c.id === id);
    if (!conv) return;
    setActiveConvId(id);
    setHideSensitive(!!conv.hideSensitive);
    setSelectedModelId(conv.modelId ?? FALLBACK_MODEL.id);
    setHistoryOpen(false);
    setError(null);
  }

  function deleteConversation(id: string) {
    setConversations((prev) => prev.filter((c) => c.id !== id));
    if (activeConvId === id) {
      const remaining = conversations.filter((c) => c.id !== id);
      if (remaining.length > 0) setActiveConvId(remaining[0].id);
      else {
        const fresh = createEmptyConversation(undefined, selectedModelId);
        setConversations([fresh]);
        setActiveConvId(fresh.id);
      }
    }
  }

  function handleModelChange(newModelId: string) {
    setSelectedModelId(newModelId);
    updateActiveConversation({ modelId: newModelId });
  }

  async function send() {
    if (!prompt.trim() || loading || rateLimited) return;

    if (prompt.length > MAX_PROMPT_LENGTH) {
      setError(`Message too long. Maximum ${MAX_PROMPT_LENGTH.toLocaleString()} characters.`);
      return;
    }

    ensureActiveConversationExists();
    setLoading(true);
    setError(null);

    const userText = prompt;
    setPrompt('');

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      text: userText,
      timestamp: new Date().toISOString(),
    };

    setConversations((prev) =>
      prev.map((c) => {
        if (c.id !== activeConvId) return c;
        const updatedMessages = [...c.messages, userMessage];
        return {
          ...c,
          hideSensitive,
          modelId: selectedModelId,
          updatedAt: new Date().toISOString(),
          messages: updatedMessages,
          title: makeTitleFromFirstUserMessage(updatedMessages),
        };
      })
    );

    try {
      const r = await apiFetch(`${API_BASE}/ai/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: userText, model: selectedModelId }),
      });

      if (r.status === 429) {
        setRateLimited(true);
        setPrompt(userText);
        setError('Rate limit reached. You can send again when the timer expires.');

        let seconds = RATE_LIMIT_WINDOW_SECONDS;
        setRetryAfter(seconds);

        const interval = setInterval(() => {
          seconds -= 1;
          setRetryAfter(seconds);
          if (seconds <= 0) {
            clearInterval(interval);
            setRateLimited(false);
            setError(null);
          }
        }, 1000);

        return;
      }

      if (!r.ok) {
        console.error(`Backend error ${r.status}`);
        if (r.status === 502 || r.status === 503) {
          throw new Error('AI model is unavailable. Please try again in a moment.');
        }
        if (r.status >= 500) {
          throw new Error('A server error occurred. Please try again.');
        }
        throw new Error(`Request failed (${r.status}). Please try again.`);
      }

      const data = (await r.json()) as QueryResponse;
      const assistantText = data.output?.text ?? 'No response text returned from backend.';

      const assistantMsg: ChatMessage = {
        id: data.request_id ?? crypto.randomUUID(),
        role: 'assistant',
        text: assistantText,
        timestamp: new Date().toISOString(),
        security: data.security,
      };

      setConversations((prev) =>
        prev.map((c) => {
          if (c.id !== activeConvId) return c;
          const updatedMessages = [...c.messages, assistantMsg];
          return {
            ...c,
            hideSensitive,
            modelId: selectedModelId,
            updatedAt: new Date().toISOString(),
            messages: updatedMessages,
            title: makeTitleFromFirstUserMessage(updatedMessages),
          };
        })
      );
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Request failed';
      setError(msg);
      setPrompt(userText);
    } finally {
      setLoading(false);
    }
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  const selectedModel =
    availableModels.find((m) => m.id === selectedModelId) ?? FALLBACK_MODEL;

  // Group models by provider for the dropdown
  const modelsByProvider = availableModels.reduce<Record<string, ModelOption[]>>(
    (acc, m) => {
      if (!acc[m.provider]) acc[m.provider] = [];
      acc[m.provider].push(m);
      return acc;
    },
    {}
  );

  return (
    <div className="h-full flex flex-col">
      {/* Top bar */}
      <div className="flex items-start justify-between gap-4 mb-6 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-100">Secure Chat</h1>
          <p className="text-sm text-slate-400">
            <span className={PROVIDER_COLOURS[selectedModel.provider] ?? 'text-slate-400'}>
              {providerLabel(selectedModel.provider)}
            </span>
            {' · '}
            {selectedModel.label}
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Hide sensitive toggle */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">Hide sensitive:</span>
            <button
              type="button"
              onClick={() => {
                setHideSensitive((v) => {
                  const next = !v;
                  updateActiveConversation({ hideSensitive: next });
                  return next;
                });
              }}
              className={
                'relative inline-flex h-5 w-10 items-center rounded-full transition ' +
                (hideSensitive ? 'bg-cyan-500' : 'bg-slate-700')
              }
              aria-pressed={hideSensitive}
            >
              <span
                className={
                  'inline-block h-4 w-4 transform rounded-full bg-white transition ' +
                  (hideSensitive ? 'translate-x-5' : 'translate-x-1')
                }
              />
            </button>
          </div>

          {/* Model selector */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">Model:</span>
            <select
              className="bg-slate-800 border border-slate-700 text-slate-100 rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
              value={selectedModelId}
              onChange={(e) => handleModelChange(e.target.value)}
            >
              {Object.entries(modelsByProvider).map(([provider, models]) => (
                <optgroup key={provider} label={providerLabel(provider)}>
                  {models.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.label}
                    </option>
                  ))}
                </optgroup>
              ))}
            </select>
          </div>

          {/* History button */}
          <button
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 hover:bg-slate-700 transition flex items-center gap-1.5"
            onClick={() => setHistoryOpen(true)}
            type="button"
          >
            History
          </button>
        </div>
      </div>

      {/* Rate limit banner */}
      {rateLimited && (
        <div className="mb-4 flex items-center gap-3 rounded-lg border border-yellow-500/30 bg-yellow-500/10 px-4 py-3">
          <div className="flex-1">
            <p className="text-sm font-semibold text-yellow-400">Rate limit reached</p>
            <p className="text-xs text-yellow-400/70 mt-0.5">
              Your role has a request limit per minute. You can send again in{' '}
              <span className="font-bold">{retryAfter}s</span>.
            </p>
          </div>
          <div className="shrink-0 h-10 w-10 rounded-full border-2 border-yellow-500/40 flex items-center justify-center">
            <span className="text-xs font-bold text-yellow-400">{retryAfter}</span>
          </div>
        </div>
      )}

      {/* Main chat area */}
      <div className="flex-1 min-h-0 flex flex-col">
        {messages.length === 0 ? (
          <div className="flex-1 min-h-0 flex flex-col items-center justify-center text-center px-6">
            <div className="text-2xl font-semibold text-slate-100 mb-2">
              Welcome to Secure Chat
            </div>
            <div className="text-sm text-slate-400 max-w-lg">
              Start a secure conversation with{' '}
              <span className={PROVIDER_COLOURS[selectedModel.provider] ?? ''}>
                {selectedModel.label}
              </span>
              . CyberOracle scans inputs and outputs for sensitive data before rendering.
            </div>

            <div className="mt-10 w-full max-w-2xl">
              <div className="flex items-center gap-3 border border-slate-700 rounded-xl bg-slate-900 px-3 py-2">
                <input
                  className="flex-1 outline-none text-sm py-2 bg-transparent text-slate-100 placeholder:text-slate-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  placeholder="Type your message here…"
                  value={prompt}
                  maxLength={MAX_PROMPT_LENGTH}
                  disabled={rateLimited}
                  onChange={(e) => setPrompt(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') send();
                  }}
                />
              </div>

              {error && (
                <div
                  className={`mt-3 rounded-lg border px-3 py-2 text-xs ${
                    rateLimited
                      ? 'border-yellow-500/20 bg-yellow-500/10 text-yellow-400'
                      : 'border-red-500/20 bg-red-500/10 text-red-400'
                  }`}
                >
                  {error}
                </div>
              )}
            </div>
          </div>
        ) : (
          <>
            {/* Scrollable messages */}
            <div ref={scrollRef} className="flex-1 min-h-0 overflow-y-auto px-2 pb-6">
              <div className="space-y-8">
                {messages.map((m) => {
                  const isUser = m.role === 'user';
                  const shownText = hideSensitive ? maskSensitiveUI(m.text) : m.text;

                  if (!isUser) {
                    return (
                      <div key={m.id} className="flex justify-start">
                        <div className="w-full max-w-3xl bg-slate-800 border border-slate-700 rounded-xl p-4">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <div className="h-6 w-6 rounded-full bg-cyan-400/10 border border-cyan-500/20 flex items-center justify-center text-xs text-cyan-400">
                                AI
                              </div>
                              <div className="text-sm font-semibold text-slate-200">
                                Assistant
                              </div>
                              <div
                                className={`text-[10px] px-1.5 py-0.5 rounded border ${
                                  PROVIDER_COLOURS[selectedModel.provider]
                                    ? `border-current ${PROVIDER_COLOURS[selectedModel.provider]}`
                                    : 'border-slate-600 text-slate-500'
                                } opacity-70`}
                              >
                                {selectedModel.label}
                              </div>
                            </div>
                            <div className="text-[11px] text-slate-500">
                              {formatTime(m.timestamp)}
                            </div>
                          </div>

                          <div className="text-sm text-slate-200 whitespace-pre-wrap">
                            {shownText}
                          </div>

                          {m.security?.policy_decision && (
                            <div className="mt-3 text-[11px] text-slate-500">
                              Policy:{' '}
                              <span className="font-semibold text-slate-400">
                                {m.security.policy_decision}
                              </span>
                              {' · '}
                              Risk:{' '}
                              <span className="font-semibold text-slate-400">
                                {(m.security.risk_score ?? 0).toFixed(2)}
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  }

                  return (
                    <div key={m.id} className="flex justify-end">
                      <div className="max-w-[420px] bg-cyan-500/10 border border-cyan-500/20 rounded-xl p-3">
                        <div className="flex items-center justify-between mb-1">
                          <div className="text-xs font-semibold text-slate-200">You</div>
                          <div className="text-[11px] text-slate-500">
                            {formatTime(m.timestamp)}
                          </div>
                        </div>
                        <div className="text-sm text-slate-100 whitespace-pre-wrap">
                          {shownText}
                        </div>
                      </div>
                    </div>
                  );
                })}

                {loading && (
                  <div className="flex justify-start">
                    <div className="bg-slate-800 border border-slate-700 rounded-xl p-4 flex items-center gap-2">
                      <Spinner className="w-4 h-4" />
                      <span className="text-xs text-slate-400">Thinking…</span>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Bottom input */}
            <div className="bg-slate-900 border-t border-slate-800 p-4">
              {error && (
                <div
                  className={`mb-3 rounded-lg border px-3 py-2 text-xs ${
                    rateLimited
                      ? 'border-yellow-500/20 bg-yellow-500/10 text-yellow-400'
                      : 'border-red-500/20 bg-red-500/10 text-red-400'
                  }`}
                >
                  {error}
                </div>
              )}

              <div className="mx-auto max-w-4xl flex items-end gap-3">
                <div
                  className={`flex-1 border rounded-xl px-3 py-2 ${
                    rateLimited
                      ? 'border-yellow-500/30 bg-slate-800/50'
                      : 'border-slate-700 bg-slate-800'
                  }`}
                >
                  <div className="flex items-start gap-2">
                    <textarea
                      value={prompt}
                      onChange={(e) => setPrompt(e.target.value)}
                      onKeyDown={onKeyDown}
                      rows={2}
                      disabled={rateLimited}
                      maxLength={MAX_PROMPT_LENGTH}
                      className="flex-1 outline-none resize-none text-sm bg-transparent text-slate-100 placeholder:text-slate-500 disabled:opacity-50 disabled:cursor-not-allowed"
                      placeholder={
                        rateLimited
                          ? `Rate limited — wait ${retryAfter}s…`
                          : 'Type your message here…'
                      }
                    />
                    {prompt.length > 7000 && (
                      <span
                        className={`text-[10px] self-end shrink-0 ${
                          prompt.length > 7500 ? 'text-red-400' : 'text-yellow-400'
                        }`}
                      >
                        {prompt.length}/{MAX_PROMPT_LENGTH}
                      </span>
                    )}
                  </div>
                </div>

                <button
                  onClick={send}
                  disabled={loading || !prompt.trim() || rateLimited}
                  className="rounded-lg bg-cyan-500 hover:bg-cyan-400 px-4 py-3 text-sm font-semibold text-slate-900 disabled:opacity-60 disabled:cursor-not-allowed transition min-w-[80px]"
                >
                  {loading ? 'Sending…' : rateLimited ? `${retryAfter}s` : 'Send'}
                </button>
              </div>
            </div>
          </>
        )}
      </div>

      {/* History modal */}
      {historyOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/60" onClick={() => setHistoryOpen(false)} />
          <div className="relative bg-slate-900 w-[680px] max-w-[92vw] rounded-xl border border-slate-800 shadow-xl overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
              <div className="text-sm font-semibold text-slate-200">Chat History</div>
              <div className="flex items-center gap-2">
                <button
                  className="text-sm px-3 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-900 font-semibold transition"
                  onClick={newChat}
                  type="button"
                >
                  New chat
                </button>
                <button
                  className="text-sm px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-800 text-slate-200 hover:bg-slate-700 transition"
                  onClick={() => setHistoryOpen(false)}
                  type="button"
                >
                  <XMarkIcon className="w-4 h-4" />
                </button>
              </div>
            </div>

            <div className="max-h-[60vh] overflow-y-auto">
              {conversations.length === 0 ? (
                <div className="p-6 text-sm text-slate-500">No conversations yet.</div>
              ) : (
                <div className="divide-y divide-slate-800">
                  {conversations.map((c) => {
                    const convModel =
                      availableModels.find((m) => m.id === c.modelId) ??
                      ({ label: c.modelId, provider: 'ollama' } as ModelOption);
                    return (
                      <div
                        key={c.id}
                        className="p-4 flex items-center justify-between gap-3 hover:bg-slate-800 transition"
                      >
                        <button
                          className="flex-1 text-left"
                          onClick={() => loadConversation(c.id)}
                          type="button"
                        >
                          <div className="text-sm font-semibold text-slate-200">
                            {c.title || 'New chat'}
                          </div>
                          <div className="text-xs text-slate-500 mt-1">
                            <span
                              className={
                                PROVIDER_COLOURS[convModel.provider] ?? 'text-slate-500'
                              }
                            >
                              {convModel.label}
                            </span>
                            {' · '}
                            {new Date(c.updatedAt).toLocaleString()}
                          </div>
                        </button>

                        <button
                          type="button"
                          className="text-xs px-3 py-1.5 rounded-lg border border-slate-700 text-slate-400 hover:bg-red-500/10 hover:border-red-500/20 hover:text-red-400 transition"
                          onClick={() => deleteConversation(c.id)}
                        >
                          Delete
                        </button>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            <div className="px-4 py-3 border-t border-slate-800 text-[11px] text-slate-500">
              History is stored locally in your browser.
            </div>
          </div>
        </div>
      )}

      {/* Security summary */}
      {messages.length > 0 && (
        <div className="mt-4 text-[11px] text-slate-500">
          Latest decision:{' '}
          <span className="font-semibold text-slate-400">{decision}</span> · risk:{' '}
          <span className="font-semibold text-slate-400">{risk.toFixed(2)}</span>
        </div>
      )}
    </div>
  );
}
