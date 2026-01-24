# 🚁 DRISHTI: Disaster Response & Intelligence System

> _Survive. Connect. Recover._

![Drishti Banner](https://github.com/SudarshanTushar/DrishtiAppFullstack/blob/main/assets/icon/app-icon.png)

## 🚨 The Problem

During floods (like Sikkim 2023), standard communication fails within **4 hours**.

- **No Internet:** Victims cannot send SOS.
- **No Data:** Rescue teams work blindly.
- **No Coordination:** Government relies on outdated manual reports.

## ⚡ The Solution: Drishti

A fully offline-capable ecosystem that combines **Mesh Networking**, **AI Prediction**, and **Government Governance**. Mesh communication is a fail-safe layer that activates only if approved routes fail or cellular/internet infrastructure collapses; it is not the primary path but a resilience backup for escalation scenarios.

## 🛡️ Operational Phases (demo briefing)

> Show this once at demo start or include in briefing docs.

The system operates in three controlled phases:

1. **Risk Assessment** – AI evaluates terrain, weather, and route safety.
2. **Authority Approval** – District or NDRF officials approve or reject routes or evacuation decisions.
3. **Fail-Safe Response** – Offline mesh communication and SITREP activate only if infrastructure fails.

## 🎮 HOW TO DEMO (SIMULATION MODE)

We have built a "God Mode" to demonstrate the system without waiting for a real disaster.

1.  **Open the Admin Dashboard** (Desktop View).
    - Login: `admin` / `india123`
2.  **Trigger Disaster:**
    - Click the **"⚠️ START SIM"** button in the top right.
    - _Effect:_ The Map turns RED, and a "Pending Decision" appears.
3.  **Governance Layer:**
    - You will see an **"ACTION REQUIRED"** panel.
    - This proves AI _cannot_ act alone. A human must **APPROVE** the evacuation order.
4.  **Resolve:**
    - Click **"AUTHORIZE"**.
    - The system dispatches alerts and resets to green.

---

## 🛠️ Tech Stack

- **Frontend:** React, Tailwind, Capacitor (Android/iOS).
- **Backend:** Python FastAPI (Heroku).
- **AI/ML:** Scikit-Learn (Risk), Sarvam AI (Voice), OpenCV (Drones).
- **Hardware:** Bluetooth Low Energy (BLE) Mesh Algorithm.

## 🌟 Key Features

1.  **📡 Offline-First App:** Works without internet using Bluetooth Mesh & P2P.
2.  **🗣️ Voice AI (Offline):** "Navigate to Shelter" - works in Hindi/English/Assamese.
3.  **🚁 Drone Recon:** Computer Vision to detect road blockages automatically _(Phase-2 Integration, Post-Pilot; de-emphasized during authority workflow)_.
4.  **🧠 Predictive AI:** Random Forest model predicts landslides 6 hours in advance.
5.  **⚖️ Governance Layer:** AI suggests, Human approves (Audit Logged).

## 🚀 How to Run Locally

### 1. Backend (Python)

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

```

### 2. Frontend (React Native)

```Bash

cd frontend
npm install
npm run dev
```
