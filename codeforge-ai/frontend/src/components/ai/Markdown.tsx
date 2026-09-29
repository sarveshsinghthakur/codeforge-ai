import { useMemo, useState } from 'react';
import { marked } from 'marked';

marked.setOptions({ breaks: true, gfm: true });

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function sanitize(html: string): string {
  return html
    .replace(/<script[\s\S]*?<\/script>/gi, '')
    .replace(/<style[\s\S]*?<\/style>/gi, '')
    .replace(/<iframe[\s\S]*?<\/iframe>/gi, '')
    .replace(/ on\w+\s*=\s*"[^"]*"/gi, '')
    .replace(/ on\w+\s*=\s*'[^']*'/gi, '')
    .replace(/on\w+\s*=\s*[^\s>]+/gi, '')
    .replace(/javascript:/gi, '');
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      className="md-copy-btn"
      onClick={() => {
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 1600);
      }}
      title="Copy code"
    >
      {copied ? 'Copied!' : 'Copy'}
    </button>
  );
}

function extractCodeBlocks(html: string): { html: string; blocks: string[] } {
  const blocks: string[] = [];
  const withPlaceholders = html.replace(/<pre><code[^>]*>([\s\S]*?)<\/code><\/pre>/g, (_m, inner: string) => {
    const idx = blocks.push(inner) - 1;
    return `<pre data-md-block="${idx}"><button class="md-copy-btn" data-copy="${idx}">Copy</button><code>${inner}</code></pre>`;
  });
  return { html: withPlaceholders, blocks };
}

export default function Markdown({ content, className }: { content: string; className?: string }) {
  const html = useMemo(() => {
    if (!content) return '';
    let raw: string;
    try {
      raw = marked.parse(content, { async: false }) as string;
    } catch {
      raw = escapeHtml(content).replace(/\n/g, '<br/>');
    }
    const { html: withButtons } = extractCodeBlocks(raw);
    return sanitize(withButtons);
  }, [content]);

  if (!content) return null;

  return (
    <div
      className={`markdown-body ${className || ''}`}
      dangerouslySetInnerHTML={{ __html: html }}
      ref={(el) => {
        if (!el) return;
        el.querySelectorAll<HTMLButtonElement>('button[data-copy]').forEach((btn) => {
          if (btn.dataset.bound) return;
          btn.dataset.bound = '1';
          btn.addEventListener('click', () => {
            const pre = btn.parentElement;
            const code = pre?.querySelector('code');
            navigator.clipboard.writeText(code?.innerText || '');
            btn.textContent = 'Copied!';
            setTimeout(() => (btn.textContent = 'Copy'), 1600);
          });
        });
      }}
    />
  );
}

export function PlainCopyButton({ text }: { text: string }) {
  return <CopyButton text={text} />;
}
