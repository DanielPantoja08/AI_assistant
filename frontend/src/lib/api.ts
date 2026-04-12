const API_BASE_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000";
const TOKEN_KEY = "lg_token";
const SESSION_KEY = "lg_session";
const SESSION_TTL_MS = 8 * 60 * 60 * 1000; // 8 hours

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export function saveToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function getOrCreateSessionId(): string {
  const raw = localStorage.getItem(SESSION_KEY);
  if (raw) {
    try {
      const parsed = JSON.parse(raw) as { id: string; expires: number };
      if (parsed.id && parsed.expires > Date.now()) {
        return parsed.id;
      }
    } catch {
      // malformed entry — fall through to create new
    }
  }
  const id = crypto.randomUUID();
  saveSessionId(id);
  return id;
}

export function saveSessionId(id: string): void {
  localStorage.setItem(SESSION_KEY, JSON.stringify({ id, expires: Date.now() + SESSION_TTL_MS }));
}

export function clearSessionId(): void {
  localStorage.removeItem(SESSION_KEY);
}

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> | undefined),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  const res = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  if (res.status === 401) {
    clearToken();
    window.location.href = "/login";
    throw new Error("Sesión expirada");
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Error desconocido" })) as { detail?: string };
    throw new Error(err.detail ?? "Error en la solicitud");
  }
  return res.json() as Promise<T>;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface User {
  id: string;
  email: string;
  is_active: boolean;
  first_name: string | null;
  last_name: string | null;
}

export interface ChatResponse {
  response: string;
}

export interface HistoryMessage {
  role: "user" | "assistant";
  content: string;
}

export interface IngestResponse {
  status: string;
  collection: string;
  source_name: string;
  chunks: number;
  images: number;
  tables: number;
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  const form = new URLSearchParams({ username: email, password });
  const res = await fetch(`${API_BASE_URL}/auth/jwt/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: form.toString(),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Credenciales inválidas" })) as { detail?: string };
    throw new Error(err.detail ?? "Credenciales inválidas");
  }
  return res.json() as Promise<LoginResponse>;
}

export async function register(
  email: string,
  password: string,
  opts?: { first_name?: string; last_name?: string }
): Promise<User> {
  const res = await fetch(`${API_BASE_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, ...opts }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Error al registrar" })) as { detail?: string };
    throw new Error(err.detail ?? "Error al registrar");
  }
  return res.json() as Promise<User>;
}

export async function getMe(): Promise<User> {
  return apiFetch<User>("/users/me");
}

export async function sendMessage(message: string, sessionId: string): Promise<ChatResponse> {
  return apiFetch<ChatResponse>("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId }),
  });
}

export async function getChatHistory(sessionId: string): Promise<HistoryMessage[]> {
  const data = await apiFetch<{ messages: HistoryMessage[] }>(`/chat/history?session_id=${sessionId}`);
  return data.messages;
}

export async function streamMessage(
  message: string,
  sessionId: string,
  onChunk: (chunk: string) => void
): Promise<void> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}/chat/stream`, {
    method: "POST",
    headers,
    body: JSON.stringify({ message, session_id: sessionId }),
  });

  if (res.status === 401) {
    clearToken();
    window.location.href = "/login";
    throw new Error("Sesión expirada");
  }
  if (!res.ok) throw new Error("Error en streaming");

  const reader = res.body?.getReader();
  if (!reader) throw new Error("Sin stream");
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const text = decoder.decode(value);
    for (const line of text.split("\n")) {
      if (line.startsWith("data: ")) {
        const data = line.slice(6);
        if (data === "[DONE]") return;
        onChunk(data === "" ? "\n" : data);
      }
    }
  }
}

export async function endSession(sessionId: string): Promise<void> {
  return apiFetch<void>("/chat/end-session", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId }),
  });
}

export async function ingestPdf(file: File, collection: string): Promise<IngestResponse> {
  const form = new FormData();
  form.append("file", file);
  form.append("collection", collection);
  form.append("source_name", file.name);
  const token = getToken();
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE_URL}/ingest/pdf`, {
    method: "POST",
    headers,
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Error al subir PDF" })) as { detail?: unknown };
    const detail = err.detail;
    const msg = Array.isArray(detail)
      ? detail.map((d: { msg?: string }) => d.msg ?? JSON.stringify(d)).join(", ")
      : typeof detail === "string"
      ? detail
      : "Error al subir PDF";
    throw new Error(msg);
  }
  return res.json() as Promise<IngestResponse>;
}

// ---------------------------------------------------------------------------
// Assessments
// ---------------------------------------------------------------------------

export interface AssessmentStatus {
  needed: boolean;
  phq9_score: number | null;
  phq9_severity: string | null;
  asq_result: string | null;
}

export interface AssessmentResult {
  phq9_score: number;
  phq9_severity: string;
  asq_result: string;
}

export interface AssessmentSubmission {
  phq9_answers: number[];
  asq_answers: boolean[];
  asq_acuity_answer: boolean | null;
}

export async function getAssessmentStatus(): Promise<AssessmentStatus> {
  return apiFetch<AssessmentStatus>("/assessments/status");
}

export async function submitAssessments(
  submission: AssessmentSubmission
): Promise<AssessmentResult> {
  return apiFetch<AssessmentResult>("/assessments/submit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(submission),
  });
}
