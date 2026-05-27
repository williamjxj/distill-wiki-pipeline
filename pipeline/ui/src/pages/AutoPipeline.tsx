import { useCallback, useEffect, useRef, useState } from "react";
import {
  getPendingRaw,
  runAutoPipeline,
  uploadRaw,
  type PendingRawItem,
} from "../api";
import styles from "./AutoPipeline.module.css";

const STEPS = [
  { key: "frontmatter", label: "Frontmatter" },
  { key: "ingest", label: "Ingest" },
  { key: "lint", label: "Lint" },
  { key: "export", label: "Export" },
  { key: "lint2", label: "Lint" },
  { key: "graph", label: "Graph" },
  { key: "sync", label: "Sync" },
] as const;

type StepStatus = "pending" | "running" | "done" | "failed" | "skipped";

interface StepState {
  status: StepStatus;
  message: string;
}

interface Summary {
  files_processed: number;
  errors: number;
  warnings: number;
}

type PipelinePhase = "idle" | "running" | "completed" | "failed";

export default function AutoPipeline() {
  const [pending, setPending] = useState<PendingRawItem[]>([]);
  const [selectedFile, setSelectedFile] = useState("all");
  const [phase, setPhase] = useState<PipelinePhase>("idle");
  const [summary, setSummary] = useState<Summary | null>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [stepStates, setStepStates] = useState<Map<string, StepState>>(
    () => new Map(),
  );
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [rawType, setRawType] = useState<"llm-chat" | "web-article">("llm-chat");
  const [source, setSource] = useState("claude");
  const [topic, setTopic] = useState("");
  const [question, setQuestion] = useState("");
  const [url, setUrl] = useState("");
  const [file, setFile] = useState<File | null>(null);

  const abortRef = useRef<AbortController | null>(null);
  const logEndRef = useRef<HTMLDivElement | null>(null);

  const loadPending = useCallback(async () => {
    setError(null);
    try {
      const data = await getPendingRaw();
      setPending(data.items);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load pending files",
      );
    }
  }, []);

  useEffect(() => {
    void loadPending();
  }, [loadPending]);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  async function handleUpload(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("type", rawType);
      formData.append("source", source);
      formData.append("topic", topic);
      formData.append("date", new Date().toISOString().slice(0, 10));
      if (rawType === "llm-chat") {
        formData.append("question", question);
      } else {
        formData.append("url", url);
      }

      const result = await uploadRaw(formData);
      setTopic("");
      setQuestion("");
      setUrl("");
      setFile(null);
      const data = await getPendingRaw();
      setPending(data.items);
      setSelectedFile(result.path);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  function handleRun() {
    if (phase === "running") return;
    setPhase("running");
    setSummary(null);
    setLogs([]);
    setStepStates(new Map());
    setError(null);
    void runPipeline();
  }

  function handleCancel() {
    abortRef.current?.abort();
    setPhase("idle");
  }

  async function runPipeline() {
    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const response = await runAutoPipeline(selectedFile);
      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }
      if (!response.body) {
        throw new Error("No response body");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() ?? "";

        for (const part of parts) {
          const dataMatch = part.match(/^data: (.+)$/m);
          if (!dataMatch) continue;
          try {
            const event = JSON.parse(dataMatch[1]) as Record<string, unknown>;
            if (event.event === "log") {
              setLogs((prev) => [...prev, (event.line as string) ?? ""]);
            } else if (event.event === "step") {
              const stepKey = event.step as string;
              const status = event.status as StepStatus;
              const message = (event.message as string) ?? "";
              setStepStates((prev) => {
                const next = new Map(prev);
                next.set(stepKey, { status, message });
                return next;
              });
              setLogs((prev) => [...prev, message]);
            } else if (event.event === "result") {
              setSummary(event.summary as Summary);
              setPhase(event.status === "completed" ? "completed" : "failed");
            }
          } catch {
            // noop
          }
        }
      }
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") {
        return;
      }
      setError(
        err instanceof Error ? err.message : "Pipeline failed unexpectedly",
      );
      setPhase("failed");
    } finally {
      abortRef.current = null;
    }
  }

  const hasPending = pending.length > 0;
  const isRunning = phase === "running";

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1>Auto Pipeline</h1>
      </header>

      {/* ── Upload form (idle only) ───────────────── */}
      {!isRunning && (
        <section className={styles.uploadSection}>
          <h2>Upload raw file</h2>
          <form className={styles.uploadForm} onSubmit={(event) => void handleUpload(event)}>
            <label className={styles.field}>
              Type
              <select value={rawType} onChange={(e) => setRawType(e.target.value as "llm-chat" | "web-article")}>
                <option value="llm-chat">llm-chat</option>
                <option value="web-article">web-article</option>
              </select>
            </label>
            <label className={styles.field}>
              Source
              <select value={source} onChange={(e) => setSource(e.target.value)}>
                <option value="claude">claude</option>
                <option value="chatgpt">chatgpt</option>
                <option value="gemini">gemini</option>
                <option value="web">web</option>
              </select>
            </label>
            <label className={styles.field}>
              Topic
              <input type="text" value={topic} onChange={(e) => setTopic(e.target.value)} required />
            </label>
            {rawType === "llm-chat" ? (
              <label className={styles.fieldWide}>
                Question
                <input type="text" value={question} onChange={(e) => setQuestion(e.target.value)} required />
              </label>
            ) : (
              <label className={styles.fieldWide}>
                URL
                <input type="url" value={url} onChange={(e) => setUrl(e.target.value)} required />
              </label>
            )}
            <label className={styles.fieldWide}>
              Markdown file
              <input
                type="file"
                accept=".md,text/markdown,text/plain"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                required
              />
            </label>
            <div className={styles.uploadActions}>
              <button type="submit" disabled={uploading}>
                {uploading ? "Uploading…" : "Upload & add to queue"}
              </button>
            </div>
          </form>
        </section>
      )}

      {/* ── Pipeline controls ─────────────────────── */}
      <section className={styles.controls}>
        <div className={styles.controlRow}>
          <label className={styles.label}>
            Target
            <select
              className={styles.select}
              value={selectedFile}
              onChange={(e) => setSelectedFile(e.target.value)}
              disabled={isRunning}
            >
              {!hasPending && (
                <option value="all" disabled>
                  No pending files — upload one above
                </option>
              )}
              {hasPending && <option value="all">All Pending ({pending.length})</option>}
              {pending.map((f) => (
                <option key={f.path} value={f.path}>
                  {f.path}
                </option>
              ))}
            </select>
          </label>

          <button
            type="button"
            className={styles.runButton}
            onClick={handleRun}
            disabled={isRunning || !hasPending}
          >
            {isRunning ? "Running…" : "Run Auto Pipeline"}
          </button>

          {isRunning && (
            <button type="button" className={styles.cancelButton} onClick={handleCancel}>
              Cancel
            </button>
          )}
        </div>
      </section>

      {/* ── Stepper ────────────────────────────────── */}
      <section className={styles.stepper}>
        {STEPS.map((step) => {
          const state = stepStates.get(step.key);
          const status: StepStatus = state?.status ?? "pending";
          return (
            <div
              key={step.key}
              className={`${styles.step} ${styles[`step${status.charAt(0).toUpperCase() + status.slice(1)}`]}`}
            >
              <span className={styles.stepIcon}>
                {status === "running" && "▶"}
                {status === "done" && "✓"}
                {status === "failed" && "✗"}
                {status === "skipped" && "→"}
                {status === "pending" && "○"}
              </span>
              <span className={styles.stepLabel}>{step.label}</span>
            </div>
          );
        })}
      </section>

      {/* ── Errors ────────────────────────────────── */}
      {error && <p className={styles.error}>{error}</p>}

      {/* ── Log output ────────────────────────────── */}
      {(isRunning || phase === "completed" || phase === "failed") &&
        logs.length > 0 && (
          <section className={styles.logSection}>
            <h2>Output</h2>
            <pre className={styles.logOutput}>
              {logs.map((line, i) => (
                <div key={i}>{line}</div>
              ))}
              <div ref={logEndRef} />
            </pre>
          </section>
        )}

      {/* ── Result banner ─────────────────────────── */}
      {summary && (
        <section
          className={`${styles.resultBanner} ${
            phase === "completed" ? styles.resultSuccess : styles.resultFailed
          }`}
        >
          <span className={styles.resultIcon}>
            {phase === "completed" ? "✓" : "✗"}
          </span>
          <div className={styles.resultBody}>
            <strong>
              {phase === "completed"
                ? "Pipeline completed"
                : "Pipeline failed"}
            </strong>
            <p>
              {summary.files_processed} file
              {summary.files_processed !== 1 ? "s" : ""} processed,{" "}
              {summary.errors} error{summary.errors !== 1 ? "s" : ""},{" "}
              {summary.warnings} warning{summary.warnings !== 1 ? "s" : ""}
            </p>
          </div>
        </section>
      )}
    </div>
  );
}
