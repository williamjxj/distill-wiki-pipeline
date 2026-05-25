import { useCallback, useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  approveAnalysis,
  approveDraft,
  confirmIngest,
  getPendingRaw,
  startIngest,
  type IngestJob,
  type PendingRawItem,
} from "../api";
import styles from "./IngestWizard.module.css";

const STEPS = ["Select file", "Analysis", "Draft", "Confirm"] as const;

export default function IngestWizard() {
  const [searchParams] = useSearchParams();
  const initialPath = searchParams.get("path");

  const [step, setStep] = useState(initialPath ? 2 : 1);
  const [pending, setPending] = useState<PendingRawItem[]>([]);
  const [selectedPath, setSelectedPath] = useState<string | null>(initialPath);
  const [job, setJob] = useState<IngestJob | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmed, setConfirmed] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function loadPending() {
      setLoading(true);
      setError(null);
      try {
        const data = await getPendingRaw();
        if (!cancelled) {
          setPending(data.items);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load queue");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadPending();
    return () => {
      cancelled = true;
    };
  }, []);

  const runStartIngest = useCallback(async (rawPath: string) => {
    setActionLoading(true);
    setError(null);
    try {
      const result = await startIngest(rawPath);
      setJob(result);
      setStep(2);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start ingest");
    } finally {
      setActionLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!initialPath || job || actionLoading || loading) {
      return;
    }
    setSelectedPath(initialPath);
    void runStartIngest(initialPath);
  }, [initialPath, job, actionLoading, loading, runStartIngest]);

  async function handleSelectContinue() {
    if (!selectedPath) {
      return;
    }
    await runStartIngest(selectedPath);
  }

  async function handleApproveAnalysis() {
    if (!job) {
      return;
    }
    setActionLoading(true);
    setError(null);
    try {
      const result = await approveAnalysis(job.id);
      setJob(result);
      setStep(3);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to approve analysis");
    } finally {
      setActionLoading(false);
    }
  }

  async function handleApproveDraft() {
    if (!job) {
      return;
    }
    setActionLoading(true);
    setError(null);
    try {
      const result = await approveDraft(job.id);
      setJob(result);
      setStep(4);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to approve draft");
    } finally {
      setActionLoading(false);
    }
  }

  async function handleConfirm() {
    if (!job) {
      return;
    }
    setActionLoading(true);
    setError(null);
    try {
      const result = await confirmIngest(job.id);
      setJob(result);
      setConfirmed(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to confirm ingest");
    } finally {
      setActionLoading(false);
    }
  }

  if (loading && step === 1) {
    return <p className={styles.muted}>Loading pending raw files…</p>;
  }

  return (
    <div className={styles.page}>
      <h1>Ingest Wizard</h1>

      <div className={styles.steps}>
        {STEPS.map((label, index) => {
          const stepNumber = index + 1;
          const className = [
            styles.step,
            stepNumber === step ? styles.stepActive : "",
            stepNumber < step || confirmed ? styles.stepDone : "",
          ]
            .filter(Boolean)
            .join(" ");
          return (
            <span key={label} className={className}>
              {stepNumber}. {label}
            </span>
          );
        })}
      </div>

      {error && <p className={styles.error}>{error}</p>}

      {step === 1 && (
        <section className={styles.section}>
          <h2>Select a pending raw file</h2>
          {pending.length === 0 ? (
            <p className={styles.muted}>No pending raw files.</p>
          ) : (
            <ul className={styles.list}>
              {pending.map((item) => (
                <li key={item.path}>
                  <label
                    className={[
                      styles.fileOption,
                      selectedPath === item.path ? styles.fileOptionSelected : "",
                    ]
                      .filter(Boolean)
                      .join(" ")}
                  >
                    <input
                      type="radio"
                      name="raw-file"
                      value={item.path}
                      checked={selectedPath === item.path}
                      onChange={() => setSelectedPath(item.path)}
                    />
                    <span className={styles.path}>{item.path}</span>
                  </label>
                </li>
              ))}
            </ul>
          )}
          <div className={styles.actions}>
            <button
              type="button"
              disabled={!selectedPath || actionLoading}
              onClick={() => void handleSelectContinue()}
            >
              {actionLoading ? "Starting…" : "Start Ingest"}
            </button>
          </div>
        </section>
      )}

      {step === 2 && (
        <section className={styles.section}>
          <h2>Analysis</h2>
          {actionLoading && !job?.analysis ? (
            <p className={styles.muted}>Running analysis…</p>
          ) : (
            <>
              {job && (
                <p className={styles.muted}>
                  Job <span className={styles.path}>{job.id}</span> ·{" "}
                  {job.raw_path}
                </p>
              )}
              <pre className={styles.pre}>
                {job?.analysis ?? "No analysis available."}
              </pre>
              <div className={styles.actions}>
                <button
                  type="button"
                  disabled={actionLoading || !job?.analysis}
                  onClick={() => void handleApproveAnalysis()}
                >
                  {actionLoading ? "Generating draft…" : "Approve Analysis"}
                </button>
              </div>
            </>
          )}
        </section>
      )}

      {step === 3 && (
        <section className={styles.section}>
          <h2>Draft preview</h2>
          <DraftFields payload={job?.draft_payload} />
          <div className={styles.actions}>
            <button
              type="button"
              disabled={actionLoading || !job?.draft_payload}
              onClick={() => void handleApproveDraft()}
            >
              {actionLoading ? "Approving…" : "Approve Draft"}
            </button>
          </div>
        </section>
      )}

      {step === 4 && (
        <section className={styles.section}>
          <h2>Confirm ingest</h2>
          {confirmed ? (
            <>
              <p className={styles.success}>
                Ingest completed for{" "}
                <span className={styles.path}>{job?.raw_path}</span>.
              </p>
              <div className={styles.actions}>
                <Link to="/" className={styles.link}>
                  Back to Dashboard
                </Link>
              </div>
            </>
          ) : (
            <>
              <p className={styles.muted}>
                This will write source pages, concept updates, thesis changes,
                and mark the raw file as ingested.
              </p>
              <div className={styles.actions}>
                <button
                  type="button"
                  disabled={actionLoading}
                  onClick={() => void handleConfirm()}
                >
                  {actionLoading ? "Confirming…" : "Confirm Ingest"}
                </button>
              </div>
            </>
          )}
        </section>
      )}
    </div>
  );
}

function DraftFields({
  payload,
}: {
  payload: IngestJob["draft_payload"] | undefined;
}) {
  if (!payload) {
    return <p className={styles.muted}>No draft payload available.</p>;
  }

  const conceptUpdates = payload.concept_updates ?? {};

  return (
    <>
      <div className={styles.field}>
        <span className={styles.fieldLabel}>source_md</span>
        <pre className={styles.pre}>{payload.source_md ?? "—"}</pre>
      </div>

      <div className={styles.field}>
        <span className={styles.fieldLabel}>concept_updates</span>
        {Object.keys(conceptUpdates).length === 0 ? (
          <pre className={styles.pre}>—</pre>
        ) : (
          Object.entries(conceptUpdates).map(([slug, content]) => (
            <div key={slug} className={styles.field}>
              <span className={styles.fieldLabel}>{slug}</span>
              <pre className={styles.pre}>{content}</pre>
            </div>
          ))
        )}
      </div>

      <div className={styles.field}>
        <span className={styles.fieldLabel}>thesis_delta</span>
        <pre className={styles.pre}>{payload.thesis_delta ?? "—"}</pre>
      </div>
    </>
  );
}
