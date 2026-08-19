# Smart Attendance SaaS

![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)
![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

A scalable, secure, and smart attendance tracking system leveraging ESP32 BLE beacons, an Edge AI-powered Flutter mobile app, and a robust FastAPI backend connected to PostgreSQL.

## Architecture Overview

The system consists of a 4-layer architecture:
1. **Hardware Layer (ESP32 BLE Beacons)**: Low-cost physical ESP32 devices placed in classrooms emitting localized BLE signals (iBeacons) identifying the room.
2. **Mobile App (Flutter + Edge AI)**: A cross-platform app used by students. It verifies physical presence by detecting classroom BLE signals and performs on-device Edge AI face spoofing detection/recognition.
3. **Backend API (FastAPI)**: A high-performance Python backend validating attendance claims using HMAC cryptography.
4. **Database (PostgreSQL)**: Scalable relational database storing user identities, schedules, and attendance logs.

### System Architecture Diagram
```text
[ ESP32 BLE Beacon ] ---> (Broadcasts UUID/Room ID)
         |
         v
[ Flutter Mobile App ] <--- 1. Detect BLE Beacon
  (Edge AI/MLKit)      <--- 2. Face Recognition & Liveness Detection
         |
         | (Encrypted HMAC Payload)
         v
[ FastAPI Backend ] <--- 3. Validate Crypto Hash & Time window
         |
         v
[ PostgreSQL DB ]   <--- 4. Record Attendance
```

## Prerequisites
- Docker and Docker Compose (for backend)
- ESP32 Development Board and Arduino IDE (for hardware beacons)
- Flutter SDK (for mobile app compilation)
- Python 3.11+ (for local development without Docker)

## Quick Start

1. Clone and enter the directory:
   ```bash
   git clone https://github.com/your-org/smart-attendance-saas.git
   cd attendce
   ```
2. Copy the example environment file and edit secrets:
   ```bash
   cp .env.example .env
   # Edit .env with your secrets
   ```
3. Run with Docker Compose:
   ```bash
   docker-compose up --build
   ```
4. The API will be available at: http://localhost:8000
5. View Swagger API documentation at: http://localhost:8000/docs

## API Endpoints

### 🔐 Authentication (`/auth`)
| Method | Path | Description | Auth Required |
| --- | --- | --- | --- |
| `POST` | `/auth/login` | Login with Device ID Lock (1st login binds device; rejects mismatch with 403) | No |
| `POST` | `/auth/reset_device/{roll_no}` | Unbind / reset device lock for a student | Yes (Admin) |
| `POST` | `/auth/forgot_password` | Generate 6-digit OTP stored in temp cache | No |

### ⚡ Attendance Verification Engine (`/attendance`)
| Method | Path | Description | Auth Required |
| --- | --- | --- | --- |
| `GET` | `/attendance/today_schedule/{roll_no}` | Fetch today's schedule and active classroom ESP32 BLE UUID | Yes (Student/Admin) |
| `POST` | `/attendance/verify` | Core 4-Lock Verification Engine (HMAC + BLE + Time + Face) | No (HMAC Protected) |
| `POST` | `/attendance/trigger_reports` | Generate Excel attendance sheets using Pandas & email teachers | Yes (Admin) |

### 🛠️ Admin Management (`/admin`)
| Method | Path | Description | Auth Required |
| --- | --- | --- | --- |
| `GET` | `/admin/dashboard_stats` | Summary metrics: total students, classrooms, attendance %, alerts | Yes (Admin) |
| `GET` | `/admin/classrooms` | List all classrooms with mapped ESP32 UUIDs | Yes (Admin) |
| `POST` | `/admin/classrooms` | Create new classroom with unique BLE UUID | Yes (Admin) |
| `DELETE` | `/admin/classrooms/{room_id}` | Delete a classroom | Yes (Admin) |
| `GET` | `/admin/timetable` | List scheduled classes | Yes (Admin) |
| `POST` | `/admin/timetable` | Schedule a class in a specific room & time | Yes (Admin) |
| `GET` | `/admin/students` | List enrolled students and device binding status | Yes (Admin) |
| `POST` | `/admin/bulk_upload_students` | Bulk upload/create students with hashed passwords | Yes (Admin) |
| `POST` | `/admin/register_face/{roll_no}` | Register 128-point face encoding for a student | Yes (Admin) |
| `GET` | `/admin/attendance_logs` | Real-time live attendance feed stream | Yes (Admin) |

*(Full interactive Swagger documentation at `http://localhost:8000/docs`)*

## ESP32 Setup

Each classroom requires an ESP32 board acting as a BLE beacon.
1. Open `hardware/esp32_scalable_beacon.ino` in the Arduino IDE.
2. Install the **ESP32 BLE Arduino** library via Library Manager.
3. Generate a unique UUID for the classroom at [uuidgenerator.net](https://www.uuidgenerator.net/).
4. Update `BEACON_UUID` and `BEACON_NAME` in the code:
   ```cpp
   #define BEACON_UUID "e2c56db5-dffb-48d2-b060-d0f5a71096e0"
   #define BEACON_NAME "ROOM_301"
   ```
5. Select your ESP32 board and compile/flash.
6. Power the ESP32 via 5V USB adapter in the designated classroom.

## Flutter App Setup

1. Navigate to the mobile app directory:
   ```bash
   cd flutter_app
   ```
2. Fetch dependencies:
   ```bash
   flutter pub get
   ```
3. Configure API base URL in `lib/services/api_service.dart` (default `http://10.0.2.2:8000` for Android emulator or your local machine IP).
4. Run the app on a physical device (Bluetooth Low Energy requires physical hardware):
   ```bash
   flutter run
   ```

## Security Architecture (The 4 Locks)

To eliminate buddy punching, proxy attendance, and replay attacks, every verification request undergoes 4 sequential security locks:
1. **Lock 1: HMAC Cryptography Check**: Validates the SHA256 cryptographic signature against replay attacks and JSON tampering. Mismatches trigger instant asynchronous intrusion alerts to the admin.
2. **Lock 2: Dynamic Classroom BLE Lock**: Fetches the expected `esp32_uuid` for the active class timetable from the database. Rejects with `"Wrong Classroom/Proxy"` if the student scanned a different room's beacon.
3. **Lock 3: Server-Enforced Time Window**: Checks server time against the timetable start time. Rejects if past the 10-minute grace cutoff.
4. **Lock 4: Edge AI Face Biometrics**: Calculates Euclidean distance between the live 128-point vector and stored database embedding. Rejects if distance > 0.6.

## Admin Dashboard

Open `frontend/admin_dashboard.html` in any modern web browser or host via static web server:
- Real-time KPI summary (Total Students, Classrooms, Attendance Rate, Security Alerts).
- Complete Classroom & BLE Beacon management with add/delete.
- Student Directory with one-click **"Unbind Device"** and **"Enroll Face"** actions.
- CSV / JSON Student Bulk Importer.
- Dynamic Class Scheduler / Timetable.
- Auto-refreshing Live Verification Stream with color-coded status badges and intrusion alert tags.

## Quick Database Seeding

To quickly populate the database with demo users, classrooms, timetables, and face encodings:
```bash
python seed_data.py
```
Default credentials:
- **Admin**: `admin` / `admin123`
- **Student**: `2026CS101` / `pass123`

## Project Structure
```text
attendce/
├── app/                              # FastAPI Backend (Python)
│   ├── __init__.py
│   ├── attendance.py                 # Core 4-Lock Engine & Reports
│   ├── auth.py                       # JWT Auth & Device Binding
│   ├── config.py                     # Environment Settings
│   ├── database.py                   # Async SQLAlchemy Engine
│   ├── email_service.py              # Async Email Alerts & Excel Dispatch
│   ├── models.py                     # SQLAlchemy 2.0 ORM Models
│   ├── schemas.py                    # Pydantic v2 Schemas
│   └── main.py                       # FastAPI Application Entry & Admin API
├── flutter_app/                      # Flutter Mobile App (Edge AI + BLE)
│   ├── pubspec.yaml
│   └── lib/
│       ├── main.dart
│       ├── screens/                  # Login, Home, Attendance Screens
│       └── services/                 # BLE, ML Kit Face, Crypto, API
├── frontend/
│   └── admin_dashboard.html          # Tailwind CSS Admin Console
├── hardware/
│   └── esp32_scalable_beacon.ino     # ESP32 BLE Beacon Firmware
├── reports/                          # Generated Excel Attendance Reports
├── .env.example                      # Template Environment Variables
├── Dockerfile                        # Multi-Stage Backend Dockerfile
├── docker-compose.yml                # PostgreSQL + FastAPI Orchestration
├── requirements.txt                  # Python Dependencies
├── seed_data.py                      # Database Seeder Script
└── README.md                         # Documentation
```

## License

This project is licensed under the MIT License.

