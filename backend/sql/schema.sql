-- Reference schema (the API also creates tables via SQLAlchemy on startup).
CREATE TABLE users (
  id SERIAL PRIMARY KEY, email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL, role VARCHAR(32) NOT NULL DEFAULT 'invigilator',
  created_at TIMESTAMP DEFAULT now());

CREATE TABLE students (
  id SERIAL PRIMARY KEY, reg_no VARCHAR(32) UNIQUE NOT NULL, name VARCHAR(120) NOT NULL,
  consent_given BOOLEAN NOT NULL DEFAULT false, consent_at TIMESTAMP,
  embedding DOUBLE PRECISION[], created_at TIMESTAMP DEFAULT now());

CREATE TABLE exam_sessions (
  id SERIAL PRIMARY KEY, hall VARCHAR(64) NOT NULL, course VARCHAR(120) NOT NULL,
  started_at TIMESTAMP DEFAULT now(), ended_at TIMESTAMP);

CREATE TABLE alerts (
  id SERIAL PRIMARY KEY, session_id INT NOT NULL REFERENCES exam_sessions(id),
  student_id INT REFERENCES students(id) ON DELETE SET NULL, seat VARCHAR(16),
  risk_score DOUBLE PRECISION NOT NULL, band VARCHAR(16) NOT NULL, reasons TEXT DEFAULT '',
  evidence_path VARCHAR(255), status VARCHAR(16) NOT NULL DEFAULT 'open',
  reviewed_by INT REFERENCES users(id), created_at TIMESTAMP DEFAULT now());
CREATE INDEX ON alerts (session_id);

CREATE TABLE audit_log (
  id SERIAL PRIMARY KEY, user_id INT, action VARCHAR(64) NOT NULL,
  detail TEXT DEFAULT '', created_at TIMESTAMP DEFAULT now());
