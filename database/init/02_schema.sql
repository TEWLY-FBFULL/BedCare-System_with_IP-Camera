CREATE TABLE provinces (
  province_id   SERIAL PRIMARY KEY,
  province_name TEXT NOT NULL
);


CREATE TABLE districts (
  district_id   SERIAL PRIMARY KEY,
  district_name TEXT NOT NULL,
  province_id   INT NOT NULL REFERENCES provinces(province_id)
);


CREATE TABLE subdistricts (
  subdistrict_id SERIAL PRIMARY KEY,
  subdistrict_name TEXT NOT NULL,
  zip_code TEXT,
  district_id INT NOT NULL REFERENCES districts(district_id)
);


CREATE TABLE addresses (
  address_id     SERIAL PRIMARY KEY,
  house_no       TEXT,
  road           TEXT,
  village        TEXT,
  subdistrict_id INT NOT NULL REFERENCES subdistricts(subdistrict_id)
);


CREATE TABLE roles (
  role_id   SERIAL PRIMARY KEY,
  role_name TEXT UNIQUE NOT NULL
);
INSERT INTO roles (role_name) VALUES
('admin'),
('doctor'),
('nurse'),
('relative');


CREATE TABLE users (
  user_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  role_id        INT NOT NULL REFERENCES roles(role_id),
  address_id     INT REFERENCES addresses(address_id),
  first_name     TEXT NOT NULL,
  last_name      TEXT NOT NULL,
  email          TEXT UNIQUE NOT NULL,
  phone          TEXT,
  password_hash  TEXT NOT NULL,
    email_verified BOOLEAN DEFAULT FALSE,
  is_active      BOOLEAN DEFAULT FALSE,
  created_at     TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_users_role_id ON users(role_id);


CREATE TABLE patients (
  patient_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  first_name      TEXT NOT NULL,
  last_name       TEXT NOT NULL,
  gender          TEXT,
  birth_date      DATE,
  weight          NUMERIC(5,2),
  height          NUMERIC(5,2),
  chronic_disease TEXT,
  address_id      INT REFERENCES addresses(address_id),
  created_at      TIMESTAMPTZ DEFAULT now()
);


CREATE TYPE relation_type_enum AS ENUM ('caregiver', 'relative', 'doctor');
CREATE TABLE user_patient (
  uspa_id       SERIAL PRIMARY KEY,
  user_id       UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  patient_id       UUID NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
  relation_type relation_type_enum NOT NULL,
  UNIQUE (user_id, patient_id)
);


CREATE TABLE facilities (
  facility_id   SERIAL PRIMARY KEY,
  facility_name TEXT NOT NULL,
  facility_type TEXT,
  address_id    INT NOT NULL REFERENCES addresses(address_id)
);


CREATE TABLE rooms (
  room_id      SERIAL PRIMARY KEY,
  room_number  TEXT NOT NULL,
  facility_id  INT NOT NULL REFERENCES facilities(facility_id),
  patient_id   UUID UNIQUE REFERENCES patients(patient_id)
);


CREATE TABLE room_assignments (
  assignment_id SERIAL PRIMARY KEY,
  patient_id    UUID NOT NULL REFERENCES patients(patient_id),
  room_id       INT  NOT NULL REFERENCES rooms(room_id),
  assigned_at   TIMESTAMPTZ NOT NULL,
  discharged_at TIMESTAMPTZ,
  assigned_by   UUID REFERENCES users(user_id),
  note          TEXT,
  CHECK (discharged_at IS NULL OR discharged_at > assigned_at)
);
CREATE UNIQUE INDEX uniq_active_room
ON room_assignments(room_id)
WHERE discharged_at IS NULL;

CREATE UNIQUE INDEX uniq_active_patient
ON room_assignments(patient_id)
WHERE discharged_at IS NULL;


CREATE TYPE auth_type_enum AS ENUM ('Digest/Basic', 'Basic');
CREATE TABLE camera_brands (
  brand_id     SERIAL PRIMARY KEY,
  brand_name   TEXT NOT NULL,
  rtsp_pattern TEXT,
  auth_type    auth_type_enum
);
INSERT INTO camera_brands(brand_name, rtsp_pattern, auth_type) VALUES
('Hikvision', 'rtsp://admin:{password}@{ip}:554/Streaming/Channels/{channel}01', 'Digest/Basic'),
('Dahua', 'rtsp://admin:{password}@{ip}:554/cam/realmonitor?channel={channel}&subtype=0', 'Digest/Basic'),
('EZVIZ', 'rtsp://admin:{verification_code}@{ip}:554/h264/ch1/main/av_stream', 'Basic'),
('TP-Link Tapo', 'rtsp://{username}:{password}@{ip}:554/stream1', 'Basic'),
('Vivotek', 'rtsp://{username}:{password}@{ip}:554/live.sdp', 'Digest/Basic'),
('Xiaomi (Mi Home)', 'rtsp://admin:{password}@{ip}:554/live', 'Basic'),
('Imou', 'rtsp://admin:{password}@{ip}:554/cam/realmonitor?channel=1&subtype=0', 'Digest/Basic'),
('Uniview (UNV)', 'rtsp://{username}:{password}@{ip}:554/unicast/c{channel}/s0/live', 'Digest/Basic'),
('HiLook', 'rtsp://admin:{password}@{ip}:554/Streaming/Channels/101', 'Digest/Basic'),
('Bosch', 'rtsp://{username}:{password}@{ip}:554/?inst=1', 'Digest/Basic');


CREATE TABLE cameras (
  camera_id  SERIAL PRIMARY KEY,
  brand_id   INT NOT NULL REFERENCES camera_brands(brand_id),
  room_id    INT UNIQUE NOT NULL REFERENCES rooms(room_id),
  ip_address INET NOT NULL,
  username   TEXT,
  password   TEXT,
  rtsp_url   TEXT
);


CREATE TABLE devices (
  device_id   SERIAL PRIMARY KEY,
  room_id     INT NOT NULL REFERENCES rooms(room_id),
  device_name TEXT,
  mqtt_topic  TEXT
);


CREATE TABLE sensors (
  sensor_id   SERIAL PRIMARY KEY,
  device_id   INT NOT NULL REFERENCES devices(device_id),
  sensor_type TEXT NOT NULL
);


CREATE TABLE sleep_sessions (
  session_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  patient_id        UUID NOT NULL REFERENCES patients(patient_id),
  room_id           INT NOT NULL REFERENCES rooms(room_id),
  start_time        TIMESTAMPTZ NOT NULL,
  end_time          TIMESTAMPTZ,
  avg_sleep_score   NUMERIC(5,2),
  dominant_posture  TEXT,
  created_by        UUID REFERENCES users(user_id)
);
CREATE INDEX idx_sleep_sessions_patient_time
ON sleep_sessions(patient_id, start_time DESC);


CREATE TABLE sleep_posture_logs (
  posture_log_id SERIAL,
  session_id UUID NOT NULL REFERENCES sleep_sessions(session_id),
  patient_id UUID NOT NULL REFERENCES patients(patient_id),
  posture_label TEXT,
  confidence NUMERIC(4,3),
  source TEXT,
  captured_at TIMESTAMPTZ NOT NULL,
  PRIMARY KEY (posture_log_id, captured_at)
);
SELECT create_hypertable('sleep_posture_logs', 'captured_at');
CREATE INDEX idx_posture_session_time
ON sleep_posture_logs(session_id, captured_at DESC);


CREATE TABLE sleep_metric_logs (
  metric_log_id SERIAL,
  session_id UUID NOT NULL REFERENCES sleep_sessions(session_id),
  patient_id UUID NOT NULL REFERENCES patients(patient_id),
  posture_type TEXT,
  neck_tilt NUMERIC,
  trunk_flex NUMERIC,
  axial_rotation NUMERIC,
  body_tilt NUMERIC,
  posture_score NUMERIC,
  posture_quality TEXT,
  captured_at TIMESTAMPTZ NOT NULL,
  PRIMARY KEY (metric_log_id, captured_at)
);
SELECT create_hypertable('sleep_metric_logs', 'captured_at');
CREATE INDEX idx_metric_session_time
ON sleep_metric_logs(session_id, captured_at DESC);


CREATE TABLE sleep_keypoint_logs (
  keypoint_log_id SERIAL,
  session_id UUID NOT NULL REFERENCES sleep_sessions(session_id),
  patient_id UUID NOT NULL REFERENCES patients(patient_id),
  keypoint_name TEXT,
  x NUMERIC,
  y NUMERIC,
  z NUMERIC,
  visibility NUMERIC,
  captured_at TIMESTAMPTZ NOT NULL,
  PRIMARY KEY (keypoint_log_id, captured_at)
);
SELECT create_hypertable('sleep_keypoint_logs', 'captured_at');
CREATE INDEX idx_keypoint_session_time
ON sleep_keypoint_logs(session_id, captured_at DESC);


CREATE TYPE motion_state_enum AS ENUM (
  'no_person',
  'person_static',
  'person_moving'
);
CREATE TABLE environment_logs (
  env_log_id SERIAL,
  room_id INT NOT NULL REFERENCES rooms(room_id),
  device_id INT NOT NULL REFERENCES devices(device_id),
  temperature_c NUMERIC,
  humidity_pct NUMERIC,
  pressure_hpa NUMERIC,
  altitude_m NUMERIC,
  air_quality_index NUMERIC,
  lux NUMERIC,
  pm25_ugm3 NUMERIC,
  co2_ppm NUMERIC,
  motion_state motion_state_enum,
  captured_at TIMESTAMPTZ NOT NULL,
  PRIMARY KEY (env_log_id, captured_at)
);
SELECT create_hypertable('environment_logs', 'captured_at');

CREATE INDEX idx_env_room_time
ON environment_logs(room_id, captured_at DESC);

CREATE INDEX idx_env_device_time
ON environment_logs(device_id, captured_at DESC);

CREATE INDEX idx_env_room_device_time
ON environment_logs(room_id, device_id, captured_at DESC);


CREATE TYPE alert_type_enum AS ENUM ('posture', 'vital', 'environment');
CREATE TYPE severity_enum   AS ENUM ('warning', 'emergency');
CREATE TABLE alert_logs (
  alert_id SERIAL PRIMARY KEY,
  patient_id UUID NOT NULL REFERENCES patients(patient_id),
  room_id INT NOT NULL REFERENCES rooms(room_id),
  alert_type alert_type_enum NOT NULL,
  severity severity_enum NOT NULL,
  trigger_source TEXT,
  trigger_value TEXT,
  message TEXT,
  is_acknowledged BOOLEAN DEFAULT FALSE,
  acknowledged_at TIMESTAMPTZ,
  acknowledged_by UUID REFERENCES users(user_id),
  created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_alert_patient_time
ON alert_logs(patient_id, created_at DESC);

CREATE INDEX idx_alert_room_time
ON alert_logs(room_id, created_at DESC);


CREATE TABLE system_configs
(
  config_key TEXT PRIMARY KEY,
  config_value TEXT NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now()
);
INSERT INTO system_configs
  (config_key, config_value)
VALUES
  ('env_log_interval_sec', '300'),
  ('sleep_log_interval_sec', '300'),
  ('keypoint_log_interval_sec', '300'),
  ('alert_cooldown_sec', '300');


CREATE TABLE professional_levels (
  level_id SERIAL PRIMARY KEY,
  level_name TEXT NOT NULL
);
INSERT INTO professional_levels (level_name) VALUES
('ปฏิบัติการ'),
('ชำนาญการ'),
('ชำนาญการพิเศษ'),
('เชี่ยวชาญ');


CREATE TABLE doctor_specialties (
  specialty_id SERIAL PRIMARY KEY,
  specialty_name TEXT NOT NULL
);
INSERT INTO doctor_specialties (specialty_name) VALUES
('แพทย์ทั่วไป'),
('จิตแพทย์'),
('กุมารแพทย์'),
('ศัลยแพทย์'),
('สูตินรีแพทย์'),
('แพทย์อายุรกรรม'),
('จักษุแพทย์'),
('รังสีแพทย์');


CREATE TABLE doctors (
  doctor_id UUID PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
  specialty_id INT NOT NULL REFERENCES doctor_specialties(specialty_id),
  level_id INT REFERENCES professional_levels(level_id),
  license_no TEXT UNIQUE,
  is_active BOOLEAN DEFAULT TRUE
);


CREATE TABLE nurse_types (
  nurse_type_id SERIAL PRIMARY KEY,
  nurse_type_name TEXT NOT NULL
);
INSERT INTO nurse_types (nurse_type_name) VALUES
('พยาบาลวิชาชีพ'),
('ผู้ช่วยพยาบาล'),
('พยาบาลผู้เชี่ยวชาญ'),
('พยาบาลเฉพาะทาง');


CREATE TABLE nurses (
  nurse_id UUID PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
  nurse_type_id INT NOT NULL REFERENCES nurse_types(nurse_type_id),
  level_id INT REFERENCES professional_levels(level_id),
  license_no TEXT UNIQUE,
  is_active BOOLEAN DEFAULT TRUE
);


CREATE TYPE token_type_enum AS ENUM ('verify_email', 'reset_password');
CREATE TABLE user_tokens (
  token_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  token TEXT UNIQUE NOT NULL,
  token_type token_type_enum NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  used_at TIMESTAMPTZ
);
CREATE INDEX idx_user_tokens_user ON user_tokens(user_id);