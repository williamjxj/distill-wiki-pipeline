import { NavLink, Route, Routes } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
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
          <Route path="/log" element={<LogViewer />} />
        </Routes>
      </main>
    </div>
  );
}
