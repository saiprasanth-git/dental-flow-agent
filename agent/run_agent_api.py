"""
DentalFlow Agent - HTTP API Wrapper
====================================
Flask microservice that exposes the DentalFlow agent over HTTP so that
UiPath Maestro can trigger it via the built-in HTTP Request Activity.

Endpoints consumed by Maestro:
  POST /run          - Run one agent cycle (poll + resolve all exceptions)
  POST /run/single   - Resolve a single appointment by ID
  GET  /status       - Agent health + last run summary
  GET  /actions      - Proxy to EHR action log (for Maestro dashboard)

Design principles:
  - Stateless per request (safe for Maestro parallel triggers)
  - Returns structured JSON Maestro can parse with deserialize activity
  - Non-blocking: each /run call is synchronous but fast (<5s typical)
  - Human-in-the-loop: /run/escalated returns items needing human review
"""

import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

# Import our agent
from dental_flow_agent import EHRClient, DentalFlowAgent, EHR_BASE_URL, AGENT_NAME

# ── Setup ──────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Shared EHR client (connection-pooled via requests.Session)
ehr = EHRClient(EHR_BASE_URL)

# In-memory run history (last 50 runs)
run_history = []


def _build_run_record(status: str, summary: dict, error: str = None) -> dict:
    record = {
        "runId": f"run-{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}",
        "agentName": AGENT_NAME,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "status": status,
        "summary": summary,
    }
    if error:
        record["error"] = error
    run_history.append(record)
    if len(run_history) > 50:
        run_history.pop(0)
    return record


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    """Maestro uses this to verify the agent service is alive."""
    ehr_ok = ehr.health_check()
    return jsonify({
        "status": "ok" if ehr_ok else "degraded",
        "agentName": AGENT_NAME,
        "ehrApiReachable": ehr_ok,
        "ehrBaseUrl": EHR_BASE_URL,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }), 200 if ehr_ok else 503


@app.post("/run")
def run_agent():
    """
    Primary Maestro trigger endpoint.
    Runs a full exception-resolution cycle and returns a structured summary.
    Maestro calls this on schedule (e.g., every 15 min) or on EHR webhook.

    Response shape:
    {
      "runId": "run-20260518T153000Z",
      "status": "success" | "partial" | "error",
      "summary": {
        "totalExceptions": 3,
        "resolved": 2,
        "escalated": 1,
        "actions": [...]
      },
      "requiresHumanReview": true | false,
      "escalations": [...]   // items needing human sign-off
    }
    """
    logger.info("Maestro triggered /run")

    # Capture pre-run action count to diff what we added
    try:
        pre_actions = ehr.get_agent_actions()
        pre_count = len(pre_actions)
    except Exception:
        pre_count = 0

    # Run agent
    agent = DentalFlowAgent(ehr)
    errors = []
    try:
        agent.run_once()
    except Exception as exc:
        logger.error(f"Agent run error: {exc}")
        errors.append(str(exc))

    # Fetch what happened
    try:
        post_actions = ehr.get_agent_actions()
        new_actions = post_actions[pre_count:]  # actions taken this run
    except Exception:
        new_actions = []

    # Check for any remaining escalations (still unresolved)
    try:
        remaining = ehr.get_exceptions()
        escalations = [
            e for e in remaining
            if e.get("exceptionType") == "provider_unavailable"
            or (e.get("exceptionType") == "insurance_unverified"
                and e.get("notes", "").startswith("Pre-authorization"))
        ]
    except Exception:
        escalations = []
        remaining = []

    resolved_count = len(new_actions)
    status = "error" if errors and not new_actions else (
        "partial" if escalations else "success"
    )

    summary = {
        "totalExceptions": len(agent.processed) + len(escalations),
        "resolved": resolved_count,
        "escalated": len(escalations),
        "actions": new_actions,
        "errors": errors,
    }

    record = _build_run_record(status, summary)
    record["requiresHumanReview"] = len(escalations) > 0
    record["escalations"] = escalations

    logger.info(
        f"Run complete: {resolved_count} resolved, "
        f"{len(escalations)} escalated, status={status}"
    )
    return jsonify(record), 200


