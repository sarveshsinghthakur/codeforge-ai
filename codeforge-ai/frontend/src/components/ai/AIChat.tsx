import { useEffect, useRef, useState } from 'react';
import { QUICK_ACTIONS, type CopilotApi, type CopilotError, type CopilotMessage } from '../../lib/copilot';
import Markdown from './Markdown';

function ErrorCard({ error, onRetry, onDismiss, busy }: { error: CopilotError; onRetry: () => void; onDismiss?: () => void; busy: boolean }) {
  const titles: Record<string, string> = {
    auth: 'AI key rejected',
    not_configured: 'AI not configured',
    rate_limit: 'Rate limited',
    upstream: 'AI service error',
    network: 'Connection problem',
    empty: 'Empty response',
    stream_failed: 'Stream interrupted',
  };
  const canRetry = error.retryable !== false;
  return (
    <div className="ai-error-card" role="alert">
      <div className="ai-error-icon">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
          <line x1="12" y1="9" x2="12" y2="13" />
          <line x1="12" y1="17" x2="12.01" y2="17" />
        </svg>
      </div>
      <div className="ai-error-body">
        <div className="ai-error-title">{titles[error.error] || 'AI request failed'}</div>
        <div className="ai-error-message">{error.message}</div>
        <div className="ai-error-actions">
          {canRetry && (
            <button className="btn btn-secondary btn-sm" onClick={onRetry} disabled={busy}>
              Retry
            </button>
          )}
          {onDismiss && (
            <button className="btn btn-ghost btn-sm" onClick={onDismiss}>
              Dismiss
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function MessageBubble({ msg, onRetry, busy }: { msg: CopilotMessage; onRetry: () => void; busy: boolean }) {
  if (msg.role === 'user') {
    return (
      <div className="ai-msg ai-msg-user">
        <div className="ai-bubble ai-bubble-user">{msg.content}</div>
      </div>
    );
  }
  return (
    <div className="ai-msg ai-msg-assistant">
      <div className="ai-avatar" title="CodeForge AI">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 2l2.4 6.6L21 11l-6.6 2.4L12 20l-2.4-6.6L3 11l6.6-2.4L12 2z" />
        </svg>
      </div>
      <div className="ai-bubble ai-bubble-assistant">
        {msg.error ? (
          msg.content ? <Markdown content={msg.content} /> : null
        ) : msg.content ? (
          <Markdown content={msg.content} />
        ) : (
          <span className="ai-typing">
            <span className="dot" />
            <span className="dot" />
            <span className="dot" />
          </span>
        )}
        {msg.streaming && msg.content && !msg.error && <span className="ai-cursor" />}
        {msg.error && (
          <div style={{ marginTop: '8px' }}>
            <ErrorCard error={msg.error} onRetry={onRetry} busy={busy} />
          </div>
        )}
      </div>
    </div>
  );
}

interface AIChatProps {
  copilot: CopilotApi;
  variant?: 'panel' | 'tab';
  title?: string;
  showActions?: boolean;
}

export default function AIChat({ copilot, variant = 'panel', title, showActions = true }: AIChatProps) {
  const [input, setInput] = useState('');
  const [dismissedErrors, setDismissedErrors] = useState<Record<string, boolean>>({});
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const { messages, busy, send, clear, retry } = copilot;

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  const submit = () => {
    const text = input.trim();
    if (!text || busy) return;
    setInput('');
    send('chat', text);
  };

  const onAction = (action: string, hint: string) => {
    if (busy) return;
    send(action, hint);
  };

  const lastErrorMessage = (() => {
    const m = [...messages].reverse().find((x) => x.role === 'assistant' && x.error);
    if (!m || dismissedErrors[m.id]) return null;
    return { id: m.id, error: m.error! };
  })();

  const empty = messages.length === 0;

  return (
    <div className={`ai-chat ai-chat-${variant}`}>
      {title && (
        <div className="ai-chat-header">
          <div className="ai-chat-title">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2l2.4 6.6L21 11l-6.6 2.4L12 20l-2.4-6.6L3 11l6.6-2.4L12 2z" />
            </svg>
            {title}
          </div>
          <button className="btn btn-ghost btn-sm" onClick={clear} title="Start a new conversation" disabled={busy && false}>
            New chat
          </button>
        </div>
      )}

      {showActions && (
        <div className="ai-quick-actions">
          {QUICK_ACTIONS.map((a) => (
            <button
              key={a.id}
              className="ai-quick-action"
              onClick={() => onAction(a.id, a.hint)}
              disabled={busy}
              title={a.hint}
            >
              {a.label}
            </button>
          ))}
        </div>
      )}

      <div className="ai-messages" ref={scrollRef}>
        {empty && (
          <div className="ai-empty">
            <div className="ai-empty-icon">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2l2.4 6.6L21 11l-6.6 2.4L12 20l-2.4-6.6L3 11l6.6-2.4L12 2z" />
              </svg>
            </div>
            <h4>Ask CodeForge AI</h4>
            <p>Explain this problem, debug my code, or walk me through a solution — I can see your editor.</p>
            <div className="ai-empty-hints">
              <button className="ai-quick-action" onClick={() => send('explain_problem', QUICK_ACTIONS[0].hint)} disabled={busy}>
                Explain this problem
              </button>
              <button className="ai-quick-action" onClick={() => send('debug', QUICK_ACTIONS[2].hint)} disabled={busy}>
                Why does my code fail?
              </button>
              <button className="ai-quick-action" onClick={() => send('edge_cases', QUICK_ACTIONS[6].hint)} disabled={busy}>
                What edge cases am I missing?
              </button>
            </div>
            <div className="ai-empty-shortcut">Press <kbd>Ctrl</kbd> + <kbd>K</kbd> to toggle the side panel</div>
          </div>
        )}

        {messages.map((m) => (
          <MessageBubble key={m.id} msg={m} onRetry={retry} busy={busy} />
        ))}

        {lastErrorMessage && !busy && (
          <ErrorCard
            error={lastErrorMessage.error}
            onRetry={() => {
              setDismissedErrors((p) => ({ ...p, [lastErrorMessage.id]: true }));
              retry();
            }}
            onDismiss={() => setDismissedErrors((p) => ({ ...p, [lastErrorMessage.id]: true }))}
            busy={busy}
          />
        )}
      </div>

      <div className="ai-composer">
        <textarea
          ref={inputRef}
          className="ai-input"
          rows={2}
          placeholder={busy ? 'AI is responding…' : 'Ask about this problem or your code… (Enter to send, Shift+Enter for newline)'}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              submit();
            }
          }}
          disabled={busy}
        />
        <button className="btn btn-primary btn-sm ai-send-btn" onClick={submit} disabled={busy || !input.trim()} title="Send">
          {busy ? (
            <span className="loading-spinner" style={{ width: '14px', height: '14px', borderWidth: '2px' }} />
          ) : (
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          )}
        </button>
      </div>
    </div>
  );
}
