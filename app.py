from agents.pivot_agent import run_pivot_suggester
from agents.prototype_agent import run_prototype_generator
from agents.orchestrator import run_ventureOS_stream, get_llm
from flask import Flask, request, jsonify, render_template, Response, stream_with_context, send_file
from dotenv import load_dotenv
import os
import json
import re
import uuid
import io
import random

load_dotenv()


app = Flask(__name__)

# Ensure reports directory exists
REPORTS_DIR = os.path.join(os.path.dirname(__file__), 'reports')
os.makedirs(REPORTS_DIR, exist_ok=True)


DECK_TEMPLATE_PRESETS = [
    {
        'template_id': 'editorial-midnight',
        'theme_name': 'Editorial Midnight',
        'palette': {
            'primary': '#0B1020',
            'secondary': '#182033',
            'accent': '#7DD3FC',
            'surface': '#121A2B',
            'text': '#F8FAFC',
        },
        'style_notes': [
            'Editorial dark canvas with restrained accent contrast',
            'Generous whitespace with left-aligned storytelling blocks',
            'Premium investor tone with quiet cinematic glow',
        ]
    },
    {
        'template_id': 'boardroom-ivory',
        'theme_name': 'Boardroom Ivory',
        'palette': {
            'primary': '#F6F2EA',
            'secondary': '#E9E3D8',
            'accent': '#1D4ED8',
            'surface': '#FFFFFF',
            'text': '#111827',
        },
        'style_notes': [
            'Consulting-style light canvas with precise alignment',
            'Minimal borders, disciplined spacing, executive clarity',
            'Feels like a premium strategy memo turned into slides',
        ]
    },
    {
        'template_id': 'kinetic-ember',
        'theme_name': 'Kinetic Ember',
        'palette': {
            'primary': '#111827',
            'secondary': '#1F2937',
            'accent': '#F97316',
            'surface': '#18212F',
            'text': '#FFF7ED',
        },
        'style_notes': [
            'Dark executive canvas with warmer highlight energy',
            'Bold accents reserved for proof points and movement cues',
            'Feels more keynote-driven and launch-oriented',
        ]
    },
    {
        'template_id': 'atlas-sapphire',
        'theme_name': 'Atlas Sapphire',
        'palette': {
            'primary': '#081A3A',
            'secondary': '#0F274F',
            'accent': '#60A5FA',
            'surface': '#0E2243',
            'text': '#EFF6FF',
        },
        'style_notes': [
            'High-contrast cobalt system for data-heavy investor stories',
            'Sharp hierarchy with crisp metric framing',
            'Feels analytical, premium, and globally scalable',
        ]
    },
    {
        'template_id': 'monochrome-luxe',
        'theme_name': 'Monochrome Luxe',
        'palette': {
            'primary': '#111111',
            'secondary': '#1E1E1E',
            'accent': '#D4B483',
            'surface': '#202020',
            'text': '#F5F5F4',
        },
        'style_notes': [
            'Luxury monochrome composition with warm metallic accent',
            'Large type, sparse copy, elevated investor-brand mood',
            'Feels premium, polished, and slightly fashion-editorial',
        ]
    },
    {
        'template_id': 'forest-venture',
        'theme_name': 'Forest Venture',
        'palette': {
            'primary': '#0D1F14',
            'secondary': '#152B1D',
            'accent': '#4ADE80',
            'surface': '#112018',
            'text': '#F0FDF4',
        },
        'style_notes': [
            'Deep forest canvas with electric green proof points',
            'Evokes sustainability, growth, and long-horizon thinking',
            'Strong for impact, climate, health, and B-corp stories',
        ]
    },
    {
        'template_id': 'crimson-capital',
        'theme_name': 'Crimson Capital',
        'palette': {
            'primary': '#1A0A0A',
            'secondary': '#2A1010',
            'accent': '#F87171',
            'surface': '#220D0D',
            'text': '#FFF1F2',
        },
        'style_notes': [
            'Bold dark-red canvas — confident, high-conviction energy',
            'Accent drives urgency and decisive proof point emphasis',
            'Ideal for fintech, security, and high-stakes market narratives',
        ]
    },
    {
        'template_id': 'arctic-clarity',
        'theme_name': 'Arctic Clarity',
        'palette': {
            'primary': '#F8FAFF',
            'secondary': '#EEF2FB',
            'accent': '#3B82F6',
            'surface': '#FFFFFF',
            'text': '#0F172A',
        },
        'style_notes': [
            'Crisp polar white canvas — airy, trustworthy, effortlessly clean',
            'Blue accent anchors data, CTAs, and hierarchy with precision',
            'Feels like a top-tier SaaS product deck or Series A raise',
        ]
    },
    {
        'template_id': 'violet-epoch',
        'theme_name': 'Violet Epoch',
        'palette': {
            'primary': '#0F0A1E',
            'secondary': '#18102E',
            'accent': '#A78BFA',
            'surface': '#130D26',
            'text': '#F5F3FF',
        },
        'style_notes': [
            'Deep violet — distinctly premium for AI, crypto, and frontier tech',
            'Lavender accent evokes intelligence, creativity, and depth',
            'Feels visionary, slightly futuristic, and quietly luxurious',
        ]
    },
]

DEFAULT_DECK_THEME = DECK_TEMPLATE_PRESETS[0]


def _get_template_preset(template_id=None, exclude_template_id=None):
    if template_id:
        for preset in DECK_TEMPLATE_PRESETS:
            if preset['template_id'] == template_id:
                return preset
    candidates = [
        preset for preset in DECK_TEMPLATE_PRESETS
        if preset['template_id'] != exclude_template_id
    ] or DECK_TEMPLATE_PRESETS
    return random.choice(candidates)


def _clean_text(value, fallback=''):
    if value is None:
        return fallback
    text = str(value).strip()
    return text or fallback


def _clean_list(value, limit=5):
    if not isinstance(value, list):
        return []
    items = []
    for item in value:
        text = _clean_text(item)
        if text:
            items.append(text)
        if len(items) >= limit:
            break
    return items


def _normalize_hex(value, fallback):
    text = _clean_text(value, fallback).replace('#', '')
    if re.fullmatch(r'[0-9a-fA-F]{6}', text):
        return f"#{text.upper()}"
    return fallback


def _default_layout(slide_type: str, index: int) -> str:
    st = (slide_type or '').lower()
    if st in {'hook', 'opening', 'title', 'cover'}:
        return 'cover'
    if st in {'market', 'impact', 'value', 'traction', 'proof', 'data'}:
        return 'metrics'
    if st in {'how_it_works', 'business_model', 'process', 'roadmap'}:
        return 'roadmap'
    if st in {'vision', 'future', 'ask', 'call_to_action', 'cta'}:
        return 'closing'
    if st in {'competition', 'competitive_landscape'}:
        return 'comparison'
    return 'spotlight' if index else 'cover'


def _normalize_stats(raw_slide: dict) -> list:
    stats = raw_slide.get('stats')
    normalized = []
    if isinstance(stats, list):
        for item in stats[:3]:
            if not isinstance(item, dict):
                continue
            value = _clean_text(item.get('value') or item.get('num'))
            label = _clean_text(item.get('label'))
            if value or label:
                normalized.append({'value': value, 'label': label})
    else:
        legacy = [
            (raw_slide.get('stat1_num'), raw_slide.get('stat1_label')),
            (raw_slide.get('stat2_num'), raw_slide.get('stat2_label')),
            (raw_slide.get('stat3_num'), raw_slide.get('stat3_label')),
        ]
        for value, label in legacy:
            value = _clean_text(value)
            label = _clean_text(label)
            if value or label:
                normalized.append({'value': value, 'label': label})
    return normalized[:3]


def _normalize_slide(raw_slide: dict, index: int) -> dict:
    raw_slide = raw_slide or {}
    animation = raw_slide.get('animation_plan') or {}
    content = _clean_list(
        raw_slide.get('content')
        or raw_slide.get('points')
        or raw_slide.get('key_points')
        or [],
        limit=5,
    )
    sequence = _clean_list(
        animation.get('sequence')
        or raw_slide.get('sequence')
        or [],
        limit=4,
    )
    slide_type = _clean_text(
        raw_slide.get('type') or raw_slide.get('slide_type'),
        'story'
    ).lower()

    return {
        'slide_number': raw_slide.get('slide_number') or index + 1,
        'type': slide_type,
        'layout': _clean_text(
            raw_slide.get('layout'),
            _default_layout(slide_type, index)
        ).lower(),
        'title': _clean_text(
            raw_slide.get('title')
            or raw_slide.get('headline')
            or raw_slide.get('slide_title'),
            f"Slide {index + 1}",
        ),
        'subtitle': _clean_text(
            raw_slide.get('subtitle')
            or raw_slide.get('subheadline')
        ),
        'objective': _clean_text(raw_slide.get('objective')),
        'content': content,
        'stats': _normalize_stats(raw_slide),
        'visual_suggestion': _clean_text(
            raw_slide.get('visual_suggestion')
            or raw_slide.get('visual')
            or raw_slide.get('chart_suggestion')
        ),
        'design_notes': _clean_text(raw_slide.get('design_notes')),
        'animation_plan': {
            'entry': _clean_text(animation.get('entry'), 'Fade'),
            'sequence': sequence or ['Title', 'Core message', 'Proof point'],
            'transition': _clean_text(animation.get('transition'), 'Smooth fade'),
            'emphasis': _clean_text(animation.get('emphasis')),
        }
    }


def _extract_json_payload(text: str):
    text = text.strip()
    text = re.sub(r'```json', '', text)
    text = re.sub(r'```', '', text)
    text = text.strip()

    start_obj = text.find('{')
    end_obj = text.rfind('}') + 1
    if start_obj != -1 and end_obj > start_obj:
        return json.loads(text[start_obj:end_obj])

    start_arr = text.find('[')
    end_arr = text.rfind(']') + 1
    if start_arr != -1 and end_arr > start_arr:
        return json.loads(text[start_arr:end_arr])

    raise ValueError('No JSON object or array found in model response')


def _normalize_deck_payload(payload, idea: str, template_preset=None) -> dict:
    payload = {'slides': payload} if isinstance(
        payload, list) else (payload or {})
    design = payload.get('design_system') or {}
    palette = design.get('palette') or {}
    template_preset = template_preset or DEFAULT_DECK_THEME

    slides = payload.get('slides') or payload.get('deck') or []
    slides = [
        _normalize_slide(slide, i)
        for i, slide in enumerate(slides[:12])
    ]

    return {
        'presentation_title': _clean_text(
            payload.get('presentation_title'),
            idea[:72] or 'Investor Presentation'
        ),
        'presentation_subtitle': _clean_text(
            payload.get('presentation_subtitle'),
            'Premium investor-ready story deck'
        ),
        'design_system': {
            'template_id': _clean_text(
                design.get('template_id'),
                template_preset['template_id']
            ),
            'theme_name': _clean_text(
                design.get('theme_name')
                or template_preset.get('theme_name'),
                DEFAULT_DECK_THEME['theme_name']
            ),
            'palette': {
                'primary': _normalize_hex(
                    template_preset['palette'].get('primary'),
                    DEFAULT_DECK_THEME['palette']['primary']
                ),
                'secondary': _normalize_hex(
                    template_preset['palette'].get('secondary'),
                    DEFAULT_DECK_THEME['palette']['secondary']
                ),
                'accent': _normalize_hex(
                    template_preset['palette'].get('accent'),
                    DEFAULT_DECK_THEME['palette']['accent']
                ),
                'surface': _normalize_hex(
                    template_preset['palette'].get('surface'),
                    DEFAULT_DECK_THEME['palette']['surface']
                ),
                'text': _normalize_hex(
                    template_preset['palette'].get('text'),
                    DEFAULT_DECK_THEME['palette']['text']
                ),
            },
            'style_notes': _clean_list(
                template_preset.get('style_notes')
                or design.get('style_notes'),
                limit=3
            ) or DEFAULT_DECK_THEME['style_notes'],
        },
        'slides': slides,
    }


# ── MAIN PAGE ──────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')


# ── ANALYZE — streams SSE from all agents ──────────────────────────────────
@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    idea = data.get('idea', '')
    if not idea:
        return jsonify({'error': 'No idea provided'}), 400

    def generate():
        try:
            for chunk in run_ventureOS_stream(idea):
                yield chunk
        except Exception as e:
            yield f"data: {json.dumps({'event': 'error', 'message': str(e)})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive'
        }
    )


# ── PROTOTYPE ──────────────────────────────────────────────────────────────
@app.route('/prototype', methods=['POST'])
def prototype():
    data = request.json
    idea = data.get('idea', '')
    product_strategy = data.get('product_strategy', {})
    context = data.get('context', {})
    seed = data.get('seed', None)
    if not idea:
        return jsonify({'error': 'No idea provided'}), 400
    try:
        llm = get_llm()
        html, theme_name = run_prototype_generator(
            idea, product_strategy, llm, seed)
        return jsonify({'html': html, 'theme': theme_name})
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500


# ── CHAT ───────────────────────────────────────────────────────────────────
@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    idea = data.get('idea', '')
    context = data.get('context', {})
    messages = data.get('messages', [])
    user_message = data.get('user_message', '')

    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    try:
        llm = get_llm()
        system_prompt = f"""You are VentureOS, an expert startup advisor and co-founder AI.

The user has already analyzed this startup idea: "{idea}"

Here is the full analysis context:
- Market Research: {json.dumps(context.get('market_research', {}))}
- Competitor Analysis: {json.dumps(context.get('competitor_analysis', {}))}
- Product Strategy: {json.dumps(context.get('product_strategy', {}))}
- Fundability Score: {json.dumps(context.get('scorecard', {}))}

Be specific, honest, and actionable. Keep responses concise — 2-4 paragraphs max."""

        from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
        lc_messages = [SystemMessage(content=system_prompt)]
        for msg in messages:
            if msg['role'] == 'user':
                lc_messages.append(HumanMessage(content=msg['content']))
            elif msg['role'] == 'assistant':
                lc_messages.append(AIMessage(content=msg['content']))
        lc_messages.append(HumanMessage(content=user_message))

        response = llm.invoke(lc_messages)
        return jsonify({'reply': response.content})

    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500


