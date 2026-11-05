import { useState } from "react";
import { getToken, setToken } from "./api";
import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Alerts from "./pages/Alerts.jsx";
import Students from "./pages/Students.jsx";

const TABS = { Dashboard, Alerts, Students };

export default function App() {
  const [authed, setAuthed] = useState(!!getToken());
  const [tab, setTab] = useState("Dashboard");
  if (!authed) return <Login onLogin={() => setAuthed(true)} />;
  const Page = TABS[tab];
  return (
    <div className="shell">
      <aside>
        <h1>ExamShield <span>AI</span></h1>
        {Object.keys(TABS).map((t) => (
          <button key={t} className={t === tab ? "nav active" : "nav"} onClick={() => setTab(t)}>{t}</button>
        ))}
        <button className="nav out" onClick={() => { setToken(null); setAuthed(false); }}>Sign out</button>
      </aside>
      <main><Page /></main>
    </div>
  );
}
