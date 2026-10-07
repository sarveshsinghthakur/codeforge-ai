import { useState, useEffect, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import CodeMirror from '@uiw/react-codemirror';
import { python } from '@codemirror/lang-python';
import { javascript } from '@codemirror/lang-javascript';
import { java } from '@codemirror/lang-java';
import { EditorView, placeholder } from '@codemirror/view';
import api from '../lib/api';
import { useCopilot } from '../lib/copilot';
import { useTheme } from '../lib/theme';
import { analyzeTemplate, assembleCode, extractDraftBody, TemplateInfo } from '../lib/templates';
import { useAuth } from '../App';
import { useToast } from '../components/Toast';
import { storageUserKey } from '../lib/userScope';
import AIChat from '../components/ai/AIChat';
import AIPanel from '../components/ai/AIPanel';
import Markdown from '../components/ai/Markdown';
import Discussions from '../components/Discussions';

const LANG_MAP: Record<string, any> = { python: python(), javascript: javascript(), java: java() };
const LANG_LABELS: Record<string, string> = { python: 'Python 3', javascript: 'JavaScript', java: 'Java' };

// Per-user localStorage scope: drafts/custom input never leak across accounts.
const draftKey = (slug: string | undefined, lang: string) => `draft:${storageUserKey()}:${slug}:${lang}`;
const customInputKey = (slug: string | undefined) => `customInput:${storageUserKey()}:${slug}`;

const STATUS_META: Record<string, { label: string; cls: 'ok' | 'fail' | 'warn' }> = {
  accepted: { label: 'Accepted', cls: 'ok' },
  completed: { label: 'Finished', cls: 'ok' },
  wrong_answer: { label: 'Wrong Answer', cls: 'fail' },
  runtime_error: { label: 'Runtime Error', cls: 'fail' },
  compilation_error: { label: 'Compile Error', cls: 'fail' },
  time_limit: { label: 'Time Limit Exceeded', cls: 'warn' },
  memory_limit: { label: 'Memory Limit Exceeded', cls: 'warn' },
};

const SUB_STATUS: Record<string, string> = {
  accepted: 'Accepted',
  wrong_answer: 'Wrong Answer',
  runtime_error: 'Runtime Error',
  time_limit: 'TLE',
  memory_limit: 'MLE',
  compilation_error: 'Compile Error',
  pending: 'Pending',
};

interface Submission {
  id: number; public_id: string; language: string; status: string;
  runtime_ms: number | null; memory_kb: number | null; created_at: string;
}

function editorTheme(dark: boolean, fontSize: number) {
  const base = {
    '&': { height: '100%', fontSize: `${fontSize}px` },
    '.cm-scroller': { fontFamily: 'var(--font-mono)', fontSize: `${fontSize}px` },
    '.cm-content': { caretColor: dark ? '#fff' : '#1f2328' },
    '.cm-cursor': { borderLeftColor: dark ? '#fff' : '#1f2328' },
    '.cm-selectionBackground': { background: dark ? 'rgba(255,255,255,0.12)' : 'rgba(0,0,0,0.12)' },
    '&.cm-focused .cm-selectionBackground': { background: dark ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.16)' },
    '.cm-matchingBracket': {
      background: dark ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.12)',
      outline: dark ? '1px solid rgba(255,255,255,0.3)' : '1px solid rgba(0,0,0,0.3)',
    },
    '.cm-keyword': { color: '#c678dd' },
    '.cm-string': { color: '#98c379' },
    '.cm-number': { color: '#d19a66' },
    '.cm-comment': { color: '#5c6370' },
    '.cm-variableName': { color: '#e06c75' },
    '.cm-function': { color: '#61afef' },
    '.cm-operator': { color: '#56b6c2' },
    '.cm-typeName': { color: '#e5c07b' },
    '.cm-propertyName': { color: '#e06c75' },
    '.cm-definition': { color: '#61afef' },
    '.cm-bool': { color: '#d19a66' },
    '.cm-null': { color: '#d19a66' },
    '.cm-punctuation': { color: '#abb2bf' },
  };
  if (dark) {
    return {
      ...base,
      '&': { ...base['&'], backgroundColor: '#0d0d0d', color: '#e0e0e0' },
      '.cm-gutters': { backgroundColor: '#0d0d0d', borderRight: '1px solid rgba(255,255,255,0.06)', color: '#555' },
      '.cm-activeLine': { backgroundColor: 'rgba(255,255,255,0.03)' },
      '.cm-activeLineGutter': { backgroundColor: 'rgba(255,255,255,0.03)', color: '#888' },
      '.cm-content': { ...base['.cm-content'], color: '#e0e0e0' },
      '.cm-line': { color: '#e0e0e0' },
    };
  }
  return {
    ...base,
    '&': { ...base['&'], backgroundColor: '#ffffff', color: '#1f2328' },
    '.cm-gutters': { backgroundColor: '#f6f8fa', borderRight: '1px solid #d0d7de', color: '#8c959f' },
    '.cm-activeLine': { backgroundColor: 'rgba(184,200,220,0.15)' },
    '.cm-activeLineGutter': { backgroundColor: 'rgba(184,200,220,0.2)', color: '#57606a' },
    '.cm-content': { ...base['.cm-content'], color: '#1f2328' },
    '.cm-line': { color: '#1f2328' },
  };
}

