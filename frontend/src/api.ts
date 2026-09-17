const BASE = "/api";
export const AUTH_REQUIRED_EVENT = "audit:sign-in-required";
export const SESSION_EXPIRED_MESSAGE = "Your sign-in has expired or is no longer valid. Please sign in again to continue.";

function getToken(): string | null {
  return localStorage.getItem("token");
}

async function request(path: string, options: RequestInit = {}) {
  const token = getToken();
  const headers: Record<string, string> = { ...(options.headers as Record<string, string> || {}) };
  if (token && path !== "/auth/login") headers["Authorization"] = `Bearer ${token}`;
  if (options.body && !(options.body instanceof URLSearchParams) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }
  const resp = await fetch(`${BASE}${path}`, { ...options, headers });
  if (!resp.ok) {
    if (resp.status === 401 && path !== "/auth/login") {
      // A delayed failure from an old request must not clear a newer sign-in.
      if (getToken() === token) {
        logout();
        window.dispatchEvent(new Event(AUTH_REQUIRED_EVENT));
      }
      throw new Error(SESSION_EXPIRED_MESSAGE);
    }
    let detail = resp.statusText;
    try {
      const body = await resp.json();
      detail = body.detail || detail;
    } catch {
      // ignore
    }
    throw new Error(resp.status === 401 && path === "/auth/login"
      ? "That username or password did not match. Use one of the demo accounts shown below."
      : detail);
  }
  const contentType = resp.headers.get("content-type") || "";
  if (contentType.includes("application/json")) return resp.json();
  return resp.text();
}

export async function login(username: string, password: string) {
  const body = new URLSearchParams({ username, password });
  const data = await request("/auth/login", { method: "POST", body });
  localStorage.setItem("token", data.access_token);
  localStorage.setItem("role", data.role);
  localStorage.setItem("display_name", data.display_name);
  return data;
}

export function logout() {
  localStorage.removeItem("token");
  localStorage.removeItem("role");
  localStorage.removeItem("display_name");
}

export function currentRole(): string | null {
  return localStorage.getItem("role");
}

export function currentDisplayName(): string | null {
  return localStorage.getItem("display_name");
}

export const api = {
  listEngagements: () => request("/engagements"),
  dashboard: (engagementId: string) => request(`/engagements/${engagementId}/dashboard`),
  listAssertions: (engagementId: string) => request(`/assertions?engagement_id=${engagementId}`),
  getAssertion: (id: string) => request(`/assertions/${id}`),
  reviewQueue: (engagementId: string, sortBy: string, statusFilter: string) =>
    request(`/review/queue?engagement_id=${engagementId}&sort_by=${sortBy}&status_filter=${statusFilter}`),
  actOnReview: (taskId: string, decision: string, note?: string) =>
    request(`/review/tasks/${taskId}/action`, { method: "POST", body: JSON.stringify({ decision, note }) }),
  getDocument: (id: string) => request(`/documents/${id}`),
  getDocumentPages: (id: string) => request(`/documents/${id}/pages`),
  amendDocument: (id: string, newAmount: number) =>
    request(`/documents/${id}/amend`, { method: "POST", body: JSON.stringify({ new_amount: newAmount }) }),
  auditEvents: (engagementId: string, entityId?: string) =>
    request(`/audit-events?engagement_id=${engagementId}${entityId ? `&entity_id=${entityId}` : ""}`),
  exportReport: (engagementId: string, format: "json" | "html") => request(`/export/${encodeURIComponent(engagementId)}.${format}`),
};

export const riskApi = {
  radar: (engagementId: string) => request(`/risk/radar?engagement_id=${engagementId}`),
  searchEvidence: (engagementId: string, query: string) =>
    request(`/evidence/search?engagement_id=${engagementId}&query=${encodeURIComponent(query)}`),
};

export const impactApi = {
  documents: (engagementId: string) => request(`/impact/documents?engagement_id=${encodeURIComponent(engagementId)}`),
  preview: (documentId: string, amount?: number) => request(`/impact/${encodeURIComponent(documentId)}${amount === undefined ? '' : `?proposed_amount=${amount}`}`),
};

export const receiptApi = {
  status: () => request("/receipts/status"),
  extract: (file: File, signal: AbortSignal) => request("/receipts/extract", {
    method: "POST", body: file, signal,
    headers: { "Content-Type": file.type, "X-Receipt-Consent": "true" },
  }),
};
