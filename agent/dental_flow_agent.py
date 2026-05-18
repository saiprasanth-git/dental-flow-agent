"""
DentalFlow Agent - UiPath AgentHack 2026
Track 1: Maestro Case

AI-powered dental practice automation agent that:
- Polls for appointment exceptions
- Verifies insurance coverage
- Reschedules with available providers
- Sends patient notifications
- Logs all actions via the EHR API

Uses UiPath Autopilot (HTTP activity) as the orchestration layer.
Python bridge script for local testing and hackathon demo.
"""

import os
import json
import time
import requests
from datetime import datetime
from typing import Optional

# ── Config ────────────────────────────────────────────────────────────────────
EHR_BASE_URL = os.getenv("EHR_BASE_URL", "http://localhost:3001")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "30"))  # seconds
AGENT_NAME = "DentalFlow-Agent-v1"

# ── EHR API Client ────────────────────────────────────────────────────────────

class EHRClient:
    """Thin wrapper around the DentalFlow EHR REST API."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def health_check(self) -> bool:
        try:
            r = self.session.get(f"{self.base_url}/health", timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    def get_exceptions(self) -> list:
        r = self.session.get(f"{self.base_url}/exceptions", timeout=10)
        r.raise_for_status()
        return r.json().get("exceptions", [])

    def get_providers(self, status: str = "available") -> list:
        r = self.session.get(
            f"{self.base_url}/providers",
            params={"status": status},
            timeout=10,
        )
        r.raise_for_status()
        return r.json().get("providers", [])

    def get_provider_slots(self, provider_id: str) -> list:
        r = self.session.get(
            f"{self.base_url}/providers/{provider_id}/slots",
            timeout=10,
        )
        r.raise_for_status()
        return r.json().get("availableSlots", [])

    def verify_insurance(
        self, insurance_id: str, patient_id: str, appointment_type: str
    ) -> dict:
        payload = {
            "insuranceId": insurance_id,
            "patientId": patient_id,
            "appointmentType": appointment_type,
        }
        r = self.session.post(
            f"{self.base_url}/insurance/verify",
            json=payload,
            timeout=10,
        )
        r.raise_for_status()
        return r.json()

    def patch_appointment(self, appt_id: str, updates: dict) -> dict:
        r = self.session.patch(
            f"{self.base_url}/appointments/{appt_id}",
            json=updates,
            timeout=10,
        )
        r.raise_for_status()
        return r.json()

    def log_action(
        self,
        action_type: str,
        appointment_id: str,
        details: dict,
        outcome: str,
    ) -> dict:
        payload = {
            "actionType": action_type,
            "agentName": AGENT_NAME,
            "appointmentId": appointment_id,
            "details": details,
            "outcome": outcome,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        r = self.session.post(
            f"{self.base_url}/agent/action",
            json=payload,
            timeout=10,
        )
        r.raise_for_status()
        return r.json()

    def get_agent_actions(self) -> list:
        r = self.session.get(f"{self.base_url}/agent/actions", timeout=10)
        r.raise_for_status()
        return r.json().get("actions", [])

# ── Agent Logic ───────────────────────────────────────────────────────────────

class DentalFlowAgent:
    """Core agent that resolves appointment exceptions autonomously."""

    def __init__(self, ehr: EHRClient):
        self.ehr = ehr
        self.processed: set = set()  # track appt IDs handled this session

    def log(self, msg: str):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {AGENT_NAME}: {msg}")

    def run_once(self):
        """Single poll-and-resolve cycle."""
        self.log("Polling for exceptions...")
        exceptions = self.ehr.get_exceptions()

        if not exceptions:
            self.log("No exceptions found. All clear.")
            return

        self.log(f"Found {len(exceptions)} exception(s).")

        # Sort by priority: critical > high > normal
        priority_order = {"critical": 0, "high": 1, "normal": 2}
        exceptions.sort(key=lambda x: priority_order.get(x.get("priority", "normal"), 2))

        for appt in exceptions:
            appt_id = appt["id"]
            if appt_id in self.processed:
                continue
            self._handle_exception(appt)

    def _handle_exception(self, appt: dict):
        appt_id = appt["id"]
        exception_type = appt.get("exceptionType", "unknown")
        suggested = appt.get("suggestedAction", "")
        priority = appt.get("priority", "normal")

        self.log(
            f"Handling [{priority.upper()}] appt {appt_id} "
            f"({appt['patientName']}) - {exception_type}"
        )

        if suggested == "verify_insurance" or exception_type == "insurance_unverified":
            self._verify_insurance(appt)

        elif suggested == "reschedule_with_available_provider" or exception_type == "provider_unavailable":
            self._reschedule(appt)

        elif suggested == "confirm_appointment":
            self._confirm(appt)

        else:
            self.log(f"  Unknown action '{suggested}' for {appt_id} - skipping.")
            return

        self.processed.add(appt_id)

    def _verify_insurance(self, appt: dict):
        appt_id = appt["id"]
        self.log(f"  Verifying insurance {appt['insuranceId']} for {appt['patientName']}...")

        result = self.ehr.verify_insurance(
            insurance_id=appt["insuranceId"],
            patient_id=appt["patientId"],
            appointment_type=appt["type"],
        )

        if result["verified"]:
            self.log(f"  Insurance VERIFIED. Auth code: {result.get('preAuthCode')}")
            outcome = "insurance_verified"
            # EHR auto-confirms on verify, but patch status explicitly
            self.ehr.patch_appointment(appt_id, {"insuranceVerified": True, "status": "confirmed"})
        else:
            self.log(
                f"  Insurance REQUIRES PRE-AUTH. {result.get('message')}"
            )
            outcome = "pre_auth_required"
            self.ehr.patch_appointment(
                appt_id,
                {
                    "notes": result.get("message", "Pre-authorization required."),
                    "status": "exception",
                },
            )

        self.ehr.log_action(
            action_type="INSURANCE_VERIFICATION",
            appointment_id=appt_id,
            details={
                "insuranceId": appt["insuranceId"],
                "patientId": appt["patientId"],
                "verified": result["verified"],
                "requiresPreAuth": result.get("requiresPreAuth", False),
            },
            outcome=outcome,
        )

    def _reschedule(self, appt: dict):
        appt_id = appt["id"]
        self.log(f"  Provider unavailable for {appt['patientName']}. Finding new provider...")

        providers = self.ehr.get_providers(status="available")
        if not providers:
            self.log("  No available providers found. Escalating.")
            self.ehr.log_action(
                action_type="RESCHEDULE_FAILED",
                appointment_id=appt_id,
                details={"reason": "No available providers"},
                outcome="escalated_to_staff",
            )
            return

        # Pick first available provider with open slots
        selected_provider = None
        selected_slot = None

        for provider in providers:
            slots = self.ehr.get_provider_slots(provider["id"])
            if slots:
                selected_provider = provider
                selected_slot = slots[0]  # take earliest available slot
                break

        if not selected_provider or not selected_slot:
            self.log("  Available providers have no open slots. Escalating.")
            self.ehr.log_action(
                action_type="RESCHEDULE_FAILED",
                appointment_id=appt_id,
                details={"reason": "No open slots among available providers"},
                outcome="escalated_to_staff",
            )
            return

        self.log(
            f"  Rescheduling with {selected_provider['name']} "
            f"at {selected_slot}"
        )

        self.ehr.patch_appointment(
            appt_id,
            {
                "providerId": selected_provider["id"],
                "providerName": selected_provider["name"],
                "scheduledAt": selected_slot,
                "status": "confirmed",
                "notes": f"Auto-rescheduled by {AGENT_NAME} to {selected_provider['name']}",
            },
        )

        self.ehr.log_action(
            action_type="APPOINTMENT_RESCHEDULED",
            appointment_id=appt_id,
            details={
                "originalProviderId": appt["providerId"],
                "newProviderId": selected_provider["id"],
                "newProviderName": selected_provider["name"],
                "newSlot": selected_slot,
                "patientNotified": True,
            },
            outcome="rescheduled_successfully",
        )

        # Simulate patient notification
        self._notify_patient(appt, selected_provider["name"], selected_slot)

    def _confirm(self, appt: dict):
        appt_id = appt["id"]
        self.log(f"  Confirming appointment {appt_id} for {appt['patientName']}...")

        self.ehr.patch_appointment(appt_id, {"status": "confirmed"})

        self.ehr.log_action(
            action_type="APPOINTMENT_CONFIRMED",
            appointment_id=appt_id,
            details={"patientName": appt["patientName"]},
            outcome="confirmed",
        )

    def _notify_patient(
        self, appt: dict, new_provider: str, new_slot: str
    ):
        """Simulate sending a patient notification (email/SMS stub)."""
        slot_fmt = datetime.fromisoformat(
            new_slot.replace("Z", "+00:00")
        ).strftime("%B %d, %Y at %I:%M %p UTC")

        message = (
            f"Dear {appt['patientName']}, your appointment has been "
            f"rescheduled with {new_provider} on {slot_fmt}. "
            f"Please contact us if you have questions."
        )
        self.log(f"  [NOTIFY] {appt['patientEmail']}: {message}")

    def run_loop(self):
        """Continuous polling loop — called by UiPath Maestro orchestration."""
        self.log("Agent started. Entering poll loop.")
        while True:
            try:
                self.run_once()
            except requests.RequestException as exc:
                self.log(f"EHR API error: {exc}")
            except Exception as exc:
                self.log(f"Unexpected error: {exc}")
            self.log(f"Sleeping {POLL_INTERVAL}s before next poll...")
            time.sleep(POLL_INTERVAL)

# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    ehr = EHRClient(EHR_BASE_URL)

    print(f"Connecting to EHR API at {EHR_BASE_URL}...")
    if not ehr.health_check():
        print("ERROR: EHR API is not reachable. Start it with: cd ehr-api && npm start")
        exit(1)

    print("EHR API healthy. Starting DentalFlow Agent...")
    agent = DentalFlowAgent(ehr)

    import sys
    if "--once" in sys.argv:
        # Single run mode for UiPath Maestro HTTP activity integration
        agent.run_once()
    else:
        agent.run_loop()
