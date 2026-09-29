import { useState, useEffect } from 'react';
import { useAuth } from '../App';
import api from '../lib/api';

export default function AdminProblemGenerator() {
  const { token } = useAuth();
  const [prompt, setPrompt] = useState('');
  const [generated, setGenerated] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  if (!token) return <div className="page-container"><div className="empty-state"><h3>Admin required</h3></div></div>;

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    setLoading(true);
    setError('');
    try {
      const res = await api.post('/admin/problems/generate', { prompt });
      setGenerated(res.data);
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Failed to generate problem');
    }
    setLoading(false);
  };

  const handlePublish = async () => {
    if (!generated || !generated.generated_data) return;
    setLoading(true);
    try {
      const data = JSON.parse(generated.generated_data);
      await api.post('/admin/problems', data);
      alert('Problem published!');
      setGenerated(null);
      setPrompt('');
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Failed to publish');
    }
    setLoading(false);
  };

  return (
    <div className="page-container">
      <h1 style={{ fontSize: '28px', fontWeight: 800, marginBottom: '8px' }}>AI Problem Generator</h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '32px' }}>
        Describe the problem you want to create. The AI will generate a complete problem with
        description, constraints, examples, starter code in 5 languages, test cases, and reference solution.
      </p>

      <div className="glass-card" style={{ padding: '32px', maxWidth: '900px' }}>
        <div style={{ marginBottom: '24px' }}>
          <label style={{ display: 'block', fontWeight: 500, marginBottom: '8px', fontSize: '14px' }}>
            Problem Description Prompt
          </label>
          <textarea
            value={prompt}
            onChange={e => setPrompt(e.target.value)}
            rows={6}
            placeholder="Create a medium-level sliding window problem involving strings and character frequencies..."
            style={{ width: '100%', background: 'var(--bg-tertiary)', border: '1px solid var(--border-color)', color: 'var(--text-primary)', padding: '12px', borderRadius: 'var(--radius-md)', fontSize: '14px', fontFamily: 'var(--font-sans)', resize: 'vertical' }}
          />
          {error && <div className="form-error" style={{ marginTop: '8px' }}>{error}</div>}
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          <button className="btn btn-primary btn-lg" onClick={handleGenerate} disabled={loading || !prompt.trim()}>
            {loading ? 'Generating...' : 'Generate Problem'}
          </button>
          {generated && generated.status === 'completed' && (
            <button className="btn btn-success btn-lg" onClick={handlePublish} disabled={loading}>
              Publish Problem
            </button>
          )}
        </div>

        {generated && generated.status === 'completed' && (
          <div style={{ marginTop: '32px', paddingTop: '24px', borderTop: '1px solid var(--border-color)' }}>
            <h2 style={{ fontSize: '20px', fontWeight: 700, marginBottom: '16px' }}>Generated Preview</h2>
            <AdminProblemPreview data={JSON.parse(generated.generated_data)} />
          </div>
        )}

        {generated && generated.status === 'failed' && (
          <div style={{ marginTop: '16px', padding: '16px', background: 'var(--error-dim)', border: '1px solid var(--error)', borderRadius: 'var(--radius-md)', color: 'var(--error)' }}>
            <strong>Generation failed:</strong> {generated.error_message}
          </div>
        )}
      </div>
    </div>
  );
}

