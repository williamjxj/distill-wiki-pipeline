import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getPendingRaw, type PendingRawItem } from "../api";
import styles from "./RawQueue.module.css";

export default function RawQueue() {
  const [items, setItems] = useState<PendingRawItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await getPendingRaw();
        if (!cancelled) {
          setItems(data.items);
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

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return <p className={styles.muted}>Loading pending raw files…</p>;
  }

  if (error) {
    return <p className={styles.error}>{error}</p>;
  }

  if (items.length === 0) {
    return <p className={styles.muted}>No pending raw files.</p>;
  }

  return (
    <div className={styles.page}>
      <h1>Raw Queue</h1>
      <p className={styles.count}>{items.length} pending file(s)</p>
      <ul className={styles.list}>
        {items.map((item) => (
          <li key={item.path} className={styles.item}>
            <div className={styles.row}>
              <span className={styles.path}>{item.path}</span>
              <Link
                to={`/ingest?path=${encodeURIComponent(item.path)}`}
                className={styles.ingestLink}
              >
                Ingest
              </Link>
            </div>
            <span className={styles.meta}>
              {formatMeta(item.meta)}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function formatMeta(meta: Record<string, unknown>): string {
  const parts = ["topic", "source", "date", "status"]
    .map((key) => {
      const value = meta[key];
      if (value == null || value === "") {
        return null;
      }
      return `${key}: ${String(value)}`;
    })
    .filter(Boolean);

  return parts.length > 0 ? parts.join(" · ") : "No metadata";
}
