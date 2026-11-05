import { useEffect, useState } from "react";
import { api } from "../api";

export default function Students() {
  const [list, setList] = useState([]);
  const [form, setForm] = useState({ reg_no: "", name: "", consent_given: false });
  const [err, setErr] = useState("");

  const load = () => api("/students").then(setList);
  useEffect(() => { load(); }, []);

  async function enrol(e) {
    e.preventDefault();
    setErr("");
    try {
      await api("/students", { method: "POST", body: form });
      setForm({ reg_no: "", name: "", consent_given: false });
      load();
    } catch (ex) { setErr(ex.message); }
  }

  async function upload(id, files) {
    const fd = new FormData();
    [...files].forEach((f) => fd.append("files", f));
    try { await api(`/students/${id}/face`, { method: "POST", form: fd }); load(); }
    catch (ex) { setErr(ex.message); }
  }

  async function withdraw(id) {
    if (confirm("Erase this student and their face data?")) { await api(`/students/${id}`, { method: "DELETE" }); load(); }
  }

  return (
    <>
      <h2>Student registration</h2>
      <form className="card row" onSubmit={enrol}>
        <input placeholder="Reg. no" value={form.reg_no} onChange={(e) => setForm({ ...form, reg_no: e.target.value })} required />
        <input placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
        <label><input type="checkbox" checked={form.consent_given}
          onChange={(e) => setForm({ ...form, consent_given: e.target.checked })} /> Written consent recorded</label>
        <button className="primary" disabled={!form.consent_given}>Enrol</button>
      </form>
      {err && <p className="err">{err}</p>}
      <div className="card">
        <table>
          <thead><tr><th>Reg. no</th><th>Name</th><th>Face</th><th></th></tr></thead>
          <tbody>{list.map((s) => (
            <tr key={s.id}>
              <td>{s.reg_no}</td><td>{s.name}</td>
              <td>{s.has_embedding ? "Enrolled" : <input type="file" accept="image/*" multiple onChange={(e) => upload(s.id, e.target.files)} />}</td>
              <td><button onClick={() => withdraw(s.id)}>Withdraw consent</button></td>
            </tr>
          ))}</tbody>
        </table>
      </div>
    </>
  );
}
