import { useEffect, useState } from "react";
import { getLog } from "../api";
import styles from "./LogViewer.module.css";

export default function LogViewer() {
  const [content, setContent] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await getLog();
        if (!cancelled) {
          setContent(data.content);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load log");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return <p className={styles.muted}>Loading log…</p>;
  }

  if (error) {
    return <p className={styles.error}>{error}</p>;
  }

  return (
    <div className={styles.page}>
      <h1>Pipeline Log</h1>
      {content ? (
        <pre className={styles.log}>{content}</pre>
      ) : (
        <p className={styles.muted}>Log is empty.</p>
      )}
    </div>
  );
}
