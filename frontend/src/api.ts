const API_BASE = `https://${location.hostname.replace('app.', '')}`;

async function req(path: string, opts: RequestInit = {}) {
  const res = await fetch(`${API_BASE}${path}`, { credentials: 'include', ...opts });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export const api = {
  me: () => req('/auth/me'),
  users: () => req('/api/users'),
  projects: () => req('/api/projects'),
  issues: (params: Record<string, any> = {}) => {
    const q = new URLSearchParams(params as any).toString();
    return req(`/api/issues${q ? `?${q}` : ''}`);
  },
  issue: (id: number) => req(`/api/issues/${id}`),
  startTimer: (issue_id: number) => req(`/api/issues/${issue_id}/timer/start`, { method: 'POST' }),
  stopTimer: (notes?: string) => req(`/api/timer/stop`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ notes }) }),
  timerStatus: () => req('/api/timer/status'),
  addTime: (issue_id: number, body: any) => req(`/api/issues/${issue_id}/time-entries`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }),
  timeEntries: (params: Record<string, any> = {}) => {
    const q = new URLSearchParams(params as any).toString();
    return req(`/api/time-entries${q ? `?${q}` : ''}`);
  },
  deleteTimeEntry: (id: number) => req(`/api/time-entries/${id}`, { method: 'DELETE' }),
  reportWeek: (params: Record<string, any> = {}) => {
    const q = new URLSearchParams(params as any).toString();
    return req(`/api/reports/week${q ? `?${q}` : ''}`);
  },
  reportPdfUrl: (params: Record<string, any> = {}) => {
    const q = new URLSearchParams(params as any).toString();
    return `${API_BASE}/api/reports/week.pdf${q ? `?${q}` : ''}`;
  },
  refreshIssues: () => req('/api/github/refresh', { method: 'POST' })
}
