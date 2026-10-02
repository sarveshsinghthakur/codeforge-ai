import { useEffect, useState } from 'react';
import api from '../lib/api';
import { useToast } from './Toast';

interface Discussion {
  id: number;
  title: string;
  content: string;
  category: string;
  username: string;
  display_name?: string | null;
  likes_count: number;
  comment_count: number;
  created_at: string;
}

interface Comment {
  id: number;
  content: string;
  username: string;
  display_name?: string | null;
  likes_count: number;
  created_at: string;
}

const CATEGORIES = ['question', 'approach', 'solution', 'hint', 'optimization'] as const;

function timeAgo(iso: string): string {
  const s = Math.max(1, Math.floor((Date.now() - new Date(iso).getTime()) / 1000));
  if (s < 60) return `${s}s ago`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

export default function Discussions({ problemId }: { problemId: number }) {
  const { toast } = useToast();
  const [items, setItems] = useState<Discussion[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [category, setCategory] = useState<string>('question');
  const [posting, setPosting] = useState(false);
  const [expanded, setExpanded] = useState<number | null>(null);
  const [comments, setComments] = useState<Record<number, Comment[]>>({});
  const [commentText, setCommentText] = useState('');
  const [commentBusy, setCommentBusy] = useState(false);

  const load = () => {
    api.get(`/problems/${problemId}/discussions`)
      .then(res => setItems(Array.isArray(res.data) ? res.data : []))
      .catch(() => toast('Could not load discussions', 'error'))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    setLoading(true);
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [problemId]);

  const submit = async () => {
    if (!title.trim() || !content.trim()) {
      toast('Title and message are required', 'error');
      return;
    }
    setPosting(true);
    try {
      await api.post(`/problems/${problemId}/discussions`, {
        problem_id: problemId,
        title: title.trim(),
        content: content.trim(),
        category,
      });
      toast('Discussion posted', 'success');
      setTitle('');
      setContent('');
      setShowForm(false);
      load();
    } catch (err: any) {
      toast(err.response?.data?.detail || 'Failed to post discussion', 'error');
    } finally {
      setPosting(false);
    }
  };

  const toggleComments = async (d: Discussion) => {
    if (expanded === d.id) {
      setExpanded(null);
      return;
    }
    setExpanded(d.id);
    if (!comments[d.id]) {
      try {
        const res = await api.get(`/discussions/${d.id}`);
        setComments(prev => ({ ...prev, [d.id]: res.data.comments || [] }));
      } catch {
        toast('Could not load comments', 'error');
      }
    }
  };

  const likeDiscussion = async (d: Discussion) => {
    try {
      const res = await api.post(`/discussions/${d.id}/like`);
      setItems(prev => prev.map(x => x.id === d.id ? { ...x, likes_count: res.data.likes_count } : x));
    } catch {
      toast('Could not like discussion', 'error');
    }
  };

  const likeComment = async (discussionId: number, c: Comment) => {
    try {
      const res = await api.post(`/comments/${c.id}/like`);
      setComments(prev => ({
        ...prev,
        [discussionId]: (prev[discussionId] || []).map(x => x.id === c.id ? { ...x, likes_count: res.data.likes_count } : x),
      }));
    } catch {
      toast('Could not like comment', 'error');
    }
  };

  const submitComment = async (discussionId: number) => {
    if (!commentText.trim()) return;
    setCommentBusy(true);
    try {
      const res = await api.post(`/discussions/${discussionId}/comments`, {
        discussion_id: discussionId,
        content: commentText.trim(),
      });
      setComments(prev => ({ ...prev, [discussionId]: [...(prev[discussionId] || []), res.data] }));
      setItems(prev => prev.map(x => x.id === discussionId ? { ...x, comment_count: x.comment_count + 1 } : x));
      setCommentText('');
    } catch (err: any) {
      toast(err.response?.data?.detail || 'Failed to post comment', 'error');
    } finally {
      setCommentBusy(false);
    }
  };

  if (loading) {
    return <div className="page-loading" style={{ minHeight: '160px' }}><div className="loading-spinner" /></div>;
  }

  return (
    <div className="discussions">
      <div className="discussions-head">
        <h1>Discussions</h1>
        <button className="btn btn-primary btn-sm" onClick={() => setShowForm(v => !v)}>
          {showForm ? 'Cancel' : '+ New Discussion'}
        </button>
      </div>

      {showForm && (
        <div className="discussion-form glass-card">
          <input
            type="text"
            placeholder="Title"
            value={title}
            maxLength={255}
            onChange={e => setTitle(e.target.value)}
          />
          <textarea
            placeholder="Describe your question, approach or solution..."
            rows={4}
            value={content}
            maxLength={10000}
            onChange={e => setContent(e.target.value)}
          />
          <div className="discussion-form-row">
            <select value={category} onChange={e => setCategory(e.target.value)}>
              {CATEGORIES.map(c => (
                <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
              ))}
            </select>
            <button className="btn btn-primary btn-sm" onClick={submit} disabled={posting}>
              {posting ? 'Posting...' : 'Post'}
            </button>
          </div>
        </div>
      )}

      {items.length === 0 ? (
        <div className="empty-state">
          <p>No discussions yet. Start the conversation!</p>
        </div>
      ) : (
        <div className="discussion-list">
          {items.map(d => (
            <div key={d.id} className="discussion-item">
              <div className="discussion-item-head" onClick={() => toggleComments(d)}>
                <div>
                  <div className="discussion-title">{d.title}</div>
                  <div className="discussion-meta">
                    <span className={`discussion-category ${d.category}`}>{d.category}</span>
                    <span>{d.display_name || d.username}</span>
                    <span>{timeAgo(d.created_at)}</span>
                  </div>
                </div>
                <div className="discussion-stats">
                  <button
                    className="chip-btn"
                    title="Like"
                    onClick={e => { e.stopPropagation(); likeDiscussion(d); }}
                  >
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3z"/>
                      <path d="M7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/>
                    </svg>
                    {d.likes_count}
                  </button>
                  <span className="chip-btn" title="Comments">
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                    </svg>
                    {d.comment_count}
                  </span>
                </div>
              </div>

              {expanded === d.id && (
                <div className="discussion-body">
                  <p>{d.content}</p>
                  <div className="comment-list">
                    {(comments[d.id] || []).map(c => (
                      <div key={c.id} className="comment-item">
                        <div className="comment-head">
                          <strong>{c.display_name || c.username}</strong>
                          <span className="comment-time">{timeAgo(c.created_at)}</span>
                          <button className="chip-btn" onClick={() => likeComment(d.id, c)} title="Like comment">
                            ♥ {c.likes_count}
                          </button>
                        </div>
                        <p>{c.content}</p>
                      </div>
                    ))}
                    {comments[d.id] && comments[d.id].length === 0 && (
                      <p className="comment-empty">No comments yet.</p>
                    )}
                  </div>
                  <div className="comment-compose">
                    <input
                      type="text"
                      placeholder="Add a comment..."
                      value={expanded === d.id ? commentText : ''}
                      onChange={e => setCommentText(e.target.value)}
                      onKeyDown={e => e.key === 'Enter' && submitComment(d.id)}
                    />
                    <button className="btn btn-secondary btn-sm" onClick={() => submitComment(d.id)} disabled={commentBusy}>
                      {commentBusy ? '...' : 'Reply'}
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
