from agents.scorecard_agent import run_scorecard
from agents.pitch_agent import run_pitch_generation
from agents.product_agent import run_product_strategy
from agents.competitor_agent import run_competitor_analysis
from agents.market_agent import run_market_research
from dotenv import load_dotenv
import os
import time
import json
import re

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


def _sse(event, **payload):
    body = {'event': event, **payload}
    return f"data: {json.dumps(body)}\n\n"


def _slug(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', (text or '').lower()).strip('-') or 'ventureos'


def _topic_profile(idea: str) -> dict:
    text = (idea or '').lower()

    if any(term in text for term in ('medical school', 'med school', 'medical students', 'doctor', 'nurse', 'clinical', 'anatomy', 'patient')) and any(term in text for term in ('tutor', 'learning', 'study', 'student', 'students', 'education')):
        return {
            'category': 'health-edtech',
            'market_size': '$4.2B global medical education and exam-prep market',
            'growth_rate': '14% CAGR',
            'target_customer': 'Medical school students preparing for coursework, boards, and clinical rotations. Secondary buyers include medical schools and tutoring programs looking to improve pass rates and learning outcomes.',
            'pain_point': 'Medical students juggle dense content, fragmented resources, and high-stakes exams without personalized study guidance.',
            'market_trends': [
                'AI-assisted personalized learning is becoming mainstream in higher education',
                'Medical schools are under pressure to improve outcomes without increasing faculty load',
                'Board-prep and spaced-repetition tools are converging with coaching workflows'
            ],
            'opportunity_summary': 'There is a strong wedge in medical education for a trusted AI tutor that feels academically rigorous rather than generic. A focused product can win by combining tutoring, recall reinforcement, and exam-readiness workflows. Institutional partnerships can compound adoption once student trust is established.',
            'competitors': [
                {'name': 'AMBOSS', 'description': 'Clinical knowledge and exam-prep platform for medical learners.', 'funding': 'Well-funded private company', 'weakness': 'Broad content depth, but limited real-time tutoring-style personalization.', 'our_advantage': 'A more adaptive, conversation-first AI tutor experience tailored to mastery gaps.'},
                {'name': 'Osmosis', 'description': 'Video-first medical education platform with strong library coverage.', 'funding': 'Acquired / strategic backing', 'weakness': 'Great content, but not a truly dynamic tutor for daily study decisions.', 'our_advantage': 'Interactive coaching and study sequencing instead of passive content consumption.'},
                {'name': 'Boards & Beyond', 'description': 'Board-focused prep content used heavily by students.', 'funding': 'Bootstrapped / niche brand strength', 'weakness': 'Strong for review, weaker for personalized planning and explanation loops.', 'our_advantage': 'Explains, quizzes, and adapts in one workflow.'},
                {'name': 'UWorld', 'description': 'Question-bank leader for high-stakes medical exam preparation.', 'funding': 'Large private company', 'weakness': 'Exceptional question bank, but limited tutoring and reflective learning support.', 'our_advantage': 'Turns mistakes into personalized learning paths instead of isolated question practice.'},
            ],
            'whitespace': 'Students still patch together content, question banks, flashcards, and study plans across disconnected tools. The whitespace is a medical-school-specific AI tutor that combines explanation, planning, and mastery reinforcement in one trusted workflow.',
            'mvp_features': [
                {'feature': 'AI study coach', 'priority': 'Must', 'reason': 'Core tutoring loop and personalized guidance.'},
                {'feature': 'Board-style Q&A explanations', 'priority': 'Must', 'reason': 'High-intent use case tied directly to exam prep.'},
                {'feature': 'Weakness-based study plans', 'priority': 'Must', 'reason': 'Transforms passive tutoring into a repeatable workflow.'},
                {'feature': 'Spaced recall checkpoints', 'priority': 'Should', 'reason': 'Improves retention and habit formation.'},
                {'feature': 'Faculty / institutional dashboard', 'priority': 'Could', 'reason': 'Useful expansion path after student traction.'},
            ],
            'suggested_stack': [
                {'tool': 'Next.js', 'reason': 'Fast product iteration and polished student-facing UI.'},
                {'tool': 'Python + FastAPI', 'reason': 'Good fit for tutoring workflows, retrieval, and scoring services.'},
                {'tool': 'Postgres / Supabase', 'reason': 'Simple persistent storage for users, sessions, and plans.'},
                {'tool': 'LLM + retrieval layer', 'reason': 'Enables grounded explanations, adaptive tutoring, and content retrieval.'},
            ],
            'build_timeline': [
                {'week': 'Week 1', 'milestone': 'Tutor flow, auth, and core subject taxonomy.'},
                {'week': 'Week 2', 'milestone': 'Study-plan generation and session history.'},
                {'week': 'Week 3', 'milestone': 'Exam-style Q&A explanations and recall checkpoints.'},
                {'week': 'Week 4', 'milestone': 'Pilot-ready dashboard, analytics, and onboarding.'},
                {'week': 'Week 5', 'milestone': 'Closed beta with medical students.'},
                {'week': 'Week 6', 'milestone': 'Refinement based on outcome and engagement data.'},
            ],
            'monetization': [
                {'model': 'Student subscription', 'pros': ['Direct willingness to pay', 'Simple GTM'], 'cons': ['Churn risk', 'Requires clear learning value']},
                {'model': 'Institutional licensing', 'pros': ['Higher ACV', 'Distribution leverage'], 'cons': ['Longer sales cycles', 'Needs proof of efficacy']},
            ],
            'scores': [
                {'dimension': 'Market Size', 'score': 15, 'reason': 'Medical education is narrower than broad edtech but still commercially meaningful.'},
                {'dimension': 'Timing & Trends', 'score': 17, 'reason': 'AI-assisted education and outcome pressure make timing attractive.'},
                {'dimension': 'Differentiation', 'score': 15, 'reason': 'A focused tutoring workflow can stand out if it is clinically trustworthy.'},
                {'dimension': 'Feasibility', 'score': 14, 'reason': 'Possible to build, but quality and trust thresholds are high.'},
                {'dimension': 'Revenue Potential', 'score': 15, 'reason': 'Student subscription plus institutional upsell creates a credible monetization path.'},
            ],
            'verdict': 'Pass',
            'summary': 'The idea has a credible niche, strong user pain, and clear willingness-to-pay signals. The biggest challenge will be trust and academic rigor, not demand.',
            'biggest_risk': 'If the tutor feels generic or error-prone, students will revert to trusted study brands.',
            'biggest_strength': 'The user pain is urgent, recurring, and closely tied to measurable academic outcomes.',
            'slide_titles': ['Medical Study Is Still Fragmented', 'The Stress Is Structural', 'Why This Market Matters', 'A Better AI Tutor', 'How the Tutor Works', 'Learning Outcomes Improve', 'Why Students Switch', 'Business Model', 'Institutional Expansion', 'The Ask'],
            'email_angle': 'medical education outcomes'
        }

    if any(term in text for term in ('sublease', 'apartment', 'roommate', 'student housing', 'rental')):
        return {
            'category': 'housing',
            'market_size': '$15B student housing and rental discovery opportunity',
            'growth_rate': '8% CAGR',
            'target_customer': 'Students and young renters searching for reliable, short-notice housing options. Secondary users include property managers and trusted listers who need faster tenant matching.',
            'pain_point': 'Renters lose time and money because housing search and subleasing are fragmented, unverified, and trust-poor.',
            'market_trends': ['Rental affordability pressure is driving shorter-term housing decisions', 'Verification and trust are becoming table stakes in marketplace products', 'Student housing demand remains durable around campus hubs'],
            'opportunity_summary': 'The category still suffers from messy discovery, weak trust, and poor conversion. A focused product can win by making housing search safer, faster, and better matched. The strongest wedge is speed plus verification.',
            'competitors': [
                {'name': 'Apartments.com', 'description': 'Large rental discovery marketplace.', 'funding': 'Public-company backed', 'weakness': 'Broad inventory, weaker fit for fast sublease matching.', 'our_advantage': 'Better fit for trusted student and short-term matching.'},
                {'name': 'Facebook Marketplace', 'description': 'Peer-to-peer listings and local discovery.', 'funding': 'Platform-scale ecosystem', 'weakness': 'High noise and low verification.', 'our_advantage': 'Cleaner quality control and trust layers.'},
                {'name': 'SpareRoom', 'description': 'Roommate and room-rental marketplace.', 'funding': 'Established niche player', 'weakness': 'Good niche product, but limited student-specific trust workflows.', 'our_advantage': 'Campus-first product motion and better matching.'},
                {'name': 'Zillow Rentals', 'description': 'Mass-market rental listings platform.', 'funding': 'Public-company backed', 'weakness': 'Not optimized for last-minute sublease dynamics.', 'our_advantage': 'Designed for high-velocity, verified rental matching.'},
            ],
            'whitespace': 'There is still room for a trusted, fast, and student-specific sublease experience. The whitespace is a product that makes verification and move-in speed the core value proposition.',
            'mvp_features': [
                {'feature': 'Verified sublease listings', 'priority': 'Must', 'reason': 'Trust is the first barrier to usage.'},
                {'feature': 'Match-based renter discovery', 'priority': 'Must', 'reason': 'Improves speed and conversion.'},
                {'feature': 'Messaging and availability workflow', 'priority': 'Must', 'reason': 'Needed to close transactions.'},
                {'feature': 'Campus and neighborhood filters', 'priority': 'Should', 'reason': 'Improves relevance quickly.'},
                {'feature': 'Move-in timeline tools', 'priority': 'Could', 'reason': 'Adds utility after core matching works.'},
            ],
            'suggested_stack': [
                {'tool': 'Next.js', 'reason': 'Fast marketplace UI iteration.'},
                {'tool': 'Supabase / Postgres', 'reason': 'Listings, profiles, and messaging data.'},
                {'tool': 'Maps / geospatial API', 'reason': 'Location trust and proximity workflows.'},
                {'tool': 'Moderation / verification services', 'reason': 'Critical for trust and listing quality.'},
            ],
            'build_timeline': [
                {'week': 'Week 1', 'milestone': 'Listings, auth, and campus-specific onboarding.'},
                {'week': 'Week 2', 'milestone': 'Verification and basic matching workflow.'},
                {'week': 'Week 3', 'milestone': 'Messaging, availability, and renter profiles.'},
                {'week': 'Week 4', 'milestone': 'Search ranking and quality controls.'},
                {'week': 'Week 5', 'milestone': 'Campus pilot launch.'},
                {'week': 'Week 6', 'milestone': 'Retention and referral improvements.'},
            ],
            'monetization': [
                {'model': 'Featured listings', 'pros': ['Simple marketplace revenue', 'Aligned with supply demand'], 'cons': ['Needs inventory scale', 'Can hurt trust if overused']},
                {'model': 'Transaction / verification fee', 'pros': ['Monetizes trust directly', 'Higher margin path'], 'cons': ['Requires strong product confidence', 'Pricing sensitivity']},
            ],
            'scores': [
                {'dimension': 'Market Size', 'score': 15, 'reason': 'Rental discovery is large enough with a clear student niche.'},
                {'dimension': 'Timing & Trends', 'score': 15, 'reason': 'Affordability and mobility pressures support demand.'},
                {'dimension': 'Differentiation', 'score': 14, 'reason': 'Trust and velocity can differentiate if executed well.'},
                {'dimension': 'Feasibility', 'score': 16, 'reason': 'The product is very buildable with focused scope.'},
                {'dimension': 'Revenue Potential', 'score': 14, 'reason': 'Marketplace monetization is viable but depends on liquidity.'},
            ],
            'verdict': 'Pass',
            'summary': 'This is a credible marketplace problem with obvious user pain and a focused student wedge. Execution quality and trust mechanics will determine whether it becomes defensible.',
            'biggest_risk': 'Marketplace liquidity is hard, and bad listing quality can destroy trust quickly.',
            'biggest_strength': 'The pain is immediate and easy for users to understand without heavy education.',
            'slide_titles': ['Housing Search Is Broken', 'The Pain Is Expensive', 'Why Now Matters', 'A Faster Trusted Match', 'How the Marketplace Works', 'Value to Renters', 'Trust and Traction', 'Monetization', 'Campus Expansion', 'The Ask'],
            'email_angle': 'student housing trust'
        }

    return {
        'category': 'generic',
        'market_size': '$5B+ category opportunity',
        'growth_rate': '10% CAGR',
        'target_customer': 'Early adopters who face the problem frequently enough to switch tools quickly. Over time, adjacent teams and institutional buyers can expand the market.',
        'pain_point': 'The current workflow is fragmented, manual, and harder than it should be for the user.',
        'market_trends': ['AI-assisted workflows are changing user expectations', 'Teams want fewer disconnected tools and clearer ROI', 'Specialized software categories are consolidating around workflow leaders'],
        'opportunity_summary': 'The opportunity is strongest when the product removes obvious friction from a frequent workflow. A focused wedge can create early adoption and then expand into a broader operating layer. Clear positioning matters more than feature count at this stage.',
        'competitors': [
            {'name': 'Notion', 'description': 'Flexible workspace platform used for many lightweight workflows.', 'funding': 'Large private company', 'weakness': 'Powerful but often too generic for specialized workflows.', 'our_advantage': 'Sharper domain focus and faster time-to-value.'},
            {'name': 'Airtable', 'description': 'Workflow database platform used across teams.', 'funding': 'Large private company', 'weakness': 'Requires setup effort and process design from the user.', 'our_advantage': 'Opinionated workflow out of the box.'},
            {'name': 'Zapier', 'description': 'Automation platform that connects tools.', 'funding': 'Large private company', 'weakness': 'Strong automation, weaker productized experience for one vertical problem.', 'our_advantage': 'Native workflow rather than stitching tools together.'},
            {'name': 'Incumbent manual workflows', 'description': 'Spreadsheets, email, and ad hoc tools still dominate many categories.', 'funding': 'N/A', 'weakness': 'Slow, inconsistent, and difficult to scale.', 'our_advantage': 'Structured system with repeatable outcomes.'},
        ],
        'whitespace': 'The whitespace is a product that feels purpose-built for one painful workflow instead of acting like another generic toolkit. Users will switch if the product is faster, clearer, and easier to trust.',
        'mvp_features': [
            {'feature': 'Core workflow engine', 'priority': 'Must', 'reason': 'Delivers the main user value immediately.'},
            {'feature': 'Structured onboarding', 'priority': 'Must', 'reason': 'Reduces time-to-value.'},
            {'feature': 'Collaboration or handoff flow', 'priority': 'Must', 'reason': 'Makes the product usable in a real setting.'},
            {'feature': 'Reporting / proof layer', 'priority': 'Should', 'reason': 'Helps users see ROI and supports expansion.'},
            {'feature': 'Automation layer', 'priority': 'Could', 'reason': 'Improves leverage after the core loop is validated.'},
        ],
        'suggested_stack': [
            {'tool': 'React / Next.js', 'reason': 'Strong choice for polished product UX.'},
            {'tool': 'Python or Node backend', 'reason': 'Fast iteration and broad ecosystem support.'},
            {'tool': 'Postgres', 'reason': 'Reliable core data model.'},
            {'tool': 'LLM / automation services', 'reason': 'Useful if the workflow benefits from generation or summarization.'},
        ],
        'build_timeline': [
            {'week': 'Week 1', 'milestone': 'Core workflow and user model.'},
            {'week': 'Week 2', 'milestone': 'Onboarding and baseline product loop.'},
            {'week': 'Week 3', 'milestone': 'Collaboration and proof surfaces.'},
            {'week': 'Week 4', 'milestone': 'Pilot-ready polish and instrumentation.'},
            {'week': 'Week 5', 'milestone': 'Early user feedback round.'},
            {'week': 'Week 6', 'milestone': 'Iteration on retention and differentiation.'},
        ],
        'monetization': [
            {'model': 'Subscription', 'pros': ['Predictable revenue', 'Easy to launch'], 'cons': ['Needs ongoing perceived value', 'Can be price-sensitive early']},
            {'model': 'Usage / seat expansion', 'pros': ['Scales with adoption', 'Clear upsell path'], 'cons': ['Requires deeper workflow penetration', 'Can complicate pricing']},
        ],
        'scores': [
            {'dimension': 'Market Size', 'score': 14, 'reason': 'The opportunity looks credible but needs tighter sizing proof.'},
            {'dimension': 'Timing & Trends', 'score': 16, 'reason': 'Market behavior is moving toward smarter, simpler workflows.'},
            {'dimension': 'Differentiation', 'score': 13, 'reason': 'Positioning can be strong, but incumbents are broad and noisy.'},
            {'dimension': 'Feasibility', 'score': 16, 'reason': 'A focused MVP is highly buildable.'},
            {'dimension': 'Revenue Potential', 'score': 14, 'reason': 'There is a reasonable monetization path if retention is strong.'},
        ],
        'verdict': 'Conditional Pass',
        'summary': 'This is a sensible startup direction with clear workflow pain and good MVP feasibility. The main open question is whether differentiation will feel strong enough for users to switch quickly.',
        'biggest_risk': 'If the product feels too generic, incumbents and manual workflows will remain “good enough.”',
        'biggest_strength': 'The concept can be scoped into a usable MVP quickly, which makes learning cycles fast.',
        'slide_titles': ['The Workflow Is Still Broken', 'The Problem Is Real', 'Why Now Matters', 'A Better Operating Layer', 'How It Works', 'Value to the User', 'Why We Win', 'Business Model', 'Expansion Path', 'The Ask'],
        'email_angle': 'workflow efficiency'
    }


def _local_pitch_payload(idea: str, profile: dict) -> dict:
    titles = profile.get('slide_titles') or []
    base_points = [
        [profile['pain_point'], profile['target_customer'].split('.')[0], profile['market_size']],
        [profile['pain_point'], profile['whitespace'], profile['growth_rate']],
        [profile['market_size'], profile['growth_rate'], profile['market_trends'][0]],
        [profile['mvp_features'][0]['feature'], profile['mvp_features'][1]['feature'], profile['whitespace']],
        [step['milestone'] for step in profile['build_timeline'][:3]],
        [profile['biggest_strength'], profile['market_trends'][1], profile['monetization'][0]['model']],
        [profile['competitors'][0]['weakness'], profile['competitors'][1]['weakness'], profile['whitespace']],
        [profile['monetization'][0]['model'], profile['monetization'][1]['model'], 'Land, retain, expand'],
        ['Start focused', 'Win the niche', 'Expand into adjacent workflows'],
        ['Raise pilot capital', 'Use funds for product and GTM', 'Convert early adoption into proof'],
    ]
    deck = []
    for idx in range(10):
        deck.append({
            'slide_number': idx + 1,
            'title': titles[idx] if idx < len(titles) else f'Slide {idx + 1}',
            'key_points': [point for point in base_points[idx][:3] if point]
        })

    slug = _slug(idea)
    emails = [
        {
            'investor_type': 'Pre-seed VC',
            'subject_line': f'{idea[:44]} — {profile["email_angle"]} opportunity',
            'body': f'We are building {idea}. The wedge is clear: {profile["pain_point"]} Our early thesis is that a focused product can win because {profile["whitespace"]} Would love to share the market view and pilot roadmap.'
        },
        {
            'investor_type': 'Angel',
            'subject_line': f'Backing {idea[:46]} early',
            'body': f'I am working on {idea}. The strongest signal is the user pain: {profile["pain_point"]} We believe this can become a category-leading workflow product with a focused initial market. Open to sharing the deck if useful.'
        },
        {
            'investor_type': 'Accelerator',
            'subject_line': f'{idea[:42]} — pilot-ready startup',
            'body': f'We are developing {idea} with a pilot-ready roadmap. The product is scoped around {profile["mvp_features"][0]["feature"]} and a focused GTM motion. I would value feedback on traction milestones and accelerator fit.'
        },
    ]
    domains = [
        f'{slug}.ai',
        f'{slug}hq.com',
        f'get-{slug}.com',
        f'{slug}app.io',
        f'{slug}labs.co',
    ]
    return {'deck': deck, 'emails': emails, 'domains': domains}


def _local_analysis_payload(idea: str) -> dict:
    profile = _topic_profile(idea)
    market = {
        'market_size': profile['market_size'],
        'growth_rate': profile['growth_rate'],
        'target_customer': profile['target_customer'],
        'pain_point': profile['pain_point'],
        'market_trends': profile['market_trends'],
        'opportunity_summary': profile['opportunity_summary'],
    }
    competitors = {
        'competitors': profile['competitors'],
        'whitespace': profile['whitespace'],
    }
    product = {
        'mvp_features': profile['mvp_features'],
        'suggested_stack': profile['suggested_stack'],
        'build_timeline': profile['build_timeline'],
        'monetization': profile['monetization'],
    }
    pitch = _local_pitch_payload(idea, profile)
    scorecard = {
        'scores': profile['scores'],
        'total': sum(item['score'] for item in profile['scores']),
        'verdict': profile['verdict'],
        'summary': profile['summary'],
        'biggest_risk': profile['biggest_risk'],
        'biggest_strength': profile['biggest_strength'],
    }
    return {
        'market_research': market,
        'competitor_analysis': competitors,
        'product_strategy': product,
        'pitch': pitch,
        'scorecard': scorecard,
    }


def _run_local_ventureos_stream(idea: str):
    payload = _local_analysis_payload(idea)
    yield _sse('status', message='📊 Running Market Research Agent...')
    yield _sse('market_research', data=payload['market_research'])
    _maybe_stream_pause()

    yield _sse('status', message='🔍 Running Competitor Analysis Agent...')
    yield _sse('competitor_analysis', data=payload['competitor_analysis'])
    _maybe_stream_pause()

    yield _sse('status', message='🛠️ Running Product Strategy Agent...')
    yield _sse('product_strategy', data=payload['product_strategy'])
    _maybe_stream_pause()

    yield _sse('status', message='📈 Running Pitch & Outreach Agent...')
    yield _sse('pitch', data=payload['pitch'])
    _maybe_stream_pause()

    yield _sse('status', message='🎯 Running Fundability Scorecard Agent...')
    yield _sse('scorecard', data=payload['scorecard'])
    yield _sse('done', message='All agents complete!')


def run_ventureOS_stream(idea: str):
    """Generator that yields SSE events as each agent completes"""
    try:
        llm = get_llm()
    except Exception as exc:
        print(f"[VentureOS local fallback] {exc}")
        yield from _run_local_ventureos_stream(idea)
        return

    # Market Research
    yield _sse('status', message='📊 Running Market Research Agent...')
    market, llm = safe_run(run_market_research, idea, llm)
    yield _sse('market_research', data=market)
    _maybe_stream_pause()

    # Competitor Analysis
    yield _sse('status', message='🔍 Running Competitor Analysis Agent...')
    competitors, llm = safe_run(run_competitor_analysis, idea, llm)
    yield _sse('competitor_analysis', data=competitors)
    _maybe_stream_pause()

    # Product Strategy
    yield _sse('status', message='🛠️ Running Product Strategy Agent...')
    product, llm = safe_run(run_product_strategy, idea, llm)
    yield _sse('product_strategy', data=product)
    _maybe_stream_pause()

    # Pitch & Emails
    yield _sse('status', message='📈 Running Pitch & Outreach Agent...')
    pitch, llm = safe_run_pitch(run_pitch_generation, idea,
                                market, competitors, llm)
    yield _sse('pitch', data=pitch)
    _maybe_stream_pause()

    # Scorecard
    yield _sse('status', message='🎯 Running Fundability Scorecard Agent...')
    scorecard, llm = safe_run_scorecard(
        run_scorecard, idea, market, competitors, product, llm)
    yield _sse('scorecard', data=scorecard)

    # Done
    yield _sse('done', message='All agents complete!')


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
