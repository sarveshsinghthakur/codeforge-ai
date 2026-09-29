import { useCallback, useEffect, useRef, useState } from 'react';

const API_BASE = '/api';

export interface QuickAction {
  id: string;
  label: string;
  hint: string;
}

export const QUICK_ACTIONS: QuickAction[] = [
  { id: 'explain_problem', label: 'Explain', hint: 'Explain the problem in simple terms' },
  { id: 'hint', label: 'Hint', hint: 'Give me a hint (no full solution)' },
  { id: 'debug', label: 'Debug', hint: 'Find the bug in my code' },
  { id: 'solution', label: 'Solution', hint: 'Walk me through a solution' },
  { id: 'explain_code', label: 'Explain code', hint: 'Explain my current code line by line' },
  { id: 'complexity', label: 'Complexity', hint: 'Analyze time and space complexity' },
  { id: 'edge_cases', label: 'Edge cases', hint: 'List edge cases I might be missing' },
  { id: 'testcases', label: 'Test cases', hint: 'Suggest more test cases' },
  { id: 'optimize', label: 'Optimize', hint: 'Make my solution faster or cleaner' },
];

export const ACTION_LABELS: Record<string, string> = QUICK_ACTIONS.reduce(
  (acc, a) => ({ ...acc, [a.id]: a.label }),
  { chat: 'Chat' } as Record<string, string>
);

export interface CopilotError {
  error: string;
  message: string;
  retryable?: boolean;
}

export interface CopilotMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  action?: string;
  error?: CopilotError | null;
  streaming?: boolean;
}

export interface CopilotPayload {
  request_type: string;
  problem_id?: number | null;
  language?: string;
  code?: string;
  testcase?: string;
  conversation_id?: number | null;
  message?: string;
  hint_level?: number;
  run_result?: any;
}

interface CopilotOptions {
  problemId: number | null;
  language: string;
  getCode: () => string;
  getRunResult: () => any;
}

const uid = () => Math.random().toString(36).slice(2) + Date.now().toString(36);

const storageKey = (problemId: number | null, kind: 'msgs' | 'conv') =>
  `copilot:${kind}:${problemId ?? 'none'}`;

function loadMessages(problemId: number | null): CopilotMessage[] {
  try {
    const raw = localStorage.getItem(storageKey(problemId, 'msgs'));
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed
      .filter((m) => m && (m.role === 'user' || m.role === 'assistant'))
      .map((m) => ({ ...m, streaming: false }))
      .slice(-50);
  } catch {
    return [];
  }
}

function loadConversationId(problemId: number | null): number | null {
  try {
    const raw = localStorage.getItem(storageKey(problemId, 'conv'));
    const n = raw ? Number(raw) : NaN;
    return Number.isFinite(n) ? n : null;
  } catch {
    return null;
  }
}

function parseSseChunk(buffer: string): { events: any[]; rest: string } {
  const events: any[] = [];
  let rest = buffer;
  let idx: number;
  while ((idx = rest.indexOf('\n\n')) !== -1) {
    const block = rest.slice(0, idx);
    rest = rest.slice(idx + 2);
    const dataLines = block
      .split('\n')
      .filter((l) => l.startsWith('data:'))
      .map((l) => l.slice(5).trim());
    if (!dataLines.length) continue;
    try {
      events.push(JSON.parse(dataLines.join('\n')));
    } catch {
      /* ignore malformed event */
    }
  }
  return { events, rest };
}

