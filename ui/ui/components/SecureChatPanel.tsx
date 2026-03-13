'use client';

import React, { useEffect, useMemo, useRef, useState } from 'react';

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
  model: 'ollama';
  hideSensitive: boolean;
  createdAt: string;
  updatedAt: string;
  messages: ChatMessage[];
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8010';
const STORAGE_KEY = 'cyberoracle_secure_chat_conversations_v1';

// --- Basic client-side masking (UI-only; backend DLP still authoritative) ---
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

function createEmptyConversation(id?: string): Conversation {
  const now = new Date().toISOString();
  return {
    id: id ?? crypto.randomUUID(),
    title: 'New chat',
    model: 'ollama',
    hideSensitive: true,
    createdAt: now,
    updatedAt: now,
    messages: [],
  };
}

export default function SecureChatPanel() {
  // MVP: Ollama only
  const [model] = useState<'ollama'>('ollama');
  const subtitle = 'Secure AI conversation with Ollama';

  const [prompt, setPrompt] = useState('');
  const [hideSensitive, setHideSensitive] = useState(true);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Conversations (UI history)
  const [conversations, setConversations] = useState<Conversation[]>(() => [createEmptyConversation()]);
  const [activeConvId, setActiveConvId] = useState<string>(() => crypto.randomUUID());
  const [historyOpen, setHistoryOpen] = useState(false);

  const scrollRef = useRef<HTMLDivElement | null>(null);

  // Ensure activeConvId matches an existing conversation after first render
  useEffect(() => {
    setConversations((prev) => {
      // If we already have a conversation matching activeConvId, keep
      if (prev.some((c) => c.id === activeConvId)) return prev;

      // Otherwise replace with a new one with that id
      return [createEmptyConversation(activeConvId)];
    });
  }, [activeConvId]);

  const activeConversation = useMemo(() => {
    return conversations.find((c) => c.id === activeConvId) ?? null;
  }, [conversations, activeConvId]);

  const messages = activeConversation?.messages ?? [];

  const lastAssistant = useMemo(
    () => [...messages].reverse().find((m) => m.role === 'assistant'),
    [messages]
  );

  const decision: PolicyDecision = lastAssistant?.security?.policy_decision ?? 'allow';
  const risk = lastAssistant?.security?.risk_score ?? 0;

  // load history from localStorage once
  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as Conversation[];
        if (Array.isArray(parsed) && parsed.length > 0) {
          setConversations(parsed);
          setActiveConvId(parsed[0].id);
          setHideSensitive(!!parsed[0].hideSensitive);
          return;
        }
      }
    } catch {
      // ignore
    }

    // If no saved history, ensure we have at least one conversation
    setConversations((prev) => (prev.length > 0 ? prev : [createEmptyConversation(activeConvId)]));
  }, []); // eslint-disable-line

  // persist history
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
    } catch {
      // ignore
    }
  }, [conversations]);

  // auto scroll to bottom on new messages
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
      return [createEmptyConversation(activeConvId), ...prev];
    });
  }

  function newChat() {
    const conv = createEmptyConversation();
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
    setHistoryOpen(false);
    setError(null);
  }

  function deleteConversation(id: string) {
    setConversations((prev) => prev.filter((c) => c.id !== id));
    if (activeConvId === id) {
      const remaining = conversations.filter((c) => c.id !== id);
      if (remaining.length > 0) setActiveConvId(remaining[0].id);
      else {
        const fresh = createEmptyConversation();
        setConversations([fresh]);
        setActiveConvId(fresh.id);
      }
    }
  }

  async function send() {
    if (!prompt.trim() || loading) return;

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

    // ✅ Append user message safely
    setConversations((prev) =>
      prev.map((c) => {
        if (c.id !== activeConvId) return c;
        const updatedMessages = [...c.messages, userMessage];
        return {
          ...c,
          hideSensitive,
          updatedAt: new Date().toISOString(),
          messages: updatedMessages,
          title: makeTitleFromFirstUserMessage(updatedMessages),
        };
      })
    );

    try {
      const r = await fetch(`${API_BASE}/ai/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: userText, model: 'ollama' }),
      });

      if (!r.ok) {
        const txt = await r.text();
        throw new Error(`Backend error (${r.status}): ${txt}`);
      }

      const data = (await r.json()) as QueryResponse;

      const assistantText =
        data.output?.text ?? 'No response text returned from backend.';

      const assistantMsg: ChatMessage = {
        id: data.request_id ?? crypto.randomUUID(),
        role: 'assistant',
        text: assistantText,
        timestamp: new Date().toISOString(),
        security: data.security,
      };

      // ✅ Append assistant safely
      setConversations((prev) =>
        prev.map((c) => {
          if (c.id !== activeConvId) return c;
          const updatedMessages = [...c.messages, assistantMsg];
          return {
            ...c,
            hideSensitive,
            updatedAt: new Date().toISOString(),
            messages: updatedMessages,
            title: makeTitleFromFirstUserMessage(updatedMessages),
          };
        })
      );
    } catch (e: any) {
      setError(e?.message ?? 'Request failed');
      setPrompt(userText); // restore input
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

  return (
    <div className="h-full flex flex-col">
      {/* Top bar */}
      <div className="flex items-start justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Secure Chat</h1>
          <p className="text-sm text-slate-500">{subtitle}</p>
        </div>

        <div className="flex items-center gap-4">
          {/* Hide sensitive toggle */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-slate-700">Hide sensitive data:</span>
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
                'relative inline-flex h-6 w-11 items-center rounded-full transition ' +
                (hideSensitive ? 'bg-violet-600' : 'bg-slate-300')
              }
              aria-pressed={hideSensitive}
            >
              <span
                className={
                  'inline-block h-5 w-5 transform rounded-full bg-white transition ' +
                  (hideSensitive ? 'translate-x-5' : 'translate-x-1')
                }
              />
            </button>
          </div>

          {/* Model dropdown (Ollama only) */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-slate-700">Model:</span>
            <select
              className="border border-slate-200 rounded-lg px-3 py-2 text-sm bg-white"
              value="ollama"
              onChange={() => {}}
            >
              <option value="ollama">Ollama (llama3)</option>
            </select>
          </div>

          {/* History button */}
          <button
            className="border border-slate-200 rounded-lg px-3 py-2 text-sm bg-white hover:bg-slate-50 flex items-center gap-2"
            onClick={() => setHistoryOpen(true)}
            type="button"
          >
            <span className="inline-block">🕘</span>
            History
          </button>
        </div>
      </div>

      {/* Main chat area */}
      <div className="flex-1 min-h-0 flex flex-col">
        {/* Empty state */}
        {messages.length === 0 ? (
          <div className="flex-1 min-h-0 flex flex-col items-center justify-center text-center px-6">
            <div className="text-2xl font-semibold text-slate-900 mb-2">
              Welcome to Secure Chat
            </div>
            <div className="text-sm text-slate-600 max-w-lg">
              Start a secure conversation with Ollama. CyberOracle scans inputs and outputs
              for sensitive data before rendering.
            </div>

            <div className="mt-10 w-full max-w-2xl">
              <div className="flex items-center gap-3 border border-slate-200 rounded-xl bg-white shadow-sm px-3 py-2">
                <div className="text-slate-400 text-xl select-none">＋</div>
                <input
                  className="flex-1 outline-none text-sm py-2"
                  placeholder="Type your message here…"
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') send();
                  }}
                />
              </div>

              {error && (
                <div className="mt-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
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
                        <div className="w-full max-w-3xl border border-slate-200 bg-slate-50 rounded-xl p-4 shadow-sm">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <div className="h-6 w-6 rounded-full bg-slate-200 flex items-center justify-center text-xs">
                                🤖
                              </div>
                              <div className="text-sm font-semibold text-slate-900">
                                Assistant
                              </div>
                            </div>
                            <div className="text-xs text-slate-400">
                              {formatTime(m.timestamp)}
                            </div>
                          </div>

                          <div className="text-sm text-slate-900 whitespace-pre-wrap">
                            {shownText}
                          </div>

                          {/* mini security chip */}
                          {m.security?.policy_decision && (
                            <div className="mt-3 text-[11px] text-slate-500">
                              Policy: <span className="font-semibold">{m.security.policy_decision}</span>
                              {' · '}
                              Risk: <span className="font-semibold">{(m.security.risk_score ?? 0).toFixed(2)}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  }

                  return (
                    <div key={m.id} className="flex justify-end">
                      <div className="max-w-[420px] bg-indigo-100 border border-indigo-200 rounded-xl p-3">
                        <div className="flex items-center justify-between mb-1">
                          <div className="text-xs font-semibold text-slate-700">You</div>
                          <div className="text-xs text-slate-400">{formatTime(m.timestamp)}</div>
                        </div>
                        <div className="text-sm text-slate-900 whitespace-pre-wrap">{shownText}</div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Bottom input */}
            <div className="border-t border-slate-200 bg-white p-4">
              {error && (
                <div className="mb-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
                  {error}
                </div>
              )}

              <div className="mx-auto max-w-4xl flex items-end gap-3">
                <div className="flex-1 border border-slate-900 rounded-xl px-3 py-2">
                  <div className="flex items-start gap-2">
                    <div className="text-slate-500 text-xl select-none leading-none mt-1">+</div>
                    <textarea
                      value={prompt}
                      onChange={(e) => setPrompt(e.target.value)}
                      onKeyDown={onKeyDown}
                      rows={2}
                      className="flex-1 outline-none resize-none text-sm"
                      placeholder="Type your message here…"
                    />
                  </div>
                </div>

                <button
                  onClick={send}
                  disabled={loading || !prompt.trim()}
                  className="rounded-lg bg-slate-900 px-4 py-3 text-sm font-semibold text-white disabled:opacity-60"
                >
                  {loading ? 'Sending…' : 'Send'}
                </button>
              </div>
            </div>
          </>
        )}
      </div>

      {/* History modal */}
      {historyOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/40" onClick={() => setHistoryOpen(false)} />
          <div className="relative bg-white w-[680px] max-w-[92vw] rounded-xl border border-slate-200 shadow-xl overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200">
              <div className="text-sm font-semibold text-slate-900">Chat History</div>
              <div className="flex items-center gap-2">
                <button
                  className="text-sm px-3 py-2 rounded-lg bg-slate-900 text-white"
                  onClick={newChat}
                  type="button"
                >
                  New chat
                </button>
                <button
                  className="text-sm px-3 py-2 rounded-lg border border-slate-200 hover:bg-slate-50"
                  onClick={() => setHistoryOpen(false)}
                  type="button"
                >
                  Close
                </button>
              </div>
            </div>

            <div className="max-h-[60vh] overflow-y-auto">
              {conversations.length === 0 ? (
                <div className="p-6 text-sm text-slate-500">No conversations yet.</div>
              ) : (
                <div className="divide-y divide-slate-100">
                  {conversations.map((c) => (
                    <div key={c.id} className="p-4 flex items-center justify-between gap-3">
                      <button className="flex-1 text-left" onClick={() => loadConversation(c.id)} type="button">
                        <div className="text-sm font-semibold text-slate-900">{c.title || 'New chat'}</div>
                        <div className="text-xs text-slate-500 mt-1">
                          Ollama • {new Date(c.updatedAt).toLocaleString()}
                        </div>
                      </button>

                      <button
                        type="button"
                        className="text-xs px-3 py-2 rounded-lg border border-slate-200 hover:bg-red-50 hover:border-red-200 hover:text-red-700"
                        onClick={() => deleteConversation(c.id)}
                      >
                        Delete
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="px-4 py-3 border-t border-slate-200 text-[11px] text-slate-400">
              History is stored locally in your browser for now. Later we can back this with DB + Audit Log.
            </div>
          </div>
        </div>
      )}

      {/* Tiny security summary panel (optional quick view) */}
      {messages.length > 0 && (
        <div className="mt-4 text-[11px] text-slate-500">
          Latest decision: <span className="font-semibold">{decision}</span> · risk:{' '}
          <span className="font-semibold">{risk.toFixed(2)}</span>
        </div>
      )}
    </div>
  );
}