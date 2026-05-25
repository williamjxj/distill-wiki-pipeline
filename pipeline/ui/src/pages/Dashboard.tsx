import { useCallback, useEffect, useState } from "react";
import { getStatus, postSync, type PipelineStatus } from "../api";
import styles from "./Dashboard.module.css";

export default function Dashboard() {
  const [status, setStatus] = useState<PipelineStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [briefOnly, setBriefOnly] = useState(false);
  const [syncMessage, setSyncMessage] = useState<string | null>(null);

  const loadStatus = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setStatus(await getStatus());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load status");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadStatus();
  }, [loadStatus]);

  async function handleSync() {
    setSyncing(true);
    setSyncMessage(null);
    setError(null);
    try {
      const result = await postSync(briefOnly);
      const warnings =
        result.warnings.length > 0
          ? `\nWarnings:\n${result.warnings.join("\n")}`
          : "";
      setSyncMessage(`${result.stdout}${warnings}`.trim() || "Sync completed.");
      await loadStatus();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sync failed");
    } finally {
      setSyncing(false);
    }
  }

  if (loading && !status) {
    return <p className={styles.muted}>Loading dashboard…</p>;
  }

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <h1>Pipeline Dashboard</h1>
        <button type="button" onClick={() => void loadStatus()} disabled={loading}>
          Refresh
        </button>
      </header>

      {error && <p className={styles.error}>{error}</p>}

      {status && (
        <div className={styles.grid}>
          <section className={styles.card}>
            <h2>Pending Raw</h2>
            <p className={styles.metric}>{status.pending_raw_count}</p>
          </section>

          <section className={styles.card}>
            <h2>Lint</h2>
            <p className={styles.metric}>
              {status.lint_error_count} errors / {status.lint_warning_count}{" "}
              warnings
            </p>
          </section>

          <section className={styles.card}>
            <h2>Brief Status</h2>
            <p>{status.brief_status ?? "—"}</p>
          </section>

          <section className={styles.card}>
            <h2>Export Cycle</h2>
            <p>{status.export_cycle ?? "—"}</p>
          </section>

          <section className={`${styles.card} ${styles.wide}`}>
            <h2>Last Log Entry</h2>
            <p className={styles.mono}>{status.last_log_entry ?? "—"}</p>
          </section>
        </div>
      )}

      <section className={styles.sync}>
        <label className={styles.checkbox}>
          <input
            type="checkbox"
            checked={briefOnly}
            onChange={(event) => setBriefOnly(event.target.checked)}
          />
          Brief only
        </label>
        <button type="button" onClick={() => void handleSync()} disabled={syncing}>
          {syncing ? "Syncing…" : "Run Sync"}
        </button>
      </section>

      {syncMessage && (
        <pre className={styles.output}>{syncMessage}</pre>
      )}
    </div>
  );
}