async function streamRequest(
  payload: CopilotPayload,
  onDelta: (text: string) => void,
  signal: AbortSignal
): Promise<{ reply: string; conversation_id: number | null; error: CopilotError | null }> {
  const token = localStorage.getItem('token');
  const res = await fetch(`${API_BASE}/ai/copilot/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(payload),
    signal,
  });

  if (!res.ok) {
    let body: any = null;
    try {
      body = await res.json();
    } catch {
      /* non-json error body */
    }
    return {
      reply: '',
      conversation_id: null,
      error: {
        error: body?.error || `http_${res.status}`,
        message: body?.message || body?.detail || 'AI service is unavailable right now.',
        retryable: res.status >= 500 || res.status === 429,
      },
    };
  }

  const contentType = res.headers.get('content-type') || '';
  if (!res.body || contentType.includes('application/json')) {
    const body = await res.json().catch(() => null);
    return {
      reply: body?.reply || body?.message || '',
      conversation_id: body?.conversation_id ? Number(body.conversation_id) : null,
      error: body?.error ? { error: body.error, message: body.message || body.error, retryable: body.retryable } : null,
    };
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let reply = '';
  let conversationId: number | null = null;
  let error: CopilotError | null = null;

  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const { events, rest } = parseSseChunk(buffer);
      buffer = rest;
      for (const ev of events) {
        if (ev.type === 'delta' && (typeof ev.text === 'string' || typeof ev.content === 'string')) {
          const chunk = typeof ev.text === 'string' ? ev.text : ev.content;
          reply += chunk;
          onDelta(chunk);
        } else if (ev.type === 'done') {
          conversationId = ev.conversation_id || conversationId;
          if (ev.reply) reply = ev.reply;
        } else if (ev.type === 'error') {
          error = { error: ev.error || 'stream_error', message: ev.message || 'AI request failed.', retryable: ev.retryable };
        }
      }
    }
  } catch (e: any) {
    if (e?.name !== 'AbortError') {
      error = { error: 'stream_failed', message: 'Connection to the AI service was interrupted.', retryable: true };
    }
  }

  return { reply, conversation_id: conversationId, error };
}

export interface CopilotApi {
  messages: CopilotMessage[];
  busy: boolean;
  conversationId: number | null;
  send: (action: string, message?: string) => Promise<void>;
  clear: () => void;
  retry: () => Promise<void>;
}

export function useCopilot({ problemId, language, getCode, getRunResult }: CopilotOptions): CopilotApi {
  const [messages, setMessages] = useState<CopilotMessage[]>(() => loadMessages(problemId));
  const [busy, setBusy] = useState(false);
  const [conversationId, setConversationId] = useState<number | null>(() => loadConversationId(problemId));
  const abortRef = useRef<AbortController | null>(null);
  const lastRequestRef = useRef<{ action: string; message?: string } | null>(null);

  useEffect(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setBusy(false);
    setMessages(loadMessages(problemId));
    setConversationId(loadConversationId(problemId));
  }, [problemId]);

  useEffect(() => {
    try {
      localStorage.setItem(storageKey(problemId, 'msgs'), JSON.stringify(messages.slice(-50)));
    } catch {
      /* quota */
    }
  }, [messages, problemId]);

  useEffect(() => {
    try {
      if (conversationId) localStorage.setItem(storageKey(problemId, 'conv'), String(conversationId));
      else localStorage.removeItem(storageKey(problemId, 'conv'));
    } catch {
      /* quota */
    }
  }, [conversationId, problemId]);

  const run = useCallback(
    async (action: string, message?: string) => {
      if (busy) return;
      lastRequestRef.current = { action, message };

      const userMsg: CopilotMessage = {
        id: uid(),
        role: 'user',
        content: message && message.trim() ? message.trim() : ACTION_LABELS[action] || action,
        action,
      };
      const assistantId = uid();
      const assistantMsg: CopilotMessage = {
        id: assistantId,
        role: 'assistant',
        content: '',
        action,
        streaming: true,
      };
      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      setBusy(true);

      const payload: CopilotPayload = {
        request_type: action,
        problem_id: problemId,
        language,
        code: getCode() || '',
        conversation_id: conversationId,
        message: message || undefined,
        run_result: getRunResult() || undefined,
      };

      const controller = new AbortController();
      abortRef.current = controller;
      let accumulated = '';

      const patchAssistant = (patch: Partial<CopilotMessage>) =>
        setMessages((prev) => prev.map((m) => (m.id === assistantId ? { ...m, ...patch } : m)));

      let result;
      try {
        result = await streamRequest(
          payload,
          (delta) => {
            accumulated += delta;
            patchAssistant({ content: accumulated });
          },
          controller.signal
        );
      } catch (e: any) {
        result = {
          reply: accumulated,
          conversation_id: null,
          error:
            e?.name === 'AbortError'
              ? null
              : { error: 'network', message: 'Could not reach the AI service. Check your connection.', retryable: true },
        };
      }

      if (result.conversation_id) setConversationId(result.conversation_id);

      if (result.error) {
        patchAssistant({
          content: accumulated,
          error: result.error,
          streaming: false,
        });
      } else if (!result.reply.trim() && !accumulated.trim()) {
        patchAssistant({
          content: 'The AI returned an empty response. Try again.',
          error: { error: 'empty', message: 'The AI returned an empty response.', retryable: true },
          streaming: false,
        });
      } else {
        patchAssistant({ content: result.reply || accumulated, streaming: false });
      }

      setBusy(false);
      abortRef.current = null;
    },
    [busy, conversationId, getCode, getRunResult, language, problemId]
  );

  const send = useCallback(
    async (action: string, message?: string) => {
      if (action === 'chat' && !(message || '').trim()) return;
      await run(action, message);
    },
    [run]
  );

  const retry = useCallback(() => {
    const last = lastRequestRef.current;
    if (!last) return run('chat', 'Please continue.');
    return run(last.action, last.message);
  }, [run]);

  const clear = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    lastRequestRef.current = null;
    setMessages([]);
    setConversationId(null);
    setBusy(false);
    try {
      localStorage.removeItem(storageKey(problemId, 'msgs'));
      localStorage.removeItem(storageKey(problemId, 'conv'));
    } catch {
      /* quota */
    }
  }, [problemId]);

  return { messages, busy, conversationId, send, clear, retry };
}
