import { NavLink, Route, Routes } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import ExportWizard from "./pages/ExportWizard";
import IngestWizard from "./pages/IngestWizard";
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
          <Route path="/log" element={<LogViewer />} />
        </Routes>
      </main>
    </div>
  );
}
