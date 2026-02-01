# 🚁 DRISHTI-NE: Disaster Response & Intelligence System

> _Survive. Connect. Recover._

![Drishti Banner](https://github.com/SudarshanTushar/DrishtiAppFullstack/blob/main/assets/icon/app-icon.png)

## 🚨 The Problem

During floods (like Sikkim 2023), standard communication fails within **4 hours**.

- **No Internet:** Victims cannot send SOS.
- **No Data:** Rescue teams work blindly.
- **No Coordination:** Government relies on outdated manual reports.

## ⚡ The Solution: Drishti-NE

A fully offline-capable ecosystem combining **AI-Powered Routing**, **Real-time Risk Assessment**, and **Government Command & Control**. The system provides intelligent disaster response with mesh networking as a fail-safe when infrastructure collapses.

## 🛡️ Operational Phases

The system operates in three controlled phases:

1. **Risk Assessment** – DistilBERT AI evaluates terrain, weather, and route safety using real geographic data.
2. **Authority Approval** – Command Center officials approve or reject AI recommendations.
3. **Fail-Safe Response** – Offline mesh communication and peer discovery activate when infrastructure fails.

## 🎮 HOW TO DEMO

### Admin Command Center (Desktop View)

1.  **Open Admin Panel** at `/admin`
2.  **Biometric Login** - Click fingerprint to authenticate
3.  **Monitor Live Incidents** - View real-time SOS incidents on the tactical dashboard
4.  **Command & Control** - Approve evacuations, dispatch teams, review SITREP reports

### Citizen App (Mobile/Desktop View)

1.  **Dashboard** - View risk status, nearby incidents, and mesh network connectivity
2.  **Voice Commands** - Tap mic to ask "Show me evacuation routes" (with AI fallback)
3.  **Map Navigation** - Get AI-powered safe routes avoiding hazards
4.  **Offline Mode** - P2P peer discovery continues working without internet

---

## 🛠️ Tech Stack

- **Frontend:** React + Vite, Tailwind CSS, Capacitor (Android/iOS), Mapbox GL
- **Backend:** Python FastAPI, DigitalOcean Deployment
- **AI/ML:**
  - DistilBERT (Sentiment/Risk Analysis)
  - OSMnx + NetworkX (Real Road Network Routing)
  - Scikit-Learn (Predictive Models)
- **Database:** PostgreSQL + SQLAlchemy + Alembic migrations
- **Offline:** Browser Speech Synthesis (Voice), Simulated Bluetooth Mesh (Desktop), Capacitor BLE (Mobile)

## 🌟 Key Features

1.  **🧠 AI-Powered Routing:** DistilBERT + OSMnx calculates real risk scores for routes based on terrain, weather, and disaster intel.
2.  **📍 Real Geographic Data:** Actual POIs (hospitals, shelters) in Assam/Meghalaya with live coordinate mapping.
3.  **🗣️ Voice AI:** Browser-based speech synthesis with cloud AI fallback for natural language commands.
4.  **📡 Mesh Networking:** P2P peer discovery simulation (desktop) with Capacitor BLE support (mobile).
5.  **⚖️ Command & Control:** Government dashboard with incident management, SITREP reports, and authority approval workflows.
6.  **🎯 Simulation Mode:** Built-in demo capabilities for testing disaster scenarios without real emergencies.

## 🚀 How to Run Locally

### 1. Backend (Python FastAPI)

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Backend runs at:** `http://localhost:8000`  
**API Docs:** `http://localhost:8000/docs`

### 2. Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

**Frontend runs at:** `http://localhost:5173`

### 3. Database Setup (Optional - for full features)

```bash
cd backend
alembic upgrade head
```
