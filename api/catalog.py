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

# Housing charges (per property, after the operator approves the client's request):
#  - CUSTOM (client's own link): an accompanied viewing — a runner goes & films it.
#  - CATALOG (our listing, already has photos/video): just the paperwork/arrangement,
#    no physical viewing needed.
VIEWING_PRICE = 30      # custom-link viewing
ARRANGEMENT_PRICE = 100  # catalog listing arrangement

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

# Steps AUTO-assigned to the client's runner (the airport meet is the only
# in-person work a runner always does). Everything else is manager work by
# default; the operator can still hand a specific task to a runner by hand.
RUNNER_STEPS = {"airportMeet", "transfer"}

# No service auto-assigns to a runner anymore. Airport services expand into the
# airportMeet + transfer STEPS below (so a standalone airport buy behaves exactly
# like the meet package's arrival), everything else is manager work.
RUNNER_SERVICES: set[str] = set()

# Standalone airport services → the two arrival steps (dashboard points + trip).
AIRPORT_SERVICE_STEPS = {
    "airportTransport": ["airportMeet", "transfer"],
    "airportTaxi": ["airportMeet", "transfer"],
}

# What we pay a runner per completed task, keyed by step/service key (GBP). The
# operator overrides these in Admin → Runners (the `runner_fees` setting). The
# airport meet pays ONCE: £50 on airportMeet, £0 on transfer, so finishing both
# points = £50 total (not per step). Unlisted keys default to 0 until the
# operator sets a price for work they assign by hand.
RUNNER_FEES = {"airportMeet": 50, "transfer": 0}

# Keys the operator can set a runner price for (shown in the Admin → Runners fee
# table). The airport meet is auto-assigned; the rest are work the operator may
# hand to a runner (viewings, move-in, moving, area scouting, temp housing).
RUNNER_FEE_KEYS = ["airportMeet", "transfer", "viewings", "moveIn",
                   "moving", "tempHousing", "neighborhood"]

# Legacy flat fee (kept as the ultimate fallback / migration default).
RUNNER_VISIT_FEE = 15

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
