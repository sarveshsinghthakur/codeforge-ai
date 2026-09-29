import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../App';
import api from '../lib/api';

export default function Dashboard() {
  const { token, user } = useAuth();
  const [profile, setProfile] = useState<any>(null);
  const [submissions, setSubmissions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    Promise.all([
      api.get('/users/me/dashboard').catch(() => ({ data: null })),
      api.get('/users/me/submissions?limit=10').catch(() => ({ data: [] })),
    ]).then(([profileRes, subsRes]) => {
      setProfile(profileRes.data);
      setSubmissions(subsRes.data);
      setLoading(false);
    });
  }, [token]);

  if (!token) {
    return (
      <div className="page-container">
        <div className="empty-state">
          <h3>Please log in</h3>
          <p style={{ marginBottom: '16px' }}>Sign in to view your dashboard</p>
          <Link to="/login"><button className="btn btn-primary">Sign In</button></Link>
        </div>
      </div>
    );
  }

  if (loading) {
    return <div className="page-loading"><div className="loading-spinner" /></div>;
  }

  const LANG_LABELS: Record<string, string> = { python: 'Python', javascript: 'JavaScript', java: 'Java' };
  const statusMap: Record<string, string> = {
    accepted: 'Accepted',
    wrong_answer: 'Wrong Answer',
    runtime_error: 'Runtime Error',
    time_limit: 'TLE',
    pending: 'Pending',
  };

  return (
    <div className="page-container">
      <h1 style={{ fontSize: '28px', fontWeight: 800, marginBottom: '8px', letterSpacing: '-0.5px' }}>
        {profile?.display_name || user?.username || 'Your'} Dashboard
      </h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '32px' }}>
        Track your progress and recent activity
      </p>

      <div className="dashboard-grid">
        <div className="dashboard-card">
          <div className="label">Problems Solved</div>
          <div className="value">{profile?.problems_solved || 0}</div>
        </div>
        <div className="dashboard-card">
          <div className="label">Total Submissions</div>
          <div className="value">{profile?.submission_count || 0}</div>
        </div>
        <div className="dashboard-card">
          <div className="label">Acceptance Rate</div>
          <div className="value">{profile?.acceptance_rate || 0}%</div>
        </div>
        <div className="dashboard-card">
          <div className="label">Easy / Medium / Hard</div>
          <div className="value" style={{ fontSize: '20px' }}>
            <span style={{ color: 'var(--easy)' }}>{profile?.easy_solved || 0}</span>
            <span style={{ color: 'var(--text-muted)' }}> / </span>
            <span style={{ color: 'var(--medium)' }}>{profile?.medium_solved || 0}</span>
            <span style={{ color: 'var(--text-muted)' }}> / </span>
            <span style={{ color: 'var(--hard)' }}>{profile?.hard_solved || 0}</span>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        <div className="glass-card" style={{ padding: '24px' }}>
          <h2 style={{ fontSize: '18px', fontWeight: 700, marginBottom: '16px' }}>Recent Submissions</h2>
          {submissions.length === 0 ? (
            <div className="empty-state" style={{ padding: '30px' }}>
              <p>No submissions yet</p>
              <Link to="/problems" style={{ marginTop: '12px', display: 'inline-block' }}>
                <button className="btn btn-secondary btn-sm">Solve a Problem</button>
              </Link>
            </div>
          ) : (
            <div className="recent-list">
              {submissions.map((sub: any) => (
                <Link to={`/problems/${sub.problem_slug}`} key={sub.id} className="recent-item" style={{ color: 'inherit' }}>
                  <div className={`recent-status ${sub.status}`} />
                  <span className="recent-title">{sub.problem_title}</span>
                  <span className="recent-meta">{LANG_LABELS[sub.language] || sub.language}</span>
                  <span className="recent-meta" style={{ color: sub.status === 'accepted' ? 'var(--success)' : 'var(--error)' }}>
                    {statusMap[sub.status] || sub.status}
                  </span>
                </Link>
              ))}
            </div>
          )}
        </div>

        <div className="glass-card" style={{ padding: '24px' }}>
          <h2 style={{ fontSize: '18px', fontWeight: 700, marginBottom: '16px' }}>Quick Actions</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <Link to="/problems">
              <button className="btn btn-secondary" style={{ width: '100%', justifyContent: 'flex-start' }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
                </svg>
                Browse All Problems
              </button>
            </Link>
            <Link to="/problems?difficulty=easy">
              <button className="btn btn-secondary" style={{ width: '100%', justifyContent: 'flex-start' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--easy)', display: 'inline-block' }} />
                Practice Easy Problems
              </button>
            </Link>
            <Link to="/problems?difficulty=medium">
              <button className="btn btn-secondary" style={{ width: '100%', justifyContent: 'flex-start' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--medium)', display: 'inline-block' }} />
                Challenge Medium Problems
              </button>
            </Link>
            <Link to="/problems?difficulty=hard">
              <button className="btn btn-secondary" style={{ width: '100%', justifyContent: 'flex-start' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--hard)', display: 'inline-block' }} />
                Tackle Hard Problems
              </button>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
