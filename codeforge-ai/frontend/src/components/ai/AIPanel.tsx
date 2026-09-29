import { useCallback, useEffect, useRef, useState } from 'react';
import type { CopilotApi } from '../../lib/copilot';
import AIChat from './AIChat';

const MIN_W = 340;
const MAX_W = 780;
const DEFAULT_W = 440;

function readWidth(): number {
  const v = parseInt(localStorage.getItem('aiPanelWidth') || '', 10);
  return Number.isFinite(v) ? Math.min(MAX_W, Math.max(MIN_W, v)) : DEFAULT_W;
}

interface AIPanelProps {
  open: boolean;
  onClose: () => void;
  copilot: CopilotApi;
}

export default function AIPanel({ open, onClose, copilot }: AIPanelProps) {
  const [width, setWidth] = useState(readWidth);
  const [fullscreen, setFullscreen] = useState(false);
  const [dragging, setDragging] = useState(false);
  const dragStart = useRef<{ x: number; w: number } | null>(null);

  const onPointerDown = useCallback((e: React.PointerEvent) => {
    e.preventDefault();
    setDragging(true);
    dragStart.current = { x: e.clientX, w: width };
    (e.target as HTMLElement).setPointerCapture?.(e.pointerId);
  }, [width]);

  useEffect(() => {
    if (!dragging) return;
    const move = (e: PointerEvent) => {
      const start = dragStart.current;
      if (!start) return;
      const next = Math.min(MAX_W, Math.max(MIN_W, start.w + (start.x - e.clientX)));
      setWidth(next);
    };
    const up = () => {
      setDragging(false);
      setWidth((w) => {
        try {
          localStorage.setItem('aiPanelWidth', String(w));
        } catch {
          /* quota */
        }
        return w;
      });
      dragStart.current = null;
    };
    window.addEventListener('pointermove', move);
    window.addEventListener('pointerup', up);
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
    return () => {
      window.removeEventListener('pointermove', move);
      window.removeEventListener('pointerup', up);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [dragging]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && open) {
        if (fullscreen) setFullscreen(false);
        else onClose();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, fullscreen, onClose]);

  if (!open) return null;

  const effectiveWidth = fullscreen ? window.innerWidth : width;

  return (
    <div
      className={`ai-panel ${fullscreen ? 'fullscreen' : ''} ${dragging ? 'dragging' : ''}`}
      style={{ width: effectiveWidth }}
      role="complementary"
      aria-label="AI assistant side panel"
    >
      {!fullscreen && (
        <div
          className="ai-panel-resizer"
          onPointerDown={onPointerDown}
          title="Drag to resize"
          aria-hidden="true"
        />
      )}

      <div className="ai-panel-header">
        <div className="ai-panel-title">
          <span className="ai-panel-spark">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2l2.4 6.6L21 11l-6.6 2.4L12 20l-2.4-6.6L3 11l6.6-2.4L12 2z" />
            </svg>
          </span>
          <span className="ai-panel-title-text">CodeForge AI</span>
          <kbd className="ai-kbd">Ctrl K</kbd>
        </div>
        <div className="ai-panel-actions">
          <button className="btn btn-ghost btn-sm" onClick={() => setFullscreen((f) => !f)} title={fullscreen ? 'Exit fullscreen' : 'Fullscreen'}>
            {fullscreen ? (
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M8 3v3a2 2 0 0 1-2 2H3" /><path d="M21 8h-3a2 2 0 0 1-2-2V3" />
                <path d="M3 16h3a2 2 0 0 1 2 2v3" /><path d="M16 21v-3a2 2 0 0 1 2-2h3" />
              </svg>
            ) : (
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="15 3 21 3 21 9" /><polyline points="9 21 3 21 3 15" />
                <line x1="21" y1="3" x2="14" y2="10" /><line x1="3" y1="21" x2="10" y2="14" />
              </svg>
            )}
          </button>
          <button className="btn btn-ghost btn-sm" onClick={onClose} title="Close panel (Esc)">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>
      </div>

      <div className="ai-panel-body">
        <AIChat copilot={copilot} variant="panel" />
      </div>
    </div>
  );
}

