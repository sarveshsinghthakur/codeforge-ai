import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../App';
import api from '../lib/api';
import { Link } from 'react-router-dom';

const AVATAR_MAX = 16000; // matches backend UserUpdateRequest.avatar_url max_length

function resizeToDataUrl(file: File, size: number, quality: number): Promise<string> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    const url = URL.createObjectURL(file);
    img.onload = () => {
      URL.revokeObjectURL(url);
      const canvas = document.createElement('canvas');
      canvas.width = size;
      canvas.height = size;
      const ctx = canvas.getContext('2d');
      if (!ctx) return reject(new Error('no canvas'));
      // center-crop square
      const s = Math.min(img.width, img.height);
      ctx.drawImage(img, (img.width - s) / 2, (img.height - s) / 2, s, s, 0, 0, size, size);
      resolve(canvas.toDataURL('image/jpeg', quality));
    };
    img.onerror = () => { URL.revokeObjectURL(url); reject(new Error('bad image')); };
    img.src = url;
  });
}

async function avatarDataUrl(file: File): Promise<string> {
  const tries: [number, number][] = [[128, 0.8], [128, 0.6], [96, 0.5]];
  for (const [size, q] of tries) {
    const dataUrl = await resizeToDataUrl(file, size, q);
    if (dataUrl.length <= AVATAR_MAX) return dataUrl;
  }
  throw new Error('Image too large');
}

export default function Profile() {
  const { token, user, updateUser } = useAuth();
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [failed, setFailed] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  // edit form
  const [displayName, setDisplayName] = useState('');
  const [bio, setBio] = useState('');
  const [preferredLang, setPreferredLang] = useState('python');
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  const load = () => {
    api.get('/users/me/dashboard').then(res => {
      setProfile(res.data);
      setDisplayName(res.data.display_name || '');
      setBio(res.data.bio || '');
      setPreferredLang(res.data.preferred_language || 'python');
      setLoading(false);
    }).catch(() => {
      setFailed(true);
      setLoading(false);
    });
  };

  useEffect(() => {
    if (!token) return;
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const flash = (msg: string) => { setToast(msg); setTimeout(() => setToast(null), 2500); };

  const patch = async (body: Record<string, any>) => {
    const res = await api.put('/auth/me', body);
    const updated = res.data;
    updateUser(updated);
    setProfile((p: any) => ({ ...p, ...body, ...updated }));
    return updated;
  };

  const onPickAvatar = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    setSaving(true);
    try {
      const dataUrl = await avatarDataUrl(file);
      await patch({ avatar_url: dataUrl });
      flash('Profile photo updated');
    } catch (err: any) {
      flash(err?.response?.data?.detail || err?.message || 'Upload failed');
    } finally {
      setSaving(false);
    }
  };

  const removeAvatar = async () => {
    setSaving(true);
    try {
      await patch({ avatar_url: '' });
      flash('Profile photo removed');
    } catch {
      flash('Remove failed');
    } finally {
      setSaving(false);
    }
  };

  const saveForm = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await patch({ display_name: displayName, bio, preferred_language: preferredLang });
      flash('Profile saved');
    } catch {
      flash('Save failed');
    } finally {
      setSaving(false);
    }
  };

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
          <button className="btn btn-secondary" onClick={() => { setFailed(false); setLoading(true); load(); }}>Retry</button>
        </div>
      </div>
    );
  }

  const sub = profile.subscription || {};
  const chats = profile.ai_chats || {};
  const avatar = profile.avatar_url || user?.avatar_url || '';
  const name = profile.display_name || profile.username;

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
        {toast && (
          <div style={{ background: 'rgba(99,102,241,0.15)', border: '1px solid rgba(99,102,241,0.4)', borderRadius: '8px', padding: '8px 14px', marginBottom: '16px', fontSize: '13px' }}>
            {toast}
          </div>
        )}

        {/* header: avatar + identity */}
        <div style={{ display: 'flex', gap: '20px', alignItems: 'center', marginBottom: '24px' }}>
          <div style={{ position: 'relative' }}>
            <div style={{ width: '80px', height: '80px', borderRadius: '50%', background: 'rgba(255,255,255,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '28px', fontWeight: 800, overflow: 'hidden' }}>
              {avatar
                ? <img src={avatar} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                : name[0].toUpperCase()}
            </div>
            <button
              className="btn btn-secondary btn-sm"
              title="Change profile photo"
              disabled={saving}
              onClick={() => fileRef.current?.click()}
              style={{ position: 'absolute', bottom: '-4px', right: '-4px', padding: '4px 7px', lineHeight: 1 }}
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>
                <circle cx="12" cy="13" r="4"/>
              </svg>
            </button>
            <input ref={fileRef} type="file" accept="image/*" style={{ display: 'none' }} onChange={onPickAvatar} />
          </div>
          <div>
            <h1 style={{ fontSize: '24px', fontWeight: 800, marginBottom: '4px' }}>{name}</h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: '14px' }}>@{profile.username} • {profile.email}</p>
            {profile.bio && <p style={{ color: 'var(--text-secondary)', fontSize: '13px', marginTop: '6px' }}>{profile.bio}</p>}
            {avatar && (
              <button className="btn btn-ghost btn-sm" style={{ marginTop: '4px', padding: 0, fontSize: '12px', color: 'var(--text-secondary)' }} onClick={removeAvatar} disabled={saving}>
                Remove photo
              </button>
            )}
          </div>
        </div>

        {/* profile setup form */}
        <form onSubmit={saveForm} style={{ display: 'grid', gap: '14px', marginBottom: '24px', padding: '18px', border: '1px solid var(--border-color, rgba(255,255,255,0.1))', borderRadius: '12px' }}>
          <div style={{ fontSize: '13px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-secondary)' }}>Profile Setup</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px' }}>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
              Display name
              <input className="form-input" value={displayName} onChange={e => setDisplayName(e.target.value)} placeholder="Your name" maxLength={100} style={{ width: '100%', marginTop: '6px' }} />
            </label>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
              Preferred language
              <select className="form-input" value={preferredLang} onChange={e => setPreferredLang(e.target.value)} style={{ width: '100%', marginTop: '6px' }}>
                <option value="python">Python</option>
                <option value="javascript">JavaScript</option>
                <option value="java">Java</option>
                <option value="cpp">C++</option>
                <option value="c">C</option>
              </select>
            </label>
          </div>
          <label style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
            Bio
            <textarea className="form-input" value={bio} onChange={e => setBio(e.target.value)} placeholder="Short intro" maxLength={300} rows={2} style={{ width: '100%', marginTop: '6px', resize: 'vertical' }} />
          </label>
          <div>
            <button className="btn btn-primary btn-sm" type="submit" disabled={saving}>
              {saving ? 'Saving…' : 'Save Profile'}
            </button>
          </div>
        </form>

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
