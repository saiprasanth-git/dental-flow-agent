# DentalFlow Agent — Devpost Submission

> **Copy this content directly into your Devpost project page fields.**
> Replace placeholders in `[brackets]` before submitting.

---

## Project Name
DentalFlow Agent

## Track
Track 1: UiPath Maestro Case

## Tagline
Autonomous dental practice scheduling agent — from exception chaos to resolved in under 30 seconds.

---

## Inspiration

Dental practices run on tight scheduling margins. A single provider calling in sick, an insurance pre-authorization delay, or an unverified policy can cascade into a day of angry patients, lost revenue, and exhausted front-desk staff. Talking to office managers at Texas dental practices, the pattern is consistent: 3–4 hours per day is spent manually firefighting these exceptions — calls to insurance companies, frantic rescheduling, and hoping patients don't just walk out.

We asked: what if an AI agent handled all of this autonomously, and only surfaced the truly edge cases to a human?

---

## What It Does

DentalFlow Agent is an AI-powered scheduling exception management system built on UiPath Maestro. It:

1. **Continuously monitors** the appointment queue for exceptions
2. **Prioritizes** by urgency (critical < 4hr, high < 24hr, normal)
3. **Autonomously resolves** the majority of exceptions:
   - Verifies insurance coverage (BCBS, UHC auto-approve)
   - Reschedules patients with available providers when their provider is unavailable
   - Confirms pending appointments ready for confirmation
   - Sends patient notifications
4. **Escalates intelligently** to human staff via UiPath Maestro Action Center when:
   - Insurance requires pre-authorization (e.g., AETNA)
   - No available providers exist for rescheduling
5. **Logs everything** to a full audit trail in the EHR system
6. **Reports** each run to an Orchestrator Queue for compliance and reporting

All orchestration flows through UiPath Maestro. Humans only touch the exceptions that genuinely need them.

---

## How We Built It

**Architecture:**
```
UiPath Maestro (Orchestration layer)
       ↓ HTTP Activity (POST /run every 15 min)
DentalFlow Agent API  ─  Flask/Python  ─  port 8080
       ↓ REST calls
DentalFlow EHR API  ─  Node.js/Express  ─  port 3001
```

**Stack:**
- **UiPath Maestro**: 7-step orchestration workflow (XAML)
  - Health check → fetch exceptions → trigger agent → evaluate → HITL → queue → log
- **Python (Flask + Gunicorn)**: Agent decision engine with 5 HTTP endpoints
  - `POST /run` — full exception-resolution cycle
  - `POST /run/single` — single appointment resolution
  - `POST /escalate/approve` — human-in-the-loop approval handler
  - `GET /status` — agent health + run history
  - `GET /exceptions` — EHR exception proxy
- **Node.js/Express**: Mock EHR with full appointment lifecycle, insurance verification, and agent action log
- **Docker Compose**: One-command full-stack deployment
- **AI Coding Assistance**: Built using Perplexity Comet (Claude) for accelerated development — eligible for UiPath Coding Agents bonus

**Agent Types Used:**
- Reactive agent (exception-triggered)
- Goal-based agent (resolve or escalate based on exception type)
- Human-in-the-loop agent (Maestro Action Center integration)

---

## Challenges We Ran Into

- **Maestro HTTP Activity vs. Agent Polling**: Bridging the UiPath synchronous HTTP trigger model with the agent's async exception-polling loop required wrapping the Python agent in a Flask microservice
- **Priority Queue Design**: Implementing critical/high/normal priority tiers that Maestro can act on without needing a message broker
- **Human Task Data Modeling**: Designing Action Center form data that gives the reviewer enough context (exception type, patient info, suggested action) without overwhelming them
- **Idempotency**: Ensuring the agent doesn't re-process already-resolved appointments within a session (solved via in-memory processed set)

---

## Accomplishments That We're Proud Of

- Full end-to-end working prototype from EHR API → Agent → Maestro → Action Center in under 48 hours
- Clean separation of concerns: EHR API, Agent logic, and Maestro orchestration are independently testable
- Human-in-the-loop is a first-class citizen, not an afterthought — every escalation includes full context for the reviewer
- The Maestro XAML workflow covers all 7 orchestration steps including queue logging for governance
- One-command `docker-compose up` demo — zero setup friction for judges

---

## What We Learned

- UiPath Maestro's HTTP Activity is a powerful, underutilized bridge to external AI services — no Robot license needed
- Action Center Form Tasks are excellent for structured HITL workflows but require careful data design upfront
- Building the mock EHR first (before the agent) made testing dramatically faster
- Priority-based exception handling is the difference between a demo and a production-grade system

---

## What's Next for DentalFlow Agent

- **Real EHR integration**: Connect to Dentrix, Eaglesoft, or Epic via HL7 FHIR
- **LLM layer**: Use GPT-4o to draft personalized patient rescheduling messages
- **Multi-tenant SaaS**: One agent deployment serves N dental practices via tenant-aware configuration
- **Twilio/SendGrid**: Replace notification stub with real SMS/email
- **UiPath Test Cloud (Track 3)**: Add automated testing layer for the agent API endpoints
- **BPMN modeling (Track 2)**: Model the full appointment lifecycle as a BPMN 2.0 process

---

## Built With

`uipath-maestro` `uipath-action-center` `uipath-orchestrator` `python` `flask` `gunicorn` `node.js` `express` `docker` `docker-compose` `rest-api` `json` `perplexity-comet`

---

## Try It Out

- **GitHub**: https://github.com/saiprasanth-git/dental-flow-agent
- **Quick Start**: `docker-compose up` then `POST http://localhost:8080/run`
- **Demo Video**: [YouTube link — add before submission]
- **Presentation**: [Google Slides link — add before submission, share with "access to all"]

---

## Submission Checklist

- [ ] Devpost project page complete with all fields above
- [ ] Demo video uploaded (5 min max, shows agent running live)
- [ ] GitHub repository public with MIT license
- [ ] Presentation deck created from template, shared publicly
- [ ] Optional: Feedback form submitted for Best Product Feedback award
- [ ] Track selected: Track 1 — UiPath Maestro Case