# ── PIVOT ──────────────────────────────────────────────────────────────────
@app.route('/pivot', methods=['POST'])
def pivot():
    data = request.json
    idea = data.get('idea', '')
    context = data.get('context', {})
    if not idea:
        return jsonify({'error': 'No idea provided'}), 400
    try:
        llm = get_llm()
        result = run_pivot_suggester(
            idea,
            context.get('market_research', {}),
            context.get('competitor_analysis', {}),
            context.get('scorecard', {}),
            llm
        )
        return jsonify(result)
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500


# ── SLIDES — proxy to avoid CORS ───────────────────────────────────────────
@app.route('/slides', methods=['POST'])
def generate_slides():
    data = request.json
    idea = data.get('idea', '')
    context = data.get('context', {})
    template_id = data.get('template_id')
    previous_template_id = data.get('previous_template_id')

    if not idea:
        return jsonify({'error': 'No idea provided'}), 400

    m = context.get('market_research', {})
    c = context.get('competitor_analysis', {})
    p = context.get('product_strategy', {})
    sc = context.get('scorecard', {})
    pitch = context.get('pitch', {})
    deck = pitch.get('deck', [])
    template_preset = _get_template_preset(
        template_id=template_id,
        exclude_template_id=previous_template_id,
    )

    prompt = f"""You are an expert Presentation Designer and Storytelling Strategist who creates premium, high-end, investor-grade presentations in the style of McKinsey, BCG, Apple keynote, and top startup pitch decks.

Create a premium 10-slide presentation structure for this startup. The deck must feel intentional, minimal, structured, and highly polished.

Selected visual template:
- Template ID: {template_preset['template_id']}
- Template name: {template_preset['theme_name']}
- Palette: {json.dumps(template_preset['palette'])}
- Style notes: {json.dumps(template_preset['style_notes'])}

Startup idea: "{idea}"
Market size: {m.get('market_size', '—')}
Growth rate: {m.get('growth_rate', '—')}
Target customer: {m.get('target_customer', '—')}
Pain point: {m.get('pain_point', '—')}
Opportunity summary: {m.get('opportunity_summary', '—')}
Competitor whitespace: {c.get('whitespace', '—')}
Fundability score: {sc.get('total', '—')}/100
Verdict: {sc.get('verdict', '—')}
Biggest strength: {sc.get('biggest_strength', '—')}
Biggest risk: {sc.get('biggest_risk', '—')}
Pitch outline: {json.dumps(deck[:10])}
Monetization: {json.dumps(p.get('monetization', [])[:3])}

Strict design rules:
- Premium, high-contrast, minimal layout
- Plenty of whitespace
- Titles short and powerful
- Minimal text: max 6-8 words per line
- Max 3-5 bullets per slide
- Avoid generic filler
- Recommend visuals, charts, icons, or imagery where useful
- Every slide must include a smooth, professional animation plan

Story flow:
1. Hook / Opening
2. Problem
3. Why it matters
4. Solution
5. How it works
6. Value / Impact
7. Proof / Data
8. Business model
9. Future / Vision
10. Call to Action

Return ONLY a valid JSON object with this exact structure:
{{
  "presentation_title": "Deck title",
  "presentation_subtitle": "Short contextual subtitle",
  "design_system": {{
    "theme_name": "Short premium theme name",
    "palette": {{
      "primary": "#0B1020",
      "secondary": "#182033",
      "accent": "#7DD3FC",
      "surface": "#121A2B",
      "text": "#F8FAFC"
    }},
    "style_notes": [
      "Deck-level design principle 1",
      "Deck-level design principle 2",
      "Deck-level design principle 3"
    ]
  }},
  "slides": [
    {{
      "slide_number": 1,
      "type": "hook|problem|stakes|solution|how_it_works|impact|proof|business_model|vision|call_to_action",
      "layout": "cover|spotlight|metrics|roadmap|comparison|closing",
      "title": "Short punchy title",
      "subtitle": "Optional support line",
      "objective": "What this slide is trying to achieve",
      "content": ["Bullet 1", "Bullet 2", "Bullet 3"],
      "stats": [
        {{"value": "$4.2B", "label": "Total Market"}},
        {{"value": "28%", "label": "Annual Growth"}}
      ],
      "visual_suggestion": "Specific visual, chart, or image direction",
      "design_notes": "Layout, alignment, spacing, hierarchy notes",
      "animation_plan": {{
        "entry": "Fade|Zoom|Slide Up",
        "sequence": ["What appears first", "What appears second", "What appears third"],
        "transition": "Fade|Push|Morph-like directional cut",
        "emphasis": "Optional subtle emphasis animation"
      }}
    }}
  ]
}}

Use real numbers from context whenever possible. Keep the tone confident, crisp, and concise."""

    try:
        llm = get_llm()
        from langchain_core.messages import HumanMessage
        response = llm.invoke([HumanMessage(content=prompt)])
        payload = _extract_json_payload(response.content)
        deck_payload = _normalize_deck_payload(payload, idea, template_preset)
        return jsonify(deck_payload)
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500


# ── DOWNLOAD PPTX ──────────────────────────────────────────────────────────
# 8 design systems — each has completely different visual structure per slide

PPTX_DESIGN_SYSTEMS = {
    # ── 1. EDITORIAL MIDNIGHT: left accent bar, right panel, serif titles ──
    'editorial-midnight': {'style': 'editorial', 'FH': 'Georgia',          'FB': 'Calibri'},
    'boardroom-ivory':    {'style': 'boardroom',  'FH': 'Cambria',          'FB': 'Calibri'},
    # ── 2. KINETIC: full-bleed diagonal geometry, bold impact layout ──────
    'kinetic-ember':      {'style': 'kinetic',    'FH': 'Arial Black',      'FB': 'Arial'},
    'crimson-capital':    {'style': 'kinetic',    'FH': 'Georgia',          'FB': 'Calibri'},
    # ── 3. ATLAS: data-forward, left sidebar accent, metric-heavy ─────────
    'atlas-sapphire':     {'style': 'atlas',      'FH': 'Georgia',          'FB': 'Calibri'},
    'violet-epoch':       {'style': 'atlas',      'FH': 'Georgia',          'FB': 'Calibri'},
    # ── 4. LUXE: centred luxury, large serif, minimal lines ───────────────
    'monochrome-luxe':    {'style': 'luxe',       'FH': 'Palatino Linotype', 'FB': 'Calibri'},
    'charcoal-gold':      {'style': 'luxe',       'FH': 'Palatino Linotype', 'FB': 'Calibri'},
    # ── 5. BOARDROOM: light canvas, thin rules, consulting aesthetic ───────
    'arctic-clarity':     {'style': 'boardroom',  'FH': 'Trebuchet MS',     'FB': 'Calibri'},
    # ── 6. FOREST: organic, bottom-anchored stats, nature motif ───────────
    'forest-venture':     {'style': 'forest',     'FH': 'Georgia',          'FB': 'Calibri'},
}


