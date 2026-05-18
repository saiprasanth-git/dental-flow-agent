# dental-flow-agent

> AI-powered dental practice automation agent built with **UiPath Maestro** for the [UiPath AgentHack 2026](https://uipath-agenthack.devpost.com/) — Track 1: Maestro Case

---

## What It Does

DentalFlow Agent autonomously monitors a dental practice's appointment queue, detects exceptions, and resolves them without human intervention:

- **Insurance Verification** — auto-verifies coverage via EHR API; flags pre-auth cases
- **Provider Rescheduling** — when a provider is unavailable, finds the next available slot and reschedules
- **Appointment Confirmation** — confirms pending appointments that are ready to go
- **Patient Notification** — sends rescheduling messages to patients (email/SMS stub)
- **Full Audit Trail** — every action is logged to the EHR API's agent action log

All orchestration runs through **UiPath Maestro** (Track 1: Maestro Case).

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                UiPath Maestro                       │
│   (Orchestrates agent via HTTP Activity triggers)   │
└────────────────────┬────────────────────────────────┘
                     │ HTTP
┌────────────────────▼────────────────────────────────┐
│           DentalFlow Agent (Python)                 │
│   agent/dental_flow_agent.py                        │
│                                                     │
│  ┌─────────────────┐   ┌──────────────────────────┐ │
│  │  EHRClient      │   │  DentalFlowAgent          │ │
│  │  (REST wrapper) │◄──│  - run_once()             │ │
│  └────────┬────────┘   │  - _verify_insurance()    │ │
│           │            │  - _reschedule()           │ │
│           │            │  - _confirm()              │ │
│           │            │  - _notify_patient()       │ │
│           │            └──────────────────────────┘ │
└───────────┼─────────────────────────────────────────┘
            │ HTTP REST
┌───────────▼─────────────────────────────────────────┐
│         DentalFlow EHR API (Node.js/Express)        │
│         ehr-api/server.js  :3001                    │
│                                                     │
│  GET  /exceptions          POST /insurance/verify   │
│  GET  /providers           PATCH /appointments/:id  │
│  GET  /providers/:id/slots POST /agent/action       │
└─────────────────────────────────────────────────────┘
```

---

## Project Structure

```
dental-flow-agent/
├── ehr-api/
│   ├── server.js          # Mock EHR REST API (Node.js/Express)
│   └── package.json
├── agent/
│   ├── dental_flow_agent.py   # Main Python agent
│   └── requirements.txt
├── .gitignore
├── LICENSE
└── README.md
```

---

## Quick Start

### 1. Start the EHR API

```bash
cd ehr-api
npm install
npm start
# Running at http://localhost:3001
```

### 2. Run the Agent

```bash
cd agent
pip install -r requirements.txt

# Single run (used by UiPath Maestro HTTP activity)
python dental_flow_agent.py --once

# Continuous polling mode (every 30s)
python dental_flow_agent.py
```

### 3. Environment Variables

| Variable | Default | Description |
|---|---|---|
| `EHR_BASE_URL` | `http://localhost:3001` | EHR API base URL |
| `POLL_INTERVAL` | `30` | Seconds between polls |

---

## UiPath Maestro Integration

The agent is designed to be triggered via **UiPath Maestro's HTTP Activity**:

1. Maestro calls `POST http://<agent-host>/run` (or via subprocess in Maestro Case)
2. Agent runs `--once` mode: polls exceptions, resolves all, exits
3. Maestro reads exit code and logs the result
4. Maestro schedules next run based on trigger (time-based or event-based)

### Exception Priority Handling

| Priority | Trigger | Agent Action |
|---|---|---|
| `critical` | Appointment < 4 hours away | Resolve first |
| `high` | Appointment < 24 hours away | Resolve second |
| `normal` | Future appointment | Resolve last |

---

## Demo Scenarios

The mock EHR API ships with 3 seed appointments:

| Patient | Type | Status | Exception |
|---|---|---|---|
| Emily Johnson | Consultation | `exception` | Provider called in sick → **auto-reschedule** |
| John Smith | Root Canal | `pending` | AETNA insurance → **pre-auth required** |
| Maria Rodriguez | Cleaning | `confirmed` | BCBS verified → **auto-confirm** |

Running the agent resolves all three in a single `--once` cycle.

---

## Hackathon

- **Event**: [UiPath AgentHack 2026](https://uipath-agenthack.devpost.com/)
- **Track**: Track 1 — UiPath Maestro Case
- **Prize pool**: $50,000
- **Deadline**: June 30, 2026

---

## License

MIT
