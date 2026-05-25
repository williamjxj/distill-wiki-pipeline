import styles from "./DiffView.module.css";

export interface DiffLine {
  type: "same" | "added" | "removed";
  text: string;
}

export function computeLineDiff(before: string, after: string): DiffLine[] {
  const beforeLines = before.split("\n");
  const afterLines = after.split("\n");
  const result: DiffLine[] = [];

  const maxLen = Math.max(beforeLines.length, afterLines.length);
  for (let index = 0; index < maxLen; index += 1) {
    const left = beforeLines[index];
    const right = afterLines[index];

    if (left === undefined) {
      result.push({ type: "added", text: right });
    } else if (right === undefined) {
      result.push({ type: "removed", text: left });
    } else if (left === right) {
      result.push({ type: "same", text: left });
    } else {
      result.push({ type: "removed", text: left });
      result.push({ type: "added", text: right });
    }
  }

  return result;
}

interface DiffViewProps {
  before: string;
  after: string;
  title?: string;
}

export default function DiffView({ before, after, title }: DiffViewProps) {
  const lines = computeLineDiff(before, after);
  const hasChanges = lines.some((line) => line.type !== "same");

  return (
    <div className={styles.wrapper}>
      {title && <h3 className={styles.title}>{title}</h3>}
      {!hasChanges ? (
        <p className={styles.muted}>No changes.</p>
      ) : (
        <pre className={styles.diff}>
          {lines.map((line, index) => (
            <div
              key={`${line.type}-${index}`}
              className={[
                styles.line,
                line.type === "added"
                  ? styles.added
                  : line.type === "removed"
                    ? styles.removed
                    : styles.same,
              ]
                .filter(Boolean)
                .join(" ")}
            >
              <span className={styles.prefix}>
                {line.type === "added" ? "+" : line.type === "removed" ? "-" : " "}
              </span>
              {line.text}
            </div>
          ))}
        </pre>
      )}
    </div>
  );
}
