# ExamShield AI

AI-assisted invigilation for offline pen-and-paper exams. Existing classroom CCTV feeds a
detection / tracking / recognition / behaviour pipeline; risky moments become alerts with
video evidence that a human invigilator confirms or dismisses.

```
backend/   FastAPI + SQLAlchemy + PostgreSQL, JWT auth, scoring engine, CV pipeline modules
frontend/  React (Vite) + Chart.js admin console
docker-compose.yml   db + backend + frontend
```

## Run

```bash
cp .env.example .env          # set JWT_SECRET, ADMIN_PASSWORD
docker compose up --build
# console: http://localhost:8080   API docs: http://localhost:8000/docs
```

Local dev: `cd backend && pip install -r requirements.txt && pytest`, and
`cd frontend && npm install && npm run dev`.

## Pipeline

Registration -> face DB -> CCTV -> YOLOv8 -> ByteTrack -> RetinaFace/InsightFace -> head pose
(MediaPipe + solvePnP) -> gaze -> gadget detection -> behaviour features -> risk score ->
alert + evidence -> dashboard.

Implemented and tested: scoring engine, hysteresis, gadget persistence gate, API, auth,
consent-gated enrolment, review workflow, dashboard. Scaffolded, needs wiring and
calibration on real hall footage: gaze, hands, Silero VAD / Whisper (optional audio).

Run the inference loop on a GPU host after installing the heavy packages listed in
`backend/requirements.txt`:

```bash
python -m app.pipeline.runner rtsp://camera/stream --session 1 --token <JWT>
```

## Honest status

No pilot has run. Risk weights in `pipeline/scoring.py` are a starting point; refit them on
labelled shadow-session data. The product metric is **false alerts per invigilator-hour
(< 0.5)**, not accuracy. Split datasets by recording session, never by frame.

## Before commercial use

- **Ultralytics YOLOv8 is AGPL-3.0** - enterprise licence needed if you host it as a service.
- **InsightFace pretrained packs are research-only.**
- **DPDP Act 2023 / Rules 2025**: consent is a hard gate on enrolment, withdrawal erases
  face data, actions are written to `audit_log`. Add encryption at rest before production.
- Change `JWT_SECRET` and the seeded admin password.
