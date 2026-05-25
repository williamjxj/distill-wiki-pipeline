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

export interface IngestDraftPayload {
  source_md?: string;
  concept_updates?: Record<string, string>;
  thesis_delta?: string;
  index_lines?: string[];
  log_entry?: string;
}

export interface IngestJob {
  id: string;
  state: string;
  raw_path: string;
  analysis: string | null;
  draft: string | null;
  draft_payload: IngestDraftPayload | null;
  error: string | null;
}

function postJson<T>(path: string, body?: unknown): Promise<T> {
  return fetchJson<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
}

export function startIngest(rawPath: string): Promise<IngestJob> {
  return postJson<IngestJob>("/api/jobs/ingest", { raw_path: rawPath });
}

export function approveAnalysis(jobId: string): Promise<IngestJob> {
  return postJson<IngestJob>(`/api/jobs/ingest/${jobId}/approve-analysis`);
}

export function approveDraft(
  jobId: string,
  edits?: IngestDraftPayload,
): Promise<IngestJob> {
  return postJson<IngestJob>(`/api/jobs/ingest/${jobId}/approve-draft`, {
    edits: edits ?? undefined,
  });
}

export function confirmIngest(jobId: string): Promise<IngestJob> {
  return postJson<IngestJob>(`/api/jobs/ingest/${jobId}/confirm`);
}

export function getJob(jobId: string): Promise<IngestJob> {
  return fetchJson<IngestJob>(`/api/jobs/ingest/${jobId}`);
}
