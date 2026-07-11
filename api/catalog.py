"""Single source of truth for packages, services and how a package expands
into a relocation path (must stay in sync with the frontend `app/lib/data.ts`)."""

SERVICE_PRICE = {
    "airportTransport": 99,
    "airportTaxi": 228,
    "sim": 15,
    "oyster": 15,
    # NOTE: home matching/shortlisting is FREE — viewings are charged per property
    # (VIEWING_PRICE) via /me/housing/<id>/viewing, not as a catalog service.
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

# One accompanied property viewing (charged per property from the housing shortlist).
VIEWING_PRICE = 30

# Bundle prices (discounted vs. buying the included services à la carte).
PACKAGE_AMOUNT = {"meet": 114, "housing": 299, "premium": 647}

# Intent-based packages (NOT cumulative): each matches one need. "Housing" has no
# airport pickup — a home seeker may already be in London. Premium is the full
# turnkey. Keys match Profile.steps.<key> in the frontend messages (cabinet path).
PACKAGE_STEPS = {
    "meet": ["airportMeet", "transfer"],
    "housing": [
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
