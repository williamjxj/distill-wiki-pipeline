import { NavLink, Route, Routes } from "react-router-dom";
import AutoPipeline from "./pages/AutoPipeline";
import Dashboard from "./pages/Dashboard";
import ExportWizard from "./pages/ExportWizard";
import GraphView from "./pages/GraphView";
import SyncView from "./pages/SyncView";
import IngestWizard from "./pages/IngestWizard";
import LintDashboard from "./pages/LintDashboard";
import LogViewer from "./pages/LogViewer";
import RawQueue from "./pages/RawQueue";
import styles from "./App.module.css";

export default function App() {
  return (
    <div className={styles.app}>
      <nav className={styles.nav}>
        <span className={styles.brand}>Wiki Pipeline</span>
        <NavLink
          to="/"
          end
          className={({ isActive }) =>
            isActive ? `${styles.link} ${styles.active}` : styles.link
          }
        >
          Dashboard
        </NavLink>

        <span className={styles.divider} />

        <span className={styles.groupLabel}>Auto</span>
        <NavLink
          to="/auto"
          className={({ isActive }) =>
            isActive
              ? `${styles.autoLink} ${styles.autoActive}`
              : styles.autoLink
          }
        >
          Auto Pipeline
        </NavLink>

        <span className={styles.divider} />

        <span className={styles.groupLabel}>Manual</span>
        <NavLink
          to="/raw"
          className={({ isActive }) =>
            isActive ? `${styles.link} ${styles.active}` : styles.link
          }
        >
          Raw Queue
        </NavLink>
        <NavLink
          to="/ingest"
          className={({ isActive }) =>
            isActive ? `${styles.link} ${styles.active}` : styles.link
          }
        >
          Ingest
        </NavLink>
        <NavLink
          to="/export"
          className={({ isActive }) =>
            isActive ? `${styles.link} ${styles.active}` : styles.link
          }
        >
          Export
        </NavLink>
        <NavLink
          to="/lint"
          className={({ isActive }) =>
            isActive ? `${styles.link} ${styles.active}` : styles.link
          }
        >
          Lint
        </NavLink>
        <NavLink
          to="/graph"
          className={({ isActive }) =>
            isActive ? `${styles.link} ${styles.active}` : styles.link
          }
        >
          Graph
        </NavLink>
        {/* Sync accessible from Dashboard; menu item removed to avoid duplication */}
        <NavLink
          to="/log"
          className={({ isActive }) =>
            isActive ? `${styles.link} ${styles.active}` : styles.link
          }
        >
          Log
        </NavLink>
      </nav>

      <main className={styles.main}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/raw" element={<RawQueue />} />
          <Route path="/ingest" element={<IngestWizard />} />
          <Route path="/export" element={<ExportWizard />} />
          <Route path="/auto" element={<AutoPipeline />} />
          <Route path="/lint" element={<LintDashboard />} />
          <Route path="/graph" element={<GraphView />} />
          <Route path="/sync" element={<SyncView />} />
          <Route path="/log" element={<LogViewer />} />
        </Routes>
      </main>
    </div>
  );
}