export default function ProblemDetail() {
  const { slug } = useParams();
  const { theme } = useTheme();
  const { token } = useAuth();
  const { toast } = useToast();
  const [problem, setProblem] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [locked, setLocked] = useState<{ title: string; difficulty: string } | null>(null);
  const [favorited, setFavorited] = useState(false);
  const [language, setLanguage] = useState('python');
  const [code, setCode] = useState('');
  const [template, setTemplate] = useState<TemplateInfo | null>(null);
  const [output, setOutput] = useState<any>(null);
  const [running, setRunning] = useState(false);
  const [leftTab, setLeftTab] = useState<'description' | 'solutions' | 'submissions' | 'discussion' | 'ai'>('description');
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [submissionsLoading, setSubmissionsLoading] = useState(false);
  const [subCode, setSubCode] = useState<Record<number, string>>({});
  const [expandedSub, setExpandedSub] = useState<number | null>(null);
  const [activeTestCase, setActiveTestCase] = useState(0);
  const [rightTab, setRightTab] = useState<'testcases' | 'custom' | 'output'>('testcases');
  const [customInput, setCustomInput] = useState('');
  const [fontSize, setFontSize] = useState(() => parseInt(localStorage.getItem('editorFontSize') || '14'));
  const [aiPanelOpen, setAiPanelOpen] = useState(() => localStorage.getItem('aiPanelOpen') === '1');
  const [lastRunResult, setLastRunResult] = useState<any>(null);
  const [headerExpanded, setHeaderExpanded] = useState(false);
  const [cursor, setCursor] = useState({ line: 1, col: 1, selected: 0 });
  const [savedAt, setSavedAt] = useState<number | null>(null);
  const [related, setRelated] = useState<any[]>([]);

  const copilot = useCopilot({
    problemId: problem?.id ?? null,
    language,
    getCode: () => code,
    getRunResult: () => lastRunResult,
  });

  // the API already decodes JSON columns (lists/objects); older payloads may
  // still carry them as raw strings, so accept both.
  const parseJSON = (s: any): any => {
    if (s == null) return [];
    if (typeof s !== 'string') return s;
    try { return JSON.parse(s); } catch { return []; }
  };

  // ── template handling: the editor only ever holds the coding block ──────
  const applyTemplate = (lang: string, p: any) => {
    const sc = parseJSON(p.starter_code);
    const raw = typeof sc[lang] === 'string' ? sc[lang] : '';
    const info = analyzeTemplate(raw, lang);
    const draft = localStorage.getItem(draftKey(slug, lang));
    setTemplate(info);
    setCode(draft ? extractDraftBody(draft, info) : info.body);
    setSavedAt(draft ? Date.now() : null);
  };

  // fetch problem
  useEffect(() => {
    setLoading(true);
    setProblem(null);
    setLocked(null);
    api.get(`/problems/slug/${slug}`).then(res => {
      setProblem(res.data);
      setFavorited(!!res.data.is_favorite);
      setLoading(false);
    }).catch((err: any) => {
      if (err.response?.status === 402) {
        const details = err.response?.data?.detail?.details || {};
        setLocked({
          title: details.title || 'This problem',
          difficulty: details.difficulty || 'medium',
        });
      }
      setLoading(false);
    });
  }, [slug]);

  const toggleFavorite = async () => {
    if (!token) {
      toast('Sign in to star problems', 'info');
      return;
    }
    if (!problem) return;
    try {
      if (favorited) {
        await api.delete(`/problems/${problem.id}/favorite`);
        setFavorited(false);
        toast('Removed from starred', 'info');
      } else {
        await api.post(`/problems/${problem.id}/favorite`);
        setFavorited(true);
        toast('Added to starred', 'success');
      }
    } catch {
      toast('Could not update starred status', 'error');
    }
  };

  // apply template whenever the problem or language changes
  useEffect(() => {
    if (problem) applyTemplate(language, problem);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [problem, language]);

  // custom input draft
  useEffect(() => {
    setCustomInput(localStorage.getItem(customInputKey(slug)) || '');
  }, [slug]);

  // auto-save the coding block draft
  useEffect(() => {
    if (!template || !slug) return;
    const key = draftKey(slug, language);
    const pristine = code === template.body;
    if (pristine && localStorage.getItem(key) === null) return; // nothing to save yet
    localStorage.setItem(key, code);
    setSavedAt(Date.now());
  }, [code, language, slug, template]);

  // related problems (by first topic)
  useEffect(() => {
    if (!problem) return;
    const topics = parseJSON(problem.topics);
    const topic = Array.isArray(topics) && topics[0] ? topics[0] : null;
    if (!topic) { setRelated([]); return; }
    api.get('/problems', { params: { topic, limit: 6 } }).then(res => {
      const items = Array.isArray(res.data) ? res.data : res.data?.items || [];
      setRelated(items.filter((p: any) => p.slug !== slug).slice(0, 4));
    }).catch(() => setRelated([]));
  }, [problem, slug]);

  useEffect(() => {
    if (leftTab === 'submissions' && problem) {
      setSubmissionsLoading(true);
      api.get(`/problems/slug/${slug}/submissions`).then(res => {
        setSubmissions(res.data);
        setSubmissionsLoading(false);
      }).catch(() => setSubmissionsLoading(false));
    }
  }, [leftTab, problem, slug]);

  const handleFontSizeChange = (delta: number) => {
    setFontSize(prev => {
      const next = Math.max(12, Math.min(24, prev + delta));
      localStorage.setItem('editorFontSize', next.toString());
      return next;
    });
  };

  const handleResetCode = () => {
    if (!template) return;
    localStorage.removeItem(draftKey(slug, language));
    setCode(template.body);
    setSavedAt(null);
  };

  const handleCopyCode = () => {
    navigator.clipboard.writeText(code);
  };

  const runCode = async (mode: 'run' | 'submit' | 'custom') => {
    if (!problem || !template || running) return;
    if (mode === 'custom' && !customInput.trim()) {
      setRightTab('custom');
      return;
    }
    setRunning(true);
    setOutput(null);
    setRightTab('output');
    try {
      const payload: any = {
        problem_id: problem.id,
        source_code: assembleCode(template, code),
        language,
        mode,
      };
      if (mode === 'custom') {
        payload.custom_input = customInput;
        localStorage.setItem(customInputKey(slug), customInput);
      }
      const res = await api.post('/submissions', payload);
      const data = { ...res.data, mode };
      setOutput(data);
      setLastRunResult(data);
      if (mode === 'submit' && leftTab !== 'submissions') {
        api.get(`/problems/slug/${slug}/submissions`).then(r => setSubmissions(r.data));
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const data = {
        status: 'error',
        message: typeof detail === 'object' ? detail?.message || JSON.stringify(detail) : detail || 'Failed to submit',
        mode,
      };
      setOutput(data);
      setLastRunResult(data);
    }
    setRunning(false);
  };

  // keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        runCode(e.shiftKey ? 'run' : 'submit');
      }
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setAiPanelOpen((open) => {
          const next = !open;
          localStorage.setItem('aiPanelOpen', next ? '1' : '0');
          return next;
        });
      }
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  });

  const extensions = useMemo(() => {
    const updateListener = EditorView.updateListener.of(update => {
      if (update.docChanged || update.selectionSet) {
        const head = update.state.selection.main.head;
        const line = update.state.doc.lineAt(head);
        const sel = update.state.selection.main;
        setCursor({
          line: line.number,
          col: head - line.from + 1,
          selected: sel.to - sel.from,
        });
      }
    });
    return [
      LANG_MAP[language] || LANG_MAP.python,
      EditorView.theme(editorTheme(theme === 'dark', fontSize), { dark: theme === 'dark' }),
      updateListener,
      placeholder('Write your solution inside the function...'),
    ];
  }, [language, theme, fontSize]);

  if (loading) {
    return <div className="page-loading"><div className="loading-spinner" /></div>;
  }
  if (locked) {
    return (
      <div className="page-container">
        <div className="glass-card paywall-card">
          <div className="paywall-icon">
            <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
              <path d="M7 11V7a5 5 0 0 1 9.9-1" />
            </svg>
          </div>
          <span className={`difficulty-badge ${locked.difficulty}`}>{locked.difficulty}</span>
          <h1>{locked.title}</h1>
          <p>
            This <strong>{locked.difficulty}</strong> problem is part of the Premium collection.
            {token
              ? ' Verify a payment to unlock Medium and Hard problems on your account.'
              : ' Sign in and verify a payment to unlock it.'}
          </p>
          <div className="paywall-actions">
            <Link to="/payment" className="btn btn-primary">Unlock with Premium</Link>
            {!token && <Link to="/login" className="btn btn-secondary">Sign In</Link>}
            <Link to="/problems" className="btn btn-ghost">Back to Problems</Link>
          </div>
        </div>
      </div>
    );
  }
  if (!problem) {
    return <div className="page-container"><div className="empty-state"><h3>Problem not found</h3><Link to="/problems"><button className="btn btn-secondary" style={{ marginTop: '12px' }}>Back to Problems</button></Link></div></div>;
  }

  const examples = parseJSON(problem.examples);
  const hints = parseJSON(problem.hints);
  const constraints = parseJSON(problem.constraints);
  const starterCode = parseJSON(problem.starter_code);
  const topics: string[] = parseJSON(problem.topics);
  const testCases = problem.test_cases || [];
  const publicTestCases = testCases.filter((tc: any) => tc.is_public);
  const bodyMode = template?.mode === 'body';
  const codeLines = code === '' ? 1 : code.split('\n').length;

  const toggleSubmission = (id: number) => {
    if (expandedSub === id) { setExpandedSub(null); return; }
    setExpandedSub(id);
    if (!subCode[id]) {
      api.get(`/submissions/${id}`).then(r => {
        setSubCode(prev => ({ ...prev, [id]: r.data.source_code }));
      }).catch(() => {});
    }
  };

  return (
    <div className="problem-detail-layout">
      {/* Left Panel */}
      <div className="problem-description-panel">
        <div className="left-tabs">
          <button className={`left-tab ${leftTab === 'description' ? 'active' : ''}`} onClick={() => setLeftTab('description')}>Description</button>
          <button className={`left-tab ${leftTab === 'solutions' ? 'active' : ''}`} onClick={() => setLeftTab('solutions')}>Solutions</button>
          <button className={`left-tab ${leftTab === 'submissions' ? 'active' : ''}`} onClick={() => setLeftTab('submissions')}>Submissions</button>
          <button className={`left-tab ${leftTab === 'discussion' ? 'active' : ''}`} onClick={() => setLeftTab('discussion')}>Discussion</button>
          <button className={`left-tab ${leftTab === 'ai' ? 'active' : ''}`} onClick={() => setLeftTab('ai')}>AI Assistant</button>
        </div>

        {leftTab === 'description' && (
          <div className="left-tab-content">
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
              <Link to="/problems" style={{ color: 'var(--text-muted)', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="15 18 9 12 15 6"/>
                </svg>
                All Problems
              </Link>
              <button
                className={`star-toggle ${favorited ? 'on' : ''}`}
                onClick={toggleFavorite}
                title={favorited ? 'Remove star' : 'Star this problem'}
                aria-label="Toggle starred"
              >
                <svg width="15" height="15" viewBox="0 0 24 24" fill={favorited ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
                </svg>
                {favorited ? 'Starred' : 'Star'}
              </button>
            </div>
            <h1>{problem.title}</h1>
            <div className="problem-meta">
              <span className={`difficulty-badge ${problem.difficulty}`}>{problem.difficulty}</span>
              {topics.map((t: string) => (
                <span key={t} className="topic-tag">{t}</span>
              ))}
              {problem.company && <span className="topic-tag company-tag">{problem.company}</span>}
              {problem.complexity_time && <span className="topic-tag">Time: {problem.complexity_time}</span>}
              {problem.complexity_space && <span className="topic-tag">Space: {problem.complexity_space}</span>}
            </div>
            <div className="problem-description">
              <Markdown content={problem.description || ''} />
            </div>

            {examples.length > 0 && (
              <div style={{ marginBottom: '24px' }}>
                <div className="section-title">Examples</div>
                {examples.map((ex: any, i: number) => (
                  <div key={i} className="example-block">
                    <h4>Example {i + 1}</h4>
                    <div style={{ marginBottom: '6px' }}><strong>Input:</strong> <pre>{ex.input}</pre></div>
                    <div style={{ marginBottom: '6px' }}><strong>Output:</strong> <pre>{ex.output}</pre></div>
                    {ex.explanation && (
                      <div className="example-explanation">
                        <Markdown content={ex.explanation} />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {constraints.length > 0 && (
              <div style={{ marginBottom: '24px' }}>
                <div className="section-title">Constraints</div>
                <ul className="constraints-list">
                  {constraints.map((c: string, i: number) => <li key={i}>{c}</li>)}
                </ul>
              </div>
            )}

            {related.length > 0 && (
              <div style={{ marginBottom: '24px' }}>
                <div className="section-title">Related Problems</div>
                <div className="related-problems">
                  {related.map(rp => (
                    <Link key={rp.id} to={`/problems/${rp.slug}`} className="related-problem-item">
                      <span className={`difficulty-dot ${rp.difficulty}`} />
                      <span className="related-problem-title">{rp.title}</span>
                      {rp.is_solved && (
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--success)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                      )}
                    </Link>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {leftTab === 'solutions' && (
          <div className="left-tab-content">
            <h1>Solutions</h1>
            <div className="problem-meta">
              <span className={`difficulty-badge ${problem.difficulty}`}>{problem.difficulty}</span>
            </div>

            {hints.length > 0 && (
              <div style={{ marginBottom: '24px' }}>
                <div className="section-title">Hints</div>
                {hints.map((h: string, i: number) => (
                  <div key={i} className="hint-item">
                    <span className="hint-number">{i + 1}</span>
                    <span>{h}</span>
                  </div>
                ))}
              </div>
            )}

            {problem.solution_explanation && (
              <div style={{ marginBottom: '24px' }}>
                <div className="section-title">Approach</div>
                <div className="solution-explanation">
                  <Markdown content={problem.solution_explanation} />
                </div>
              </div>
            )}

            {!problem.solution_explanation && hints.length === 0 && (
              <div className="empty-state">
                <p>No solutions available yet. Solve the problem to see the approach!</p>
              </div>
            )}

            {(problem.complexity_time || problem.complexity_space) && (
              <div style={{ marginBottom: '24px' }}>
                <div className="section-title">Complexity Analysis</div>
                <div className="complexity-grid">
                  {problem.complexity_time && (
                    <div className="complexity-card">
                      <span className="complexity-label">Time Complexity</span>
                      <span className="complexity-value">{problem.complexity_time}</span>
                    </div>
                  )}
                  {problem.complexity_space && (
                    <div className="complexity-card">
                      <span className="complexity-label">Space Complexity</span>
                      <span className="complexity-value">{problem.complexity_space}</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {starterCode && Object.keys(starterCode).length > 0 && (
              <div style={{ marginBottom: '24px' }}>
                <div className="section-title">Starter Code</div>
                {Object.entries(starterCode).filter(([k]) => k !== 'solution').map(([lang, c]) => (
                  <div key={lang} className="starter-code-block">
                    <div className="starter-code-header">{LANG_LABELS[lang] || lang}</div>
                    <pre className="starter-code-content">{c as string}</pre>
                  </div>
                ))}
              </div>
            )}

            {starterCode?.solution && (
              <div style={{ marginBottom: '24px' }}>
                <div className="section-title">Solution</div>
                <div className="solution-tabs">
                  {Object.entries(starterCode.solution).map(([lang, c]) => (
                    <SolutionCode key={lang} lang={lang} code={c as string} />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {leftTab === 'submissions' && (
          <div className="left-tab-content">
            <h1>Submissions</h1>
            {submissionsLoading ? (
              <div className="page-loading" style={{ minHeight: '200px' }}><div className="loading-spinner" /></div>
            ) : submissions.length === 0 ? (
              <div className="empty-state">
                <p>No submissions yet. Write code and hit Submit!</p>
              </div>
            ) : (
              <div className="submissions-table">
                <div className="submissions-header">
                  <span>Status</span>
                  <span>Language</span>
                  <span>Runtime</span>
                  <span>Memory</span>
                  <span>Submitted</span>
                </div>
                {submissions.map((sub) => (
                  <div key={sub.id} className="submission-entry">
                    <div
                      className={`submissions-row ${expandedSub === sub.id ? 'expanded' : ''}`}
                      onClick={() => toggleSubmission(sub.id)}
                      role="button"
                      tabIndex={0}
                      onKeyDown={e => { if (e.key === 'Enter') toggleSubmission(sub.id); }}
                      title="View submitted code"
                    >
                      <span className={`submission-status ${sub.status}`}>
                        {SUB_STATUS[sub.status] || sub.status}
                      </span>
                      <span className="submission-lang">{LANG_LABELS[sub.language] || sub.language}</span>
                      <span>{sub.runtime_ms != null ? `${sub.runtime_ms}ms` : '-'}</span>
                      <span>{sub.memory_kb != null ? `${(sub.memory_kb / 1024).toFixed(1)}MB` : '-'}</span>
                      <span className="submission-time">{formatTime(sub.created_at)}</span>
                    </div>
                    {expandedSub === sub.id && (
                      <div className="submission-code">
                        {subCode[sub.id] !== undefined ? (
                          <pre>{subCode[sub.id]}</pre>
                        ) : (
                          <div className="output-info" style={{ padding: '8px 0' }}>Loading code...</div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {leftTab === 'discussion' && (
          <div className="left-tab-content">
            {token ? (
              <Discussions problemId={problem.id} />
            ) : (
              <div className="empty-state">
                <h3>Join the discussion</h3>
                <p>Sign in to read and post approaches, hints and questions.</p>
                <Link to="/login" style={{ marginTop: '12px', display: 'inline-block' }}>
                  <button className="btn btn-primary">Sign In</button>
                </Link>
              </div>
            )}
          </div>
        )}

        {leftTab === 'ai' && (
          <div className="left-tab-content ai-tab-content">
            <AIChat copilot={copilot} variant="tab" title="AI Assistant" />
          </div>
        )}
      </div>

      {/* Right Panel */}
      <div className="code-editor-panel">
        <div className="editor-toolbar">
          <div className="editor-toolbar-left">
            <select className="language-select" value={language} onChange={e => setLanguage(e.target.value)}>
              {Object.entries(LANG_LABELS).map(([key, label]) => (
                <option key={key} value={key}>{label}</option>
              ))}
            </select>
            {bodyMode && (
              <span className="template-badge" title="The class and function signature are predefined. Only the coding block is editable.">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                Template locked
              </span>
            )}
          </div>
          <div className="editor-actions">
            <div className="font-size-stepper">
              <span>Font</span>
              <button className="btn btn-ghost btn-sm" onClick={() => handleFontSizeChange(-1)} aria-label="Decrease font size">−</button>
              <span>{fontSize}</span>
              <button className="btn btn-ghost btn-sm" onClick={() => handleFontSizeChange(1)} aria-label="Increase font size">+</button>
            </div>
            <button className="btn btn-ghost btn-sm" onClick={handleCopyCode} title="Copy code">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
            </button>
            <button className="btn btn-ghost btn-sm" onClick={handleResetCode} title="Reset coding block">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/></svg>
            </button>
            <button className="btn btn-secondary btn-sm" onClick={() => runCode('run')} disabled={running}>
              {running ? (
                <><span className="loading-spinner" style={{ width: '14px', height: '14px', borderWidth: '2px' }} /> Running...</>
              ) : (
                <><svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg> Run</>
              )}
            </button>
            <button className="btn btn-success btn-sm" onClick={() => runCode('submit')} disabled={running} title="Submit (Ctrl+Enter)">
              {running ? 'Submitting...' : 'Submit'}
            </button>
          </div>
        </div>

        {bodyMode && template && (
          <div className={`template-strip ${headerExpanded ? 'expanded' : ''}`}>
            <button
              className="template-strip-bar"
              onClick={() => setHeaderExpanded(v => !v)}
              title={headerExpanded ? 'Collapse template' : 'Expand template'}
            >
              <span className="template-lock-label">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                Locked template
              </span>
              <span className="template-strip-hint">Class &amp; function signature are predefined — write your logic in the coding block below</span>
              <span className="template-strip-toggle">{headerExpanded ? 'Hide' : 'Show'}</span>
            </button>
            <pre className="template-strip-code">{template.header}</pre>
          </div>
        )}

        <div className="code-editor-wrapper">
          <CodeMirror
            value={code}
            onChange={val => setCode(val)}
            extensions={extensions}
            style={{ height: '100%' }}
          />
        </div>

        {bodyMode && template?.footer && (
          <div className="template-footer-strip">
            <pre>{template.footer}</pre>
          </div>
        )}

        <div className="editor-statusbar">
          <span className="statusbar-item">Ln {cursor.line}, Col {cursor.col}{cursor.selected > 0 ? ` (${cursor.selected} selected)` : ''}</span>
          <span className="statusbar-item">{codeLines} lines · {code.length} chars</span>
          <span className="statusbar-spacer" />
          {savedAt && <span className="statusbar-saved">Draft auto-saved</span>}
          <span className="statusbar-item">{LANG_LABELS[language]}</span>
        </div>

        <div className="output-panel">
          <div className="output-tabs">
            <button className={`output-tab ${rightTab === 'testcases' ? 'active' : ''}`} onClick={() => setRightTab('testcases')}>
              Testcases ({publicTestCases.length})
            </button>
            <button className={`output-tab ${rightTab === 'custom' ? 'active' : ''}`} onClick={() => setRightTab('custom')}>
              Custom Test
            </button>
            <button className={`output-tab ${rightTab === 'output' ? 'active' : ''}`} onClick={() => setRightTab('output')}>
              Result
            </button>
          </div>

          {rightTab === 'testcases' && (
            <div>
              <div className="test-case-panel">
                {publicTestCases.map((tc: any, i: number) => (
                  <button key={tc.id || i} className={`test-case-item ${i === activeTestCase ? 'active' : ''}`} onClick={() => setActiveTestCase(i)}>
                    Case {i + 1}
                  </button>
                ))}
                {publicTestCases.length === 0 && <span className="output-info">No public test cases.</span>}
              </div>
              {publicTestCases[activeTestCase] && (
                <div className="output-content">
                  <div style={{ marginBottom: '8px' }}>
                    <span style={{ color: 'var(--text-muted)' }}>Input: </span>
                    <code>{publicTestCases[activeTestCase].input_data}</code>
                  </div>
                  <div>
                    <span style={{ color: 'var(--text-muted)' }}>Expected: </span>
                    <code>{publicTestCases[activeTestCase].expected_output}</code>
                  </div>
                </div>
              )}
            </div>
          )}

          {rightTab === 'custom' && (
            <div className="custom-test">
              <div className="custom-test-header">
                <span className="custom-test-label">Run your code against your own input</span>
                <span className="custom-test-format">Format: <code>nums = [2,7,11,15], target = 9</code></span>
              </div>
              <textarea
                className="custom-test-input"
                value={customInput}
                onChange={e => setCustomInput(e.target.value)}
                placeholder={'nums = [2,7,11,15], target = 9\n\n# or a bare value like:\n# [1,2,3]'}
                spellCheck={false}
                rows={4}
              />
              <div className="custom-test-actions">
                <button className="btn btn-secondary btn-sm" onClick={() => runCode('custom')} disabled={running || !customInput.trim()}>
                  {running ? 'Running...' : 'Run custom test'}
                </button>
                <button className="btn btn-ghost btn-sm" onClick={() => { setCustomInput(''); localStorage.removeItem(customInputKey(slug)); }}>
                  Clear
                </button>
              </div>
            </div>
          )}

          {rightTab === 'output' && (
            <div className="output-content">
              {running && <div className="output-info">Running your code...</div>}
              {!running && !output && <div className="output-info">Run your code to see the result here.</div>}
              {output && <ResultView output={output} />}
            </div>
          )}
        </div>
      </div>

      <button
        className={`ai-fab ${aiPanelOpen ? 'active' : ''}`}
        onClick={() => setAiPanelOpen((open) => {
          const next = !open;
          localStorage.setItem('aiPanelOpen', next ? '1' : '0');
          return next;
        })}
        title="AI assistant (Ctrl+K)"
        aria-label="Toggle AI assistant"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.1" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 2l2.4 6.6L21 11l-6.6 2.4L12 20l-2.4-6.6L3 11l6.6-2.4L12 2z" />
        </svg>
        {!aiPanelOpen && <span className="ai-fab-label">Ask AI</span>}
      </button>

      <AIPanel
        open={aiPanelOpen}
        onClose={() => {
          setAiPanelOpen(false);
          localStorage.setItem('aiPanelOpen', '0');
        }}
        copilot={copilot}
      />
    </div>
  );
}

function ResultView({ output }: { output: any }) {
  if (output.status === 'error') {
    return <div className="output-error">{output.message}</div>;
  }
  const meta = STATUS_META[output.status] || { label: output.status, cls: 'fail' as const };
  const isCustom = output.mode === 'custom';
  const results: any[] = output.test_results || [];

  return (
    <div>
      <div className={`result-banner ${meta.cls}`}>
        <div className="result-banner-main">
          <span className={`result-banner-icon ${meta.cls}`}>
            {meta.cls === 'ok'
              ? <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
              : <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>}
          </span>
          <div>
            <div className="result-banner-title">{meta.label}</div>
            <div className="result-banner-sub">
              {isCustom
                ? 'Your code ran on your custom input'
                : output.passed_count != null && output.total_count != null
                  ? `${output.passed_count} of ${output.total_count} test cases passed`
                  : ''}
            </div>
          </div>
        </div>
        <div className="result-banner-metrics">
          {output.runtime_ms != null && (
            <span className="metric-chip">Runtime: {output.runtime_ms} ms</span>
          )}
          {output.memory_kb != null && output.memory_kb > 0 && (
            <span className="metric-chip">Memory: {(output.memory_kb / 1024).toFixed(1)} MB</span>
          )}
        </div>
      </div>

      {output.error_message && (
        <div className="result-error-message">{output.error_message}</div>
      )}
      {output.stdout && !output.error_message && (
        <div className="result-stdout">
          <div className="result-stdout-label">stdout</div>
          <pre>{output.stdout}</pre>
        </div>
      )}

      {results.length > 0 && (
        <div className="test-results-list">
          {results.map((tr, i) => {
            const showDetail = !tr.passed || isCustom;
            return (
              <div key={i} className={`test-result-item ${tr.passed ? 'pass' : 'fail'}`}>
                <div className="test-result-head">
                  <span className="test-result-icon">{tr.passed ? '\u2713' : '\u2717'}</span>
                  <span>Case {tr.test_number ?? i + 1}</span>
                  {!tr.passed && !isCustom && <span className="test-result-fail-label">failed</span>}
                </div>
                {showDetail && (
                  <div className="test-result-grid">
                    <div>
                      <span className="trg-label">Input</span>
                      <pre>{tr.input_data || '(none)'}</pre>
                    </div>
                    {!isCustom && (
                      <div>
                        <span className="trg-label">Expected</span>
                        <pre>{tr.expected_output || '(empty)'}</pre>
                      </div>
                    )}
                    <div>
                      <span className="trg-label">{isCustom ? 'Output' : 'Got'}</span>
                      <pre>{tr.actual_output || tr.got || '(empty)'}</pre>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function formatTime(iso: string): string {
  try {
    const d = new Date(iso);
    const now = new Date();
    const diff = now.getTime() - d.getTime();
    if (diff < 60000) return 'just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return d.toLocaleDateString();
  } catch { return iso; }
}

function SolutionCode({ lang, code }: { lang: string; code: string }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <div className="starter-code-block">
      <div className="starter-code-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span>{LANG_LABELS[lang] || lang}</span>
        <button className="btn btn-ghost btn-sm" onClick={copy} style={{ fontSize: '11px', padding: '2px 8px' }}>
          {copied ? 'Copied!' : 'Copy'}
        </button>
      </div>
      <pre className="starter-code-content">{code}</pre>
    </div>
  );
}
