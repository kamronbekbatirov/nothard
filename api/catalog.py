"""Single source of truth for packages, services and how a package expands
into a relocation path (must stay in sync with the frontend `app/lib/data.ts`)."""

SERVICE_PRICE = {
    "airportTransport": 99,
    "airportTaxi": 228,
    "sim": 15,
    "oyster": 15,
    "housingSearch": 38,
    "tempHousing": 38,
    "moving": 76,
    "nhs": 76,
    "support7": 76,
    "neighborhood": 38,
    "utilities": 76,
    "bankOnline": 38,
    "lease": 38,
    "docTranslate": 20,
}

# Bundle prices (discounted vs. buying the included services à la carte).
PACKAGE_AMOUNT = {"meet": 114, "housing": 342, "premium": 647}

# Cumulative tiers: each higher tier is a superset of the lower one.
# Keys match Profile.steps.<key> in the frontend messages (the cabinet timeline).
PACKAGE_STEPS = {
    "meet": ["airportMeet", "transfer"],
    "housing": [
        "airportMeet",
        "transfer",
        "tempStay",
        "housingSearch",
        "viewings",
        "lease",
        "moveIn",
    ],
    "premium": [
        "airportMeet",
        "transfer",
        "tempStay",
        "housingSearch",
        "viewings",
        "lease",
        "bank",
        "nhs",
        "moveIn",
    ],
}

# Steps that are field visits performed by a runner (get a time + address).
RUNNER_STEPS = {"airportMeet", "transfer", "viewings", "moveIn"}

# Individual services that also involve a field runner visit.
RUNNER_SERVICES = {"airportTransport", "airportTaxi", "moving", "tempHousing"}

PACKAGE_ORDER = ["meet", "housing", "premium"]


def package_rank(pkg: str) -> int:
    return PACKAGE_ORDER.index(pkg) if pkg in PACKAGE_ORDER else -1


# Documents the service actually handles — shown as a checklist in the cabinet.
# Only relevant docs appear; a SIM-only or arrival-only order has none.
DOC_FOR_PACKAGE = {
    "meet": [],
    "housing": ["lease"],
    "premium": ["lease", "bank", "nhs"],
}
DOC_FOR_SERVICE = {
    "lease": ["lease"],
    "bankOnline": ["bank"],
    "nhs": ["nhs"],
}


def docs_for_package(pkg: str) -> list[str]:
    return DOC_FOR_PACKAGE.get(pkg, [])


def docs_for_service(service_id: str) -> list[str]:
    return DOC_FOR_SERVICE.get(service_id, [])
