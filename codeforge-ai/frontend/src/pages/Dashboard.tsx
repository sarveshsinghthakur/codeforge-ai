import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../App';
import api from '../lib/api';

interface DashboardData {
  stats: {
    problems_solved: number;
    easy_solved: number;
    medium_solved: number;
    hard_solved: number;
    easy_total: number;
    medium_total: number;
    hard_total: number;
    submission_count: number;
    acceptance_rate: number;
    current_streak: number;
    longest_streak: number;
    total_problems_attempted: number;
    favorites_count: number;
    time_spent_seconds: number;
  };
  activity_calendar: { date: string; count: number }[];
  topic_progress: { topic: string; solved: number; attempted: number; percentage: number }[];
  recent_submissions: any[];
  recent_problems: any[];
}

const LANG_LABELS: Record<string, string> = { python: 'Python', javascript: 'JavaScript', java: 'Java' };
const STATUS_MAP: Record<string, string> = {
  accepted: 'Accepted',
  wrong_answer: 'Wrong Answer',
  runtime_error: 'Runtime Error',
  time_limit: 'TLE',
  pending: 'Pending',
  completed: 'Completed',
};

function daysAgoISO(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString().slice(0, 10);
}

function fmtDuration(totalSeconds: number): string {
  const s = Math.max(0, totalSeconds || 0);
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  if (h > 0) return `${h}h ${m}m`;
  if (m > 0) return `${m}m`;
  return `${s}s`;
}

function MonthlyChart({ calendar }: { calendar: { date: string; count: number }[] }) {
  const now = new Date();
  const months: { key: string; label: string; total: number }[] = [];
  for (let i = 11; i >= 0; i--) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
    const label = d.toLocaleString('en', { month: 'short' }) + (d.getMonth() === 0 ? ` '${String(d.getFullYear()).slice(2)}` : '');
    months.push({ key, label, total: 0 });
  }
  const byKey = new Map(months.map(m => [m.key, m]));
  for (const p of calendar || []) {
    const m = byKey.get(p.date.slice(0, 7));
    if (m) m.total += p.count;
  }
  const max = Math.max(1, ...months.map(m => m.total));
  const grand = months.reduce((a, m) => a + m.total, 0);

  if (grand === 0) {
    return <p className="muted-note">No activity yet — monthly graph fills in as you submit.</p>;
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'flex-end', gap: '6px', height: '140px', marginTop: '4px' }}>
        {months.map(m => {
          const pct = Math.round((m.total / max) * 100);
          return (
            <div key={m.key} title={`${m.label}: ${m.total} submission${m.total === 1 ? '' : 's'}`}
              style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px', height: '100%', justifyContent: 'flex-end', minWidth: 0 }}>
              <span style={{ fontSize: '10px', color: 'var(--text-secondary)', fontFamily: 'var(--font-mono)' }}>{m.total || ''}</span>
              <div style={{ width: '100%', maxWidth: '34px', height: `${Math.max(m.total > 0 ? 4 : 1, pct)}%`, borderRadius: '4px 4px 2px 2px', background: m.total > 0 ? 'linear-gradient(180deg, var(--accent, #6366f1), rgba(99,102,241,0.45))' : 'rgba(255,255,255,0.06)', transition: 'height 0.3s' }} />
              <span style={{ fontSize: '10px', color: 'var(--text-secondary)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '100%' }}>{m.label}</span>
            </div>
          );
        })}
      </div>
      <div style={{ marginTop: '10px', fontSize: '12px', color: 'var(--text-secondary)' }}>
        {grand} submission{grand === 1 ? '' : 's'} in the last 12 months · busiest {months.reduce((a, b) => (b.total > a.total ? b : a)).label}
      </div>
    </div>
  );
}

