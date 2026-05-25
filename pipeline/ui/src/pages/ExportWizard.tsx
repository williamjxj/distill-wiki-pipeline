import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  approveExport,
  getExportJob,
  getLint,
  postSync,
  startExport,
  type ExportJob,
  type LintFinding,
} from "../api";
import styles from "./ExportWizard.module.css";

export default function ExportWizard() {
  const [findings, setFindings] = useState<LintFinding[]>([]);
  const [job, setJob] = useState<ExportJob | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [force, setForce] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [approved, setApproved] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);

  const loadLint = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getLint();
      setFindings(data.findings);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load lint");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadLint();
  }, [loadLint]);

  const errorCount = findings.filter((f) => f.severity === "error").length;
  const warningCount = findings.filter((f) => f.severity === "warning").length;
  const infoCount = findings.filter((f) => f.severity === "info").length;

  async function handleStartExport() {
    setActionLoading(true);
    setError(null);
    setApproved(false);
    setSyncMessage(null);
    try {
      const result = await startExport(force);
      setJob(result);
      if (result.state === "lint_blocked") {
        setForce(true);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start export");
    } finally {
      setActionLoading(false);
    }
  }

  async function handleApprove() {
    if (!job) {
      return;
    }
    setActionLoading(true);
    setError(null);
    try {
      const result = await approveExport(job.id);
      setJob(result);
      setApproved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to approve export");
    } finally {
      setActionLoading(false);
    }
  }

  async function handleSync() {
    setSyncing(true);
    setError(null);
    try {
      const result = await postSync(true);
      const warnings =
        result.warnings.length > 0
          ? `\nWarnings:\n${result.warnings.join("\n")}`
          : "";
      setSyncMessage(`${result.stdout}${warnings}`.trim() || "Sync completed.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sync failed");
    } finally {
      setSyncing(false);
    }
  }

  async function handleRefreshJob() {
    if (!job) {
      return;
    }
    setActionLoading(true);
    setError(null);
    try {
      setJob(await getExportJob(job.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to refresh job");
    } finally {
      setActionLoading(false);
    }
  }

  if (loading) {
    return <p className={styles.muted}>Loading lint summary…</p>;
  }

  return (
    <div className={styles.page}>
      <h1>Export Wizard</h1>

      <section className={styles.section}>
        <h2>Lint summary</h2>
        <div className={styles.summaryGrid}>
          <div className={styles.summaryCard}>
            <span className={styles.summaryLabel}>Errors</span>
            <span className={styles.summaryValue}>{errorCount}</span>
          </div>
          <div className={styles.summaryCard}>
            <span className={styles.summaryLabel}>Warnings</span>
            <span className={styles.summaryValue}>{warningCount}</span>
          </div>
          <div className={styles.summaryCard}>
            <span className={styles.summaryLabel}>Info</span>
            <span className={styles.summaryValue}>{infoCount}</span>
          </div>
        </div>

        {findings.length === 0 ? (
          <p className={styles.muted}>No lint findings.</p>
        ) : (
          <ul className={styles.findings}>
            {findings.map((finding, index) => (
              <li
                key={`${finding.code}-${finding.path ?? index}`}
                className={[
                  styles.finding,
                  finding.severity === "error"
                    ? styles.findingError
                    : finding.severity === "warning"
                      ? styles.findingWarning
                      : styles.findingInfo,
                ]
                  .filter(Boolean)
                  .join(" ")}
              >
                [{finding.severity}] {finding.code}: {finding.message}
              </li>
            ))}
          </ul>
        )}
      </section>

      {error && <p className={styles.error}>{error}</p>}

      {!job || job.state === "lint_blocked" ? (
        <section className={styles.section}>
          <h2>Start export</h2>
          {job?.state === "lint_blocked" && (
            <p className={styles.error}>
              Export blocked by {job.lint_findings.length} lint error(s). Enable
              force to proceed anyway.
            </p>
          )}
          <div className={styles.actions}>
            <label className={styles.checkbox}>
              <input
                type="checkbox"
                checked={force}
                onChange={(event) => setForce(event.target.checked)}
              />
              Force export despite lint errors
            </label>
            <button
              type="button"
              disabled={actionLoading}
              onClick={() => void handleStartExport()}
            >
              {actionLoading ? "Starting…" : "Start Export"}
            </button>
            <button type="button" onClick={() => void loadLint()} disabled={loading}>
              Refresh Lint
            </button>
          </div>
        </section>
      ) : null}

      {job?.state === "draft_done" && (
        <section className={styles.section}>
          <h2>Draft brief preview</h2>
          <p className={styles.muted}>
            Cycle {job.export_cycle ?? "—"} · status draft ·{" "}
            {job.sources_ingested ?? 0} sources ingested
          </p>
          {job.prior_brief && (
            <div>
              <p className={styles.muted}>
                Prior brief (cycle {job.prior_export_cycle ?? "—"}, status{" "}
                {job.prior_brief_status ?? "unknown"})
              </p>
              <pre className={styles.pre}>{job.prior_brief}</pre>
            </div>
          )}
          <pre className={styles.pre}>{job.draft_body ?? "No draft body."}</pre>
          <div className={styles.actions}>
            <button
              type="button"
              disabled={actionLoading}
              onClick={() => void handleApprove()}
            >
              {actionLoading ? "Approving…" : "Approve Export"}
            </button>
            <button
              type="button"
              disabled={actionLoading}
              onClick={() => void handleRefreshJob()}
            >
              Refresh
            </button>
          </div>
        </section>
      )}

      {approved && job?.state === "completed" && (
        <section className={styles.section}>
          <h2>Export approved</h2>
          <p className={styles.success}>
            Project brief cycle {job.export_cycle ?? "—"} is now current.
          </p>
          <div className={styles.actions}>
            <button type="button" disabled={syncing} onClick={() => void handleSync()}>
              {syncing ? "Syncing…" : "Sync to Parent Docs"}
            </button>
            <Link to="/" className={styles.link}>
              Back to Dashboard
            </Link>
          </div>
          {syncMessage && <pre className={styles.output}>{syncMessage}</pre>}
        </section>
      )}
    </div>
  );
}
