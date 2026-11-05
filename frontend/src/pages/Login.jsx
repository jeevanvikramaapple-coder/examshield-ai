import { useState } from "react";
import { api, setToken } from "../api";

export default function Login({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");

  async function submit(e) {
    e.preventDefault();
    try {
      const r = await api("/auth/login", { method: "POST", body: { email, password } });
      setToken(r.access_token);
      onLogin();
    } catch (ex) {
      setErr(ex.message);
    }
  }

  return (
    <form className="login card" onSubmit={submit}>
      <h1>ExamShield <span>AI</span></h1>
      <input placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
      <input placeholder="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
      {err && <p className="err">{err}</p>}
      <button className="primary">Sign in</button>
    </form>
  );
}
