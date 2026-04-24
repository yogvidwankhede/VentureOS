from agents.scorecard_agent import run_scorecard
from agents.pitch_agent import run_pitch_generation
from agents.product_agent import run_product_strategy
from agents.competitor_agent import run_competitor_analysis
from agents.market_agent import run_market_research
from dotenv import load_dotenv
import os
import time
import json

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:  # pragma: no cover - optional provider
    ChatGoogleGenerativeAI = None

try:
    from langchain_groq import ChatGroq
except ImportError:  # pragma: no cover - optional provider
    ChatGroq = None

load_dotenv()


DEFAULT_PROVIDER = os.getenv("VENTUREOS_LLM_PROVIDER", "auto").strip().lower() or "auto"
DEFAULT_GOOGLE_MODEL = os.getenv("VENTUREOS_GOOGLE_MODEL", "gemini-2.5-flash-lite").strip() or "gemini-2.5-flash-lite"
DEFAULT_GROQ_MODEL = os.getenv("VENTUREOS_GROQ_MODEL", "llama-3.1-8b-instant").strip() or "llama-3.1-8b-instant"
DEFAULT_TEMPERATURE = float(os.getenv("VENTUREOS_LLM_TEMPERATURE", "0.45"))
STREAM_DELAY_SECONDS = float(os.getenv("VENTUREOS_STREAM_DELAY_SECONDS", "0"))
RETRY_DELAY_SECONDS = float(os.getenv("VENTUREOS_RETRY_DELAY_SECONDS", "2"))
QUOTA_ERROR_MARKERS = (
    "429",
    "quota",
    "resource_exhausted",
    "rate limit",
    "rate_limit",
    "too many requests",
    "exceeded your current quota",
)


def _build_google_llm():
    google_api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    if not google_api_key:
        raise RuntimeError("GOOGLE_API_KEY is not configured")
    if ChatGoogleGenerativeAI is None:
        raise RuntimeError("langchain-google-genai is not installed")
    llm = ChatGoogleGenerativeAI(
        model=DEFAULT_GOOGLE_MODEL,
        google_api_key=google_api_key,
        temperature=DEFAULT_TEMPERATURE,
    )
    setattr(llm, "_ventureos_provider", "google")
    return llm


def _build_groq_llm():
    groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not groq_api_key:
        raise RuntimeError("GROQ_API_KEY is not configured")
    if ChatGroq is None:
        raise RuntimeError("langchain-groq is not installed")
    llm = ChatGroq(
        model=DEFAULT_GROQ_MODEL,
        groq_api_key=groq_api_key,
        temperature=DEFAULT_TEMPERATURE,
    )
    setattr(llm, "_ventureos_provider", "groq")
    return llm


def _provider_order():
    provider = DEFAULT_PROVIDER
    google_available = bool(os.getenv("GOOGLE_API_KEY", "").strip())
    groq_available = bool(os.getenv("GROQ_API_KEY", "").strip())

    if not google_available and not groq_available:
        raise RuntimeError("No supported LLM provider is configured")

    if provider == "google":
        return ["google", "groq"]
    if provider == "groq":
        return ["groq", "google"]
    if google_available:
        return ["google", "groq"]
    return ["groq", "google"]


def get_llm(exclude_providers=None):
    excluded = set()
    if exclude_providers:
        if isinstance(exclude_providers, str):
            excluded.add(exclude_providers)
        else:
            excluded.update(exclude_providers)

    provider_builders = {
        "google": _build_google_llm,
        "groq": _build_groq_llm,
    }

    last_error = None
    for provider in _provider_order():
        if provider in excluded:
            continue
        builder = provider_builders[provider]
        try:
            return builder()
        except Exception as exc:
            last_error = exc
            print(f"[LLM init failed provider={provider}] {exc}")
    raise RuntimeError(f"Unable to initialize an LLM provider: {last_error}")


def _provider_name(llm):
    return getattr(llm, "_ventureos_provider", "unknown")


def _is_quota_or_rate_limit_error(exc):
    message = str(exc).lower()
    return any(marker in message for marker in QUOTA_ERROR_MARKERS)


