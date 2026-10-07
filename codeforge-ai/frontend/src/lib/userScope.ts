// Scope of localStorage data that belongs to a signed-in user.
// Password logins historically stored only { username }, Google logins store
// the full user (id, role, ...) — accept both so each account gets its own
// isolated browser state (AI chat history, code drafts, custom input).
export function storageUserKey(): string {
  try {
    const raw = localStorage.getItem('user');
    if (raw) {
      const u = JSON.parse(raw);
      const v = u?.id ?? u?.username;
      if (v !== undefined && v !== null && v !== '') return String(v);
    }
  } catch {
    // corrupted user blob → fall through
  }
  return 'anon';
}
