import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import api from '../lib/api';

interface Problem {
  id: number;
  public_id: string;
  title: string;
  slug: string;
  difficulty: string;
  topics: string[];
  acceptance_rate: number;
  solved_count: number;
  attempt_count: number;
  is_solved?: boolean;
  is_favorite?: boolean;
  is_locked?: boolean;
}

export default function Problems() {
  const [problems, setProblems] = useState<Problem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchParams, setSearchParams] = useSearchParams();
  const [filter, setFilter] = useState<string>(searchParams.get('difficulty') || 'all');
  const [statusFilter, setStatusFilter] = useState<'all' | 'solved' | 'unsolved' | 'starred'>('all');
  const [search, setSearch] = useState('');
  const [sortField, setSortField] = useState<string>('id');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  useEffect(() => {
    const diff = searchParams.get('difficulty');
    if (diff) setFilter(diff);
  }, [searchParams]);

  useEffect(() => {
    setLoading(true);
    api.get('/problems?limit=500').then(res => {
      const data = res.data;
      setProblems(Array.isArray(data) ? data : (data?.items || []));
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  const filteredProblems = problems.filter(p => {
    if (filter !== 'all' && p.difficulty !== filter) return false;
    if (statusFilter === 'solved' && !p.is_solved) return false;
    if (statusFilter === 'unsolved' && p.is_solved) return false;
    if (statusFilter === 'starred' && !p.is_favorite) return false;
    if (search) {
      const q = search.toLowerCase();
      const inTitle = p.title.toLowerCase().includes(q);
      const inTopics = (Array.isArray(p.topics) ? p.topics : []).some(t => t.toLowerCase().includes(q));
      if (!inTitle && !inTopics) return false;
    }
    return true;
  }).sort((a, b) => {
    let cmp = 0;
    switch (sortField) {
      case 'title': cmp = a.title.localeCompare(b.title); break;
      case 'difficulty':
        const order: Record<string, number> = { easy: 0, medium: 1, hard: 2 };
        cmp = (order[a.difficulty] || 0) - (order[b.difficulty] || 0);
        break;
      case 'acceptance': cmp = a.acceptance_rate - b.acceptance_rate; break;
      case 'solved': cmp = a.solved_count - b.solved_count; break;
      default: cmp = a.id - b.id;
    }
    return sortOrder === 'asc' ? cmp : -cmp;
  });

  const toggleSort = (field: string) => {
    if (sortField === field) {
      setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('asc');
    }
  };

  const SortIcon = ({ field }: { field: string }) => (
    <span style={{ marginLeft: '4px', opacity: sortField === field ? 1 : 0.3, fontSize: '10px' }}>
      {sortField === field ? (sortOrder === 'asc' ? '\u25B2' : '\u25BC') : '\u25B2'}
    </span>
  );

  const handleFilter = (d: string) => {
    setFilter(d);
    if (d === 'all') {
      searchParams.delete('difficulty');
    } else {
      searchParams.set('difficulty', d);
    }
    setSearchParams(searchParams);
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="problem-list-header"><div><h1>Problems</h1></div></div>
        <div className="glass-card" style={{ overflow: 'hidden' }}>
          <table className="problem-table">
            <thead>
              <tr><th style={{ width: '60px' }}>#</th><th>Title</th><th style={{ width: '110px' }}>Difficulty</th><th style={{ width: '100px' }}>Acceptance</th><th>Topics</th></tr>
            </thead>
            <tbody>
              {Array.from({ length: 8 }).map((_, i) => (
                <tr key={i} className="skeleton-row">
                  <td><span className="skeleton-bar" style={{ width: '20px' }} /></td>
                  <td><span className="skeleton-bar" style={{ width: `${40 + (i % 4) * 12}%` }} /></td>
                  <td><span className="skeleton-bar" style={{ width: '64px' }} /></td>
                  <td><span className="skeleton-bar" style={{ width: '44px' }} /></td>
                  <td><span className="skeleton-bar" style={{ width: '70%' }} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  const easyCount = problems.filter(p => p.difficulty === 'easy').length;
  const mediumCount = problems.filter(p => p.difficulty === 'medium').length;
  const hardCount = problems.filter(p => p.difficulty === 'hard').length;
  const solvedCount = problems.filter(p => p.is_solved).length;
  const lockedCount = problems.filter(p => p.is_locked).length;

  return (
    <div className="page-container">
      <div className="problem-list-header">
        <div>
          <h1>Problems</h1>
          <div style={{ display: 'flex', gap: '16px', marginTop: '8px', fontSize: '13px', color: 'var(--text-muted)', flexWrap: 'wrap' }}>
            <span><span style={{ color: 'var(--easy)', fontWeight: 600 }}>{easyCount}</span> Easy</span>
            <span><span style={{ color: 'var(--medium)', fontWeight: 600 }}>{mediumCount}</span> Medium</span>
            <span><span style={{ color: 'var(--hard)', fontWeight: 600 }}>{hardCount}</span> Hard</span>
            <span>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="var(--success)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" style={{ verticalAlign: '-1px', marginRight: '4px' }}>
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              <span style={{ color: 'var(--success)', fontWeight: 600 }}>{solvedCount}</span> Solved
            </span>
          </div>
        </div>
        <span style={{ color: 'var(--text-muted)', fontSize: '14px' }}>
          {filteredProblems.length} problem{filteredProblems.length !== 1 ? 's' : ''}
        </span>
      </div>

      {lockedCount > 0 && (
        <div className="paywall-banner">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
            <path d="M7 11V7a5 5 0 0 1 9.9-1" />
          </svg>
          <span>
            <strong>{lockedCount} problems</strong> (Medium &amp; Hard) are locked. Upgrade to Premium to unlock them all.
          </span>
          <Link to="/payment" className="btn btn-primary btn-sm">Upgrade</Link>
        </div>
      )}

      <div style={{ display: 'flex', gap: '12px', marginBottom: '20px', alignItems: 'center', flexWrap: 'wrap' }}>
        <input
          type="text"
          placeholder="Search title or topic..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{ flex: 1, maxWidth: '320px' }}
        />
        <div className="problem-filters">
          {['all', 'easy', 'medium', 'hard'].map(d => (
            <button
              key={d}
              className={`filter-btn ${filter === d ? 'active' : ''}`}
              onClick={() => handleFilter(d)}
            >
              {d === 'all' ? 'All' : d.charAt(0).toUpperCase() + d.slice(1)}
            </button>
          ))}
        </div>
        <div className="problem-filters">
          {(['all', 'unsolved', 'solved', 'starred'] as const).map(s => (
            <button
              key={s}
              className={`filter-btn ${statusFilter === s ? 'active' : ''}`}
              onClick={() => setStatusFilter(s)}
            >
              {s === 'all' ? 'Any Status' : s === 'solved' ? 'Solved' : s === 'unsolved' ? 'Unsolved' : '★ Starred'}
            </button>
          ))}
        </div>
      </div>

      <div className="glass-card" style={{ overflow: 'hidden' }}>
        <table className="problem-table">
          <thead>
            <tr>
              <th style={{ width: '60px', cursor: 'pointer' }} onClick={() => toggleSort('id')}>
                #<SortIcon field="id" />
              </th>
              <th style={{ cursor: 'pointer' }} onClick={() => toggleSort('title')}>
                Title<SortIcon field="title" />
              </th>
              <th style={{ width: '110px', cursor: 'pointer' }} onClick={() => toggleSort('difficulty')}>
                Difficulty<SortIcon field="difficulty" />
              </th>
              <th style={{ width: '100px', cursor: 'pointer' }} onClick={() => toggleSort('acceptance')}>
                Acceptance<SortIcon field="acceptance" />
              </th>
              <th>Topics</th>
            </tr>
          </thead>
          <tbody>
            {filteredProblems.map((problem, idx) => (
              <tr key={problem.id} className={problem.is_solved ? 'row-solved' : ''}>
                <td className="problem-id">{idx + 1}</td>
                <td>
                  <Link to={`/problems/${problem.slug}`} className="problem-title-link">
                    {problem.is_solved && (
                      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="var(--success)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" className="solved-check">
                        <polyline points="20 6 9 17 4 12"/>
                      </svg>
                    )}
                    {problem.is_favorite && <span className="star-mark" title="Starred">★</span>}
                    {problem.title}
                    {problem.is_locked && (
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" className="lock-mark">
                        <title>Premium — locked</title>
                        <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                        <path d="M7 11V7a5 5 0 0 1 9.9-1" />
                      </svg>
                    )}
                  </Link>
                </td>
                <td>
                  <span className={`difficulty-badge ${problem.difficulty}`}>
                    {problem.difficulty}
                  </span>
                </td>
                <td style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', color: 'var(--text-secondary)' }}>
                  {problem.acceptance_rate > 0 ? `${problem.acceptance_rate}%` : '-'}
                </td>
                <td>
                  {(Array.isArray(problem.topics) ? problem.topics : []).slice(0, 3).map(topic => (
                    <span key={topic} className="topic-tag">{topic}</span>
                  ))}
                  {(Array.isArray(problem.topics) ? problem.topics : []).length > 3 && (
                    <span className="topic-tag">+{((Array.isArray(problem.topics) ? problem.topics : []).length - 3)}</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filteredProblems.length === 0 && (
          <div className="empty-state">
            <h3>No problems found</h3>
            <p>Try adjusting your search or filter.</p>
          </div>
        )}
      </div>
    </div>
  );
}