@app.route('/download_pptx', methods=['POST'])
def download_pptx():
    try:
        from pptx import Presentation
        from pptx.util import Inches, Pt
        from pptx.dml.color import RGBColor
        from pptx.enum.text import PP_ALIGN
        from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE

        data = request.json
        idea = data.get('idea', 'ventureos')
        raw_slides = data.get('slides') or data.get('deck') or []
        slides_data = [_normalize_slide(s, i)
                       for i, s in enumerate(raw_slides)]
        if not slides_data:
            return jsonify({'error': 'No slides provided'}), 400

        design = data.get('design_system') or DEFAULT_DECK_THEME
        palette = design.get('palette') or DEFAULT_DECK_THEME['palette']
        tid = design.get('template_id', DEFAULT_DECK_THEME['template_id'])
        theme_name = design.get('theme_name', 'VentureOS')

        # ── Colour helpers ─────────────────────────────────────────────────
        def _h2r(val, fb):
            v = _normalize_hex(val, fb).replace('#', '')
            return RGBColor(int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16))

        def _luma(val, fb='#000000'):
            v = _normalize_hex(val, fb).replace('#', '')
            return 0.299*int(v[0:2], 16)+0.587*int(v[2:4], 16)+0.114*int(v[4:6], 16)

        C_BG = _h2r(palette.get('primary'),
                    DEFAULT_DECK_THEME['palette']['primary'])
        C_BG2 = _h2r(palette.get('secondary'),
                     DEFAULT_DECK_THEME['palette']['secondary'])
        C_SURF = _h2r(palette.get('surface'),
                      DEFAULT_DECK_THEME['palette']['surface'])
        C_ACC = _h2r(palette.get('accent'),
                     DEFAULT_DECK_THEME['palette']['accent'])
        C_TEXT = _h2r(palette.get('text'),
                      DEFAULT_DECK_THEME['palette']['text'])
        is_light = _luma(palette.get('primary', '#000')) > 160
        C_DIM = RGBColor(0x44, 0x55, 0x66) if is_light else RGBColor(
            0xB0, 0xC4, 0xD8)
        C_WHITE = RGBColor(0xFF, 0xFF, 0xFF)
        C_BLACK = RGBColor(0x0F, 0x0F, 0x0F)

        def _blend(a, b, t):
            return RGBColor(int(a[0]+(b[0]-a[0])*t), int(a[1]+(b[1]-a[1])*t), int(a[2]+(b[2]-a[2])*t))

        def _acc(t): return _blend(C_BG, C_ACC, t)
        def _sur(t): return _blend(C_BG, C_SURF, t)
        def _bg2(t): return _blend(C_BG, C_BG2, t)

        def _acc_light(t): return _blend(
            C_WHITE if is_light else C_BG, C_ACC, t)

        ds = PPTX_DESIGN_SYSTEMS.get(
            tid, {'style': 'editorial', 'FH': 'Georgia', 'FB': 'Calibri'})
        STYLE = ds['style']
        FH = ds['FH']
        FB = ds['FB']

        prs = Presentation()
        prs.slide_width = Inches(13.33)
        prs.slide_height = Inches(7.5)
        BLANK = prs.slide_layouts[6]

        # ── Draw primitives ────────────────────────────────────────────────
        def txt(sl, text, L, T, W, H, sz, col, bold=False, italic=False,
                align=PP_ALIGN.LEFT, fn=None):
            if not text:
                return
            tb = sl.shapes.add_textbox(
                Inches(L), Inches(T), Inches(W), Inches(H))
            tf = tb.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.alignment = align
            r = p.add_run()
            r.text = str(text)
            r.font.size = Pt(sz)
            r.font.color.rgb = col
            r.font.bold = bold
            r.font.italic = italic
            r.font.name = fn or FB

        def rect(sl, L, T, W, H, fill, border=None, bw=0.5, rnd=False):
            st = MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE if rnd else MSO_AUTO_SHAPE_TYPE.RECTANGLE
            sh = sl.shapes.add_shape(st, Inches(
                L), Inches(T), Inches(W), Inches(H))
            sh.fill.solid()
            sh.fill.fore_color.rgb = fill
            if border:
                sh.line.color.rgb = border
                sh.line.width = Pt(bw)
            else:
                sh.line.fill.background()
            return sh

        def oval(sl, L, T, W, H, fill):
            sh = sl.shapes.add_shape(MSO_AUTO_SHAPE_TYPE.OVAL,
                                     Inches(L), Inches(T), Inches(W), Inches(H))
            sh.fill.solid()
            sh.fill.fore_color.rgb = fill
            sh.line.fill.background()
            return sh

        def footer(sl, idx, total):
            rect(sl, 0, 7.22, 13.33, 0.28, _bg2(0.8))
            rect(sl, 0, 7.22, 13.33, 0.016, C_ACC)
            txt(sl, 'VentureOS', 0.40, 7.28, 3.0, 0.22, 7, C_DIM)
            txt(sl, theme_name,  4.66, 7.28, 4.0,
                0.22, 7, C_DIM, align=PP_ALIGN.CENTER)
            txt(sl, f'{idx+1:02d} / {total:02d}', 9.50, 7.28, 3.3, 0.22,
                7, C_DIM, bold=True, align=PP_ALIGN.RIGHT)

        total = len(slides_data)

        for i, sd in enumerate(slides_data):
            sl = prs.slides.add_slide(BLANK)
            layout = sd.get('layout', 'spotlight')
            title = sd.get('title') or f'Slide {i+1}'
            sub = sd.get('subtitle') or ''
            pts = (sd.get('content') or sd.get('points') or [])[:5]
            stats = (sd.get('stats') or [])[:3]
            obj = sd.get('objective') or ''
            vis = sd.get('visual_suggestion') or ''
            kicker = sd.get('type', 'story').replace('_', ' ').upper()

            sl.background.fill.solid()
            sl.background.fill.fore_color.rgb = C_BG

            # ══════════════════════════════════════════════════════════════════
            # STYLE A — EDITORIAL  (left accent stripe + right panel)
            # DNA: vertical left bar, right glassmorphic panel, serif headlines
            # ══════════════════════════════════════════════════════════════════
            if STYLE == 'editorial':
                if layout == 'cover':
                    rect(sl, 0, 0, 5.6, 7.5, _bg2(0.88))
                    rect(sl, 5.6, 0, 7.73, 7.5, _bg2(0.35))
                    oval(sl, 5.2, -1.8, 8.0, 8.0, _acc(0.16))
                    oval(sl, 8.5,  3.8, 5.5, 5.5, _acc(0.10))
                    rect(sl, 0, 0, 0.08, 7.5, C_ACC)
                    rect(sl, 0.55, 0.55, 3.0, 0.32, _acc(0.28), rnd=True)
                    txt(sl, kicker, 0.72, 0.59, 2.8, 0.26, 8, C_ACC, bold=True)
                    txt(sl, title, 0.55, 1.10, 4.8, 2.80,
                        38, C_TEXT, bold=True, fn=FH)
                    if sub:
                        txt(sl, sub, 0.55, 3.85, 4.6,
                            0.80, 13, C_DIM, italic=True)
                    rect(sl, 0.55, 4.72, 3.8, 0.04, _acc(0.60))
                    txt(sl, idea.title()[:40], 0.55,
                        4.92, 4.5, 0.40, 10.5, C_DIM)
                    if stats:
                        txt(sl, stats[0].get('value', ''), 6.2, 1.80, 7.0, 1.90,
                            70, _acc(0.88), bold=True, fn=FH, align=PP_ALIGN.CENTER)
                        txt(sl, stats[0].get('label', '').upper(), 6.2, 4.00, 7.0, 0.38,
                            10, C_DIM, bold=True, align=PP_ALIGN.CENTER)
                    else:
                        txt(sl, vis or 'The future starts here.', 6.2, 2.80, 7.0,
                            1.40, 15, C_DIM, italic=True, align=PP_ALIGN.CENTER)
                elif layout == 'metrics':
                    rect(sl, 0, 0, 13.33, 1.38, _bg2(0.88))
                    rect(sl, 0, 1.38, 13.33, 0.05, C_ACC)
                    rect(sl, 0, 0, 0.08, 1.38, C_ACC)
                    txt(sl, kicker, 0.52, 0.18, 6.0, 0.26, 8, C_ACC, bold=True)
                    txt(sl, title,  0.52, 0.50, 9.0, 0.78,
                        26, C_TEXT, bold=True, fn=FH)
                    if stats:
                        n = len(stats)
                        cw = (12.33 - 0.18*(n-1)) / n
                        for bi, st in enumerate(stats):
                            bx = 0.50 + bi*(cw+0.18)
                            rect(sl, bx, 1.65, cw, 3.30, _sur(0.75),
                                 border=_acc(0.25), bw=0.6, rnd=True)
                            rect(sl, bx, 1.65, cw, 0.12, C_ACC)
                            txt(sl, st.get('value', ''), bx+0.18, 1.92, cw-0.36, 1.60,
                                50, C_TEXT, bold=True, fn=FH, align=PP_ALIGN.CENTER)
                            txt(sl, st.get('label', '').upper(), bx+0.18, 3.62, cw-0.36,
                                0.34, 9, C_DIM, bold=True, align=PP_ALIGN.CENTER)
                    for bi, pt in enumerate((pts or [obj])[:3]):
                        ty = 5.22 + bi*0.42
                        oval(sl, 0.52, ty+0.10, 0.11, 0.11, C_ACC)
                        txt(sl, pt, 0.78, ty, 12.0, 0.38, 11.5, C_TEXT)
                elif layout == 'roadmap':
                    rect(sl, 0, 0, 13.33, 1.28, _bg2(0.88))
                    rect(sl, 0, 1.28, 13.33, 0.05, C_ACC)
                    rect(sl, 0, 0, 0.08, 1.28, C_ACC)
                    txt(sl, kicker, 0.52, 0.16, 6.0, 0.26, 8, C_ACC, bold=True)
                    txt(sl, title,  0.52, 0.44, 9.0, 0.74,
                        24, C_TEXT, bold=True, fn=FH)
                    if sub:
                        txt(sl, sub, 0.52, 1.04, 8.0,
                            0.30, 10.5, C_DIM, italic=True)
                    rect(sl, 0.55, 3.05, 12.22, 0.04, _acc(0.32))
                    steps = pts[:4]
                    n = len(steps) or 1
                    sw = 12.22/n
                    for bi, st in enumerate(steps):
                        cx = 0.55 + bi*sw + sw/2
                        oval(sl, cx-0.34, 2.86, 0.68, 0.68, _acc(0.38))
                        oval(sl, cx-0.21, 3.00, 0.42, 0.42, C_ACC)
                        txt(sl, f'{bi+1}', cx-0.21, 3.00, 0.42, 0.42, 10,
                            C_BG if not is_light else C_WHITE, bold=True, align=PP_ALIGN.CENTER)
                        bx = 0.55+bi*sw+0.10
                        cw = sw-0.20
                        rect(sl, bx, 3.82, cw, 2.62, _sur(0.70),
                             border=_acc(0.20), bw=0.5, rnd=True)
                        txt(sl, st, bx+0.14, 3.95, cw-0.28, 2.32, 11.5, C_TEXT)
                elif layout == 'comparison':
                    rect(sl, 0, 0, 13.33, 0.90, _bg2(0.88))
                    rect(sl, 0, 0.90, 13.33, 0.04, C_ACC)
                    rect(sl, 0, 0, 0.08, 0.90, C_ACC)
                    rect(sl, 6.46, 0.94, 0.05, 6.28, _acc(0.38))
                    txt(sl, kicker, 0.48, 0.10, 5.0, 0.24, 8, C_ACC, bold=True)
                    txt(sl, title,  0.48, 0.34, 12.3,
                        0.48, 21, C_TEXT, bold=True, fn=FH)
                    rect(sl, 0.48, 1.06, 5.76, 0.42, _acc(0.20), rnd=True)
                    txt(sl, 'PROBLEM / BEFORE', 0.66, 1.12,
                        5.40, 0.30, 8.5, C_ACC, bold=True)
                    rect(sl, 6.70, 1.06, 6.10, 0.42, _acc(0.38), rnd=True)
                    txt(sl, 'SOLUTION / AFTER',  6.88, 1.12,
                        5.70, 0.30, 8.5, C_ACC, bold=True)
                    lp = pts[:3]
                    rp = pts[3:] or pts[:3]
                    for bi, p in enumerate(lp):
                        ty = 1.74 + bi*0.96
                        oval(sl, 0.52, ty+0.13, 0.13, 0.13, _acc(0.50))
                        txt(sl, p, 0.80, ty, 5.30, 0.84, 11.5, C_TEXT)
                    for bi, p in enumerate(rp):
                        ty = 1.74 + bi*0.96
                        oval(sl, 6.76, ty+0.13, 0.13, 0.13, C_ACC)
                        txt(sl, p, 7.04, ty, 5.82, 0.84, 11.5, C_TEXT)
                    if sub:
                        txt(sl, sub, 0.48, 6.60, 12.3,
                            0.38, 10, C_DIM, italic=True)
                elif layout == 'closing':
                    rect(sl, 0, 0, 13.33, 0.10, C_ACC)
                    oval(sl, -2.0, -1.5, 8.5, 8.5, _acc(0.12))
                    oval(sl, 7.5, 1.0, 7.0, 7.0, _acc(0.10))
                    txt(sl, kicker, 0, 1.10, 13.33, 0.30, 9,
                        C_ACC, bold=True, align=PP_ALIGN.CENTER)
                    txt(sl, title, 0.80, 1.52, 11.73, 1.90, 42, C_TEXT,
                        bold=True, fn=FH, align=PP_ALIGN.CENTER)
                    rect(sl, 4.66, 3.50, 4.0, 0.05, _acc(0.58))
                    if sub:
                        txt(sl, sub, 1.0, 3.68, 11.33, 0.68, 13.5,
                            C_DIM, italic=True, align=PP_ALIGN.CENTER)
                    if stats:
                        n = min(len(stats), 3)
                        cw = 3.5
                        sx = (13.33-(n*cw+(n-1)*0.28))/2
                        for bi, st in enumerate(stats[:3]):
                            bx = sx+bi*(cw+0.28)
                            rect(sl, bx, 4.56, cw, 1.60, _sur(0.75),
                                 border=_acc(0.30), bw=0.6, rnd=True)
                            rect(sl, bx, 4.56, cw, 0.10, C_ACC)
                            txt(sl, st.get('value', ''), bx+0.14, 4.72, cw-0.28, 0.80,
                                30, C_TEXT, bold=True, fn=FH, align=PP_ALIGN.CENTER)
                            txt(sl, st.get('label', '').upper(), bx+0.14, 5.58, cw -
                                0.28, 0.30, 8, C_DIM, bold=True, align=PP_ALIGN.CENTER)
                    rect(sl, 0, 7.40, 13.33, 0.10, C_ACC)
                else:  # spotlight
                    rect(sl, 7.88, 0, 5.45, 7.5, _bg2(0.85))
                    oval(sl, 8.5, -1.0, 5.5, 5.5, _acc(0.18))
                    oval(sl, 9.5,  4.0, 3.8, 3.8, _acc(0.10))
                    rect(sl, 0, 0, 0.08, 7.5, C_ACC)
                    txt(sl, kicker, 0.38, 0.40, 5.5, 0.26, 8, C_ACC, bold=True)
                    txt(sl, title,  0.38, 0.80, 7.2, 1.80,
                        28, C_TEXT, bold=True, fn=FH)
                    if sub:
                        txt(sl, sub, 0.38, 2.54, 7.0,
                            0.58, 12, C_DIM, italic=True)
                    rect(sl, 0.38, 3.20, 5.0, 0.04, _acc(0.42))
                    if pts:
                        for bi, pt in enumerate(pts):
                            ty = 3.40 + bi*0.57
                            rect(sl, 0.38, ty+0.07, 0.22,
                                 0.22, _acc(0.30), rnd=True)
                            txt(sl, f'{bi+1}', 0.38, ty+0.07, 0.22, 0.22,
                                7, C_ACC, bold=True, align=PP_ALIGN.CENTER)
                            txt(sl, pt, 0.72, ty, 6.90, 0.52, 11.5, C_TEXT)
                    elif obj:
                        txt(sl, obj, 0.38, 3.40, 7.0,
                            0.80, 12, C_DIM, italic=True)
                    if stats:
                        for bi, st in enumerate(stats[:3]):
                            ty = 0.68 + bi*2.08
                            rect(sl, 8.08, ty, 4.92, 1.82, _sur(0.70),
                                 border=_acc(0.22), bw=0.5, rnd=True)
                            rect(sl, 8.08, ty, 4.92, 0.12, C_ACC)
                            txt(sl, st.get('value', ''), 8.26, ty+0.17, 4.56, 1.0,
                                34, C_TEXT, bold=True, fn=FH, align=PP_ALIGN.CENTER)
                            txt(sl, st.get('label', '').upper(), 8.26, ty+1.28,
                                4.56, 0.30, 8, C_DIM, bold=True, align=PP_ALIGN.CENTER)
                    else:
                        rect(sl, 8.08, 0.68, 4.92, 5.82, _sur(0.70),
                             border=_acc(0.18), bw=0.5, rnd=True)
                        txt(sl, 'VISUAL DIRECTION', 8.28, 0.86,
                            4.52, 0.26, 7.5, C_ACC, bold=True)
                        rect(sl, 8.08, 1.10, 4.92, 0.04, _acc(0.32))
                        txt(sl, vis or 'Use one dominant visual.',
                            8.28, 1.20, 4.52, 4.92, 11.5, C_TEXT)

            # ══════════════════════════════════════════════════════════════════
            # STYLE B — KINETIC  (diagonal slash, impact typography, bold energy)
            # DNA: angled accent band top-right, full-bleed color blocks, huge type
            # ══════════════════════════════════════════════════════════════════
            elif STYLE == 'kinetic':
                # Shared kinetic BG motif — thick accent slash top-right
                rect(sl, 9.0, 0, 4.33, 0.06, C_ACC)
                rect(sl, 0, 7.44, 13.33, 0.06, C_ACC)

                if layout == 'cover':
                    rect(sl, 0, 0, 13.33, 3.8, _bg2(0.92))
                    oval(sl, 8.0, -1.0, 7.0, 7.0, _acc(0.22))
                    txt(sl, kicker, 0.65, 0.42, 6.0, 0.28, 8, C_ACC, bold=True)
                    txt(sl, title, 0.65, 0.85, 10.0, 2.60,
                        48, C_TEXT, bold=True, fn=FH)
                    if sub:
                        txt(sl, sub, 0.65, 3.60, 8.0,
                            0.70, 14, C_DIM, italic=True)
                    rect(sl, 0.65, 4.42, 4.0, 0.06, C_ACC)
                    txt(sl, idea.title()[:40], 0.65,
                        4.58, 6.0, 0.42, 11, C_DIM)
                    if stats:
                        for bi, st in enumerate(stats[:2]):
                            bx = 7.0 + bi*3.1
                            txt(sl, st.get('value', ''), bx, 1.0, 3.0,
                                1.60, 54, C_ACC, bold=True, fn=FH)
                            txt(sl, st.get('label', '').upper(), bx,
                                2.70, 3.0, 0.36, 9, C_DIM, bold=True)
                elif layout == 'metrics':
                    rect(sl, 0, 0, 13.33, 0.80, C_ACC)
                    txt(sl, kicker, 0.55, 0.10, 6.0, 0.26, 8,
                        C_BG if not is_light else C_WHITE, bold=True)
                    txt(sl, title,  0.55, 0.42, 10.0,
                        0.84, 28, C_TEXT, bold=True, fn=FH)
                    if stats:
                        n = len(stats)
                        cw = (12.33 - 0.2*(n-1)) / n
                        for bi, st in enumerate(stats):
                            bx = 0.50 + bi*(cw+0.20)
                            rect(sl, bx, 1.60, cw, 4.0, _sur(0.72),
                                 border=C_ACC, bw=1.2, rnd=False)
                            txt(sl, st.get('value', ''), bx+0.20, 1.90, cw-0.40, 2.0,
                                56, C_ACC, bold=True, fn=FH, align=PP_ALIGN.CENTER)
                            txt(sl, st.get('label', '').upper(), bx+0.20, 4.10, cw-0.40,
                                0.38, 9.5, C_TEXT, bold=True, align=PP_ALIGN.CENTER)
                    for bi, pt in enumerate((pts or [obj])[:2]):
                        ty = 5.85 + bi*0.46
                        rect(sl, 0.50, ty+0.06, 0.30, 0.22, C_ACC)
                        txt(sl, pt, 0.94, ty, 11.8, 0.40, 11.5, C_TEXT)
                elif layout == 'roadmap':
                    rect(sl, 0, 0, 13.33, 1.0, _bg2(0.90))
                    txt(sl, kicker, 0.55, 0.12, 6.0, 0.24, 8, C_ACC, bold=True)
                    txt(sl, title,  0.55, 0.38, 10.0,
                        0.56, 22, C_TEXT, bold=True, fn=FH)
                    # Vertical timeline (left edge)
                    rect(sl, 1.20, 1.20, 0.05, 5.80, _acc(0.40))
                    steps = pts[:4]
                    for bi, st in enumerate(steps):
                        ty = 1.40 + bi*1.48
                        oval(sl, 0.90, ty, 0.60, 0.60, C_ACC)
                        txt(sl, f'{bi+1}', 0.90, ty, 0.60, 0.60, 11,
                            C_BG if not is_light else C_WHITE, bold=True, align=PP_ALIGN.CENTER)
                        rect(sl, 1.80, ty, 11.0, 1.24, _sur(0.70),
                             border=_acc(0.22), bw=0.5, rnd=False)
                        txt(sl, st, 2.00, ty+0.10, 10.60, 1.0, 12, C_TEXT)
                elif layout == 'comparison':
                    rect(sl, 0, 0, 6.46, 7.5, _bg2(0.90))
                    rect(sl, 6.46, 0, 6.87, 7.5, _acc(0.20))
                    txt(sl, kicker, 0.50, 0.22, 5.5, 0.26, 8, C_ACC, bold=True)
                    txt(sl, title,  0.50, 0.55, 12.0,
                        0.80, 24, C_TEXT, bold=True, fn=FH)
                    txt(sl, 'BEFORE', 1.0, 1.55, 4.5,
                        0.38, 11, C_DIM, bold=True)
                    txt(sl, 'AFTER',  7.0, 1.55, 5.5,
                        0.38, 11, C_ACC, bold=True)
                    lp = pts[:3]
                    rp = pts[3:] or pts[:3]
                    for bi, p in enumerate(lp):
                        ty = 2.10 + bi*1.12
                        rect(sl, 0.50, ty, 5.60, 0.88, _sur(0.65), rnd=False)
                        txt(sl, p, 0.70, ty+0.12, 5.20, 0.72, 11.5, C_TEXT)
                    for bi, p in enumerate(rp):
                        ty = 2.10 + bi*1.12
                        rect(sl, 6.66, ty, 6.30, 0.88, _acc(0.28), rnd=False)
                        txt(sl, p, 6.86, ty+0.12, 5.90, 0.72, 11.5, C_TEXT)
                elif layout == 'closing':
                    rect(sl, 0, 0, 13.33, 7.5, _bg2(0.95))
                    rect(sl, 0, 0, 13.33, 0.12, C_ACC)
                    rect(sl, 0, 7.38, 13.33, 0.12, C_ACC)
                    oval(sl, -1.5, -1.5, 7.5, 7.5, _acc(0.14))
                    oval(sl, 9.0,  3.0, 6.0, 6.0, _acc(0.12))
                    txt(sl, title, 0.80, 0.90, 11.73, 2.20, 50, C_TEXT,
                        bold=True, fn=FH, align=PP_ALIGN.CENTER)
                    rect(sl, 4.66, 3.20, 4.0, 0.06, C_ACC)
                    if sub:
                        txt(sl, sub, 1.0, 3.38, 11.33, 0.70, 14,
                            C_DIM, italic=True, align=PP_ALIGN.CENTER)
                    if stats:
                        n = min(len(stats), 3)
                        cw = 3.5
                        sx = (13.33-(n*cw+(n-1)*0.28))/2
                        for bi, st in enumerate(stats[:3]):
                            bx = sx+bi*(cw+0.28)
                            rect(sl, bx, 4.40, cw, 1.80, _acc(0.22),
                                 border=C_ACC, bw=1.0, rnd=False)
                            txt(sl, st.get('value', ''), bx+0.14, 4.55, cw-0.28, 0.90,
                                32, C_ACC, bold=True, fn=FH, align=PP_ALIGN.CENTER)
                            txt(sl, st.get('label', '').upper(), bx+0.14, 5.58, cw -
                                0.28, 0.34, 8.5, C_TEXT, bold=True, align=PP_ALIGN.CENTER)
                else:  # spotlight
                    rect(sl, 0, 0, 0.18, 7.5, C_ACC)
                    rect(sl, 0.18, 0, 13.15, 0.72, _bg2(0.90))
                    txt(sl, kicker, 0.42, 0.12, 5.5, 0.26, 8, C_ACC, bold=True)
                    txt(sl, title,  0.42, 0.80, 7.8, 2.0,
                        32, C_TEXT, bold=True, fn=FH)
                    if sub:
                        txt(sl, sub, 0.42, 2.76, 7.8,
                            0.58, 12, C_DIM, italic=True)
                    rect(sl, 0.42, 3.48, 0.60, 0.06, C_ACC)
                    if pts:
                        for bi, pt in enumerate(pts):
                            ty = 3.70 + bi*0.62
                            rect(sl, 0.42, ty+0.10, 0.28,
                                 0.28, C_ACC, rnd=False)
                            txt(sl, f'{bi+1}', 0.42, ty+0.10, 0.28, 0.28, 8,
                                C_BG if not is_light else C_WHITE, bold=True, align=PP_ALIGN.CENTER)
                            txt(sl, pt, 0.84, ty, 7.20, 0.56, 12, C_TEXT)
                    elif obj:
                        txt(sl, obj, 0.42, 3.70, 7.8,
                            0.80, 12, C_DIM, italic=True)
                    if stats:
                        for bi, st in enumerate(stats[:3]):
                            ty = 0.20 + bi*2.32
                            rect(sl, 8.70, ty, 4.30, 2.10, _acc(0.22),
                                 border=C_ACC, bw=0.8, rnd=False)
                            txt(sl, st.get('value', ''), 8.88, ty+0.22, 3.94, 1.20,
                                38, C_ACC, bold=True, fn=FH, align=PP_ALIGN.CENTER)
                            txt(sl, st.get('label', '').upper(), 8.88, ty+1.62, 3.94,
                                0.32, 8.5, C_TEXT, bold=True, align=PP_ALIGN.CENTER)
                    else:
                        rect(sl, 8.70, 0.20, 4.30, 6.82, _sur(0.70),
                             border=_acc(0.22), bw=0.6, rnd=False)
                        txt(sl, 'VISUAL DIRECTION', 8.90, 0.38,
                            3.90, 0.26, 7.5, C_ACC, bold=True)
                        rect(sl, 8.70, 0.62, 4.30, 0.05, C_ACC)
                        txt(sl, vis or 'Lead with a bold proof visual.',
                            8.90, 0.72, 3.90, 6.10, 12, C_TEXT)

            # ══════════════════════════════════════════════════════════════════
            # STYLE C — ATLAS  (left sidebar strip + data-centric layout)
            # DNA: narrow left accent sidebar, top header bar, right panel for data
            # ══════════════════════════════════════════════════════════════════
            elif STYLE == 'atlas':
                # Persistent left sidebar
                rect(sl, 0, 0, 0.90, 7.5, _bg2(0.92))
                rect(sl, 0.90, 0, 0.04, 7.5, _acc(0.30))
                # Sidebar kicker text (rotated effect via tall narrow box)
                txt(sl, str(i+1).zfill(2), 0.08, 0.30, 0.74, 0.50, 18,
                    C_ACC, bold=True, fn=FH, align=PP_ALIGN.CENTER)
                txt(sl, kicker[:8], 0.05, 1.0, 0.80, 3.0, 8,
                    C_DIM, bold=True, align=PP_ALIGN.CENTER)

                if layout == 'cover':
                    rect(sl, 0.94, 0, 12.39, 7.5, _bg2(0.40))
                    oval(sl, 7.0, -1.5, 7.5, 7.5, _acc(0.18))
                    oval(sl, 9.5,  3.5, 5.0, 5.0, _acc(0.12))
                    txt(sl, title, 1.10, 0.80, 9.0, 3.20,
                        44, C_TEXT, bold=True, fn=FH)
                    if sub:
                        txt(sl, sub, 1.10, 4.10, 8.0,
                            0.80, 13, C_DIM, italic=True)
                    rect(sl, 1.10, 5.00, 4.0, 0.04, C_ACC)
                    txt(sl, idea.title()[:38], 1.10,
                        5.18, 6.0, 0.38, 10.5, C_DIM)
                    if stats:
                        txt(sl, stats[0].get('value', ''), 7.5, 1.60, 5.5, 2.20, 64, _acc(
                            0.88), bold=True, fn=FH, align=PP_ALIGN.CENTER)
                        txt(sl, stats[0].get('label', '').upper(
                        ), 7.5, 3.92, 5.5, 0.36, 10, C_DIM, bold=True, align=PP_ALIGN.CENTER)
                elif layout == 'metrics':
                    rect(sl, 0.94, 0, 12.39, 1.10, _bg2(0.88))
                    rect(sl, 0.94, 1.10, 12.39, 0.05, C_ACC)
                    txt(sl, title, 1.10, 0.20, 10.0, 0.80,
                        26, C_TEXT, bold=True, fn=FH)
                    if stats:
                        n = len(stats)
                        cw = (11.83 - 0.18*(n-1)) / n
                        for bi, st in enumerate(stats):
                            bx = 1.10 + bi*(cw+0.18)
                            rect(sl, bx, 1.32, cw, 3.60, _sur(0.75),
                                 border=_acc(0.28), bw=0.7, rnd=True)
                            rect(sl, bx, 1.32, cw, 0.14, C_ACC)
                            txt(sl, st.get('value', ''), bx+0.18, 1.58, cw-0.36, 1.80,
                                52, C_TEXT, bold=True, fn=FH, align=PP_ALIGN.CENTER)
                            txt(sl, st.get('label', '').upper(), bx+0.18, 3.50, cw-0.36,
                                0.34, 9, C_DIM, bold=True, align=PP_ALIGN.CENTER)
                    for bi, pt in enumerate((pts or [obj])[:3]):
                        ty = 5.22 + bi*0.40
                        rect(sl, 1.10, ty+0.08, 0.20, 0.20, C_ACC, rnd=True)
                        txt(sl, pt, 1.44, ty, 11.5, 0.38, 11, C_TEXT)
                elif layout == 'roadmap':
                    rect(sl, 0.94, 0, 12.39, 1.0, _bg2(0.88))
                    rect(sl, 0.94, 1.0, 12.39, 0.04, C_ACC)
                    txt(sl, title, 1.10, 0.14, 10.0, 0.76,
                        24, C_TEXT, bold=True, fn=FH)
                    if sub:
                        txt(sl, sub, 1.10, 0.78, 8.0,
                            0.28, 10, C_DIM, italic=True)
                    rect(sl, 1.10, 3.04, 12.0, 0.04, _acc(0.32))
                    steps = pts[:4]
                    n = len(steps) or 1
                    sw = 12.0/n
                    for bi, st in enumerate(steps):
                        cx = 1.10 + bi*sw + sw/2
                        oval(sl, cx-0.32, 2.84, 0.64, 0.64, _acc(0.40))
                        oval(sl, cx-0.20, 2.98, 0.40, 0.40, C_ACC)
                        txt(sl, f'{bi+1}', cx-0.20, 2.98, 0.40, 0.40, 9,
                            C_BG if not is_light else C_WHITE, bold=True, align=PP_ALIGN.CENTER)
                        bx = 1.10+bi*sw+0.08
                        cw = sw-0.16
                        rect(sl, bx, 3.80, cw, 2.70, _sur(0.72),
                             border=_acc(0.20), bw=0.5, rnd=True)
                        txt(sl, st, bx+0.12, 3.92, cw-0.24, 2.42, 11, C_TEXT)
                elif layout == 'comparison':
                    rect(sl, 0.94, 0, 12.39, 0.80, _bg2(0.88))
                    rect(sl, 0.94, 0.80, 12.39, 0.04, C_ACC)
                    rect(sl, 7.16, 0.84, 0.05, 6.38, _acc(0.36))
                    txt(sl, title, 1.10, 0.10, 11.5, 0.64,
                        22, C_TEXT, bold=True, fn=FH)
                    rect(sl, 1.10, 0.98, 5.78, 0.40, _acc(0.20), rnd=True)
                    txt(sl, 'PROBLEM / BEFORE', 1.28, 1.04,
                        5.40, 0.28, 8.5, C_ACC, bold=True)
                    rect(sl, 7.40, 0.98, 5.78, 0.40, _acc(0.36), rnd=True)
                    txt(sl, 'SOLUTION / AFTER', 7.58, 1.04,
                        5.40, 0.28, 8.5, C_ACC, bold=True)
                    lp = pts[:3]
                    rp = pts[3:] or pts[:3]
                    for bi, p in enumerate(lp):
                        ty = 1.58 + bi*1.0
                        oval(sl, 1.14, ty+0.12, 0.12, 0.12, _acc(0.50))
                        txt(sl, p, 1.40, ty, 5.38, 0.88, 11.5, C_TEXT)
                    for bi, p in enumerate(rp):
                        ty = 1.58 + bi*1.0
                        oval(sl, 7.44, ty+0.12, 0.12, 0.12, C_ACC)
                        txt(sl, p, 7.70, ty, 5.58, 0.88, 11.5, C_TEXT)
                elif layout == 'closing':
                    rect(sl, 0.94, 0, 12.39, 7.5, _bg2(0.50))
                    oval(sl, 5.0, -1.0, 9.0, 9.0, _acc(0.12))
                    txt(sl, title, 1.10, 1.20, 11.20, 2.10, 44, C_TEXT,
                        bold=True, fn=FH, align=PP_ALIGN.CENTER)
                    rect(sl, 4.66, 3.42, 4.0, 0.05, C_ACC)
                    if sub:
                        txt(sl, sub, 1.10, 3.60, 11.2, 0.70, 13.5,
                            C_DIM, italic=True, align=PP_ALIGN.CENTER)
                    if stats:
                        n = min(len(stats), 3)
                        cw = 3.4
                        sx = (11.23-(n*cw+(n-1)*0.26))/2 + 1.0
                        for bi, st in enumerate(stats[:3]):
                            bx = sx+bi*(cw+0.26)
                            rect(sl, bx, 4.50, cw, 1.72, _sur(0.75),
                                 border=_acc(0.30), bw=0.7, rnd=True)
                            rect(sl, bx, 4.50, cw, 0.12, C_ACC)
                            txt(sl, st.get('value', ''), bx+0.14, 4.65, cw-0.28, 0.82,
                                30, C_TEXT, bold=True, fn=FH, align=PP_ALIGN.CENTER)
                            txt(sl, st.get('label', '').upper(), bx+0.14, 5.56, cw -
                                0.28, 0.30, 8, C_DIM, bold=True, align=PP_ALIGN.CENTER)
                    rect(sl, 0.94, 7.38, 12.39, 0.10, C_ACC)
                else:  # spotlight
                    rect(sl, 0.94, 0, 7.0, 7.5, _bg2(0.50))
                    rect(sl, 7.94, 0, 5.39, 7.5, _sur(0.80))
                    oval(sl, 8.0, -0.8, 5.2, 5.2, _acc(0.16))
                    txt(sl, title, 1.10, 0.50, 6.60, 2.20,
                        30, C_TEXT, bold=True, fn=FH)
                    if sub:
                        txt(sl, sub, 1.10, 2.68, 6.60,
                            0.56, 12, C_DIM, italic=True)
                    rect(sl, 1.10, 3.34, 4.50, 0.04, C_ACC)
                    if pts:
                        for bi, pt in enumerate(pts):
                            ty = 3.52 + bi*0.60
                            rect(sl, 1.10, ty+0.08, 0.22,
                                 0.22, _acc(0.30), rnd=True)
                            txt(sl, f'{bi+1}', 1.10, ty+0.08, 0.22, 0.22,
                                7, C_ACC, bold=True, align=PP_ALIGN.CENTER)
                            txt(sl, pt, 1.44, ty, 6.30, 0.54, 11.5, C_TEXT)
                    elif obj:
                        txt(sl, obj, 1.10, 3.52, 6.60,
                            0.80, 12, C_DIM, italic=True)
                    if stats:
                        for bi, st in enumerate(stats[:3]):
                            ty = 0.40 + bi*2.26
                            rect(sl, 8.12, ty, 5.0, 2.06, _sur(0.70),
                                 border=_acc(0.22), bw=0.5, rnd=True)
                            rect(sl, 8.12, ty, 5.0, 0.12, C_ACC)
                            txt(sl, st.get('value', ''), 8.30, ty+0.18, 4.64, 1.12,
                                36, C_TEXT, bold=True, fn=FH, align=PP_ALIGN.CENTER)
                            txt(sl, st.get('label', '').upper(), 8.30, ty+1.40,
                                4.64, 0.30, 8, C_DIM, bold=True, align=PP_ALIGN.CENTER)
                    else:
                        rect(sl, 8.12, 0.40, 5.0, 6.32, _sur(0.70),
                             border=_acc(0.18), bw=0.5, rnd=True)
                        txt(sl, 'VISUAL DIRECTION', 8.32, 0.58,
                            4.60, 0.26, 7.5, C_ACC, bold=True)
                        rect(sl, 8.12, 0.82, 5.0, 0.04, _acc(0.32))
                        txt(sl, vis or 'Use one proof visual.',
                            8.32, 0.92, 4.60, 5.50, 12, C_TEXT)

            # ══════════════════════════════════════════════════════════════════
            # STYLE D — LUXE  (centred luxury, large serif, gold rule system)
            # DNA: centred everything, thin horizontal rules, editorial white space
            # ══════════════════════════════════════════════════════════════════
            elif STYLE == 'luxe':
                # Top + bottom thin gold rules
                rect(sl, 0, 0.25, 13.33, 0.016, C_ACC)
                rect(sl, 0, 7.22, 13.33, 0.016, C_ACC)

                if layout == 'cover':
                    oval(sl, -2.0, -2.0, 8.0, 8.0, _acc(0.10))
                    oval(sl, 9.0,  3.0, 7.0, 7.0, _acc(0.08))
                    # Centred rule above headline
                    rect(sl, 5.66, 0.80, 2.0, 0.016, C_ACC)
                    txt(sl, kicker, 0, 0.90, 13.33, 0.28, 9,
                        C_ACC, bold=True, align=PP_ALIGN.CENTER)
                    txt(sl, title, 0.80, 1.28, 11.73, 3.20, 52, C_TEXT,
                        bold=True, fn=FH, align=PP_ALIGN.CENTER)
                    rect(sl, 5.66, 4.58, 2.0, 0.016, C_ACC)
                    if sub:
                        txt(sl, sub, 1.0, 4.74, 11.33, 0.72, 14,
                            C_DIM, italic=True, align=PP_ALIGN.CENTER)
                    txt(sl, idea.title()[:48], 0, 5.60, 13.33,
                        0.38, 10.5, C_DIM, align=PP_ALIGN.CENTER)
                    if stats:
                        txt(sl, stats[0].get('value', ''), 0, 3.00, 13.33, 1.40, 60, _acc(
                            0.80), bold=True, fn=FH, align=PP_ALIGN.CENTER)
                elif layout == 'metrics':
                    rect(sl, 0, 0.92, 13.33, 0.016, C_ACC)
                    txt(sl, kicker, 0, 0.46, 13.33, 0.28, 9,
                        C_ACC, bold=True, align=PP_ALIGN.CENTER)
                    txt(sl, title, 0.80, 1.10, 11.73, 1.40, 30, C_TEXT,
                        bold=True, fn=FH, align=PP_ALIGN.CENTER)
                    if stats:
                        n = len(stats)
                        cw = (11.73 - 0.20*(n-1)) / n
                        sx = (13.33-(n*cw+(n-1)*0.20))/2
                        for bi, st in enumerate(stats):
                            bx = sx + bi*(cw+0.20)
                            rect(sl, bx, 2.72, cw, 3.20, _sur(0.72),
                                 border=_acc(0.22), bw=0.5, rnd=True)
                            rect(sl, bx, 2.72, cw, 0.016, C_ACC)
                            txt(sl, st.get('value', ''), bx+0.18, 2.90, cw-0.36, 1.70,
                                52, C_TEXT, bold=True, fn=FH, align=PP_ALIGN.CENTER)
                            txt(sl, st.get('label', '').upper(), bx+0.18, 4.68, cw-0.36,
                                0.34, 9, C_DIM, bold=True, align=PP_ALIGN.CENTER)
                    for bi, pt in enumerate((pts or [obj])[:2]):
                        txt(sl, pt, 1.0, 6.10+bi*0.42, 11.33, 0.38,
                            11.5, C_TEXT, align=PP_ALIGN.CENTER)
                elif layout == 'roadmap':
                    rect(sl, 0, 0.92, 13.33, 0.016, C_ACC)
                    txt(sl, kicker, 0, 0.46, 13.33, 0.28, 9,
                        C_ACC, bold=True, align=PP_ALIGN.CENTER)
                    txt(sl, title, 0.80, 1.10, 11.73, 1.10, 28, C_TEXT,
                        bold=True, fn=FH, align=PP_ALIGN.CENTER)
                    if sub:
                        txt(sl, sub, 1.0, 2.10, 11.33, 0.38, 11,
                            C_DIM, italic=True, align=PP_ALIGN.CENTER)
                    rect(sl, 0.55, 3.28, 12.22, 0.016, _acc(0.40))
                    steps = pts[:4]
                    n = len(steps) or 1
                    sw = 12.22/n
                    for bi, st in enumerate(steps):
                        cx = 0.55 + bi*sw + sw/2
                        oval(sl, cx-0.28, 3.12, 0.56, 0.56, C_ACC)
                        txt(sl, f'{bi+1}', cx-0.28, 3.12, 0.56, 0.56, 9,
                            C_BG if not is_light else C_WHITE, bold=True, align=PP_ALIGN.CENTER)
                        bx = 0.55+bi*sw+0.10
                        cw = sw-0.20
                        rect(sl, bx, 3.96, cw, 2.56, _sur(0.68),
                             border=_acc(0.18), bw=0.4, rnd=True)
                        txt(sl, st, bx+0.14, 4.10, cw-0.28, 2.28,
                            11.5, C_TEXT, align=PP_ALIGN.CENTER)
                elif layout == 'comparison':
                    rect(sl, 0, 0.92, 13.33, 0.016, C_ACC)
                    rect(sl, 6.66, 1.0, 0.016, 6.22, _acc(0.40))
                    txt(sl, kicker, 0, 0.46, 13.33, 0.28, 9,
                        C_ACC, bold=True, align=PP_ALIGN.CENTER)
                    txt(sl, title, 0.80, 1.10, 11.73, 0.88, 26, C_TEXT,
                        bold=True, fn=FH, align=PP_ALIGN.CENTER)
                    txt(sl, 'BEFORE', 0.55, 2.06, 5.88, 0.32, 10,
                        C_DIM, bold=True, align=PP_ALIGN.CENTER)
                    txt(sl, 'AFTER',  6.88, 2.06, 6.10, 0.32, 10,
                        C_ACC, bold=True, align=PP_ALIGN.CENTER)
                    lp = pts[:3]
                    rp = pts[3:] or pts[:3]
                    for bi, p in enumerate(lp):
                        ty = 2.58 + bi*1.10
                        txt(sl, p, 0.55, ty, 5.88, 0.96, 12,
                            C_TEXT, align=PP_ALIGN.CENTER)
                        rect(sl, 2.0, ty+1.04, 2.96, 0.014, _acc(0.20))
                    for bi, p in enumerate(rp):
                        ty = 2.58 + bi*1.10
                        txt(sl, p, 6.88, ty, 6.10, 0.96, 12,
                            C_TEXT, align=PP_ALIGN.CENTER)
                        rect(sl, 8.0, ty+1.04, 3.10, 0.014, _acc(0.20))
                elif layout == 'closing':
                    oval(sl, -1.5, -1.5, 7.0, 7.0, _acc(0.11))
                    oval(sl, 9.0,  2.5, 6.0, 6.0, _acc(0.09))
                    rect(sl, 5.66, 1.10, 2.0, 0.016, C_ACC)
                    txt(sl, kicker, 0, 1.24, 13.33, 0.30, 9,
                        C_ACC, bold=True, align=PP_ALIGN.CENTER)
                    txt(sl, title, 0.80, 1.60, 11.73, 2.40, 50, C_TEXT,
                        bold=True, fn=FH, align=PP_ALIGN.CENTER)
                    rect(sl, 5.66, 4.10, 2.0, 0.016, C_ACC)
                    if sub:
                        txt(sl, sub, 1.0, 4.26, 11.33, 0.68, 14,
                            C_DIM, italic=True, align=PP_ALIGN.CENTER)
                    if stats:
                        n = min(len(stats), 3)
                        cw = 3.4
                        sx = (13.33-(n*cw+(n-1)*0.26))/2
                        for bi, st in enumerate(stats[:3]):
                            bx = sx+bi*(cw+0.26)
                            rect(sl, bx, 5.10, cw, 1.80, _sur(0.72),
                                 border=_acc(0.24), bw=0.5, rnd=True)
                            rect(sl, bx+cw*0.3, 5.10, cw*0.4, 0.016, C_ACC)
                            txt(sl, st.get('value', ''), bx+0.14, 5.24, cw-0.28, 0.88,
                                30, C_TEXT, bold=True, fn=FH, align=PP_ALIGN.CENTER)
                            txt(sl, st.get('label', '').upper(), bx+0.14, 6.18, cw -
                                0.28, 0.30, 8, C_DIM, bold=True, align=PP_ALIGN.CENTER)
                else:  # spotlight
                    rect(sl, 0, 0.92, 13.33, 0.016, C_ACC)
                    txt(sl, kicker, 0, 0.46, 13.33, 0.28, 9,
                        C_ACC, bold=True, align=PP_ALIGN.CENTER)
                    txt(sl, title, 0.80, 1.10, 11.73, 2.0, 34, C_TEXT,
                        bold=True, fn=FH, align=PP_ALIGN.CENTER)
                    if sub:
                        txt(sl, sub, 1.0, 3.00, 11.33, 0.58, 12.5,
                            C_DIM, italic=True, align=PP_ALIGN.CENTER)
                    rect(sl, 5.66, 3.68, 2.0, 0.016, C_ACC)
                    if pts:
                        for bi, pt in enumerate(pts[:4]):
                            ty = 3.90 + bi*0.68
                            txt(sl, f'— {pt}', 1.50, ty, 10.33, 0.60,
                                12, C_TEXT, align=PP_ALIGN.CENTER)
                    elif obj:
                        txt(sl, obj, 1.0, 3.90, 11.33, 0.80, 12,
                            C_DIM, italic=True, align=PP_ALIGN.CENTER)
                    if stats:
                        n = len(stats)
                        cw = (11.33-(0.20*(n-1)))/n
                        sx = (13.33-(n*cw+(n-1)*0.20))/2
                        for bi, st in enumerate(stats):
                            bx = sx + bi*(cw+0.20)
                            rect(sl, bx, 5.90, cw, 1.10, _sur(0.72),
                                 border=_acc(0.22), bw=0.4, rnd=True)
                            txt(sl, st.get('value', ''), bx+0.12, 5.98, cw-0.24, 0.64,
                                26, C_TEXT, bold=True, fn=FH, align=PP_ALIGN.CENTER)
                            txt(sl, st.get('label', '').upper(), bx+0.12, 6.68, cw -
                                0.24, 0.24, 7.5, C_DIM, bold=True, align=PP_ALIGN.CENTER)

            # ══════════════════════════════════════════════════════════════════
            # STYLE E — BOARDROOM  (light canvas, consulting aesthetic, thin rules)
            # DNA: top thin header rule, serif titles, structured grid, clean spacing
            # ══════════════════════════════════════════════════════════════════
            elif STYLE == 'boardroom':
                # Light bg already set; add structural chrome
                rect(sl, 0, 0, 13.33, 0.60, _bg2(0.70))
                rect(sl, 0, 0.60, 13.33, 0.024, C_ACC)

                if layout == 'cover':
                    rect(sl, 0, 0, 0.06, 7.5, C_ACC)
                    txt(sl, kicker, 0.50, 0.14, 6.0, 0.26, 8, C_ACC, bold=True)
                    txt(sl, title, 0.50, 0.82, 8.5, 3.50,
                        46, C_TEXT, bold=True, fn=FH)
                    if sub:
                        txt(sl, sub, 0.50, 4.40, 7.5,
                            0.80, 14, C_DIM, italic=True)
                    rect(sl, 0.50, 5.30, 3.50, 0.024, C_ACC)
                    txt(sl, idea.title()[:44], 0.50,
                        5.46, 6.0, 0.44, 11, C_DIM)
                    if stats:
                        for bi, st in enumerate(stats[:2]):
                            bx = 9.20 + bi*1.8
                            rect(sl, 9.0, 0.80, 4.0, 6.0, _bg2(
                                0.60), border=_acc(0.30), bw=0.5)
                            txt(sl, st.get('value', ''), 9.10, 1.60, 3.80, 2.0,
                                52, C_ACC, bold=True, fn=FH, align=PP_ALIGN.CENTER)
                            txt(sl, st.get('label', '').upper(), 9.10, 3.70, 3.80,
                                0.36, 9, C_DIM, bold=True, align=PP_ALIGN.CENTER)
                            break
                    else:
                        rect(sl, 9.0, 0.80, 4.0, 6.0, _bg2(
                            0.60), border=_acc(0.30), bw=0.5)
                        txt(sl, vis or 'Lead with precision.', 9.10, 2.60, 3.80,
                            2.0, 13, C_DIM, italic=True, align=PP_ALIGN.CENTER)
                elif layout == 'metrics':
                    txt(sl, kicker, 0.50, 0.14, 6.0, 0.26, 8, C_ACC, bold=True)
                    txt(sl, title,  0.50, 0.72, 10.0,
                        1.30, 30, C_TEXT, bold=True, fn=FH)
                    if stats:
                        n = len(stats)
                        cw = (12.33 - 0.16*(n-1)) / n
                        for bi, st in enumerate(stats):
                            bx = 0.50 + bi*(cw+0.16)
                            rect(sl, bx, 2.20, cw, 3.50, _bg2(
                                0.60), border=_acc(0.28), bw=0.5)
                            rect(sl, bx, 2.20, cw, 0.024, C_ACC)
                            txt(sl, st.get('value', ''), bx+0.18, 2.44, cw-0.36, 1.90,
                                52, C_ACC, bold=True, fn=FH, align=PP_ALIGN.CENTER)
                            txt(sl, st.get('label', '').upper(), bx+0.18, 4.42, cw-0.36,
                                0.36, 9, C_DIM, bold=True, align=PP_ALIGN.CENTER)
                    for bi, pt in enumerate((pts or [obj])[:3]):
                        ty = 6.00 + bi*0.38
                        rect(sl, 0.50, ty+0.10, 0.10, 0.10, C_ACC)
                        txt(sl, pt, 0.74, ty, 12.0, 0.36, 11, C_TEXT)
                elif layout == 'roadmap':
                    txt(sl, kicker, 0.50, 0.14, 6.0, 0.26, 8, C_ACC, bold=True)
                    txt(sl, title,  0.50, 0.72, 9.0, 0.88,
                        26, C_TEXT, bold=True, fn=FH)
                    if sub:
                        txt(sl, sub, 0.50, 1.48, 8.0,
                            0.34, 11, C_DIM, italic=True)
                    rect(sl, 0.50, 3.12, 12.33, 0.024, _acc(0.36))
                    steps = pts[:4]
                    n = len(steps) or 1
                    sw = 12.33/n
                    for bi, st in enumerate(steps):
                        cx = 0.50 + bi*sw + sw/2
                        rect(sl, cx-0.28, 2.96, 0.56, 0.32, C_ACC)
                        txt(sl, f'{bi+1:02d}', cx-0.28, 2.96, 0.56, 0.32, 10,
                            C_BG if not is_light else C_WHITE, bold=True, align=PP_ALIGN.CENTER)
                        bx = 0.50+bi*sw+0.08
                        cw = sw-0.16
                        rect(sl, bx, 3.30, cw, 3.42, _bg2(
                            0.65), border=_acc(0.22), bw=0.4)
                        txt(sl, st, bx+0.14, 3.44, cw-0.28, 3.12, 12, C_TEXT)
                elif layout == 'comparison':
                    rect(sl, 6.46, 0.64, 0.024, 6.58, _acc(0.36))
                    txt(sl, kicker, 0.50, 0.14, 5.0, 0.26, 8, C_ACC, bold=True)
                    txt(sl, title,  0.50, 0.72, 12.3,
                        0.88, 24, C_TEXT, bold=True, fn=FH)
                    rect(sl, 0.50, 1.72, 5.70, 0.36, _bg2(
                        0.70), border=_acc(0.28), bw=0.4)
                    txt(sl, 'STATUS QUO', 0.68, 1.78,
                        5.32, 0.24, 8.5, C_DIM, bold=True)
                    rect(sl, 6.70, 1.72, 6.30, 0.36, _bg2(
                        0.70), border=_acc(0.28), bw=0.4)
                    txt(sl, 'WITH THIS SOLUTION', 6.88, 1.78,
                        5.92, 0.24, 8.5, C_ACC, bold=True)
                    lp = pts[:4]
                    rp = pts[4:] or pts[:4]
                    for bi, p in enumerate(lp[:3]):
                        ty = 2.24 + bi*1.14
                        rect(sl, 0.50, ty, 5.70, 0.94, _bg2(
                            0.60), border=_acc(0.14), bw=0.4)
                        txt(sl, p, 0.66, ty+0.12, 5.38, 0.70, 11.5, C_TEXT)
                    for bi, p in enumerate(rp[:3]):
                        ty = 2.24 + bi*1.14
                        rect(sl, 6.70, ty, 6.30, 0.94, _bg2(
                            0.60), border=_acc(0.14), bw=0.4)
                        txt(sl, p, 6.86, ty+0.12, 5.98, 0.70, 11.5, C_TEXT)
                elif layout == 'closing':
                    oval(sl, 2.0, 0.5, 9.0, 7.0, _acc(0.07))
                    txt(sl, kicker, 0, 1.10, 13.33, 0.30, 9,
                        C_ACC, bold=True, align=PP_ALIGN.CENTER)
                    txt(sl, title, 0.80, 1.50, 11.73, 2.50, 46, C_TEXT,
                        bold=True, fn=FH, align=PP_ALIGN.CENTER)
                    rect(sl, 4.66, 4.10, 4.0, 0.024, C_ACC)
                    if sub:
                        txt(sl, sub, 1.0, 4.28, 11.33, 0.72, 13.5,
                            C_DIM, italic=True, align=PP_ALIGN.CENTER)
                    if stats:
                        n = min(len(stats), 3)
                        cw = 3.5
                        sx = (13.33-(n*cw+(n-1)*0.28))/2
                        for bi, st in enumerate(stats[:3]):
                            bx = sx+bi*(cw+0.28)
                            rect(sl, bx, 5.10, cw, 1.70, _bg2(
                                0.60), border=_acc(0.30), bw=0.5)
                            rect(sl, bx, 5.10, cw, 0.024, C_ACC)
                            txt(sl, st.get('value', ''), bx+0.14, 5.24, cw-0.28, 0.84,
                                30, C_ACC, bold=True, fn=FH, align=PP_ALIGN.CENTER)
                            txt(sl, st.get('label', '').upper(), bx+0.14, 6.18, cw -
                                0.28, 0.30, 8, C_DIM, bold=True, align=PP_ALIGN.CENTER)
                else:  # spotlight
                    txt(sl, kicker, 0.50, 0.14, 5.5, 0.26, 8, C_ACC, bold=True)
                    txt(sl, title,  0.50, 0.72, 7.5, 2.20,
                        32, C_TEXT, bold=True, fn=FH)
                    if sub:
                        txt(sl, sub, 0.50, 2.88, 7.5,
                            0.60, 12.5, C_DIM, italic=True)
                    rect(sl, 0.50, 3.58, 5.0, 0.024, C_ACC)
                    if pts:
                        for bi, pt in enumerate(pts):
                            ty = 3.76 + bi*0.62
                            rect(sl, 0.50, ty+0.14, 0.10, 0.10, C_ACC)
                            txt(sl, pt, 0.74, ty, 7.0, 0.56, 12, C_TEXT)
                    elif obj:
                        txt(sl, obj, 0.50, 3.76, 7.5,
                            0.80, 12, C_DIM, italic=True)
                    rect(sl, 8.30, 0.64, 4.60, 6.58, _bg2(
                        0.65), border=_acc(0.24), bw=0.5)
                    if stats:
                        for bi, st in enumerate(stats[:3]):
                            ty = 1.0 + bi*2.14
                            rect(sl, 8.30, ty, 4.60, 1.90, _bg2(
                                0.60), border=_acc(0.22), bw=0.4)
                            txt(sl, st.get('value', ''), 8.46, ty+0.18, 4.28, 1.10,
                                36, C_ACC, bold=True, fn=FH, align=PP_ALIGN.CENTER)
                            txt(sl, st.get('label', '').upper(), 8.46, ty+1.38,
                                4.28, 0.30, 8, C_DIM, bold=True, align=PP_ALIGN.CENTER)
                    else:
                        txt(sl, 'VISUAL DIRECTION', 8.50, 0.82,
                            4.20, 0.26, 7.5, C_ACC, bold=True)
                        rect(sl, 8.30, 1.06, 4.60, 0.024, C_ACC)
                        txt(sl, vis or 'Use a clean structured visual.',
                            8.50, 1.16, 4.20, 5.70, 12, C_TEXT)

            # ══════════════════════════════════════════════════════════════════
            # STYLE F — FOREST  (organic, bottom-anchored stats, nature motif)
            # DNA: large bottom accent bar, organic orbs, bottom-up composition
            # ══════════════════════════════════════════════════════════════════
            else:  # forest
                # Bottom anchor bar (green ground)
                rect(sl, 0, 6.70, 13.33, 0.80, _bg2(0.88))
                rect(sl, 0, 6.70, 13.33, 0.05, C_ACC)

                if layout == 'cover':
                    oval(sl, -1.0, -1.0, 7.0, 7.0, _acc(0.14))
                    oval(sl, 8.5,  2.0, 6.5, 6.5, _acc(0.10))
                    rect(sl, 0, 0, 0.08, 6.70, C_ACC)
                    txt(sl, kicker, 0.48, 0.40, 5.0, 0.28, 8, C_ACC, bold=True)
                    txt(sl, title, 0.48, 0.88, 7.8, 3.20,
                        42, C_TEXT, bold=True, fn=FH)
                    if sub:
                        txt(sl, sub, 0.48, 4.18, 7.0,
                            0.80, 13.5, C_DIM, italic=True)
                    rect(sl, 0.48, 5.08, 3.6, 0.04, C_ACC)
                    txt(sl, idea.title()[:40], 0.48,
                        5.26, 6.0, 0.40, 10.5, C_DIM)
                    if stats:
                        s0 = stats[0]
                        txt(sl, s0.get('value', ''), 7.5, 1.60, 5.5, 2.40, 68, _acc(
                            0.88), bold=True, fn=FH, align=PP_ALIGN.CENTER)
                        txt(sl, s0.get('label', '').upper(), 7.5, 4.10, 5.5,
                            0.40, 10.5, C_DIM, bold=True, align=PP_ALIGN.CENTER)
                    txt(sl, 'VentureOS', 0.48, 6.78, 4.0, 0.22, 7, C_DIM)
                    txt(sl, theme_name, 4.66, 6.78, 4.0,
                        0.22, 7, C_DIM, align=PP_ALIGN.CENTER)
                    txt(sl, f'{i+1:02d} / {total:02d}', 9.50, 6.78, 3.3,
                        0.22, 7, C_DIM, bold=True, align=PP_ALIGN.RIGHT)
                    footer(sl, i, total)
                    continue
                elif layout == 'metrics':
                    oval(sl, 9.0, -1.0, 5.5, 5.5, _acc(0.14))
                    rect(sl, 0, 0, 13.33, 0.80, _bg2(0.88))
                    txt(sl, kicker, 0.50, 0.12, 6.0, 0.26, 8, C_ACC, bold=True)
                    txt(sl, title,  0.50, 0.42, 9.0, 0.80,
                        26, C_TEXT, bold=True, fn=FH)
                    if stats:
                        n = len(stats)
                        cw = (12.33 - 0.18*(n-1)) / n
                        for bi, st in enumerate(stats):
                            bx = 0.50 + bi*(cw+0.18)
                            rect(sl, bx, 1.20, cw, 3.80, _sur(0.72),
                                 border=_acc(0.22), bw=0.5, rnd=True)
                            rect(sl, bx, 1.20, cw, 0.12, C_ACC)
                            txt(sl, st.get('value', ''), bx+0.18, 1.46, cw-0.36, 1.80,
                                50, C_TEXT, bold=True, fn=FH, align=PP_ALIGN.CENTER)
                            txt(sl, st.get('label', '').upper(), bx+0.18, 3.38, cw-0.36,
                                0.36, 9, C_DIM, bold=True, align=PP_ALIGN.CENTER)
                    for bi, pt in enumerate((pts or [obj])[:3]):
                        ty = 5.42 + bi*0.38
                        oval(sl, 0.50, ty+0.10, 0.10, 0.10, C_ACC)
                        txt(sl, pt, 0.74, ty, 12.0, 0.34, 11, C_TEXT)
                elif layout == 'roadmap':
                    oval(sl, 10.0, -0.5, 4.5, 4.5, _acc(0.12))
                    rect(sl, 0, 0, 13.33, 0.80, _bg2(0.88))
                    txt(sl, kicker, 0.50, 0.12, 6.0, 0.26, 8, C_ACC, bold=True)
                    txt(sl, title,  0.50, 0.42, 9.0, 0.72,
                        24, C_TEXT, bold=True, fn=FH)
                    rect(sl, 0.55, 2.88, 12.22, 0.04, _acc(0.32))
                    steps = pts[:4]
                    n = len(steps) or 1
                    sw = 12.22/n
                    for bi, st in enumerate(steps):
                        cx = 0.55+bi*sw+sw/2
                        oval(sl, cx-0.30, 2.70, 0.60, 0.60, _acc(0.38))
                        oval(sl, cx-0.18, 2.84, 0.36, 0.36, C_ACC)
                        txt(sl, f'{bi+1}', cx-0.18, 2.84, 0.36, 0.36, 9,
                            C_BG if not is_light else C_WHITE, bold=True, align=PP_ALIGN.CENTER)
                        bx = 0.55+bi*sw+0.10
                        cw = sw-0.20
                        rect(sl, bx, 3.54, cw, 2.86, _sur(0.70),
                             border=_acc(0.20), bw=0.5, rnd=True)
                        txt(sl, st, bx+0.14, 3.68, cw-0.28, 2.54, 11.5, C_TEXT)
                elif layout == 'comparison':
                    oval(sl, 11.0, -0.5, 4.0, 4.0, _acc(0.12))
                    rect(sl, 0, 0, 13.33, 0.72, _bg2(0.88))
                    rect(sl, 6.46, 0.72, 0.05, 5.98, _acc(0.34))
                    txt(sl, kicker, 0.50, 0.12, 5.0, 0.26, 8, C_ACC, bold=True)
                    txt(sl, title,  0.50, 0.42, 12.0,
                        0.72, 22, C_TEXT, bold=True, fn=FH)
                    rect(sl, 0.50, 0.88, 5.68, 0.40, _acc(0.20), rnd=True)
                    txt(sl, 'BEFORE', 0.68, 0.94, 5.30,
                        0.28, 8.5, C_ACC, bold=True)
                    rect(sl, 6.68, 0.88, 6.12, 0.40, _acc(0.36), rnd=True)
                    txt(sl, 'AFTER', 6.86, 0.94, 5.74,
                        0.28, 8.5, C_ACC, bold=True)
                    lp = pts[:3]
                    rp = pts[3:] or pts[:3]
                    for bi, p in enumerate(lp):
                        ty = 1.48 + bi*1.0
                        oval(sl, 0.54, ty+0.12, 0.12, 0.12, _acc(0.50))
                        txt(sl, p, 0.80, ty, 5.28, 0.88, 11.5, C_TEXT)
                    for bi, p in enumerate(rp):
                        ty = 1.48 + bi*1.0
                        oval(sl, 6.72, ty+0.12, 0.12, 0.12, C_ACC)
                        txt(sl, p, 6.98, ty, 5.80, 0.88, 11.5, C_TEXT)
                elif layout == 'closing':
                    oval(sl, -1.5, -1.0, 7.0, 7.0, _acc(0.12))
                    oval(sl, 9.0,  1.5, 6.0, 6.0, _acc(0.09))
                    rect(sl, 0, 0, 13.33, 0.08, C_ACC)
                    txt(sl, kicker, 0, 1.0, 13.33, 0.30, 9,
                        C_ACC, bold=True, align=PP_ALIGN.CENTER)
                    txt(sl, title, 0.80, 1.44, 11.73, 2.20, 44, C_TEXT,
                        bold=True, fn=FH, align=PP_ALIGN.CENTER)
                    rect(sl, 4.66, 3.74, 4.0, 0.05, C_ACC)
                    if sub:
                        txt(sl, sub, 1.0, 3.92, 11.33, 0.68, 13.5,
                            C_DIM, italic=True, align=PP_ALIGN.CENTER)
                    if stats:
                        n = min(len(stats), 3)
                        cw = 3.5
                        sx = (13.33-(n*cw+(n-1)*0.28))/2
                        for bi, st in enumerate(stats[:3]):
                            bx = sx+bi*(cw+0.28)
                            rect(sl, bx, 4.80, cw, 1.70, _sur(0.75),
                                 border=_acc(0.30), bw=0.6, rnd=True)
                            rect(sl, bx, 4.80, cw, 0.10, C_ACC)
                            txt(sl, st.get('value', ''), bx+0.14, 4.95, cw-0.28, 0.84,
                                30, C_TEXT, bold=True, fn=FH, align=PP_ALIGN.CENTER)
                            txt(sl, st.get('label', '').upper(), bx+0.14, 5.90, cw -
                                0.28, 0.30, 8, C_DIM, bold=True, align=PP_ALIGN.CENTER)
                else:  # spotlight
                    oval(sl, 9.5, -0.5, 5.0, 5.0, _acc(0.14))
                    rect(sl, 0, 0, 0.08, 6.70, C_ACC)
                    rect(sl, 7.88, 0, 5.45, 6.70, _bg2(0.85))
                    txt(sl, kicker, 0.38, 0.38, 5.5, 0.26, 8, C_ACC, bold=True)
                    txt(sl, title,  0.38, 0.76, 7.2, 1.80,
                        28, C_TEXT, bold=True, fn=FH)
                    if sub:
                        txt(sl, sub, 0.38, 2.52, 7.0,
                            0.58, 12, C_DIM, italic=True)
                    rect(sl, 0.38, 3.20, 4.8, 0.04, C_ACC)
                    if pts:
                        for bi, pt in enumerate(pts):
                            ty = 3.38 + bi*0.58
                            oval(sl, 0.38, ty+0.12, 0.10, 0.10, C_ACC)
                            txt(sl, pt, 0.62, ty, 6.90, 0.52, 11.5, C_TEXT)
                    elif obj:
                        txt(sl, obj, 0.38, 3.38, 7.0,
                            0.80, 12, C_DIM, italic=True)
                    if stats:
                        for bi, st in enumerate(stats[:3]):
                            ty = 0.50 + bi*2.02
                            rect(sl, 8.08, ty, 4.92, 1.82, _sur(0.70),
                                 border=_acc(0.22), bw=0.5, rnd=True)
                            rect(sl, 8.08, ty, 4.92, 0.12, C_ACC)
                            txt(sl, st.get('value', ''), 8.26, ty+0.17, 4.56, 1.0,
                                34, C_TEXT, bold=True, fn=FH, align=PP_ALIGN.CENTER)
                            txt(sl, st.get('label', '').upper(), 8.26, ty+1.28,
                                4.56, 0.30, 8, C_DIM, bold=True, align=PP_ALIGN.CENTER)
                    else:
                        rect(sl, 8.08, 0.50, 4.92, 5.90, _sur(0.70),
                             border=_acc(0.18), bw=0.5, rnd=True)
                        txt(sl, 'VISUAL DIRECTION', 8.28, 0.68,
                            4.52, 0.26, 7.5, C_ACC, bold=True)
                        rect(sl, 8.08, 0.92, 4.92, 0.04, _acc(0.32))
                        txt(sl, vis or 'One compelling nature-inspired visual.',
                            8.28, 1.02, 4.52, 5.10, 12, C_TEXT)

            footer(sl, i, total)

        buf = io.BytesIO()
        prs.save(buf)
        buf.seek(0)
        fname = re.sub(r'[^a-z0-9]+', '-', idea.lower()
                       )[:40] + '-pitch-deck.pptx'
        return send_file(buf,
                         mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation',
                         as_attachment=True, download_name=fname)

    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500
    try:
        from pptx import Presentation
        from pptx.util import Inches, Pt
        from pptx.dml.color import RGBColor
        from pptx.enum.text import PP_ALIGN
        from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE

        data = request.json
        idea = data.get('idea', 'ventureos')
        raw_slides = data.get('slides') or data.get('deck') or []
        slides_data = [_normalize_slide(s, i)
                       for i, s in enumerate(raw_slides)]
        if not slides_data:
            return jsonify({'error': 'No slides provided'}), 400

        # ── Theme & colour setup ───────────────────────────────────────────
        design = data.get('design_system') or DEFAULT_DECK_THEME
        palette = design.get('palette') or DEFAULT_DECK_THEME['palette']
        template_id = design.get(
            'template_id', DEFAULT_DECK_THEME['template_id'])
        theme_name = design.get('theme_name', 'VentureOS')

        def _h2r(val, fallback):
            v = _normalize_hex(val, fallback).replace('#', '')
            return RGBColor(int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16))

        def _luma(val, fb='#000000'):
            v = _normalize_hex(val, fb).replace('#', '')
            return 0.299*int(v[0:2], 16) + 0.587*int(v[2:4], 16) + 0.114*int(v[4:6], 16)

        C_BG = _h2r(palette.get('primary'),
                    DEFAULT_DECK_THEME['palette']['primary'])
        C_BG2 = _h2r(palette.get('secondary'),
                     DEFAULT_DECK_THEME['palette']['secondary'])
        C_SURF = _h2r(palette.get('surface'),
                      DEFAULT_DECK_THEME['palette']['surface'])
        C_ACC = _h2r(palette.get('accent'),
                     DEFAULT_DECK_THEME['palette']['accent'])
        C_TEXT = _h2r(palette.get('text'),
                      DEFAULT_DECK_THEME['palette']['text'])
        is_light = _luma(palette.get('primary', '#000')) > 160
        C_DIM = RGBColor(0x44, 0x55, 0x66) if is_light else RGBColor(
            0xB0, 0xC4, 0xD8)
        C_WHITE = RGBColor(0xFF, 0xFF, 0xFF)
        C_BLACK = RGBColor(0x0F, 0x0F, 0x0F)

        def _blend(a: RGBColor, b: RGBColor, t: float) -> RGBColor:
            return RGBColor(int(a[0]+(b[0]-a[0])*t),
                            int(a[1]+(b[1]-a[1])*t),
                            int(a[2]+(b[2]-a[2])*t))

        def _acc(t): return _blend(C_BG, C_ACC, t)
        def _sur(t): return _blend(C_BG, C_SURF, t)
        def _bg2(t): return _blend(C_BG, C_BG2, t)

        font_pairs = {
            'editorial-midnight': ('Georgia',          'Calibri'),
            'boardroom-ivory':    ('Cambria',           'Calibri'),
            'kinetic-ember':      ('Arial Black',       'Arial'),
            'atlas-sapphire':     ('Georgia',           'Calibri'),
            'monochrome-luxe':    ('Palatino Linotype', 'Calibri'),
            'forest-venture':     ('Georgia',           'Calibri'),
            'crimson-capital':    ('Georgia',           'Calibri'),
            'arctic-clarity':     ('Trebuchet MS',      'Calibri'),
            'violet-epoch':       ('Georgia',           'Calibri'),
        }
        FH, FB = font_pairs.get(template_id, ('Georgia', 'Calibri'))

        prs = Presentation()
        prs.slide_width = Inches(13.33)
        prs.slide_height = Inches(7.5)
        BLANK = prs.slide_layouts[6]

        # ── Primitive helpers ──────────────────────────────────────────────
        def txt(sl, text, L, T, W, H, sz, col,
                bold=False, italic=False, align=PP_ALIGN.LEFT, fn=None):
            if not text:
                return
            tb = sl.shapes.add_textbox(
                Inches(L), Inches(T), Inches(W), Inches(H))
            tf = tb.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.alignment = align
            r = p.add_run()
            r.text = str(text)
            r.font.size = Pt(sz)
            r.font.color.rgb = col
            r.font.bold = bold
            r.font.italic = italic
            r.font.name = fn or FB
            return tb

        def rect(sl, L, T, W, H, fill, border=None, bw=0.5, rnd=False):
            st = MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE if rnd else MSO_AUTO_SHAPE_TYPE.RECTANGLE
            sh = sl.shapes.add_shape(st, Inches(
                L), Inches(T), Inches(W), Inches(H))
            sh.fill.solid()
            sh.fill.fore_color.rgb = fill
            if border:
                sh.line.color.rgb = border
                sh.line.width = Pt(bw)
            else:
                sh.line.fill.background()
            return sh

        def oval(sl, L, T, W, H, fill):
            sh = sl.shapes.add_shape(
                MSO_AUTO_SHAPE_TYPE.OVAL, Inches(L), Inches(T), Inches(W), Inches(H))
            sh.fill.solid()
            sh.fill.fore_color.rgb = fill
            sh.line.fill.background()
            return sh

        # ── Shared chrome: footer ──────────────────────────────────────────
        def footer(sl, idx, total):
            rect(sl, 0, 7.22, 13.33, 0.28, _bg2(0.8), border=None)
            rect(sl, 0, 7.22, 13.33, 0.014, _acc(0.35), border=None)
            txt(sl, 'VentureOS',   0.40, 7.28, 3.0, 0.22, 7.5, C_DIM)
            txt(sl, theme_name,    4.66, 7.28, 4.0, 0.22, 7.5, C_DIM,
                align=PP_ALIGN.CENTER)
            txt(sl, f'{idx+1:02d} / {total:02d}',
                9.50, 7.28, 3.3, 0.22, 7.5, C_DIM,
                bold=True, align=PP_ALIGN.RIGHT)

        total = len(slides_data)

        for i, sd in enumerate(slides_data):
            sl = prs.slides.add_slide(BLANK)
            layout = sd.get('layout', 'spotlight')
            title = sd.get('title') or f'Slide {i+1}'
            sub = sd.get('subtitle') or ''
            pts = (sd.get('content') or sd.get('points') or [])[:5]
            stats = (sd.get('stats') or [])[:3]
            obj = sd.get('objective') or ''
            vis = sd.get('visual_suggestion') or ''
            kicker = sd.get('type', 'story').replace('_', ' ').upper()

            # ── Full background ────────────────────────────────────────────
            sl.background.fill.solid()
            sl.background.fill.fore_color.rgb = C_BG

            # ══════════════════════════════════════════════════════════════
            # LAYOUT 1 — COVER  (full bleed, big centred hero)
            # ══════════════════════════════════════════════════════════════
            if layout == 'cover':
                # Left accent panel (40% wide)
                rect(sl, 0, 0, 5.4, 7.5, _bg2(0.9))
                # Decorative large orb bottom-left
                oval(sl, -1.2, 3.8, 5.5, 5.5, _acc(0.14))
                oval(sl, -0.4, 4.4, 3.2, 3.2, _acc(0.20))
                # Right panel slightly lighter
                rect(sl, 5.4, 0, 7.93, 7.5, _bg2(0.4))
                # Big accent orb top-right
                oval(sl, 7.5, -1.5, 7.0, 7.0, _acc(0.18))
                oval(sl, 9.5,  3.5, 4.5, 4.5, _acc(0.10))

                # Thick left accent stripe
                rect(sl, 0, 0, 0.07, 7.5, C_ACC)

                # Kicker pill
                rect(sl, 0.55, 0.55, 2.8, 0.34, _acc(0.28), rnd=True)
                txt(sl, kicker, 0.72, 0.59, 2.6, 0.26, 8, C_ACC, bold=True)

                # Giant title — left panel
                txt(sl, title, 0.55, 1.10, 4.6, 2.8, 40, C_TEXT,
                    bold=True, fn=FH)

                # Subtitle
                if sub:
                    txt(sl, sub, 0.55, 3.80, 4.5, 0.9, 13.5, C_DIM,
                        italic=True)

                # Horizontal rule
                rect(sl, 0.55, 4.72, 3.8, 0.04, _acc(0.55))

                # Idea / company label bottom-left
                txt(sl, idea.title()[:48], 0.55, 4.90, 4.4, 0.5, 11, C_DIM)

                # Right side — big decorative stat or visual cue
                if stats:
                    s0 = stats[0]
                    txt(sl, s0.get('value', ''), 6.0, 1.8, 7.0, 2.0, 72,
                        _acc(0.9), bold=True, fn=FH, align=PP_ALIGN.CENTER)
                    txt(sl, s0.get('label', '').upper(), 6.0, 4.2, 7.0, 0.4, 11,
                        C_DIM, bold=True, align=PP_ALIGN.CENTER)
                else:
                    txt(sl, vis or 'The future starts here.', 6.0, 2.6, 7.0,
                        1.6, 16, C_DIM, italic=True, align=PP_ALIGN.CENTER)

            # ══════════════════════════════════════════════════════════════
            # LAYOUT 2 — METRICS  (big numbers dominate the slide)
            # ══════════════════════════════════════════════════════════════
            elif layout == 'metrics':
                # Top accent band
                rect(sl, 0, 0, 13.33, 1.40, _bg2(0.85))
                rect(sl, 0, 1.40, 13.33, 0.05, _acc(0.50))

                # Kicker top-left
                txt(sl, kicker, 0.55, 0.20, 6.0, 0.28, 8, C_ACC, bold=True)

                # Title in top band
                txt(sl, title, 0.55, 0.52, 8.5, 0.80, 28, C_TEXT,
                    bold=True, fn=FH)

                # Stat cards — 3-up large format
                n_stats = len(stats) if stats else 0
                if n_stats:
                    card_w = (12.33 - 0.2*(n_stats-1)) / n_stats
                    for bi, st in enumerate(stats):
                        bx = 0.50 + bi*(card_w+0.20)
                        # Card bg
                        rect(sl, bx, 1.70, card_w, 3.20, _sur(0.75),
                             border=_acc(0.25), bw=0.6, rnd=True)
                        # Top accent bar inside card
                        rect(sl, bx, 1.70, card_w, 0.14, C_ACC, rnd=False)
                        # Huge stat value
                        txt(sl, st.get('value', ''), bx+0.20, 1.98,
                            card_w-0.40, 1.60, 52, C_TEXT,
                            bold=True, fn=FH, align=PP_ALIGN.CENTER)
                        # Label
                        txt(sl, st.get('label', '').upper(),
                            bx+0.20, 3.60, card_w-0.40, 0.38,
                            9, C_DIM, bold=True, align=PP_ALIGN.CENTER)

                # Bullet points below cards
                if pts:
                    for bi, pt in enumerate(pts[:3]):
                        ty = 5.22 + bi*0.42
                        oval(sl, 0.55, ty+0.10, 0.12, 0.12, C_ACC)
                        txt(sl, pt, 0.80, ty, 12.0, 0.38, 11.5, C_TEXT)
                elif obj:
                    txt(sl, obj, 0.55, 5.22, 12.0, 0.60, 12, C_DIM, italic=True)

            # ══════════════════════════════════════════════════════════════
            # LAYOUT 3 — ROADMAP  (numbered horizontal timeline)
            # ══════════════════════════════════════════════════════════════
            elif layout == 'roadmap':
                # Top band
                rect(sl, 0, 0, 13.33, 1.30, _bg2(0.85))
                rect(sl, 0, 1.30, 13.33, 0.05, _acc(0.45))

                txt(sl, kicker, 0.55, 0.18, 6.0, 0.28, 8, C_ACC, bold=True)
                txt(sl, title,  0.55, 0.48, 9.0, 0.76, 26, C_TEXT,
                    bold=True, fn=FH)
                if sub:
                    txt(sl, sub, 0.55, 1.05, 8.0, 0.34, 11, C_DIM, italic=True)

                # Horizontal connector line
                rect(sl, 0.55, 3.08, 12.22, 0.04, _acc(0.30))

                steps = pts[:4] if pts else []
                n = len(steps) or 1
                step_w = 12.22 / n
                for bi, step_txt in enumerate(steps):
                    cx = 0.55 + bi*step_w + step_w/2
                    # Circle on timeline
                    oval(sl, cx-0.35, 2.88, 0.70, 0.70, _acc(0.40))
                    oval(sl, cx-0.22, 3.01, 0.44, 0.44, C_ACC)
                    txt(sl, f'{bi+1}', cx-0.22, 3.01, 0.44, 0.44,
                        10, C_BG if not is_light else C_WHITE,
                        bold=True, align=PP_ALIGN.CENTER)
                    # Card below
                    bx = 0.55 + bi*step_w + 0.10
                    cw = step_w - 0.20
                    rect(sl, bx, 3.85, cw, 2.60, _sur(0.7),
                         border=_acc(0.20), bw=0.5, rnd=True)
                    txt(sl, step_txt, bx+0.16, 3.98, cw-0.32, 2.30,
                        11.5, C_TEXT)

                # Visual suggestion bottom strip
                if vis:
                    txt(sl, f'Visual: {vis}', 0.55, 6.70, 12.22, 0.30,
                        8.5, C_DIM, italic=True)

            # ══════════════════════════════════════════════════════════════
            # LAYOUT 4 — COMPARISON  (two-column split)
            # ══════════════════════════════════════════════════════════════
            elif layout == 'comparison':
                # Vertical divider
                rect(sl, 6.46, 0.9, 0.06, 6.3, _acc(0.35))

                # Header band
                rect(sl, 0, 0, 13.33, 0.90, _bg2(0.88))
                rect(sl, 0, 0.90, 13.33, 0.04, _acc(0.40))
                txt(sl, kicker, 0.50, 0.12, 5.0, 0.26, 8, C_ACC, bold=True)
                txt(sl, title,  0.50, 0.38, 12.3, 0.50, 22, C_TEXT,
                    bold=True, fn=FH)

                # Left column header
                rect(sl, 0.50, 1.08, 5.76, 0.44, _acc(0.22), rnd=True)
                txt(sl, 'PROBLEM / STATUS QUO', 0.68, 1.14, 5.40, 0.32,
                    9, C_ACC, bold=True)

                # Right column header
                rect(sl, 6.72, 1.08, 6.10, 0.44, _acc(0.35), rnd=True)
                txt(sl, 'OUR SOLUTION', 6.90, 1.14, 5.70, 0.32,
                    9, C_ACC, bold=True)

                left_pts = pts[:3]
                right_pts = pts[3:] or pts[:3]
                for bi, p in enumerate(left_pts):
                    ty = 1.76 + bi*0.96
                    oval(sl, 0.55, ty+0.14, 0.14, 0.14, _acc(0.50))
                    txt(sl, p, 0.82, ty, 5.30, 0.84, 12, C_TEXT)

                for bi, p in enumerate(right_pts):
                    ty = 1.76 + bi*0.96
                    oval(sl, 6.78, ty+0.14, 0.14, 0.14, C_ACC)
                    txt(sl, p, 7.06, ty, 5.82, 0.84, 12, C_TEXT)

                if sub:
                    txt(sl, sub, 0.50, 6.60, 12.3, 0.40, 10.5,
                        C_DIM, italic=True)

            # ══════════════════════════════════════════════════════════════
            # LAYOUT 5 — CLOSING / CTA  (centred, bold, minimal)
            # ══════════════════════════════════════════════════════════════
            elif layout == 'closing':
                # Full-bleed accent bar at top
                rect(sl, 0, 0, 13.33, 0.10, C_ACC)
                # Large ambient orbs
                oval(sl, -2.0, -1.5, 8.0, 8.0, _acc(0.12))
                oval(sl, 7.5,  1.0,  7.0, 7.0, _acc(0.10))

                # Centred layout
                txt(sl, kicker, 0, 1.10, 13.33, 0.32, 9, C_ACC,
                    bold=True, align=PP_ALIGN.CENTER)

                # Giant title centred
                txt(sl, title, 0.80, 1.55, 11.73, 2.0, 44, C_TEXT,
                    bold=True, fn=FH, align=PP_ALIGN.CENTER)

                rect(sl, 4.66, 3.55, 4.0, 0.05, _acc(0.55))

                if sub:
                    txt(sl, sub, 1.0, 3.72, 11.33, 0.70, 14, C_DIM,
                        italic=True, align=PP_ALIGN.CENTER)

                # CTA stat callouts (up to 3)
                if stats:
                    n_s = len(stats)
                    sw = min(n_s, 3)
                    cw = 3.6
                    start_x = (13.33 - (sw*cw + (sw-1)*0.30)) / 2
                    for bi, st in enumerate(stats[:3]):
                        bx = start_x + bi*(cw+0.30)
                        rect(sl, bx, 4.60, cw, 1.60, _sur(0.75),
                             border=_acc(0.30), bw=0.6, rnd=True)
                        rect(sl, bx, 4.60, cw, 0.10, C_ACC, rnd=False)
                        txt(sl, st.get('value', ''), bx+0.15, 4.76,
                            cw-0.30, 0.80, 32, C_TEXT,
                            bold=True, fn=FH, align=PP_ALIGN.CENTER)
                        txt(sl, st.get('label', '').upper(),
                            bx+0.15, 5.60, cw-0.30, 0.32,
                            8.5, C_DIM, bold=True, align=PP_ALIGN.CENTER)
                elif pts:
                    combined = '   ·   '.join(pts[:3])
                    txt(sl, combined, 1.0, 4.70, 11.33, 0.50, 12,
                        C_DIM, align=PP_ALIGN.CENTER)

                # Bottom accent bar
                rect(sl, 0, 7.40, 13.33, 0.10, C_ACC)

            # ══════════════════════════════════════════════════════════════
            # LAYOUT 6 — SPOTLIGHT  (default: split left-text / right-card)
            # ══════════════════════════════════════════════════════════════
            else:
                # Right panel background
                rect(sl, 7.90, 0, 5.43, 7.5, _bg2(0.85))
                # Top-right orb
                oval(sl, 8.5, -1.0, 5.5, 5.5, _acc(0.18))
                oval(sl, 9.5,  4.0, 3.8, 3.8, _acc(0.10))

                # Left accent bar
                rect(sl, 0, 0, 0.08, 7.5, C_ACC)

                # Kicker
                txt(sl, kicker, 0.38, 0.42, 5.5, 0.28, 8, C_ACC, bold=True)

                # Title
                txt(sl, title, 0.38, 0.82, 7.2, 1.80, 30, C_TEXT,
                    bold=True, fn=FH)

                # Subtitle
                if sub:
                    txt(sl, sub, 0.38, 2.56, 7.0, 0.60, 12.5, C_DIM,
                        italic=True)

                # Thin rule
                rect(sl, 0.38, 3.22, 5.0, 0.04, _acc(0.40))

                # Bullet points
                if pts:
                    for bi, pt in enumerate(pts):
                        ty = 3.42 + bi*0.58
                        rect(sl, 0.38, ty+0.08, 0.22, 0.22, _acc(0.30),
                             rnd=True)
                        txt(sl, f'{bi+1}', 0.38, ty+0.08, 0.22, 0.22,
                            7, C_ACC, bold=True, align=PP_ALIGN.CENTER)
                        txt(sl, pt, 0.72, ty, 6.90, 0.52, 12, C_TEXT)
                elif obj:
                    txt(sl, obj, 0.38, 3.42, 7.0, 0.80, 12.5, C_DIM,
                        italic=True)

                # Stat boxes stacked on right panel
                if stats:
                    for bi, st in enumerate(stats[:3]):
                        ty = 0.70 + bi*2.10
                        rect(sl, 8.10, ty, 4.90, 1.82, _sur(0.7),
                             border=_acc(0.22), bw=0.5, rnd=True)
                        rect(sl, 8.10, ty, 4.90, 0.12, C_ACC, rnd=False)
                        txt(sl, st.get('value', ''), 8.28, ty+0.18,
                            4.52, 1.0, 36, C_TEXT,
                            bold=True, fn=FH, align=PP_ALIGN.CENTER)
                        txt(sl, st.get('label', '').upper(),
                            8.28, ty+1.30, 4.52, 0.30,
                            8.5, C_DIM, bold=True, align=PP_ALIGN.CENTER)
                else:
                    # Visual cue card
                    rect(sl, 8.10, 0.70, 4.90, 5.80, _sur(0.7),
                         border=_acc(0.18), bw=0.5, rnd=True)
                    txt(sl, 'VISUAL DIRECTION', 8.30, 0.88, 4.50, 0.28,
                        7.5, C_ACC, bold=True)
                    rect(sl, 8.10, 1.12, 4.90, 0.04, _acc(0.30))
                    txt(sl, vis or 'Use one dominant proof visual.',
                        8.30, 1.22, 4.50, 4.90, 12, C_TEXT)

            # ── Shared footer ──────────────────────────────────────────────
            footer(sl, i, total)

        buf = io.BytesIO()
        prs.save(buf)
        buf.seek(0)
        fname = re.sub(r'[^a-z0-9]+', '-', idea.lower()
                       )[:40] + '-pitch-deck.pptx'
        return send_file(buf,
                         mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation',
                         as_attachment=True, download_name=fname)

    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500


# ── SHARE / REPORT ─────────────────────────────────────────────────────────
@app.route('/report/save', methods=['POST'])
def save_report():
    data = request.json
    report_id = str(uuid.uuid4())[:8]
    path = os.path.join(REPORTS_DIR, f'{report_id}.json')
    with open(path, 'w') as f:
        json.dump(data, f)
    return jsonify({'id': report_id, 'url': f'/report/{report_id}'})


@app.route('/report/<report_id>')
def view_report(report_id):
    path = os.path.join(REPORTS_DIR, f'{report_id}.json')
    if not os.path.exists(path):
        return 'Report not found', 404
    return render_template('index.html')


# ── RUN ────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True, threaded=True)