def _fallback_llm(used_providers):
    try:
        return get_llm(exclude_providers=used_providers)
    except Exception as exc:
        print(f"[LLM fallback unavailable] {exc}")
        return None


def _invoke_with_resilience(label, invoke_fn, llm, retries=3):
    current_llm = llm
    used_providers = {_provider_name(current_llm)}
    last_error = None

    for attempt in range(retries):
        try:
            return invoke_fn(current_llm), current_llm
        except Exception as exc:
            last_error = exc
            provider = _provider_name(current_llm)
            print(f"[{label} attempt {attempt + 1} provider={provider}] {exc}")

            if _is_quota_or_rate_limit_error(exc):
                backup_llm = _fallback_llm(used_providers)
                if backup_llm is not None:
                    current_llm = backup_llm
                    used_providers.add(_provider_name(current_llm))
                    print(f"[{label}] Switching to backup provider={_provider_name(current_llm)}")
                    continue
                break

            if attempt < retries - 1 and RETRY_DELAY_SECONDS > 0:
                time.sleep(RETRY_DELAY_SECONDS)

    raise RuntimeError(f"{label} failed after {retries} attempts: {last_error}")


def _maybe_stream_pause():
    if STREAM_DELAY_SECONDS > 0:
        time.sleep(STREAM_DELAY_SECONDS)


def run_ventureOS_stream(idea: str):
    """Generator that yields SSE events as each agent completes"""
    llm = get_llm()

    # Market Research
    yield f"data: {json.dumps({'event': 'status', 'message': '📊 Running Market Research Agent...'})}\n\n"
    market, llm = safe_run(run_market_research, idea, llm)
    yield f"data: {json.dumps({'event': 'market_research', 'data': market})}\n\n"
    _maybe_stream_pause()

    # Competitor Analysis
    yield f"data: {json.dumps({'event': 'status', 'message': '🔍 Running Competitor Analysis Agent...'})}\n\n"
    competitors, llm = safe_run(run_competitor_analysis, idea, llm)
    yield f"data: {json.dumps({'event': 'competitor_analysis', 'data': competitors})}\n\n"
    _maybe_stream_pause()

    # Product Strategy
    yield f"data: {json.dumps({'event': 'status', 'message': '🛠️ Running Product Strategy Agent...'})}\n\n"
    product, llm = safe_run(run_product_strategy, idea, llm)
    yield f"data: {json.dumps({'event': 'product_strategy', 'data': product})}\n\n"
    _maybe_stream_pause()

    # Pitch & Emails
    yield f"data: {json.dumps({'event': 'status', 'message': '📈 Running Pitch & Outreach Agent...'})}\n\n"
    pitch, llm = safe_run_pitch(run_pitch_generation, idea,
                                market, competitors, llm)
    yield f"data: {json.dumps({'event': 'pitch', 'data': pitch})}\n\n"
    _maybe_stream_pause()

    # Scorecard
    yield f"data: {json.dumps({'event': 'status', 'message': '🎯 Running Fundability Scorecard Agent...'})}\n\n"
    scorecard, llm = safe_run_scorecard(
        run_scorecard, idea, market, competitors, product, llm)
    yield f"data: {json.dumps({'event': 'scorecard', 'data': scorecard})}\n\n"

    # Done
    yield f"data: {json.dumps({'event': 'done', 'message': 'All agents complete!'})}\n\n"


def safe_run(fn, idea, llm, retries=3):
    label = getattr(fn, "__name__", "Agent")
    return _invoke_with_resilience(
        label,
        lambda active_llm: fn(idea, active_llm),
        llm,
        retries=retries,
    )


def safe_run_pitch(fn, idea, market, competitors, llm, retries=3):
    label = getattr(fn, "__name__", "PitchAgent")
    return _invoke_with_resilience(
        label,
        lambda active_llm: fn(idea, market, competitors, active_llm),
        llm,
        retries=retries,
    )


def safe_run_scorecard(fn, idea, market, competitors, product, llm, retries=3):
    label = getattr(fn, "__name__", "ScorecardAgent")
    return _invoke_with_resilience(
        label,
        lambda active_llm: fn(idea, market, competitors, product, active_llm),
        llm,
        retries=retries,
    )
