export const API_BASE =
  import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8787";

export interface RawFile {
  path: string;
  status: string;
  topic: string | null;
  source: string | null;
  date: string | null;
}

export interface PipelineStatus {
  pending_raw_count: number;
  pending_raw_files: RawFile[];
  lint_error_count: number;
  lint_warning_count: number;
  export_cycle: number | null;
  brief_status: string | null;
  last_log_entry: string | null;
}

export interface PendingRawItem {
  path: string;
  meta: Record<string, unknown>;
}

export interface LintFinding {
  severity: string;
  code: string;
  message: string;
  path: string | null;
}

export interface SyncResult {
  stdout: string;
  warnings: string[];
}

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function getStatus(): Promise<PipelineStatus> {
  return fetchJson<PipelineStatus>("/api/status");
}

export function getPendingRaw(): Promise<{ items: PendingRawItem[] }> {
  return fetchJson<{ items: PendingRawItem[] }>("/api/raw/pending");
}

export function getLog(): Promise<{ content: string }> {
  return fetchJson<{ content: string }>("/api/log");
}

export function getLint(): Promise<{ findings: LintFinding[] }> {
  return fetchJson<{ findings: LintFinding[] }>("/api/lint");
}

export function postSync(briefOnly: boolean): Promise<SyncResult> {
  return fetchJson<SyncResult>("/api/sync", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ brief_only: briefOnly }),
  });
}
