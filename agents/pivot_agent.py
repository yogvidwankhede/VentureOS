from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import json
import re

load_dotenv()


def _safe_text(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return ", ".join(item for item in (_safe_text(v) for v in value) if item)
    if isinstance(value, dict):
        return ", ".join(item for item in (_safe_text(v) for v in value.values()) if item)
    return str(value).strip()


def _clean_model_response(text):
    cleaned = re.sub(r"```(?:json)?", "", text or "", flags=re.IGNORECASE).replace("```", "").strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}") + 1
    if start != -1 and end > start:
        cleaned = cleaned[start:end]
    return cleaned


def _extract_customer(idea, market):
    market_customer = _safe_text(market.get("target_customer") or market.get("customer"))
    if market_customer:
        return market_customer

    match = re.search(r"\bfor\s+([^,.]+)", idea, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip()

    match = re.search(r"\bto\s+([^,.]+)", idea, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip()

    return "an underserved customer segment"


def _extract_problem(idea, market):
    return (
        _safe_text(market.get("pain_point"))
        or _safe_text(market.get("opportunity_summary"))
        or f"The current version of {idea.strip()} is not yet differentiated enough."
    )


def _extract_whitespace(competitors):
    whitespace = _safe_text(competitors.get("whitespace"))
    if whitespace:
        return whitespace

    competitors_list = competitors.get("competitors") or []
    weaknesses = []
    for competitor in competitors_list[:3]:
        weak = _safe_text(competitor.get("weakness"))
        if weak:
            weaknesses.append(weak)
    if weaknesses:
        return "; ".join(weaknesses)

    return "buyers still want something narrower, more trusted, and easier to adopt."


def _extract_low_dimensions(scorecard):
    lows = []
    for entry in scorecard.get("scores") or []:
        if not isinstance(entry, dict):
            continue
        dimension = _safe_text(entry.get("dimension"))
        try:
            score = float(entry.get("score", 0))
        except (TypeError, ValueError):
            continue
        if dimension and score <= 14:
            lows.append(dimension)
    return lows


def _detect_sector(idea, market, competitors):
    combined = " ".join(
        part
        for part in (
            idea,
            _safe_text(market),
            _safe_text(competitors),
        )
        if part
    ).lower()

    keyword_map = {
        "medical": ["medical", "med school", "doctor", "clinical", "patient", "hospital", "board prep", "residency"],
        "climate": ["carbon", "climate", "emissions", "sustainability", "sustainable", "footprint", "esg"],
        "housing": ["sublease", "subleaser", "apartment", "housing", "rent", "rental", "student housing"],
        "gaming": ["game", "gaming", "gamer", "indie dev", "indie game", "studio", "creator"],
        "education": ["tutor", "learning", "education", "students", "school", "course", "exam"],
        "restaurant": ["restaurant", "inventory", "food", "kitchen", "hospitality"],
        "fintech": ["finance", "payments", "bank", "invoice", "payroll", "accounting", "credit"],
    }
    for sector, keywords in keyword_map.items():
        if any(keyword in combined for keyword in keywords):
            return sector
    return "general"


SECTOR_GUIDANCE = {
    "medical": {
        "buyer": "medical schools, residency programs, and board-prep providers",
        "workflow": "board prep, spaced repetition, and weak-topic remediation",
        "service": "clinical outcomes analytics and premium tutoring support",
        "example_a": "AMBOSS",
        "example_b": "Boards & Beyond",
        "example_c": "Osmosis",
    },
    "climate": {
        "buyer": "multi-location SMBs, accountants, and sustainability consultants",
        "workflow": "expense ingestion, emissions categorization, and supplier nudges",
        "service": "reporting workflows, audit support, and benchmarking data",
        "example_a": "Watershed",
        "example_b": "Normative",
        "example_c": "Sweep",
    },
    "housing": {
        "buyer": "campuses, student housing operators, and property managers",
        "workflow": "verified listing intake, trust checks, and fast matching",
        "service": "verification services and premium placement for supply partners",
        "example_a": "Student.com",
        "example_b": "Airbnb",
        "example_c": "Zillow",
    },
    "gaming": {
        "buyer": "indie studios, accelerators, and creator communities",
        "workflow": "launch prep, asset discovery, and release coordination",
        "service": "creator commerce, analytics, and premium partner bundles",
        "example_a": "Unity Asset Store",
        "example_b": "Patreon",
        "example_c": "Itch.io",
    },
    "education": {
        "buyer": "schools, bootcamps, cohort operators, and tutoring businesses",
        "workflow": "lesson planning, progress tracking, and weak-skill reinforcement",
        "service": "teacher dashboards, assessment analytics, and premium support",
        "example_a": "Duolingo",
        "example_b": "Khan Academy",
        "example_c": "Quizlet",
    },
    "restaurant": {
        "buyer": "restaurant groups, operators, and back-office finance teams",
        "workflow": "inventory forecasting, reorder timing, and waste reduction",
        "service": "benchmarking, managed onboarding, and supplier integrations",
        "example_a": "Toast",
        "example_b": "Square",
        "example_c": "MarginEdge",
    },
    "fintech": {
        "buyer": "finance teams, SMB operators, and channel partners",
        "workflow": "cash tracking, approvals, and reconciliation",
        "service": "embedded finance, risk insights, and premium advisory",
        "example_a": "Brex",
        "example_b": "Ramp",
        "example_c": "Mercury",
    },
    "general": {
        "buyer": "teams already serving this audience",
        "workflow": "one high-frequency job with clear ROI",
        "service": "managed onboarding, benchmarks, and premium workflows",
        "example_a": "Notion",
        "example_b": "Figma",
        "example_c": "HubSpot",
    },
}


def _make_pivot_set(idea, market, competitors, scorecard):
    sector = _detect_sector(idea, market, competitors)
    guidance = SECTOR_GUIDANCE.get(sector, SECTOR_GUIDANCE["general"])
    customer = _extract_customer(idea, market)
    problem = _extract_problem(idea, market)
    whitespace = _extract_whitespace(competitors)
    risk = _safe_text(scorecard.get("biggest_risk")) or "The concept risks feeling too generic."
    strength = _safe_text(scorecard.get("biggest_strength")) or "The pain point is real enough to support a sharper angle."
    low_dimensions = [dim.lower() for dim in _extract_low_dimensions(scorecard)]

    institution_title = {
        "medical": "Institution-Led Board Prep",
        "climate": "Accountant-Led Carbon OS",
        "housing": "Campus Housing Command",
        "gaming": "Studio Partnership Platform",
        "education": "School-Sponsored Tutor Stack",
    }.get(sector, "Channel-Led Adoption Model")

    wedge_title = {
        "medical": "Clinical Mastery Wedge",
        "climate": "Receipt-to-Carbon Wedge",
        "housing": "Verified Sublease Match",
        "gaming": "Launch Workflow Toolkit",
        "education": "Outcome-Focused Tutor Wedge",
    }.get(sector, "Single Workflow Wedge")

    service_title = {
        "medical": "Outcomes Analytics Layer",
        "climate": "Reporting Concierge Layer",
        "housing": "Trust + Verification Network",
        "gaming": "Creator Commerce Layer",
        "education": "Assessment Intelligence Layer",
    }.get(sector, "Services + Data Layer")

    pivots = [
        {
            "title": institution_title,
            "description": (
                f"Reposition {idea.strip()} as a platform sold to {guidance['buyer']} instead of only selling directly to {customer}. "
                f"End users still get the core experience, but the buyer receives admin visibility, onboarding support, and clearer ROI."
            ),
            "why": (
                f"This pivot directly addresses adoption risk by borrowing trusted distribution and makes the concept easier to justify commercially. "
                f"It also turns the current whitespace into a channel advantage: {whitespace}"
            ),
            "target_customer": guidance["buyer"],
            "revenue_model": "Annual team licenses plus onboarding and premium seats",
            "difficulty": "Medium",
            "potential": "Very High" if "revenue potential" in low_dimensions or "market size" in low_dimensions else "High",
            "example": guidance["example_a"],
            "_fit": 3 if any(tag in low_dimensions for tag in ("revenue potential", "market size", "timing & trends")) else 2,
        },
        {
            "title": wedge_title,
            "description": (
                f"Narrow the product to one urgent workflow: {guidance['workflow']}. "
                f"That makes the first version easier to trust, easier to explain, and faster to prove with measurable outcomes."
            ),
            "why": (
                f"This reduces the risk that the idea feels generic or overbuilt. "
                f"It sharpens differentiation around the actual problem: {problem}"
            ),
            "target_customer": customer,
            "revenue_model": "Premium subscription with advanced workflow add-ons",
            "difficulty": "Easy" if "feasibility" in low_dimensions else "Medium",
            "potential": "High",
            "example": guidance["example_b"],
            "_fit": 3 if any(tag in low_dimensions for tag in ("differentiation", "feasibility")) else 2,
        },
        {
            "title": service_title,
            "description": (
                f"Layer a higher-value service or analytics product on top of the core experience, focused on {guidance['service']}. "
                f"This creates a defensible premium tier instead of relying only on basic end-user subscription revenue."
            ),
            "why": (
                f"This pivot strengthens monetization and defensibility while building on the existing strength: {strength} "
                f"It also helps offset the biggest risk: {risk}"
            ),
            "target_customer": f"{customer} plus enterprise partners that need visibility and workflow support",
            "revenue_model": "Platform fee plus premium analytics, services, or enterprise contracts",
            "difficulty": "Hard",
            "potential": "Very High" if "revenue potential" in low_dimensions else "High",
            "example": guidance["example_c"],
            "_fit": 3 if "revenue potential" in low_dimensions else 2,
        },
    ]

    recommendation = max(pivots, key=lambda pivot: pivot["_fit"])
    clean_pivots = []
    for pivot in pivots:
        pivot = dict(pivot)
        pivot.pop("_fit", None)
        clean_pivots.append(pivot)

    return {
        "pivots": clean_pivots,
        "recommendation": (
            f"Start with {recommendation['title']}. It most directly fixes the current weak points in the scorecard while preserving the strongest part of the idea. "
            f"Once that wedge works, you can expand into the other pivot paths with much less risk."
        ),
        "source": "local-fallback",
    }


def run_pivot_suggester(idea: str, market: dict, competitors: dict, scorecard: dict, llm) -> dict:
    prompt = ChatPromptTemplate.from_template("""
You are a seasoned startup strategist who has helped hundreds of founders find their winning pivot.

Original idea: {idea}
Market research: {market}
Competitor landscape: {competitors}
Fundability scorecard: {scorecard}

Based on the weaknesses revealed in the scorecard and the gaps in the competitor landscape,
suggest 3 strategic pivots that could make this idea significantly stronger.

Each pivot should be meaningfully different — not just a small tweak.
Think: different customer segment, different business model, different distribution channel,
adjacent problem, or completely different monetization approach.

Return ONLY valid JSON with no markdown, no backticks, no explanation:
{{
  "pivots": [
    {{
      "title": "short catchy name for the pivot (4-6 words)",
      "description": "what the pivoted idea looks like in 2 sentences",
      "why": "why this pivot addresses the original idea's weaknesses",
      "target_customer": "who this pivot serves",
      "revenue_model": "how this pivot makes money",
      "difficulty": "Easy | Medium | Hard",
      "potential": "Low | Medium | High | Very High",
      "example": "a real company that succeeded with a similar pivot"
    }}
  ],
  "recommendation": "which pivot you recommend most and why in 2 sentences"
}}
""")

    fallback = _make_pivot_set(idea, market or {}, competitors or {}, scorecard or {})

    if llm is None:
        return fallback

    try:
        chain = prompt | llm
        response = chain.invoke({
            "idea": idea,
            "market": json.dumps(market or {}),
            "competitors": json.dumps(competitors or {}),
            "scorecard": json.dumps(scorecard or {})
        })
        parsed = json.loads(_clean_model_response(getattr(response, "content", "")))
        if not isinstance(parsed, dict) or not parsed.get("pivots"):
            return fallback
        parsed.setdefault("source", "llm")
        return parsed
    except Exception as exc:
        print(f"[pivot_agent fallback] {exc}")
        return fallback
