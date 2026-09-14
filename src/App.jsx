import React, { useEffect, useState } from "react";
import MapView from "./components/MapView";
import CandidatePanel from "./components/CandidatePanel";
import StatusBanner from "./components/StatusBanner";
import UncertaintyPanel from "./components/UncertaintyPanel";

function App() {
  const [runResult, setRunResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch("/demo_run_result.json")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Could not load demo_run_result.json");
        }

        return response.json();
      })
      .then((data) => {
        setRunResult(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div style={styles.loading}>
        Loading Oil Spill Dashboard...
      </div>
    );
  }

  if (error) {
    return (
      <div style={styles.error}>
        <h2>Dashboard Error</h2>
        <p>{error}</p>
        <p>
          Make sure demo_run_result.json exists inside the public folder.
        </p>
      </div>
    );
  }

  return (
    <div style={styles.app}>
      <header style={styles.header}>
        <div>
          <h1 style={styles.title}>OceanGuard</h1>
          <p style={styles.subtitle}>
            Satellite-Based Oil Spill Detection & Source Attribution
          </p>
        </div>

        <div style={styles.demoBadge}>
          DEMO MODE
        </div>
      </header>

      <StatusBanner runResult={runResult} />

      <div style={styles.dashboard}>
        <div style={styles.mapSection}>
          <MapView runResult={runResult} />
        </div>

        <div style={styles.sidePanel}>
          <UncertaintyPanel runResult={runResult} />

          <CandidatePanel runResult={runResult} />
        </div>
      </div>
    </div>
  );
}

const styles = {
  app: {
    width: "100vw",
    height: "100vh",
    backgroundColor: "#0b1120",
    color: "white",
    overflow: "hidden",
    fontFamily: "Arial, sans-serif",
  },

  header: {
    height: "75px",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "0 25px",
    backgroundColor: "#111827",
    borderBottom: "1px solid #263244",
  },

  title: {
    margin: 0,
    fontSize: "26px",
  },

  subtitle: {
    margin: "5px 0 0",
    color: "#9ca3af",
    fontSize: "13px",
  },

  demoBadge: {
    padding: "8px 14px",
    borderRadius: "6px",
    backgroundColor: "#374151",
    color: "#facc15",
    fontSize: "12px",
    fontWeight: "bold",
  },

  dashboard: {
    display: "flex",
    height: "calc(100vh - 125px)",
  },

  mapSection: {
    width: "70%",
    height: "100%",
  },

  sidePanel: {
    width: "30%",
    height: "100%",
    overflowY: "auto",
    backgroundColor: "#111827",
    padding: "15px",
    boxSizing: "border-box",
  },

  loading: {
    width: "100vw",
    height: "100vh",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#0b1120",
    color: "white",
    fontSize: "22px",
  },

  error: {
    width: "100vw",
    height: "100vh",
    padding: "50px",
    boxSizing: "border-box",
    backgroundColor: "#0b1120",
    color: "white",
  },
};

export default App;