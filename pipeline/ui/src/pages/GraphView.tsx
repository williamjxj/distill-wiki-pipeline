import { useEffect, useMemo, useState } from "react";
import { getGraph, type GraphData, type GraphEdge, type GraphNode } from "../api";
import styles from "./GraphView.module.css";

const NODE_RADIUS = 18;
const GRID_COLS = 6;
const CELL = 80;
const PADDING = 40;

function layoutNodes(nodes: GraphNode[]): Map<string, { x: number; y: number }> {
  const positions = new Map<string, { x: number; y: number }>();
  nodes.forEach((node, index) => {
    const col = index % GRID_COLS;
    const row = Math.floor(index / GRID_COLS);
    positions.set(node.id, {
      x: PADDING + col * CELL,
      y: PADDING + row * CELL,
    });
  });
  return positions;
}

export default function GraphView() {
  const [graph, setGraph] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await getGraph();
        if (!cancelled) {
          setGraph(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load graph");
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

  const positions = useMemo(
    () => layoutNodes(graph?.nodes ?? []),
    [graph?.nodes],
  );

  const svgSize = useMemo(() => {
    const nodeCount = graph?.nodes.length ?? 0;
    const rows = Math.max(1, Math.ceil(nodeCount / GRID_COLS));
    return {
      width: PADDING * 2 + GRID_COLS * CELL,
      height: PADDING * 2 + rows * CELL,
    };
  }, [graph?.nodes.length]);

  if (loading) {
    return <p className={styles.muted}>Loading wikilink graph…</p>;
  }

  if (error) {
    return <p className={styles.error}>{error}</p>;
  }

  if (!graph) {
    return <p className={styles.muted}>No graph data.</p>;
  }

  return (
    <div className={styles.page}>
      <h1>Wikilink Graph</h1>
      <p className={styles.meta}>
        {graph.nodes.length} node(s) · {graph.edges.length} edge(s)
      </p>

      <div className={styles.layout}>
        <section className={styles.panel}>
          <h2>Graph</h2>
          <div className={styles.svgWrap}>
            <svg
              width={svgSize.width}
              height={svgSize.height}
              role="img"
              aria-label="Wikilink graph"
            >
              {graph.edges.map((edge: GraphEdge) => {
                const source = positions.get(edge.source);
                const target = positions.get(edge.target);
                if (!source || !target) {
                  return null;
                }
                return (
                  <line
                    key={`${edge.source}-${edge.target}`}
                    x1={source.x}
                    y1={source.y}
                    x2={target.x}
                    y2={target.y}
                    stroke="#ccc"
                    strokeWidth={1}
                  />
                );
              })}
              {graph.nodes.map((node: GraphNode) => {
                const point = positions.get(node.id);
                if (!point) {
                  return null;
                }
                return (
                  <g key={node.id}>
                    <circle
                      cx={point.x}
                      cy={point.y}
                      r={NODE_RADIUS}
                      fill="#eef4ff"
                      stroke="#175cd3"
                      strokeWidth={1.5}
                    />
                    <text
                      x={point.x}
                      y={point.y + NODE_RADIUS + 12}
                      textAnchor="middle"
                      fontSize="10"
                      fill="#333"
                    >
                      {node.label.length > 14
                        ? `${node.label.slice(0, 12)}…`
                        : node.label}
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>
        </section>

        <section className={styles.panel}>
          <h2>Edges</h2>
          {graph.edges.length === 0 ? (
            <p className={styles.muted}>No wikilinks found.</p>
          ) : (
            <ul className={styles.edgeList}>
              {graph.edges.map((edge) => (
                <li key={`${edge.source}-${edge.target}`} className={styles.edgeItem}>
                  [[{edge.source}]] → [[{edge.target}]]
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  );
}
