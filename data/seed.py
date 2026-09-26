"""Builds the mocked Iterum IQ data layer (PRD section 4.2).

Mirrors IQ's visits-nested-within-issues model so the agent logic would transfer if it
were ever pointed at production. Properties, operators, appliance brands/models and
supply-chain partners are real Iterum names taken from Issue Category Analysis.xlsx and
the onboarding CSVs. Individual people - residents, engineers, property managers - are
invented; there is no source data for them and no reason to use real ones.
"""

import json
from datetime import date, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent
STORE = DATA_DIR / "store.json"
TAXONOMY = DATA_DIR / "taxonomy.json"

TODAY = date(2026, 9, 11)


def _iso(d):
    return d.isoformat()


def _years_ago(n, months=0):
    return _iso(TODAY - timedelta(days=int(n * 365.25 + months * 30.4)))


def build_world():
    """The static world: properties, residents, appliances, engineers, stock."""

    properties = {
        "prop_bmy": {
            "id": "prop_bmy",
            "name": "Box Makers Yard",
            "operator": "Urbanbubble",
            "address": "Avon Street, Bristol",
            "postcode": "BS2 0PT",
            "assigned_engineer_id": "eng_dad_01",
            "access_notes": "Concierge holds keys. Engineers must sign in at the ground-floor desk.",
        },
        "prop_hawkings": {
            "id": "prop_hawkings",
            "name": "The Hawkings",
            "operator": "Allsop",
            "address": "Sweet Street, Leeds",
            "postcode": "LS11 9DB",
            "assigned_engineer_id": "eng_glotech_01",
            "access_notes": "No concierge. Resident must be home; 1hr arrival window.",
        },
        "prop_equinox": {
            "id": "prop_equinox",
            "name": "Equinox",
            "operator": "Verv Life",
            "address": "Chester Road, Manchester",
            "postcode": "M15 4ZY",
            "assigned_engineer_id": "eng_ad_01",
            "access_notes": "Loading bay booking required for replacements.",
        },
        "prop_canalside": {
            "id": "prop_canalside",
            "name": "One Canalside",
            "operator": "Urbanbubble",
            "address": "Sheepcote Street, Birmingham",
            "postcode": "B16 8AE",
            "assigned_engineer_id": "eng_dad_01",
            "access_notes": "Service lift booking needed for anything larger than a hob.",
        },
    }

    # Supply-chain partners are real Iterum partners; the named individuals are fictional.
    engineers = {
        "eng_dad_01": {
            "id": "eng_dad_01",
            "name": "Marcus Ellery",
            "partner": "DAD (Domestic Appliance Installations)",
            "phone": "+44 7700 900142",
            "properties": ["prop_bmy", "prop_canalside"],
            "service_days": ["Tuesday", "Thursday"],
        },
        "eng_glotech_01": {
            "id": "eng_glotech_01",
            "name": "Priya Raman",
            "partner": "Glotech",
            "phone": "+44 7700 900318",
            "properties": ["prop_hawkings"],
            "service_days": ["Monday", "Wednesday", "Friday"],
        },
        "eng_ad_01": {
            "id": "eng_ad_01",
            "name": "Tomas Novak",
            "partner": "Appliances Direct",
            "phone": "+44 7700 900577",
            "properties": ["prop_equinox"],
            "service_days": ["Wednesday", "Friday"],
        },
    }

    residents = {
        "res_001": {"id": "res_001", "name": "Aisha Bello", "phone": "+44 7700 900201",
                    "flat": "0704", "property_id": "prop_bmy"},
        "res_002": {"id": "res_002", "name": "Daniel Okonkwo", "phone": "+44 7700 900233",
                    "flat": "1102", "property_id": "prop_hawkings"},
        "res_003": {"id": "res_003", "name": "Fiona Wright", "phone": "+44 7700 900264",
                    "flat": "0316", "property_id": "prop_equinox"},
        "res_004": {"id": "res_004", "name": "Sam Achterberg", "phone": "+44 7700 900295",
                    "flat": "0208", "property_id": "prop_canalside"},
        "res_005": {"id": "res_005", "name": "Leila Haddad", "phone": "+44 7700 900311",
                    "flat": "0905", "property_id": "prop_bmy"},
        "res_006": {"id": "res_006", "name": "George Mbeki", "phone": "+44 7700 900347",
                    "flat": "0411", "property_id": "prop_canalside"},
        "res_007": {"id": "res_007", "name": "Ruth Castellano", "phone": "+44 7700 900388",
                    "flat": "1408", "property_id": "prop_hawkings"},
        "res_008": {"id": "res_008", "name": "Nadia Kowalczyk", "phone": "+44 7700 900412",
                    "flat": "0617", "property_id": "prop_hawkings"},
    }

    property_managers = {
        "prop_bmy": {"name": "Chloe Danvers", "email": "chloe.danvers@urbanbubble.example.co.uk"},
        "prop_hawkings": {"name": "Ian Rutherford", "email": "ian.rutherford@allsop.example.co.uk"},
        "prop_equinox": {"name": "Marta Oyelaran", "email": "marta.oyelaran@vervlife.example.co.uk"},
        "prop_canalside": {"name": "Chloe Danvers", "email": "chloe.danvers@urbanbubble.example.co.uk"},
    }

    # Real brands and model numbers drawn from Iterum's onboarding appliance CSVs.
    appliances = {
        "app_001": {
            "id": "app_001", "property_id": "prop_bmy", "flat": "0704",
            "appliance_type": "Dishwasher", "brand": "Bosch", "model": "SMV2ITX18G",
            "serial": "DW-SN-4471", "installation_date": _years_ago(2, 3),
            "warranty_months": 24, "oem": "BSH Home Appliances",
            "retail_price": 429.00, "iterum_price": 331.00,
        },
        "app_002": {
            "id": "app_002", "property_id": "prop_hawkings", "flat": "1102",
            "appliance_type": "Washer-Dryer", "brand": "Zanussi", "model": "ZWD86SB4PW",
            "serial": "WD-SN-1180", "installation_date": _years_ago(3, 5),
            "warranty_months": 24, "oem": "Electrolux",
            "retail_price": 549.00, "iterum_price": 438.00,
        },
        "app_003": {
            "id": "app_003", "property_id": "prop_equinox", "flat": "0316",
            "appliance_type": "Oven", "brand": "Hotpoint", "model": "SA2540HIX",
            "serial": "OV-SN-8802", "installation_date": _years_ago(9, 1),
            "warranty_months": 12, "oem": "Whirlpool",
            "retail_price": 419.00, "iterum_price": 338.00,
        },
        "app_004": {
            "id": "app_004", "property_id": "prop_canalside", "flat": "0208",
            "appliance_type": "Fridge-Freezer", "brand": "Bosch", "model": "KGN34NWEAG",
            "serial": "FF-SN-2245", "installation_date": _years_ago(0, 8),
            "warranty_months": 24, "oem": "BSH Home Appliances",
            "retail_price": 599.00, "iterum_price": 471.00,
        },
        "app_005": {
            "id": "app_005", "property_id": "prop_bmy", "flat": "0905",
            "appliance_type": "Hob", "brand": "CDA", "model": "HN6111FR",
            "serial": "HB-SN-6610", "installation_date": _years_ago(4, 2),
            "warranty_months": 24, "oem": "CDA Appliances",
            "retail_price": 389.00, "iterum_price": 305.00,
        },
        "app_006": {
            "id": "app_006", "property_id": "prop_canalside", "flat": "0411",
            "appliance_type": "Oven", "brand": "Beko", "model": "BBIF22300X",
            "serial": "OV-SN-3390", "installation_date": _years_ago(5, 0),
            "warranty_months": 24, "oem": "Beko plc",
            "retail_price": 329.00, "iterum_price": 259.00,
        },
        "app_007": {
            "id": "app_007", "property_id": "prop_hawkings", "flat": "1408",
            "appliance_type": "Hob", "brand": "Zanussi", "model": "ZITN644K",
            "serial": "HB-SN-9924", "installation_date": _years_ago(3, 8),
            "warranty_months": 24, "oem": "Electrolux",
            "retail_price": 359.00, "iterum_price": 284.00,
        },
        # Module 3 step 5 (new_fault_info). Same real model as app_004, older and out of
        # warranty, so the re-assessment has an age question to weigh.
        "app_008": {
            "id": "app_008", "property_id": "prop_hawkings", "flat": "0617",
            "appliance_type": "Fridge-Freezer", "brand": "Bosch", "model": "KGN34NWEAG",
            "serial": "FF-SN-3071", "installation_date": _years_ago(6, 4),
            "warranty_months": 24, "oem": "BSH Home Appliances",
            "retail_price": 599.00, "iterum_price": 471.00,
        },
    }

    inventory = {
        "SKU-DW-DRAINPUMP": {"sku": "SKU-DW-DRAINPUMP", "description": "Dishwasher drain pump assembly",
                             "appliance_type": "Dishwasher", "stock": 6, "lead_time_days": 0},
        "SKU-WD-PUMP": {"sku": "SKU-WD-PUMP", "description": "Washer-dryer drain pump + filter housing",
                        "appliance_type": "Washer-Dryer", "stock": 4, "lead_time_days": 0},
        "SKU-WD-DOORSEAL": {"sku": "SKU-WD-DOORSEAL", "description": "Washer-dryer door seal",
                            "appliance_type": "Washer-Dryer", "stock": 2, "lead_time_days": 0},
        "SKU-OV-ELEMENT": {"sku": "SKU-OV-ELEMENT", "description": "Oven fan element 2000W",
                           "appliance_type": "Oven", "stock": 3, "lead_time_days": 0},
        "SKU-OV-DOORHINGE": {"sku": "SKU-OV-DOORHINGE", "description": "Oven door hinge pair",
                             "appliance_type": "Oven", "stock": 5, "lead_time_days": 0},
        "SKU-HOB-INDMOD": {"sku": "SKU-HOB-INDMOD", "description": "Induction generator module (single zone)",
                           "appliance_type": "Hob", "stock": 0, "lead_time_days": 9},
        "SKU-FF-THERMOSTAT": {"sku": "SKU-FF-THERMOSTAT", "description": "Fridge-freezer thermostat",
                              "appliance_type": "Fridge-Freezer", "stock": 4, "lead_time_days": 0},
        "SKU-FF-FANMOTOR": {"sku": "SKU-FF-FANMOTOR", "description": "Fridge-freezer evaporator fan motor",
                            "appliance_type": "Fridge-Freezer", "stock": 3, "lead_time_days": 0},
        "SKU-DW-DOORSPRING": {"sku": "SKU-DW-DOORSPRING", "description": "Dishwasher door hinge spring and cable kit",
                              "appliance_type": "Dishwasher", "stock": 5, "lead_time_days": 0},
        "SKU-HOOD-FANMOTOR": {"sku": "SKU-HOOD-FANMOTOR", "description": "Extractor hood fan motor",
                              "appliance_type": "Hood", "stock": 1, "lead_time_days": 0},
    }

    return {
        "today": _iso(TODAY),
        "properties": properties,
        "engineers": engineers,
        "residents": residents,
        "property_managers": property_managers,
        "appliances": appliances,
        "inventory": inventory,
        "taxonomy": json.loads(TAXONOMY.read_text()),
        "issues": {},
        "approvals": [],
        "conversation_log": [],
        "ops_queue": [],
        "email_outbox": [],
        "engineer_outbox": [],
    }


