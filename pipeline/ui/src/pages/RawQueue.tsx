import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getPendingRaw, uploadRaw, type PendingRawItem } from "../api";
import styles from "./RawQueue.module.css";

export default function RawQueue() {
  const [items, setItems] = useState<PendingRawItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);
  const [rawType, setRawType] = useState<"llm-chat" | "web-article">("llm-chat");
  const [source, setSource] = useState("claude");
  const [topic, setTopic] = useState("");
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [question, setQuestion] = useState("");
  const [url, setUrl] = useState("");
  const [file, setFile] = useState<File | null>(null);

  async function loadQueue() {
    setLoading(true);
    setError(null);
    try {
      const data = await getPendingRaw();
      setItems(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load queue");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadQueue();
  }, []);

  async function handleUpload(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file) {
      setError("Choose a markdown file to upload.");
      return;
    }

    setUploading(true);
    setError(null);
    setUploadMessage(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("type", rawType);
      formData.append("source", source);
      formData.append("topic", topic);
      formData.append("date", date);
      if (rawType === "llm-chat") {
        formData.append("question", question);
      } else {
        formData.append("url", url);
      }

      const result = await uploadRaw(formData);
      setUploadMessage(`Uploaded ${result.path}`);
      setTopic("");
      setQuestion("");
      setUrl("");
      setFile(null);
      await loadQueue();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className={styles.page}>
      <h1>Raw Queue</h1>

      <section className={styles.uploadSection}>
        <h2>Upload raw file</h2>
        <form className={styles.uploadForm} onSubmit={(event) => void handleUpload(event)}>
          <label className={styles.field}>
            Type
            <select
              value={rawType}
              onChange={(event) =>
                setRawType(event.target.value as "llm-chat" | "web-article")
              }
            >
              <option value="llm-chat">llm-chat</option>
              <option value="web-article">web-article</option>
            </select>
          </label>

          <label className={styles.field}>
            Source
            <select value={source} onChange={(event) => setSource(event.target.value)}>
              <option value="claude">claude</option>
              <option value="chatgpt">chatgpt</option>
              <option value="gemini">gemini</option>
              <option value="web">web</option>
            </select>
          </label>

          <label className={styles.field}>
            Topic
            <input
              type="text"
              value={topic}
              onChange={(event) => setTopic(event.target.value)}
              required
            />
          </label>

          <label className={styles.field}>
            Date
            <input
              type="date"
              value={date}
              onChange={(event) => setDate(event.target.value)}
              required
            />
          </label>

          {rawType === "llm-chat" ? (
            <label className={styles.fieldWide}>
              Question
              <input
                type="text"
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                required
              />
            </label>
          ) : (
            <label className={styles.fieldWide}>
              URL
              <input
                type="url"
                value={url}
                onChange={(event) => setUrl(event.target.value)}
                required
              />
            </label>
          )}

          <label className={styles.fieldWide}>
            Markdown file
            <input
              type="file"
              accept=".md,text/markdown,text/plain"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              required
            />
          </label>

          <div className={styles.uploadActions}>
            <button type="submit" disabled={uploading}>
              {uploading ? "Uploading…" : "Upload"}
            </button>
          </div>
        </form>
        {uploadMessage && <p className={styles.success}>{uploadMessage}</p>}
      </section>

      {loading ? (
        <p className={styles.muted}>Loading pending raw files…</p>
      ) : error ? (
        <p className={styles.error}>{error}</p>
      ) : items.length === 0 ? (
        <p className={styles.muted}>No pending raw files.</p>
      ) : (
        <>
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
                <span className={styles.meta}>{formatMeta(item.meta)}</span>
              </li>
            ))}
          </ul>
        </>
      )}
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