@app.post("/run/single")
def run_single():
    """
    Resolve a single appointment exception by ID.
    Maestro calls this when a human-review task is approved.

    Body: { "appointmentId": "appt-001" }
    """
    body = request.get_json(force=True, silent=True) or {}
    appt_id = body.get("appointmentId")

    if not appt_id:
        return jsonify({"error": "appointmentId is required"}), 400

    try:
        # Fetch exceptions and find the requested one
        exceptions = ehr.get_exceptions()
        target = next((e for e in exceptions if e["id"] == appt_id), None)

        if not target:
            return jsonify({"error": f"No open exception found for {appt_id}"}), 404

        agent = DentalFlowAgent(ehr)
        agent._handle_exception(target)
        agent.processed.add(appt_id)

        return jsonify({
            "status": "resolved",
            "appointmentId": appt_id,
            "actionsLogged": len(agent.processed),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }), 200

    except Exception as exc:
        logger.error(f"Single run error for {appt_id}: {exc}")
        return jsonify({"error": str(exc), "appointmentId": appt_id}), 500


@app.get("/status")
def status():
    """Returns agent status + last N run records. Used by Maestro dashboard."""
    return jsonify({
        "agentName": AGENT_NAME,
        "ehrBaseUrl": EHR_BASE_URL,
        "totalRunsThisSession": len(run_history),
        "lastRun": run_history[-1] if run_history else None,
        "recentRuns": run_history[-5:],
        "timestamp": datetime.utcnow().isoformat() + "Z",
    })


@app.get("/exceptions")
def get_exceptions():
    """Proxy to EHR exceptions - Maestro reads this to populate its dashboard."""
    try:
        exceptions = ehr.get_exceptions()
        return jsonify({
            "exceptions": exceptions,
            "total": len(exceptions),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        })
    except Exception as exc:
        return jsonify({"error": str(exc)}), 503


@app.get("/actions")
def get_actions():
    """Proxy to EHR agent action log."""
    try:
        actions = ehr.get_agent_actions()
        return jsonify({
            "actions": actions,
            "total": len(actions),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        })
    except Exception as exc:
        return jsonify({"error": str(exc)}), 503


@app.post("/escalate/approve")
def approve_escalation():
    """
    Human-in-the-loop approval endpoint.
    When a Maestro human task is approved, Maestro posts here to trigger resolution.

    Body: {
      "appointmentId": "appt-002",
      "approvedBy": "Dr. Admin",
      "action": "reschedule" | "confirm" | "cancel"
    }
    """
    body = request.get_json(force=True, silent=True) or {}
    appt_id = body.get("appointmentId")
    approved_by = body.get("approvedBy", "Unknown")
    action = body.get("action", "reschedule")

    if not appt_id:
        return jsonify({"error": "appointmentId is required"}), 400

    try:
        # Log the human approval
        ehr.log_action(
            action_type="HUMAN_APPROVAL",
            appointment_id=appt_id,
            details={"approvedBy": approved_by, "action": action},
            outcome="human_approved",
        )

        # Now execute the approved action
        if action in ("reschedule", "confirm"):
            exceptions = ehr.get_exceptions()
            target = next((e for e in exceptions if e["id"] == appt_id), None)
            if target:
                agent = DentalFlowAgent(ehr)
                agent._handle_exception(target)

        elif action == "cancel":
            # Soft cancel via EHR API
            import requests as req
            req.delete(f"{EHR_BASE_URL}/appointments/{appt_id}", timeout=10)
            ehr.log_action(
                action_type="APPOINTMENT_CANCELLED",
                appointment_id=appt_id,
                details={"cancelledBy": approved_by},
                outcome="cancelled_by_human",
            )

        return jsonify({
            "status": "executed",
            "appointmentId": appt_id,
            "action": action,
            "approvedBy": approved_by,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }), 200

    except Exception as exc:
        logger.error(f"Escalation approval error: {exc}")
        return jsonify({"error": str(exc)}), 500


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("AGENT_API_PORT", "8080"))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    logger.info(f"DentalFlow Agent API starting on port {port}")
    logger.info(f"EHR API target: {EHR_BASE_URL}")
    app.run(host="0.0.0.0", port=port, debug=debug)