function AdminProblemPreview({ data }: { data: any }) {
  return (
    <div style={{ maxHeight: '600px', overflow: 'auto' }}>
      <div style={{ marginBottom: '12px' }}>
        <strong style={{ color: 'var(--text-muted)', fontSize: '12px', textTransform: 'uppercase' }}>Title:</strong>
        <div style={{ fontSize: '18px', fontWeight: '600', marginTop: '4px' }}>{data.title}</div>
      </div>
      <div style={{ marginBottom: '12px', display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
        <span className={`difficulty-badge ${data.difficulty}`}>{data.difficulty}</span>
        {data.topics?.map((t: string) => <span key={t} className="topic-tag">{t}</span>)}
        {data.company && <span className="topic-tag">{data.company}</span>}
      </div>
      <div style={{ marginBottom: '12px' }}>
        <strong style={{ color: 'var(--text-muted)', fontSize: '12px', textTransform: 'uppercase' }}>Description:</strong>
        <div className="problem-description" style={{ marginTop: '8px' }} dangerouslySetInnerHTML={{ __html: formatDesc(data.description) }} />
      </div>
      <div style={{ marginBottom: '12px' }}>
        <strong style={{ color: 'var(--text-muted)', fontSize: '12px', textTransform: 'uppercase' }}>Constraints:</strong>
        <ul style={{ marginTop: '8px', paddingLeft: '20px', color: 'var(--text-secondary)' }}>
          {data.constraints?.map((c: string) => <li key={c}>{c}</li>)}
        </ul>
      </div>
      <div style={{ marginBottom: '12px' }}>
        <strong style={{ color: 'var(--text-muted)', fontSize: '12px', textTransform: 'uppercase' }}>Examples:</strong>
        {data.examples?.map((ex: any, i: number) => (
          <div key={i} className="example-block" style={{ marginTop: '12px' }}>
            <strong>Example {i + 1}</strong>
            <div style={{ marginTop: '8px' }}><strong>Input:</strong> <pre>{ex.input}</pre></div>
            <div style={{ marginTop: '8px' }}><strong>Output:</strong> <pre>{ex.output}</pre></div>
            {ex.explanation && <div className="example-explanation" style={{ marginTop: '8px' }}>{ex.explanation}</div>}
          </div>
        ))}
      </div>
      <div style={{ marginBottom: '12px' }}>
        <strong style={{ color: 'var(--text-muted)', fontSize: '12px', textTransform: 'uppercase' }}>Hints:</strong>
        <ul style={{ marginTop: '8px', paddingLeft: '20px', color: 'var(--text-secondary)' }}>
          {data.hints?.map((h: string, i: number) => <li key={i}>{h}</li>)}
        </ul>
      </div>
      <div style={{ marginBottom: '12px' }}>
        <strong style={{ color: 'var(--text-muted)', fontSize: '12px', textTransform: 'uppercase' }}>Complexity:</strong>
        <div style={{ display: 'flex', gap: '16px', marginTop: '8px' }}>
          <span><strong>Time:</strong> {data.complexity?.time || data.complexity_time}</span>
          <span><strong>Space:</strong> {data.complexity?.space || data.complexity_space}</span>
        </div>
      </div>
      <div style={{ marginBottom: '12px' }}>
        <strong style={{ color: 'var(--text-muted)', fontSize: '12px', textTransform: 'uppercase' }}>Starter Code (Python):</strong>
        <pre style={{ marginTop: '8px', background: 'var(--bg-tertiary)', padding: '12px', borderRadius: 'var(--radius-md)', overflow: 'auto', fontSize: '13px', fontFamily: 'var(--font-mono)' }}>
          {data.starter_code?.python || '// Not provided'}
        </pre>
      </div>
      <div>
        <strong style={{ color: 'var(--text-muted)', fontSize: '12px', textTransform: 'uppercase' }}>Test Cases: {data.test_cases?.length || 0}</strong>
        <div style={{ marginTop: '8px', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {data.test_cases?.slice(0, 5).map((tc: any, i: number) => (
            <div key={i} style={{ background: 'var(--bg-tertiary)', padding: '8px 12px', borderRadius: 'var(--radius-sm)', fontSize: '12px', fontFamily: 'var(--font-mono)', border: '1px solid var(--border-color)' }}>
              <div>In: {tc.input}</div>
              <div>Out: {tc.output}</div>
            </div>
          ))}
          {(data.test_cases?.length || 0) > 5 && <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>... and {(data.test_cases?.length || 0) - 5} more</span>}
        </div>
      </div>
    </div>
  );
}

function formatDesc(desc: string): string {
  if (!desc) return '';
  return desc.replace(/`([^`]+)`/g, '<code>$1</code>').replace(/\n/g, '<br/>');
}