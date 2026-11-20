# GridPulse AI — Autonomous Neuro-Symbolic Smart Energy & Sustainability Agent

GridPulse AI is an autonomous energy and sustainability co-pilot for a **Smart Commercial Building Microgrid** (60 kW Rooftop Solar PV, 120 kWh / 40 kW BESS Battery, 3 HVAC Thermal Zones, 3 Smart EV Chargers, and Deferrable Loads).

## Architecture
- **Neuro-Symbolic Control:** A deterministic 24-hour LP optimizer (`PuLP` / CBC) solves power balance, battery SoC bounds (15%–95%), EV departure deadlines, and RC thermal comfort bands in `< 300 ms`, while a LangGraph agent (`Observe -> Compile -> Guardrail -> Solve -> Explain`) compiles natural-language policies into validated Pydantic constraint patches.
- **Dual-Twin Counterfactual Engine:** Simulates both the **Agent-Optimized Building** and an **Unoptimized Baseline Building** in real time so every dollar saved, kW shaved, and kg CO₂ avoided is auditable.
- **Live External Feeds:** Integrates **Open-Meteo** (solar irradiance & temperature) and **UK Carbon Intensity API** (zero-config default) or **Electricity Maps v4**, with a 15-minute TTL cache and automatic synthetic fallback.
- **Zero-Key Demo Resilience:** Works out-of-the-box with zero API keys via a deterministic NLP fallback parser.

## Quick Start

### 1. Backend (FastAPI + PuLP + LangGraph)
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend (React + Vite + Tailwind + Recharts)
```bash
cd frontend
npm install
npm run dev
```

### 3. Run Automated Tests
```bash
cd backend
PYTHONPATH=. pytest -v
```
