import { useState, useEffect } from 'react';
import { useAuth } from '../App';
import api from '../lib/api';
import { Link } from 'react-router-dom';

export default function Profile() {
  const { token } = useAuth();
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    if (!token) return;
    // dashboard = full per-user overview (identity + subscription + questions done + ai chats)
    api.get('/users/me/dashboard').then(res => {
      setProfile(res.data);
      setLoading(false);
    }).catch(() => {
      setFailed(true);
      setLoading(false);
    });
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

  if (failed || !profile) {
    return (
      <div className="page-container">
        <div className="empty-state">
          <h3>Could not load your profile</h3>
          <button className="btn btn-secondary" onClick={() => { setFailed(false); setLoading(true); api.get('/users/me/dashboard').then(res => { setProfile(res.data); setLoading(false); }).catch(() => { setFailed(true); setLoading(false); }); }}>Retry</button>
        </div>
      </div>
    );
  }

  const sub = profile.subscription || {};
  const chats = profile.ai_chats || {};

  const planLabel =
    sub.plan === 'monthly' ? 'PRO Monthly'
    : sub.plan === 'annual' ? 'PRO Annual'
    : sub.plan === 'admin' ? 'Admin'
    : 'Free';

  let planSub: string;
  if (sub.active) {
    planSub = `Active${sub.days_left != null ? ` · ${sub.days_left} days left` : ''}`;
  } else if (sub.is_admin) {
    planSub = 'Full access';
  } else if (sub.status && sub.status !== 'free') {
    planSub = sub.status.charAt(0).toUpperCase() + sub.status.slice(1);
  } else {
    planSub = 'No active plan';
  }

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

        {/* per-user overview: the three separated stats */}
        <div className="dashboard-grid">
          <Stat label="Subscription" value={planLabel} sub={planSub} />
          <Stat label="Questions Done" value={profile.problems_solved || 0} sub={`${profile.easy_solved || 0} easy · ${profile.medium_solved || 0} medium · ${profile.hard_solved || 0} hard`} />
          <Stat label="AI Chats" value={chats.conversations || 0} sub={`${chats.messages || 0} messages`} />
        </div>

        {/* secondary stats */}
        <div className="dashboard-grid" style={{ marginTop: '16px' }}>
          <Stat label="Submissions" value={profile.submission_count || 0} />
          <Stat label="Acceptance Rate" value={`${profile.acceptance_rate || 0}%`} />
          <Stat label="Member Since" value={new Date(profile.created_at).toLocaleDateString()} />
        </div>

        <div style={{ marginTop: '24px', display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          {!sub.active && !sub.is_admin && (
            <Link to="/payment"><button className="btn btn-primary">Upgrade</button></Link>
          )}
          <Link to="/dashboard"><button className="btn btn-secondary">View Dashboard</button></Link>
          <Link to="/problems"><button className="btn btn-secondary">Browse Problems</button></Link>
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="dashboard-card">
      <div className="label">{label}</div>
      <div className="value" style={{ fontSize: '24px' }}>{value}</div>
      {sub && <div className="sub" style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>{sub}</div>}
    </div>
  );
}
