# CodeForge AI - Specification

## Product Vision

CodeForge AI is a minimalist black-and-white coding practice platform where users solve original algorithm problems in a Monaco editor, execute code in isolated sandboxes, receive test results, track progress, and receive AI-powered assistance from Mistral.

## Design System

### Visual Language
- Monochrome: white, black, grays only
- Liquid-glass cards: translucent surfaces with backdrop-filter: blur
- Thin low-contrast borders
- Subtle shadows
- Typography: Inter or Geist, large headings, generous whitespace
- Rounded corners: 12-20px
- Animations: 150-400ms, subtle, no bouncing

### Color Palette
- `--bg-primary`: #ffffff / #0a0a0a (dark mode)
- `--bg-secondary`: #f5f5f5 / #1a1a1a
- `--bg-glass`: rgba(255,255,255,0.7) / rgba(0,0,0,0.7)
- `--border`: rgba(0,0,0,0.08) / rgba(255,255,255,0.08)
- `--text-primary`: #0a0a0a / #ffffff
- `--text-secondary`: #666666 / #999999
- `--accent`: #000000 / #ffffff (single accent)
- `--success`: #0a0a0a on white / `#ffffff` on dark
- `--error`: #cc0000 / #ff4444

### Status Colors (semantic, not decorative)
- Accepted: dark/light accent with checkmark icon
- Wrong Answer: error tone + X icon
- Runtime Error: error tone + bug icon
- Compilation Error: error tone + code icon
- Time Limit: warning tone + clock icon
- Memory Limit: warning tone + memory icon

## Sections

1. Landing page (hero, features, CTA)
2. Problems list (/problems)
3. Problem detail / workspace (/problems/[slug])
4. Submissions
5. Dashboard (/dashboard)
6. Profile
7. Leaderboard (/leaderboard)
8. AI Assistant
9. Admin dashboard (/admin)
10. Admin problem generator (/admin/problems/generate)
11. Admin problem management
12. Admin test-case management
13. Admin analytics
14. Settings

## API Design

Base URL: /api

### Auth
- POST /api/auth/register
- POST /api/auth/login
- POST /api/auth/logout
- POST /api/auth/refresh
- GET /api/users/me

### Problems
- GET /api/problems (list, search, filter, paginate)
- GET /api/problems/{id}
- GET /api/problems/{slug}
- POST /api/problems (admin)
- PUT /api/problems/{id} (admin)
- DELETE /api/problems/{id} (admin)
- GET /api/problems/{id}/submissions

### Submissions
- POST /api/submissions
- GET /api/submissions/{id}
- GET /api/users/me/submissions

### Test Cases (admin only for management)
- GET /api/problems/{id}/test-cases (admin)
- POST /api/problems/{id}/test-cases (admin)
- PUT /api/test-cases/{id} (admin)
- DELETE /api/test-cases/{id} (admin)

### AI
- POST /api/ai/chat
- POST /api/ai/generate-problem (admin)
- POST /api/ai/generate-test-cases (admin)
- POST /api/ai/analyze-code
- POST /api/ai/generate-hints

### Contests
- GET /api/contests
- GET /api/contests/{id}
- POST /api/contests (admin)
- POST /api/contests/{id}/join
- GET /api/contests/{id}/leaderboard

### Discussions
- GET /api/problems/{id}/discussions
- POST /api/problems/{id}/discussions
- POST /api/discussions/{id}/comments
- POST /api/discussions/{id}/like

### Admin
- GET /admin/analytics
- GET /admin/users
- GET /admin/submissions
- POST /admin/problems/generate
- POST /admin/problems/{id}/review
- POST /admin/problems/{id}/publish