def historical_issues():
    """Closed jobs that search_similar_issues() reads. Comparable outcomes are what the
    decision-analysis loop leans on, so these carry real outcomes and costs."""
    return [
        {"appliance_type": "Dishwasher", "fault_slug": "dishwasher_not_draining",
         "brand": "Bosch", "age_years": 2.0, "outcome": "Repair",
         "repair_cost": 95.0, "notes": "Blocked filter and debris in sump. Resolved on first visit."},
        {"appliance_type": "Dishwasher", "fault_slug": "dishwasher_not_draining",
         "brand": "Zanussi", "age_years": 1.5, "outcome": "Resolved without visit",
         "repair_cost": 0.0, "notes": "Resident cleared filter after phone guidance."},
        {"appliance_type": "Washer-Dryer", "fault_slug": "washer_dryer_not_draining",
         "brand": "Zanussi", "age_years": 3.0, "outcome": "Repair",
         "repair_cost": 165.0, "notes": "Drain pump replaced. Single visit."},
        {"appliance_type": "Washer-Dryer", "fault_slug": "washer_dryer_leak",
         "brand": "Beko", "age_years": 4.0, "outcome": "Repair",
         "repair_cost": 140.0, "notes": "Door seal perished; replaced."},
        {"appliance_type": "Oven", "fault_slug": "oven_not_heating",
         "brand": "Hotpoint", "age_years": 8.0, "outcome": "Repair to Replacement",
         "repair_cost": 0.0, "replacement_cost": 402.0,
         "notes": "Attended as repair. Element and thermostat both failed, cavity corrosion. "
                  "Condemned on site; replacement ordered. Two extra weeks to resolve."},
        {"appliance_type": "Oven", "fault_slug": "oven_not_heating",
         "brand": "Hotpoint", "age_years": 9.5, "outcome": "Replacement",
         "replacement_cost": 418.0, "notes": "Beyond economic repair on inspection."},
        {"appliance_type": "Oven", "fault_slug": "oven_not_heating",
         "brand": "Zanussi", "age_years": 3.0, "outcome": "Repair",
         "repair_cost": 120.0, "notes": "Fan element replaced."},
        {"appliance_type": "Oven", "fault_slug": "oven_door_issue",
         "brand": "Beko", "age_years": 5.0, "outcome": "Repair",
         "repair_cost": 110.0, "notes": "Hinge pair replaced, door reseated."},
        {"appliance_type": "Hob", "fault_slug": "hob_single_zone_fault",
         "brand": "CDA", "age_years": 4.0, "outcome": "Repair",
         "repair_cost": 185.0, "notes": "Induction generator module for the affected zone replaced. "
                                        "Part was not held in stock; 9 day wait."},
        {"appliance_type": "Fridge-Freezer", "fault_slug": "fridge_not_cooling",
         "brand": "Bosch", "age_years": 0.5, "outcome": "OEM warranty",
         "notes": "In warranty. Handled by BSH engineer, not Iterum."},
        # Module 3 step 5 scenarios: comparables for the new fault categories.
        {"appliance_type": "Fridge-Freezer", "fault_slug": "fridge_not_cooling",
         "brand": "Bosch", "age_years": 5.5, "outcome": "Repair",
         "repair_cost": 175.0, "notes": "Evaporator fan motor seized. Replaced; cooling restored."},
        {"appliance_type": "Fridge-Freezer", "fault_slug": "fridge_not_cooling",
         "brand": "Hotpoint", "age_years": 7.0, "outcome": "Replacement",
         "replacement_cost": 560.0, "notes": "Compressor cutting out on thermal overload, "
                                             "both compartments warming. Beyond economic repair."},
        {"appliance_type": "Dishwasher", "fault_slug": "dishwasher_door_issue",
         "brand": "Bosch", "age_years": 3.0, "outcome": "Repair",
         "repair_cost": 85.0, "notes": "Door hinge spring snapped; spring and cable kit fitted."},
    ]


def build(scenario=None):
    world = build_world()
    world["historical_issues"] = historical_issues()
    if scenario:
        world["issues"][scenario["issue"]["id"]] = scenario["issue"]
        world["active_issue_id"] = scenario["issue"]["id"]
        world["scenario"] = {k: v for k, v in scenario.items() if k != "issue"}
    return world


def write(world):
    STORE.write_text(json.dumps(world, indent=2) + "\n")
    return STORE


if __name__ == "__main__":
    w = build()
    write(w)
    print(f"Seeded {STORE}")
    print(f"  {len(w['properties'])} properties, {len(w['appliances'])} appliances, "
          f"{len(w['engineers'])} engineers, {len(w['inventory'])} stock lines, "
          f"{len(w['historical_issues'])} historical jobs")
