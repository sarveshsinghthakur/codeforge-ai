import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import CodeMirror from '@uiw/react-codemirror';
import { python } from '@codemirror/lang-python';
import { javascript } from '@codemirror/lang-javascript';
import { java } from '@codemirror/lang-java';
import { EditorView } from '@codemirror/view';
import api from '../lib/api';
import { useCopilot } from '../lib/copilot';
import AIChat from '../components/ai/AIChat';
import AIPanel from '../components/ai/AIPanel';

const LANG_MAP: Record<string, any> = { python: python(), javascript: javascript(), java: java() };
const LANG_LABELS: Record<string, string> = { python: 'Python 3', javascript: 'JavaScript', java: 'Java' };

interface Submission {
  id: number; public_id: string; language: string; status: string;
  runtime_ms: number | null; memory_kb: number | null; created_at: string;
}

export default function ProblemDetail() {
  const { slug } = useParams();
  const [problem, setProblem] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [language, setLanguage] = useState('python');
  const [code, setCode] = useState('');
  const [output, setOutput] = useState<any>(null);
  const [running, setRunning] = useState(false);
  const [leftTab, setLeftTab] = useState<'description' | 'solutions' | 'submissions' | 'ai'>('description');
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [submissionsLoading, setSubmissionsLoading] = useState(false);
  const [activeTestCase, setActiveTestCase] = useState(0);
  const [rightTab, setRightTab] = useState<'testcases' | 'output'>('testcases');
  const [fontSize, setFontSize] = useState(() => parseInt(localStorage.getItem('editorFontSize') || '14'));
  const [aiPanelOpen, setAiPanelOpen] = useState(() => localStorage.getItem('aiPanelOpen') === '1');
  const [lastRunResult, setLastRunResult] = useState<any>(null);

  const copilot = useCopilot({
    problemId: problem?.id ?? null,
    language,
    getCode: () => code,
    getRunResult: () => lastRunResult,
  });

  const parseJSON = (s: string) => { try { return JSON.parse(s); } catch { return []; } };

  useEffect(() => {
    setLoading(true);
    api.get(`/problems/slug/${slug}`).then(res => {
      const p = res.data;
      setProblem(p);
      try {
        const sc = JSON.parse(p.starter_code || '{}');
        setCode(sc[language] || '');
      } catch { setCode(''); }
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [slug]);

  useEffect(() => {
    if (problem) {
      try {
        const sc = JSON.parse(problem.starter_code || '{}');
        setCode(sc[language] || '');
      } catch { setCode(''); }
    }
  }, [language, problem]);

useEffect(() => {
    if (leftTab === 'submissions' && problem) {
      setSubmissionsLoading(true);
      api.get(`/problems/slug/${slug}/submissions`).then(res => {
        setSubmissions(res.data);
        setSubmissionsLoading(false);
      }).catch(() => setSubmissionsLoading(false));
    }
  }, [leftTab, problem, slug]);

  // Auto-save draft
  useEffect(() => {
    const key = `draft:${slug}:${language}`;
    localStorage.setItem(key, code);
  }, [code, slug, language]);

  // Load draft on mount
  useEffect(() => {
    const key = `draft:${slug}:${language}`;
    const saved = localStorage.getItem(key);
    if (saved) setCode(saved);
  }, [slug, language]);

  const handleFontSizeChange = (delta: number) => {
    setFontSize(prev => {
      const next = Math.max(12, Math.min(24, prev + delta));
      localStorage.setItem('editorFontSize', next.toString());
      return next;
    });
  };

  const handleResetCode = () => {
    if (problem) {
      try {
        const sc = JSON.parse(problem.starter_code || '{}');
        setCode(sc[language] || '');
      } catch { setCode(''); }
    }
  };

const handleCopyCode = () => {
    navigator.clipboard.writeText(code);
  };

  const runCode = async (mode: 'run' | 'submit') => {
    if (!problem || running) return;
    setRunning(true);
    setOutput(null);
    setRightTab('output');
    try {
      const res = await api.post('/submissions', {
        problem_id: problem.id,
        source_code: code,
        language,
        mode,
      });
      const data = { ...res.data, mode };
      setOutput(data);
      setLastRunResult(data);
      if (mode === 'submit' && leftTab !== 'submissions') {
        api.get(`/problems/slug/${slug}/submissions`).then(res => setSubmissions(res.data));
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const data = {
        status: 'error',
        message: typeof detail === 'object' ? detail.message || JSON.stringify(detail) : detail || 'Failed to submit',
        mode,
      };
      setOutput(data);
      setLastRunResult(data);
    }
    setRunning(false);
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        runCode('submit');
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
  }, [runCode, code, slug, language]);

  if (loading) {
    return <div className="page-loading"><div className="loading-spinner" /></div>;
  }
  if (!problem) {
    return <div className="page-container"><div className="empty-state"><h3>Problem not found</h3><Link to="/problems"><button className="btn btn-secondary" style={{ marginTop: '12px' }}>Back to Problems</button></Link></div></div>;
  }

  const examples = parseJSON(problem.examples);
  const hints = parseJSON(problem.hints);
  const constraints = parseJSON(problem.constraints);
  const starterCode = parseJSON(problem.starter_code);
  const testCases = problem.test_cases || [];
  const publicTestCases = testCases.filter((tc: any) => tc.is_public);

  return (
    <div className="problem-detail-layout">
      {/* Left Panel */}
      <div className="problem-description-panel">
        <div className="left-tabs">
          <button className={`left-tab ${leftTab === 'description' ? 'active' : ''}`} onClick={() => setLeftTab('description')}>Description</button>
          <button className={`left-tab ${leftTab === 'solutions' ? 'active' : ''}`} onClick={() => setLeftTab('solutions')}>Solutions</button>
          <button className={`left-tab ${leftTab === 'submissions' ? 'active' : ''}`} onClick={() => setLeftTab('submissions')}>Submissions</button>
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
            </div>
            <h1>{problem.title}</h1>
            <div className="problem-meta">
              <span className={`difficulty-badge ${problem.difficulty}`}>{problem.difficulty}</span>
              {Array.isArray(parseJSON(problem.topics)) && parseJSON(problem.topics).map((t: string) => (
                <span key={t} className="topic-tag">{t}</span>
              ))}
              {problem.complexity_time && <span className="topic-tag">Time: {problem.complexity_time}</span>}
              {problem.complexity_space && <span className="topic-tag">Space: {problem.complexity_space}</span>}
            </div>
            <div className="problem-description" dangerouslySetInnerHTML={{ __html: formatDescription(problem.description) }} />

            {examples.length > 0 && (
              <div style={{ marginBottom: '24px' }}>
                <div className="section-title">Examples</div>
                {examples.map((ex: any, i: number) => (
                  <div key={i} className="example-block">
                    <h4>Example {i + 1}</h4>
                    <div style={{ marginBottom: '6px' }}><strong>Input:</strong> <pre>{ex.input}</pre></div>
                    <div style={{ marginBottom: '6px' }}><strong>Output:</strong> <pre>{ex.output}</pre></div>
                    {ex.explanation && <div className="example-explanation">{ex.explanation}</div>}
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
                <div className="solution-explanation" dangerouslySetInnerHTML={{ __html: formatDescription(problem.solution_explanation) }} />
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
                {Object.entries(starterCode).filter(([k]) => k !== 'solution').map(([lang, code]) => (
                  <div key={lang} className="starter-code-block">
                    <div className="starter-code-header">{LANG_LABELS[lang] || lang}</div>
                    <pre className="starter-code-content">{code as string}</pre>
                  </div>
                ))}
              </div>
            )}

            {starterCode?.solution && (
              <div style={{ marginBottom: '24px' }}>
                <div className="section-title">Solution</div>
                <div className="solution-tabs">
                  {Object.entries(starterCode.solution).map(([lang, code]) => (
                    <SolutionCode key={lang} lang={lang} code={code as string} />
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
                  <div key={sub.id} className="submissions-row">
                    <span className={`submission-status ${sub.status}`}>
                      {sub.status === 'accepted' ? 'Accepted' : sub.status === 'wrong_answer' ? 'Wrong Answer' : sub.status === 'runtime_error' ? 'Runtime Error' : sub.status === 'time_limit' ? 'TLE' : sub.status}
                    </span>
                    <span className="submission-lang">{LANG_LABELS[sub.language] || sub.language}</span>
                    <span>{sub.runtime_ms != null ? `${sub.runtime_ms}ms` : '-'}</span>
                    <span>{sub.memory_kb != null ? `${(sub.memory_kb / 1024).toFixed(1)}MB` : '-'}</span>
                    <span className="submission-time">{formatTime(sub.created_at)}</span>
                  </div>
                ))}
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
          <select className="language-select" value={language} onChange={e => setLanguage(e.target.value)}>
            {Object.entries(LANG_LABELS).map(([key, label]) => (
              <option key={key} value={key}>{label}</option>
            ))}
          </select>
          <div className="editor-actions" style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginRight: '8px', padding: '0 8px', borderRight: '1px solid var(--border-color)' }}>
              <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Font:</span>
              <button className="btn btn-ghost btn-sm" onClick={() => handleFontSizeChange(-1)} style={{ padding: '2px 6px' }} aria-label="Decrease font size">−</button>
              <span style={{ fontSize: '12px', minWidth: '24px', textAlign: 'center' }}>{fontSize}</span>
              <button className="btn btn-ghost btn-sm" onClick={() => handleFontSizeChange(1)} style={{ padding: '2px 6px' }} aria-label="Increase font size">+</button>
            </div>
            <button className="btn btn-ghost btn-sm" onClick={handleCopyCode} title="Copy code (Ctrl+Shift+C)">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
            </button>
            <button className="btn btn-ghost btn-sm" onClick={handleResetCode} title="Reset to starter code">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/></svg>
            </button>
            <button className="btn btn-secondary btn-sm" onClick={() => runCode('run')} disabled={running}>
              {running ? (
                <><span className="loading-spinner" style={{ width: '14px', height: '14px', borderWidth: '2px' }} /> Running...</>
              ) : (
                <><svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg> Run</>
              )}
            </button>
            <button className="btn btn-success btn-sm" onClick={() => runCode('submit')} disabled={running}>
              {running ? 'Submitting...' : 'Submit'}
            </button>
          </div>
        </div>

<div className="code-editor-wrapper">
          <CodeMirror
            value={code}
            onChange={val => setCode(val)}
            extensions={[LANG_MAP[language], EditorView.theme({
              '&': { backgroundColor: '#0d0d0d', height: '100%', color: '#e0e0e0', fontSize: `${fontSize}px` },
              '.cm-scroller': { fontFamily: 'var(--font-mono)', fontSize: `${fontSize}px` },
              '.cm-gutters': { backgroundColor: '#0d0d0d', borderRight: '1px solid rgba(255,255,255,0.06)', color: '#555' },
              '.cm-activeLine': { backgroundColor: 'rgba(255,255,255,0.03)' },
              '.cm-activeLineGutter': { backgroundColor: 'rgba(255,255,255,0.03)', color: '#888' },
              '.cm-content': { color: '#e0e0e0', caretColor: '#fff' },
              '.cm-cursor': { borderLeftColor: '#fff' },
              '.cm-selectionBackground': { background: 'rgba(255,255,255,0.12)' },
              '&.cm-focused .cm-selectionBackground': { background: 'rgba(255,255,255,0.15)' },
              '.cm-line': { color: '#e0e0e0' },
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
              '.cm-matchingBracket': { background: 'rgba(255,255,255,0.15)', outline: '1px solid rgba(255,255,255,0.3)' },
            })]}
            style={{ height: '100%' }}
          />
        </div>

        <div className="output-panel">
          <div className="output-tabs">
            <button className={`output-tab ${rightTab === 'testcases' ? 'active' : ''}`} onClick={() => setRightTab('testcases')}>
              Testcases ({publicTestCases.length})
            </button>
            <button className={`output-tab ${rightTab === 'output' ? 'active' : ''}`} onClick={() => setRightTab('output')}>
              Output
            </button>
          </div>

          {rightTab === 'testcases' && (
            <div>
              <div className="test-case-panel">
                {publicTestCases.map((tc: any, i: number) => (
                  <button key={tc.id} className={`test-case-item ${i === activeTestCase ? 'active' : ''}`} onClick={() => setActiveTestCase(i)}>
                    Case {i + 1}
                  </button>
                ))}
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

          {rightTab === 'output' && (
            <div className="output-content">
              {running && <div className="output-info">Running your code...</div>}
              {!running && !output && <div className="output-info">Run your code to see output here.</div>}
              {output && (
                <div>
                  {output.status === 'error' ? (
                    <div className="output-error">{output.message}</div>
                  ) : (
                    <div>
                      <div style={{ marginBottom: '8px' }}>
                        <strong className={output.status === 'accepted' ? 'output-success' : 'output-error'}>
                          {output.status === 'accepted' ? 'Accepted' : output.status === 'wrong_answer' ? 'Wrong Answer' : output.status === 'runtime_error' ? 'Runtime Error' : output.status === 'time_limit' ? 'Time Limit Exceeded' : output.status}
                        </strong>
                        {output.passed_count != null && output.total_count != null && (
                          <span className="output-info" style={{ marginLeft: '12px' }}>
                            {output.passed_count}/{output.total_count} testcases passed
                          </span>
                        )}
                      </div>
                      {output.test_results && (
                        <div className="test-results-list">
                          {output.test_results.map((tr: any, i: number) => (
                            <div key={i} className={`test-result-item ${tr.passed ? 'pass' : 'fail'}`}>
                              <span className="test-result-icon">{tr.passed ? '\u2713' : '\u2717'}</span>
                              <span>Test {i + 1}</span>
                              {!tr.passed && (
                                <div className="test-result-detail">
                                  <div>Got: {tr.actual_output || tr.got || ''}</div>
                                  <div>Expected: {tr.expected_output || tr.expected || ''}</div>
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                      {output.runtime_ms != null && (
                        <div className="output-info" style={{ marginTop: '8px' }}>
                          Runtime: {output.runtime_ms}ms | Memory: {output.memory_kb != null ? `${(output.memory_kb / 1024).toFixed(1)}MB` : 'N/A'}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
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

function formatDescription(desc: string): string {
  if (!desc) return '';
  return desc.replace(/`([^`]+)`/g, '<code>$1</code>').replace(/\n/g, '<br/>');
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
