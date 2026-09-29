import { useState, useEffect } from 'react';
import { useAuth } from '../App';
import api from '../lib/api';
import { Link } from 'react-router-dom';

export default function Profile() {
  const { token, user } = useAuth();
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    api.get('/auth/me').then(res => {
      setProfile(res.data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, [token]);

  if (!token) {
    return (
      <div className="page-container">
        <div className="empty-state">
          <h3>Please log in</h3>
          <Link to="/login"><button className="btn btn-primary">Sign In</button></Link>
        </div>
      </div>
    );
  }

  if (loading) return <div className="page-loading"><div className="loading-spinner" /></div>;

  return (
    <div className="page-container">
      <div className="glass-card" style={{ padding: '32px', maxWidth: '800px' }}>
        <div style={{ display: 'flex', gap: '20px', alignItems: 'center', marginBottom: '24px' }}>
          <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: 'rgba(255,255,255,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '24px', fontWeight: '800' }}>
            {(profile.display_name || profile.username)[0].toUpperCase()}
          </div>
          <div>
            <h1 style={{ fontSize: '24px', fontWeight: 800, marginBottom: '4px' }}>{profile.display_name || profile.username}</h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>@{profile.username} • {profile.email}</p>
          </div>
        </div>
        <div className="dashboard-grid">
          <Stat label="Problems Solved" value={profile.problems_solved || 0} />
          <Stat label="Submissions" value={profile.submission_count || 0} />
          <Stat label="Acceptance Rate" value={`${profile.acceptance_rate || 0}%`} />
          <Stat label="Member Since" value={new Date(profile.created_at).toLocaleDateString()} />
        </div>
        <div style={{ marginTop: '24px', display: 'flex', gap: '12px' }}>
          <Link to="/dashboard"><button className="btn btn-primary">View Dashboard</button></Link>
          <Link to="/problems"><button className="btn btn-secondary">Browse Problems</button></Link>
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="dashboard-card">
      <div className="label">{label}</div>
      <div className="value" style={{ fontSize: '24px' }}>{value}</div>
    </div>
  );
}
