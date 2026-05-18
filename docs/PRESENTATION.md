# DentalFlow Agent - Presentation Deck Outline
## UiPath AgentHack 2026 | Track 1: Maestro Case

> Use this outline with the [UiPath AgentHack slide template](https://uipath-agenthack.devpost.com/).
> Slides should be shared with "access to all" permissions before submission.

---

## Slide 1: Title
**DentalFlow Agent**
*Autonomous Dental Practice Exception Management*

- Subtitle: Eliminating scheduling chaos with AI + UiPath Maestro
- Track: Track 1 — Maestro Case
- Team: saiprasanth-git
- Date: June 2026

---

## Slide 2: The Problem
**Dental practices lose 15-20% of appointment revenue to scheduling exceptions**

- Insurance not verified before patient arrives → denied claims
- Provider calls in sick → patient gets no-call / angry cancellation
- Pre-auth delays (especially AETNA) → rescheduling bottleneck
- Front desk staff spending 40% of day firefighting exceptions

**Quote**: “I spend half my morning just chasing insurance approvals.” — Dental office manager

---

## Slide 3: Our Solution
**DentalFlow Agent: Autonomous Exception Resolution**

- AI agent monitors the appointment queue 24/7
- Detects exceptions: unverified insurance, unavailable providers, pending confirmations
- Resolves them autonomously — or escalates to staff with full context
- Built on UiPath Maestro + Python + Express EHR API

---

## Slide 4: Architecture
```
UiPath Maestro (Orchestration)
        ↓ HTTP Activity
DentalFlow Agent API (Flask/Python)
        ↓ REST calls
DentalFlow EHR API (Node.js/Express)
```

**Key Components:**
| Layer | Technology | Role |
|---|---|---|
| Orchestrator | UiPath Maestro | Trigger, HITL, audit |
| Agent API | Python Flask + Gunicorn | Decision engine |
| EHR API | Node.js / Express | Data + action log |
| Infra | Docker Compose | One-command demo |

---

## Slide 5: How It Works (Demo Flow)

**Step-by-step:**
1. Maestro triggers `POST /run` on schedule (every 15 min)
2. Agent polls `/exceptions` — finds 3 exceptions
3. **Critical** (< 4hr): Emily Johnson — provider sick → auto-reschedule with Dr. Marcus Williams
4. **High** (< 24hr): John Smith — AETNA pre-auth needed → escalate to Action Center
5. **Normal**: Maria Rodriguez — BCBS verified → auto-confirm
6. Human reviews John Smith in Maestro Action Center → approves reschedule
7. Agent executes approval, logs all actions to EHR audit trail
8. Maestro writes run summary to Orchestrator Queue

---

## Slide 6: Key Features

**Autonomous Capabilities:**
- ✅ Insurance verification (BCBS, UHC auto-approve; AETNA escalates)
- ✅ Provider rescheduling (slot-aware, real-time availability)
- ✅ Appointment confirmation
- ✅ Patient notification (email/SMS stub, extensible)
- ✅ Full audit trail via EHR action log

**Maestro Integration:**
- ✅ HTTP Activity triggers (no UiPath Robot license needed)
- ✅ Human-in-the-loop via Action Center Form Tasks
- ✅ Priority-based exception handling (critical > high > normal)
- ✅ Orchestrator Queue for run summaries
- ✅ 24h human task timeout with auto-escalation

---

## Slide 7: Business Impact

| Metric | Before | After |
|---|---|---|
| Time to resolve exception | 2-4 hours (manual) | < 30 seconds (autonomous) |
| Staff hours on exceptions | 3-4 hr/day | < 30 min/day (review only) |
| Insurance denials at desk | ~15% of appointments | Near 0% (pre-verified) |
| Patient satisfaction | Disrupted by last-minute calls | Proactive reschedule notification |
| Scalability | 1 front desk = 1 clinic | 1 agent = unlimited clinics |

**ROI estimate**: For a 100-patient/day practice, recovering even 5% lost revenue from denied claims = $50K+ annually.

---

## Slide 8: UiPath Platform Usage

**Deep integration with UiPath Automation Cloud:**

- **Maestro Case**: Exception-driven orchestration workflow
- **HTTP Activity**: Maestro ↔ Agent API communication
- **Action Center**: Human-in-the-loop approval for escalations
- **Form Tasks**: Structured review forms with appointment context
- **Orchestrator Queues**: Run audit log for governance
- **Maestro Triggers**: Time-based (every 15 min) + webhook-ready

**Bonus**: Built with AI coding assistance (Perplexity/Comet) — eligible for UiPath Coding Agents bonus

---

## Slide 9: Scalability & Extensibility

**Today (Hackathon Demo):**
- 1 dental practice, mock EHR, 3 seed appointments

**Production Ready:**
- Connect to real EHR: Epic, Dentrix, Eaglesoft (swap EHR API)
- Multi-tenant: one agent instance per practice via env config
- Add SMS/email via Twilio/SendGrid
- LLM layer: use GPT-4o to draft escalation messages
- BPMN extension: add Track 2 BPMN modeling layer

**Infrastructure:**
- Docker Compose → Kubernetes (Helm chart ready)
- EHR API → swap with real integration (HL7 FHIR)

---

## Slide 10: Demo

**Live Demo / Video Walkthrough:**

1. `docker-compose up` — stack starts in 30 seconds
2. Curl `/exceptions` — see 3 appointments with priorities
3. Trigger Maestro workflow — watch agent resolve in real-time
4. AETNA escalation surfaces in Action Center
5. Approve → agent resolves → audit log shows full trace

**GitHub**: https://github.com/saiprasanth-git/dental-flow-agent

---

## Slide 11: Team

- **Sai Prasanth** — Full-stack & AI Engineer, Houston TX
  - Built: RepoMind (GitHub AI), AI agents for Texas dental practices
  - Tech: Python, Node.js, Docker, GCP, UiPath Automation Cloud

---

## Slide 12: Thank You

**DentalFlow Agent**
*From scheduling chaos to autonomous clarity*

GitHub: https://github.com/saiprasanth-git/dental-flow-agent
Devpost: [submission link]

> Questions?
