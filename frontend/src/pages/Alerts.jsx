import { useEffect, useState } from "react";
import { api, evidenceUrl } from "../api";

export default function Alerts() {
  const [alerts, setAlerts] = useState([]);
  const [filter, setFilter] = useState("open");
  const [img, setImg] = useState(null);

  const load = () => api(`/alerts${filter ? `?status=${filter}` : ""}`).then(setAlerts);
  useEffect(() => { load(); const t = setInterval(load, 5000); return () => clearInterval(t); }, [filter]);

  async function review(id, status) {
    await api(`/alerts/${id}`, { method: "PATCH", body: { status } });
    load();
  }

  return (
    <>
      <h2>Alerts</h2>
      <div className="row">
        {["open", "confirmed", "dismissed", ""].map((f) => (
          <button key={f} className={f === filter ? "chip active" : "chip"} onClick={() => setFilter(f)}>{f || "all"}</button>
        ))}
      </div>
      <div className="card">
        <table>
          <thead><tr><th>Time</th><th>Seat</th><th>Risk</th><th>Band</th><th>Reasons</th><th></th></tr></thead>
          <tbody>
            {alerts.map((a) => (
              <tr key={a.id}>
                <td>{new Date(a.created_at).toLocaleTimeString()}</td>
                <td>{a.seat || "–"}</td>
                <td>{a.risk_score.toFixed(2)}</td>
                <td><span className={`tag ${a.band}`}>{a.band}</span></td>
                <td>{a.reasons}</td>
                <td className="actions">
                  {a.evidence_path && <button onClick={async () => setImg(await evidenceUrl(a.id))}>Evidence</button>}
                  {a.status === "open" && <>
                    <button onClick={() => review(a.id, "confirmed")}>Confirm</button>
                    <button onClick={() => review(a.id, "dismissed")}>Dismiss</button>
                  </>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {alerts.length === 0 && <p className="muted">No alerts.</p>}
      </div>
      {img && <div className="modal" onClick={() => setImg(null)}><img src={img} alt="evidence" /></div>}
    </>
  );
}
