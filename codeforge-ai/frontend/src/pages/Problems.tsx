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
}

export default function Problems() {
  const [problems, setProblems] = useState<Problem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchParams, setSearchParams] = useSearchParams();
  const [filter, setFilter] = useState<string>(searchParams.get('difficulty') || 'all');
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
    if (search && !p.title.toLowerCase().includes(search.toLowerCase())) return false;
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
    return <div className="page-loading"><div className="loading-spinner" /></div>;
  }

  const easyCount = problems.filter(p => p.difficulty === 'easy').length;
  const mediumCount = problems.filter(p => p.difficulty === 'medium').length;
  const hardCount = problems.filter(p => p.difficulty === 'hard').length;

  return (
    <div className="page-container">
      <div className="problem-list-header">
        <div>
          <h1>Problems</h1>
          <div style={{ display: 'flex', gap: '16px', marginTop: '8px', fontSize: '13px', color: 'var(--text-muted)' }}>
            <span><span style={{ color: 'var(--easy)', fontWeight: 600 }}>{easyCount}</span> Easy</span>
            <span><span style={{ color: 'var(--medium)', fontWeight: 600 }}>{mediumCount}</span> Medium</span>
            <span><span style={{ color: 'var(--hard)', fontWeight: 600 }}>{hardCount}</span> Hard</span>
          </div>
        </div>
        <span style={{ color: 'var(--text-muted)', fontSize: '14px' }}>
          {filteredProblems.length} problems
        </span>
      </div>

      <div style={{ display: 'flex', gap: '12px', marginBottom: '20px', alignItems: 'center' }}>
        <input
          type="text"
          placeholder="Search problems..."
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
              <tr key={problem.id}>
                <td className="problem-id">{idx + 1}</td>
                <td>
                  <Link to={`/problems/${problem.slug}`} className="problem-title-link">
                    {problem.title}
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
