"""Mocked Iterum IQ persistence (PRD section 4.2).

A single JSON document standing in for IQ and the Airtable trackers. Deliberately simple:
the point of the prototype is the agent's behaviour, not the database.
"""

import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
STORE_PATH = DATA_DIR / "store.json"
SCENARIO_DIR = ROOT / "scenarios"

sys.path.insert(0, str(DATA_DIR))
import seed  # noqa: E402


class Store:
    def __init__(self):
        self._data = None

    # --- lifecycle -----------------------------------------------------------------
    def load_scenario(self, scenario_id: str) -> dict:
        path = SCENARIO_DIR / f"{scenario_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"No scenario named {scenario_id!r}")
        scenario = json.loads(path.read_text())
        self._data = seed.build(scenario)
        self.save()
        return scenario

    def save(self) -> None:
        STORE_PATH.write_text(json.dumps(self._data, indent=2) + "\n")

    @property
    def data(self) -> dict:
        if self._data is None:
            raise RuntimeError("No scenario loaded. Call load_scenario() first.")
        return self._data

    # --- clock ---------------------------------------------------------------------
    @property
    def today(self) -> date:
        return date.fromisoformat(self.data["today"])

    # --- reads ---------------------------------------------------------------------
    def issue(self, issue_id: str | None = None) -> dict:
        issue_id = issue_id or self.data["active_issue_id"]
        issue = self.data["issues"].get(issue_id)
        if issue is None:
            raise KeyError(f"Unknown issue {issue_id!r}")
        return issue

    def active_issue(self) -> dict:
        return self.issue(self.data["active_issue_id"])

    def appliance(self, appliance_id: str) -> dict | None:
        return self.data["appliances"].get(appliance_id)

    def property(self, property_id: str) -> dict | None:
        return self.data["properties"].get(property_id)

    def resident(self, resident_id: str) -> dict | None:
        return self.data["residents"].get(resident_id)

    def engineer(self, engineer_id: str) -> dict | None:
        return self.data["engineers"].get(engineer_id)

    def engineer_for_property(self, property_id: str) -> dict | None:
        prop = self.property(property_id)
        return self.engineer(prop["assigned_engineer_id"]) if prop else None

    def property_manager(self, property_id: str) -> dict | None:
        return self.data["property_managers"].get(property_id)

    def inventory(self, sku: str) -> dict | None:
        return self.data["inventory"].get(sku)

    def inventory_for_type(self, appliance_type: str) -> list[dict]:
        return [i for i in self.data["inventory"].values()
                if i["appliance_type"] == appliance_type]

    def similar_issues(self, appliance_type: str) -> list[dict]:
        return [h for h in self.data["historical_issues"]
                if h["appliance_type"] == appliance_type]

    # --- derived -------------------------------------------------------------------
    def appliance_age_years(self, appliance: dict) -> float:
        installed = date.fromisoformat(appliance["installation_date"])
        return round((self.today - installed).days / 365.25, 2)

    def warranty(self, appliance: dict) -> dict:
        installed = date.fromisoformat(appliance["installation_date"])
        months = appliance.get("warranty_months", 0)
        expiry = installed + timedelta(days=int(months * 30.44))
        in_warranty = expiry >= self.today
        return {
            "in_warranty": in_warranty,
            "expiry": expiry.isoformat(),
            "oem": appliance.get("oem"),
            "warranty_months": months,
        }

    # --- writes --------------------------------------------------------------------
    def append_conversation(self, role: str, text: str, channel: str = "whatsapp") -> None:
        self.data["conversation_log"].append({
            "at": datetime.utcnow().isoformat() + "Z",
            "issue_id": self.data.get("active_issue_id"),
            "channel": channel, "role": role, "text": text,
        })
        self.save()

    def add_ops_request(self, request: str, category: str) -> dict:
        entry = {"issue_id": self.data.get("active_issue_id"), "category": category,
                 "request": request, "at": datetime.utcnow().isoformat() + "Z"}
        self.data["ops_queue"].append(entry)
        self.save()
        return entry

    def add_email(self, to: str, subject: str, body: str) -> dict:
        entry = {"to": to, "subject": subject, "body": body,
                 "at": datetime.utcnow().isoformat() + "Z"}
        self.data["email_outbox"].append(entry)
        self.save()
        return entry

    def add_engineer_message(self, engineer_id: str, message: str) -> dict:
        entry = {"engineer_id": engineer_id, "message": message,
                 "at": datetime.utcnow().isoformat() + "Z"}
        self.data["engineer_outbox"].append(entry)
        self.save()
        return entry

    def add_approval(self, kind: str, decision: str, actor: str, note: str = "") -> dict:
        entry = {"issue_id": self.data.get("active_issue_id"), "kind": kind,
                 "decision": decision, "actor": actor, "note": note,
                 "at": datetime.utcnow().isoformat() + "Z"}
        self.data["approvals"].append(entry)
        self.save()
        return entry

    def add_visit(self, visit: dict) -> dict:
        self.active_issue()["visits"].append(visit)
        self.save()
        return visit


STORE = Store()
