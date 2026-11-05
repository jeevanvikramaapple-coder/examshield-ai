import { useEffect, useState } from "react";
import { ArcElement, BarElement, CategoryScale, Chart as ChartJS, Legend, LinearScale, Tooltip } from "chart.js";
import { Bar, Doughnut } from "react-chartjs-2";
import { api } from "../api";

ChartJS.register(ArcElement, BarElement, CategoryScale, LinearScale, Legend, Tooltip);
const BLUE = "#1d4ed8";

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [form, setForm] = useState({ hall: "", course: "" });

  const load = () => {
    api("/stats").then(setStats);
    api("/sessions").then(setSessions);
  };
  useEffect(() => { load(); const t = setInterval(load, 10000); return () => clearInterval(t); }, []);

  async function start(e) {
    e.preventDefault();
    await api("/sessions", { method: "POST", body: form });
    setForm({ hall: "", course: "" });
    load();
  }

  const band = stats?.by_band || {};
  const status = stats?.by_status || {};
  return (
    <>
      <h2>Overview</h2>
      <div className="grid">
        <div className="card kpi"><b>{(band.review || 0) + (band.high || 0)}</b><span>Total alerts</span></div>
        <div className="card kpi"><b>{band.high || 0}</b><span>High risk</span></div>
        <div className="card kpi"><b>{status.open || 0}</b><span>Awaiting review</span></div>
        <div className="card kpi"><b>{stats?.precision_of_reviewed ?? "–"}</b><span>Precision of reviewed</span></div>
      </div>
      <div className="grid two">
        <div className="card">
          <h3>Alerts by band</h3>
          <Bar data={{ labels: ["review", "high"], datasets: [{ data: [band.review || 0, band.high || 0], backgroundColor: BLUE }] }}
               options={{ plugins: { legend: { display: false } } }} />
        </div>
        <div className="card">
          <h3>Review outcome</h3>
          <Doughnut data={{ labels: ["open", "confirmed", "dismissed"],
            datasets: [{ data: [status.open || 0, status.confirmed || 0, status.dismissed || 0],
                         backgroundColor: [BLUE, "#111827", "#9ca3af"] }] }} />
        </div>
      </div>
      <div className="card">
        <h3>Exam sessions</h3>
        <form className="row" onSubmit={start}>
          <input placeholder="Hall" value={form.hall} onChange={(e) => setForm({ ...form, hall: e.target.value })} required />
          <input placeholder="Course" value={form.course} onChange={(e) => setForm({ ...form, course: e.target.value })} required />
          <button className="primary">Start session</button>
        </form>
        <table><thead><tr><th>ID</th><th>Hall</th><th>Course</th><th>Started</th></tr></thead>
          <tbody>{sessions.map((s) => (
            <tr key={s.id}><td>{s.id}</td><td>{s.hall}</td><td>{s.course}</td><td>{new Date(s.started_at).toLocaleString()}</td></tr>
          ))}</tbody></table>
      </div>
    </>
  );
}
