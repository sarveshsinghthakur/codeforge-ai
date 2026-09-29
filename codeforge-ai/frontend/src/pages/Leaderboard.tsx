import { useState, useEffect } from 'react';
import api from '../lib/api';

interface UserRank {
  id: number;
  username: string;
  display_name: string;
  problems_solved: number;
  easy_solved: number;
  medium_solved: number;
  hard_solved: number;
  submission_count: number;
  acceptance_rate: number;
}

export default function Leaderboard() {
  const [users, setUsers] = useState<UserRank[]>([]);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState<'all' | 'week' | 'month'>('all');

  useEffect(() => {
    setLoading(true);
    api.get(`/admin/analytics/leaderboard?period=${period}`).then(res => {
      setUsers(res.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [period]);

  if (loading) return <div className="page-loading"><div className="loading-spinner" /></div>;

  return (
    <div className="page-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h1 style={{ fontSize: '28px', fontWeight: 800 }}>Leaderboard</h1>
        <div style={{ display: 'flex', gap: '4px' }}>
          {(['all', 'week', 'month'] as const).map(p => (
            <button
              key={p}
              className={`filter-btn ${period === p ? 'active' : ''}`}
              onClick={() => setPeriod(p)}
            >
              {p.charAt(0).toUpperCase() + p.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div className="glass-card" style={{ overflow: 'hidden' }}>
        <table className="problem-table">
          <thead>
            <tr>
              <th style={{ width: '60px' }}>Rank</th>
              <th>User</th>
              <th style={{ width: '100px' }}>Solved</th>
              <th style={{ width: '100px' }}>Easy / Med / Hard</th>
              <th style={{ width: '120px' }}>Submissions</th>
              <th style={{ width: '120px' }}>Acceptance</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user, idx) => (
              <tr key={user.id}>
                <td className="problem-id" style={{ fontWeight: '700', fontSize: '16px' }}>
                  #{idx + 1}
                  {idx === 0 && <span style={{ marginLeft: '6px', color: '#ffaa00' }}>👑</span>}
                  {idx === 1 && <span style={{ marginLeft: '6px', color: '#999' }}>🥈</span>}
                  {idx === 2 && <span style={{ marginLeft: '6px', color: '#cd7f32' }}>🥉</span>}
                </td>
                <td>
                  <div style={{ fontWeight: '500' }}>{user.display_name || user.username}</div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>@{user.username}</div>
                </td>
                <td style={{ fontFamily: 'var(--font-mono)', fontWeight: '600', fontSize: '16px' }}>{user.problems_solved}</td>
                <td style={{ fontSize: '13px' }}>
                  <span style={{ color: 'var(--easy)' }}>{user.easy_solved}</span>
                  <span style={{ color: 'var(--text-muted)' }}> / </span>
                  <span style={{ color: 'var(--medium)' }}>{user.medium_solved}</span>
                  <span style={{ color: 'var(--text-muted)' }}> / </span>
                  <span style={{ color: 'var(--hard)' }}>{user.hard_solved}</span>
                </td>
                <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>{user.submission_count}</td>
                <td style={{ fontFamily: 'var(--font-mono)', fontWeight: '600' }}>{user.acceptance_rate}%</td>
              </tr>
            ))}
          </tbody>
        </table>
        {users.length === 0 && (
          <div className="empty-state" style={{ padding: '60px' }}>
            <p>No users on leaderboard yet</p>
          </div>
        )}
      </div>
    </div>
  );
}