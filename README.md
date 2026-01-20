# 🚁 DRISHTI: Disaster Response & Intelligence System

> **Winner of [Hackathon Name]** - Best Disaster Management Solution.
> *Survive. Connect. Recover.*

![Drishti Banner](https://i.imgur.com/your-banner-image.png)

## 🚨 The Problem
During floods (like Sikkim 2023), standard communication fails within **4 hours**.
* **No Internet:** Victims cannot send SOS.
* **No Data:** Rescue teams work blindly.
* **No Coordination:** Government relies on outdated manual reports.

## ⚡ The Solution: Drishti
A fully offline-capable ecosystem that combines **Mesh Networking**, **AI Prediction**, and **Drones**.

### 🌟 Key Features
1.  **📡 Offline-First App:** Works without internet using Bluetooth Mesh & P2P.
2.  **🗣️ Voice AI (Offline):** "Navigate to Shelter" - works in Hindi/English/Assamese without 4G.
3.  **🚁 Drone Recon:** Computer Vision to detect road blockages automatically.
4.  **🧠 Predictive AI:** Random Forest model predicts landslides 6 hours in advance.
5.  **🚑 Live Logistics:** Uber-like tracking for Ambulances & NDRF units.

## 🛠️ Tech Stack
* **Frontend:** React, Tailwind, Capacitor (Android/iOS).
* **Backend:** Python FastAPI (Heroku).
* **AI/ML:** Scikit-Learn (Risk), Sarvam AI (Voice), OpenCV (Drones).
* **Hardware:** Bluetooth Low Energy (BLE), Device Gyroscope (AR HUD).

## 📸 Screenshots
| **Survival Mode** | **AR Navigation** | **Command Center** |
|:---:|:---:|:---:|
| ![Map](https://via.placeholder.com/200x400) | ![AR](https://via.placeholder.com/200x400) | ![Dash](https://via.placeholder.com/200x400) |

## 🚀 How to Run
### 1. Backend (Python)
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

2. Frontend (React Native)
Bash

cd frontend
npm install
npm run start
🌍 Live Links

Backend API: https://drishtiappbackend-9d88613ee49f.herokuapp.com/docs

Demo Video: [YouTube Link]


