import { useCallback, useEffect, useMemo, useState } from "react";
import { getLint, type LintFinding } from "../api";
import styles from "./LintDashboard.module.css";

const SEVERITY_ORDER = ["error", "warning", "info"] as const;

export default function LintDashboard() {
  const [findings, setFindings] = useState<LintFinding[]>([]);
  const [dismissed, setDismissed] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  const grouped = useMemo(() => {
    const groups: Record<string, LintFinding[]> = {
      error: [],
      warning: [],
      info: [],
    };
    for (const finding of findings) {
      const bucket = groups[finding.severity] ?? groups.info;
      bucket.push(finding);
    }
    return groups;
  }, [findings]);

  function findingKey(finding: LintFinding, index: number): string {
    return `${finding.severity}:${finding.code}:${finding.path ?? index}`;
  }

  function toggleDismissed(key: string) {
    setDismissed((current) => {
      const next = new Set(current);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  }

  if (loading) {
    return <p className={styles.muted}>Loading lint findings…</p>;
  }

  return (
    <div className={styles.page}>
      <h1>Lint Dashboard</h1>

      <div className={styles.summaryGrid}>
        {SEVERITY_ORDER.map((severity) => (
          <div key={severity} className={styles.summaryCard}>
            <span className={styles.summaryLabel}>{severity}</span>
            <span className={styles.summaryValue}>{grouped[severity].length}</span>
          </div>
        ))}
      </div>

      {error && <p className={styles.error}>{error}</p>}

      {SEVERITY_ORDER.map((severity) => {
        const items = grouped[severity];
        if (items.length === 0) {
          return null;
        }

        return (
          <section key={severity} className={styles.section}>
            <h2>{severity.charAt(0).toUpperCase() + severity.slice(1)}</h2>
            <ul className={styles.checklist}>
              {items.map((finding, index) => {
                const key = findingKey(finding, index);
                const isDismissed = dismissed.has(key);
                return (
                  <li
                    key={key}
                    className={[
                      styles.item,
                      styles[severity],
                      isDismissed ? styles.itemDismissed : "",
                    ]
                      .filter(Boolean)
                      .join(" ")}
                  >
                    <input
                      type="checkbox"
                      className={styles.checkbox}
                      checked={isDismissed}
                      onChange={() => toggleDismissed(key)}
                      aria-label={`Acknowledge ${finding.code}`}
                    />
                    <div className={styles.content}>
                      <span className={styles.code}>{finding.code}</span>
                      <p className={styles.message}>{finding.message}</p>
                      {finding.path && (
                        <p className={styles.path}>{finding.path}</p>
                      )}
                    </div>
                  </li>
                );
              })}
            </ul>
          </section>
        );
      })}

      {findings.length === 0 && !error && (
        <p className={styles.muted}>No lint findings.</p>
      )}

      <div className={styles.actions}>
        <button type="button" onClick={() => void loadLint()} disabled={loading}>
          Refresh
        </button>
      </div>
    </div>
  );
}
