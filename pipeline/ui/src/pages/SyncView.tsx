import { useEffect, useState } from "react";
import { postSync } from "../api";
import { useLocation } from "react-router-dom";
import styles from "./SyncView.module.css";

export default function SyncView() {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [briefOnly, setBriefOnly] = useState(false);
  const loc = useLocation();

  useEffect(() => {
    const qp = new URLSearchParams(loc.search);
    const val = qp.get("brief_only");
    setBriefOnly(val === "1" || val === "true");
  }, [loc.search]);

  async function handleSync() {
    setLoading(true);
    setMessage(null);
    setError(null);
    try {
      const result = await postSync(briefOnly);
      const warnings = result.warnings?.length
        ? `\nWarnings:\n${result.warnings.join("\n")}`
        : "";
      setMessage(`${result.stdout || ""}${warnings}`.trim() || "Sync completed.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sync failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={styles.page}>
      <h1>Sync Wiki Synthesis</h1>
      <p className={styles.help}>
        Copy the wiki synthesis exports into the parent project's `docs/`.
      </p>

      <div className={styles.controls}>
        <label className={styles.checkbox}>
          <input
            type="checkbox"
            checked={briefOnly}
            onChange={(e) => setBriefOnly(e.target.checked)}
          />
          Brief only
        </label>

        <button type="button" onClick={() => void handleSync()} disabled={loading}>
          {loading ? "Syncing…" : "Run Sync"}
        </button>
      </div>

      {message && <pre className={styles.output}>{message}</pre>}
      {error && <p className={styles.error}>{error}</p>}
    </div>
  );
}