function Heatmap({ calendar }: { calendar: { date: string; count: number }[] }) {
  const counts = new Map<string, number>();
  for (const point of calendar || []) {
    counts.set(point.date.slice(0, 10), (counts.get(point.date.slice(0, 10)) || 0) + point.count);
  }
  const today = new Date();
  const totalDays = 364;
  const start = new Date(today);
  start.setDate(start.getDate() - totalDays);
  // align the first column to Sunday
  const gridStart = new Date(start);
  gridStart.setDate(gridStart.getDate() - start.getDay());

  const cells: { key: string; count: number; future: boolean }[] = [];
  const cursor = new Date(gridStart);
  while (cursor <= today) {
    const key = cursor.toISOString().slice(0, 10);
    const future = cursor > today;
    cells.push({ key, count: counts.get(key) || 0, future });
    cursor.setDate(cursor.getDate() + 1);
  }
  const weeks: (typeof cells)[] = [];
  for (let i = 0; i < cells.length; i += 7) weeks.push(cells.slice(i, i + 7));

  const level = (n: number) => (n === 0 ? 0 : n < 2 ? 1 : n < 4 ? 2 : n < 7 ? 3 : 4);
  const activeDays = cells.filter(c => c.count > 0).length;

  return (
    <div className="heatmap-wrap">
      <div className="heatmap-scroll">
        <div className="heatmap-grid">
          {weeks.map((week, wi) => (
            <div key={wi} className="heatmap-col">
              {week.map(cell => (
                <div
                  key={cell.key}
                  className={`heatmap-cell ${cell.future ? 'future' : `l${level(cell.count)}`}`}
                  title={cell.future ? '' : `${cell.key}: ${cell.count} submission${cell.count === 1 ? '' : 's'}`}
                />
              ))}
            </div>
          ))}
        </div>
      </div>
      <div className="heatmap-legend">
        <span>{activeDays} active days in the last year</span>
        <div className="heatmap-scale">
          <span>Less</span>
          {[0, 1, 2, 3, 4].map(l => <span key={l} className={`heatmap-cell l${l}`} />)}
          <span>More</span>
        </div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const { token, user } = useAuth();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const surpriseMe = async () => {
    try {
      const res = await api.get('/problems/random');
      navigate(`/problems/${res.data.slug}`);
    } catch {
      // backend down — stay put
    }
  };

  useEffect(() => {
    if (!token) return;
    api.get('/dashboard')
      .then(res => setData(res.data))
      .catch(() => setData(null))
      .finally(() => setLoading(false));
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

  const stats = data?.stats;
  const submissions = data?.recent_submissions || [];
  const topics = [...(data?.topic_progress || [])]
    .filter(t => t.attempted > 0)
    .sort((a, b) => b.percentage - a.percentage)
    .slice(0, 8);
  const diffs: { key: 'easy' | 'medium' | 'hard'; label: string; cls: string }[] = [
    { key: 'easy', label: 'Easy', cls: 'easy' },
    { key: 'medium', label: 'Medium', cls: 'medium' },
    { key: 'hard', label: 'Hard', cls: 'hard' },
  ];

  return (
    <div className="page-container">
      <div className="dashboard-head">
        <div>
          <h1>{stats?.current_streak ? `${stats.current_streak}-day streak` : 'Welcome back'}</h1>
          <p>
            {stats?.current_streak
              ? `Keep it going — you are on a ${stats.current_streak} day streak (best: ${stats.longest_streak}).`
              : 'Track your progress and recent activity'}
          </p>
        </div>
        <Link to="/problems"><button className="btn btn-primary">Solve a problem</button></Link>
      </div>

      <div className="dashboard-grid">
        <div className="dashboard-card">
          <div className="label">Problems Solved</div>
          <div className="value">{stats?.problems_solved || 0}</div>
          <div className="sub">of {stats ? stats.easy_total + stats.medium_total + stats.hard_total : 0} total</div>
        </div>
        <div className="dashboard-card">
          <div className="label">Submissions</div>
          <div className="value">{stats?.submission_count || 0}</div>
          <div className="sub">{stats?.total_problems_attempted || 0} attempted</div>
        </div>
        <div className="dashboard-card">
          <div className="label">Acceptance Rate</div>
          <div className="value">{stats?.acceptance_rate || 0}%</div>
          <div className="sub">across all submissions</div>
        </div>
        <div className="dashboard-card">
          <div className="label">Streak</div>
          <div className="value">{stats?.current_streak || 0}<span style={{ fontSize: '16px', fontWeight: 600 }}>d</span></div>
          <div className="sub">best {stats?.longest_streak || 0} days</div>
        </div>
        <div className="dashboard-card">
          <div className="label">Time Coded</div>
          <div className="value">{fmtDuration(stats?.time_spent_seconds || 0)}</div>
          <div className="sub">solve time flushed on submit</div>
        </div>
      </div>

      <div className="glass-card dashboard-section">
        <div className="section-title">Difficulty Breakdown</div>
        <div className="diff-progress-list">
          {diffs.map(d => {
            const solved = stats?.[`${d.key}_solved`] || 0;
            const total = stats?.[`${d.key}_total`] || 0;
            const pct = total ? Math.round((solved / total) * 100) : 0;
            return (
              <div key={d.key} className="diff-progress-row">
                <span className={`diff-progress-label ${d.cls}`}>{d.label}</span>
                <div className="diff-progress-track">
                  <div className={`diff-progress-fill ${d.cls}`} style={{ width: `${pct}%` }} />
                </div>
                <span className="diff-progress-count">{solved}/{total}</span>
              </div>
            );
          })}
        </div>
      </div>

      <div className="glass-card dashboard-section">
        <div className="section-title">Activity — last 12 months</div>
        <Heatmap calendar={data?.activity_calendar || []} />
      </div>

      <div className="glass-card dashboard-section">
        <div className="section-title">Activity by Month</div>
        <MonthlyChart calendar={data?.activity_calendar || []} />
      </div>

      <div className="dashboard-two-col">
        <div className="glass-card dashboard-section">
          <div className="section-title">Topic Progress</div>
          {topics.length === 0 ? (
            <p className="muted-note">Solve a few problems to see your topic breakdown.</p>
          ) : (
            <div className="topic-progress-list">
              {topics.map(t => (
                <div key={t.topic} className="topic-progress-row">
                  <div className="topic-progress-meta">
                    <span className="topic-tag">{t.topic}</span>
                    <span>{t.solved}/{t.attempted} · {Math.round(t.percentage)}%</span>
                  </div>
                  <div className="diff-progress-track">
                    <div className="diff-progress-fill easy" style={{ width: `${Math.round(t.percentage)}%` }} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="glass-card dashboard-section">
          <div className="section-title">Recent Submissions</div>
          {submissions.length === 0 ? (
            <div className="empty-state" style={{ padding: '30px' }}>
              <p>No submissions yet</p>
              <Link to="/problems" style={{ marginTop: '12px', display: 'inline-block' }}>
                <button className="btn btn-secondary btn-sm">Solve a Problem</button>
              </Link>
            </div>
          ) : (
            <div className="recent-list">
              {submissions.slice(0, 8).map((sub: any) => (
                <Link to={`/problems/${sub.problem_slug}`} key={sub.id} className="recent-item" style={{ color: 'inherit' }}>
                  <div className={`recent-status ${sub.status}`} />
                  <span className="recent-title">{sub.problem_title}</span>
                  <span className="recent-meta">{LANG_LABELS[sub.language] || sub.language}</span>
                  <span className="recent-meta" style={{ color: sub.status === 'accepted' ? 'var(--success)' : 'var(--error)' }}>
                    {STATUS_MAP[sub.status] || sub.status}
                  </span>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="glass-card dashboard-section">
        <div className="section-title">Quick Actions</div>
        <div className="quick-actions-row">
          <Link to="/problems"><button className="btn btn-secondary">Browse All Problems</button></Link>
          <Link to="/problems?difficulty=easy"><button className="btn btn-secondary">Practice Easy</button></Link>
          <Link to="/problems?difficulty=medium"><button className="btn btn-secondary">Challenge Medium</button></Link>
          <Link to="/problems?difficulty=hard"><button className="btn btn-secondary">Tackle Hard</button></Link>
          <button className="btn btn-secondary" onClick={surpriseMe}>Random Problem</button>
          <Link to="/leaderboard"><button className="btn btn-secondary">Leaderboard</button></Link>
        </div>
      </div>
    </div>
  );
}
