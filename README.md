# 🚁 DRISHTI: Disaster Response & Intelligence System

> *Survive. Connect. Recover.*

![Drishti Banner](https://via.placeholder.com/800x400?text=DRISHTI+DASHBOARD)

## 🚨 The Problem
During floods (like Sikkim 2023), standard communication fails within **4 hours**.
* **No Internet:** Victims cannot send SOS.
* **No Data:** Rescue teams work blindly.
* **No Coordination:** Government relies on outdated manual reports.

## ⚡ The Solution: Drishti
A fully offline-capable ecosystem that combines **Mesh Networking**, **AI Prediction**, and **Government Governance**.


## 🎮 HOW TO DEMO (SIMULATION MODE)
We have built a "God Mode" to demonstrate the system without waiting for a real disaster.

1.  **Open the Admin Dashboard** (Desktop View).
    * Login: `admin` / `india123`
2.  **Trigger Disaster:**
    * Click the **"⚠️ START SIM"** button in the top right.
    * *Effect:* The Map turns RED, and a "Pending Decision" appears.
3.  **Governance Layer:**
    * You will see an **"ACTION REQUIRED"** panel.
    * This proves AI *cannot* act alone. A human must **APPROVE** the evacuation order.
4.  **Resolve:**
    * Click **"AUTHORIZE"**.
    * The system dispatches alerts and resets to green.

---

## 🛠️ Tech Stack
* **Frontend:** React, Tailwind, Capacitor (Android/iOS).
* **Backend:** Python FastAPI (Heroku).
* **AI/ML:** Scikit-Learn (Risk), Sarvam AI (Voice), OpenCV (Drones).
* **Hardware:** Bluetooth Low Energy (BLE) Mesh Algorithm.

## 🌟 Key Features
1.  **📡 Offline-First App:** Works without internet using Bluetooth Mesh & P2P.
2.  **🗣️ Voice AI (Offline):** "Navigate to Shelter" - works in Hindi/English/Assamese.
3.  **🚁 Drone Recon:** Computer Vision to detect road blockages automatically.
4.  **🧠 Predictive AI:** Random Forest model predicts landslides 6 hours in advance.
5.  **⚖️ Governance Layer:** AI suggests, Human approves (Audit Logged).

## 🚀 How to Run Locally
### 1. Backend (Python)
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
2. Frontend (React Native)
```

```Bash

cd frontend
npm install
npm run dev
Built with ❤️ by Team Drishti
```


### **Step 3: Final Deployment**

This is the last code push before you present.

1.  **Commit:**
    ```bash
    git add .
    git commit -m "Phase 36: Final Polish and Documentation"
    git push origin main
    ```

2.  **Deploy Backend:**
    ```bash
    git push heroku main
    ```

3.  **Deploy Frontend:**
    ```bash
    cd frontend
    vercel --prod
    ```
