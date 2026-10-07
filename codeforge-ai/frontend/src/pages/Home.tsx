import { Link } from 'react-router-dom';
import { useAuth } from '../App';
import { useState, useEffect } from 'react';
import api from '../lib/api';

export default function Home() {
  const { token } = useAuth();
  const [stats, setStats] = useState({ total: 0, easy: 0, medium: 0, hard: 0 });
  const [daily, setDaily] = useState<any>(null);

  useEffect(() => {
    api.get('/problems/stats').then(res => {
      setStats({
        total: res.data.total || 0,
        easy: res.data.easy || 0,
        medium: res.data.medium || 0,
        hard: res.data.hard || 0,
      });
    }).catch(() => {});
    api.get('/problems/daily').then(res => setDaily(res.data)).catch(() => {});
  }, []);

  return (
    <div className="page-container" style={{ maxWidth: '100%', padding: 0 }}>
      <div className="hero">
        <h1>Master Your<br /><span>Coding Skills</span></h1>
        <p>Practice algorithms, data structures, and system design with curated challenges and instant code execution.</p>
        <div className="hero-actions">
          <Link to="/problems">
            <button className="btn btn-primary btn-lg">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="16 18 22 12 16 6" /><polyline points="8 6 2 12 8 18" />
              </svg>
              Start Coding
            </button>
          </Link>
          {!token && (
            <Link to="/register">
              <button className="btn btn-secondary btn-lg">Create Free Account</button>
            </Link>
          )}
          {token && (
            <Link to="/dashboard">
              <button className="btn btn-secondary btn-lg">My Dashboard</button>
            </Link>
          )}
        </div>

        <div className="difficulty-bar">
          <div className="difficulty-item">
            <div className="difficulty-dot easy" />
            <span className="difficulty-text"><span className="difficulty-count">{stats.easy}</span> Easy</span>
          </div>
          <div className="difficulty-item">
            <div className="difficulty-dot medium" />
            <span className="difficulty-text"><span className="difficulty-count">{stats.medium}</span> Medium</span>
          </div>
          <div className="difficulty-item">
            <div className="difficulty-dot hard" />
            <span className="difficulty-text"><span className="difficulty-count">{stats.hard}</span> Hard</span>
          </div>
        </div>

        <div className="stats-row">
          <div className="stat-item">
            <div className="stat-number">{stats.total}+</div>
            <div className="stat-label">Problems</div>
          </div>
          <div className="stat-item">
            <div className="stat-number">3</div>
            <div className="stat-label">Languages</div>
          </div>
          <div className="stat-item">
            <div className="stat-number">3</div>
            <div className="stat-label">Difficulties</div>
          </div>
        </div>

        {daily && (
          <div className="glass-card" style={{ maxWidth: '1000px', margin: '40px auto 0', padding: '20px 24px', display: 'flex', gap: '16px', alignItems: 'center', flexWrap: 'wrap' }}>
            <span className={`difficulty-badge ${daily.difficulty}`}>{daily.difficulty}</span>
            <div style={{ flex: 1, minWidth: '220px' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '4px' }}>
                Problem of the day
              </div>
              <Link to={`/problems/${daily.slug}`} style={{ fontWeight: 700, fontSize: '17px', color: 'inherit' }}>
                {daily.title}
              </Link>
              <div style={{ marginTop: '6px', display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                {(daily.topics || []).slice(0, 3).map((t: string) => <span key={t} className="topic-tag">{t}</span>)}
              </div>
            </div>
            <Link to={`/problems/${daily.slug}`}>
              <button className="btn btn-primary">Solve it</button>
            </Link>
          </div>
        )}

        <div className="features-grid" style={{ maxWidth: '1000px', margin: '60px auto 0', padding: '0 24px' }}>
          <div className="feature-card">
            <div className="feature-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="16 18 22 12 16 6" /><polyline points="8 6 2 12 8 18" />
              </svg>
            </div>
            <h3>Online Code Editor</h3>
            <p>Write and run code directly in your browser with syntax highlighting, auto-completion, and multi-language support.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/>
                <path d="M9 12l2 2 4-4"/>
              </svg>
            </div>
            <h3>Instant Feedback</h3>
            <p>Get immediate results with detailed test case analysis, runtime metrics, and memory usage breakdown.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/>
                <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>
              </svg>
            </div>
            <h3>Curated Problems</h3>
            <p>Hand-picked algorithm challenges covering arrays, trees, graphs, dynamic programming, and more.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
