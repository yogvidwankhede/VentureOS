import uuid
from flask import request, jsonify, render_template
import random
import json
from agents.pivot_agent import run_pivot_suggester
from agents.prototype_agent import run_prototype_generator
from agents.orchestrator import run_ventureOS_stream, get_llm
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from flask import Flask, request, jsonify, render_template, Response, stream_with_context
from dotenv import load_dotenv
import os
from flask import send_file
import io
load_dotenv()

os.makedirs('reports', exist_ok=True)

app = Flask(__name__)


# ── ADD THIS ROUTE TO YOUR app.py ──
# Also add to imports at top of app.py:
#   from pptx import Presentation
#   from pptx.util import Inches, Pt
#   from pptx.dml.color import RGBColor
#   import io

@app.route('/download_pptx', methods=['POST'])
def download_pptx():
    """Generate a real PPTX from slide data sent by the frontend"""
    try:
        from pptx import Presentation
        from pptx.util import Inches, Pt
        from pptx.dml.color import RGBColor
        from pptx.enum.text import PP_ALIGN
        import io

        data = request.json
        slides_data = data.get('slides', [])
        idea = data.get('idea', 'ventureos')

        if not slides_data:
            return jsonify({'error': 'No slides provided'}), 400

        # Theme backgrounds and accents
        THEMES = [
            {'bg': (0x0f, 0x17, 0x2a), 'accent': (0x81, 0x8c, 0xf8)},  # title
            {'bg': (0x1e, 0x1b, 0x4b), 'accent': (
                0x81, 0x8c, 0xf8)},  # theme-0
            {'bg': (0x0f, 0x17, 0x2a), 'accent': (
                0x38, 0xbd, 0xf8)},  # theme-1
            {'bg': (0x7c, 0x3a, 0xed), 'accent': (
                0xf9, 0xa8, 0xd4)},  # theme-2
        ]

        prs = Presentation()
        prs.slide_width = Inches(13.33)
        prs.slide_height = Inches(7.5)
        blank = prs.slide_layouts[6]

        for i, sd in enumerate(slides_data):
            slide = prs.slides.add_slide(blank)

            # Background color — cycle through themes
            theme = THEMES[i % len(THEMES)]
            bg = slide.background.fill
            bg.solid()
            bg.fore_color.rgb = RGBColor(*theme['bg'])

            accent = RGBColor(*theme['accent'])
            white = RGBColor(0xFF, 0xFF, 0xFF)
            white_dim = RGBColor(0xCC, 0xCC, 0xCC)

            def add_text(text, left, top, width, height, size, color, bold=False, align=PP_ALIGN.LEFT, italic=False):
                txBox = slide.shapes.add_textbox(
                    Inches(left), Inches(top), Inches(width), Inches(height)
                )
                tf = txBox.text_frame
                tf.word_wrap = True
                p = tf.paragraphs[0]
                p.alignment = align
                run = p.add_run()
                run.text = text
                run.font.size = Pt(size)
                run.font.color.rgb = color
                run.font.bold = bold
                run.font.italic = italic

            # LABEL
            label = sd.get('label', f"SLIDE {sd.get('slide_number', i+1)}")
            add_text(label, 0.8, 0.45, 11.5, 0.4, 9, accent, bold=True)

            # HEADLINE
            headline = sd.get('headline', '')
            if headline:
                has_stats = bool(sd.get('stats'))
                add_text(headline, 0.8, 0.95, 11.5,
                         1.6 if has_stats else 2.2,
                         28 if has_stats else 34, white)

            # DIVIDER — thin rectangle
            from pptx.util import Emu
            div = slide.shapes.add_shape(
                1,  # MSO_SHAPE_TYPE.RECTANGLE
                Inches(0.8), Inches(3.0 if sd.get('stats') else 3.5),
                Inches(0.6), Inches(0.04)
            )
            div.fill.solid()
            div.fill.fore_color.rgb = accent
            div.line.fill.background()

            content_top = 3.2 if sd.get('stats') else 3.7

            # BULLET POINTS
            points = sd.get('points', [])
            if points and not sd.get('stats'):
                combined = '\n'.join(f'  \u2192  {p}' for p in points)
                add_text(combined, 0.8, content_top, 11.5, 3.0, 14, white_dim)

            # BODY TEXT (no bullets, no stats)
            body = sd.get('subheadline', '')
            if body and not points and not sd.get('stats'):
                add_text(body, 0.8, content_top, 11.5, 2.0, 14, white_dim)

            # STATS BOXES
            stats = sd.get('stats', [])
            if stats:
                count = len(stats)
                box_w = 3.4
                gap = (11.5 - count * box_w) / (count + 1)
                top_y = 5.1

                for bi, stat in enumerate(stats):
                    bx = 0.8 + bi * (box_w + gap) + gap

                    # Box background (white 15% opacity via shape)
                    rect = slide.shapes.add_shape(
                        1, Inches(bx), Inches(top_y), Inches(
                            box_w), Inches(1.6)
                    )
                    rect.fill.solid()
                    rect.fill.fore_color.rgb = RGBColor(0x2a, 0x2a, 0x5a)
                    rect.line.color.rgb = RGBColor(0x4a, 0x4a, 0x8a)

                    num = stat.get('num', '')
                    lbl = stat.get('label', '')
                    if num:
                        add_text(num, bx, top_y + 0.15, box_w, 0.8,
                                 26, white, align=PP_ALIGN.CENTER)
                    if lbl:
                        add_text(lbl, bx, top_y + 1.1, box_w, 0.4,
                                 9, white_dim, align=PP_ALIGN.CENTER)

            # WATERMARK
            add_text('VentureOS', 9.5, 0.15, 3.0, 0.3, 9, RGBColor(
                0x66, 0x66, 0x88), align=PP_ALIGN.RIGHT)

            # SLIDE NUMBER
            slide_num = f"{sd.get('slide_number', i+1)} / {len(slides_data)}"
            add_text(slide_num, 9.5, 7.05, 3.0, 0.3, 9, RGBColor(
                0x66, 0x66, 0x88), align=PP_ALIGN.RIGHT)

        # Save to buffer and return as file download
        buf = io.BytesIO()
        prs.save(buf)
        buf.seek(0)

        fname = idea.lower().replace(' ', '-')[:40] + '-pitch-deck.pptx'

        return send_file(
            buf,
            mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation',
            as_attachment=True,
            download_name=fname
        )

    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500
    
@app.route('/')
def index():
    return render_template('index.html')


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


# Simple file-based report store (no DB needed for hackathon)
REPORTS_DIR = os.path.join(os.path.dirname(__file__), 'reports')
os.makedirs(REPORTS_DIR, exist_ok=True)


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
    with open(path) as f:
        data = json.load(f)
    return render_template('index.html', prefill=json.dumps(data))

@app.route('/prototype', methods=['POST'])
def prototype():
    data = request.json
    idea = data.get('idea', '')
    product_strategy = data.get('product_strategy', {})
    # Accept a seed for variety — if not provided, generate random
    seed = data.get('seed', random.randint(0, 100))
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


@app.route('/slides', methods=['POST'])
def generate_slides():
    """Proxy slide generation through Flask to avoid CORS"""
    data = request.json
    idea = data.get('idea', '')
    context = data.get('context', {})

    if not idea:
        return jsonify({'error': 'No idea provided'}), 400

    m = context.get('market_research', {})
    c = context.get('competitor_analysis', {})
    p = context.get('product_strategy', {})
    sc = context.get('scorecard', {})
    pitch = context.get('pitch', {})
    deck = pitch.get('deck', [])

    prompt = f"""You are a world-class pitch deck designer. Generate a complete 10-slide investor pitch deck as a JSON array.

Startup idea: "{idea}"
Market size: {m.get('market_size','—')}, Growth: {m.get('growth_rate','—')}
Target customer: {m.get('target_customer','—')}
Pain point: {m.get('pain_point','—')}
Opportunity: {m.get('opportunity_summary','—')}
Competitors whitespace: {c.get('whitespace','—')}
Fundability score: {sc.get('total','—')}/100 — {sc.get('verdict','—')}
Biggest strength: {sc.get('biggest_strength','—')}
Biggest risk: {sc.get('biggest_risk','—')}
Pitch outline: {json.dumps(deck[:5])}
Monetization: {json.dumps(p.get('monetization', [])[:2])}

Return ONLY a valid JSON array of exactly 10 slide objects. No markdown, no backticks, no explanation.

Each object:
{{
  "slide_number": 1,
  "type": "title|problem|solution|market|product|business_model|traction|competition|team|ask",
  "headline": "Short punchy headline max 8 words",
  "subheadline": "One sentence supporting statement",
  "points": ["bullet 1 max 10 words", "bullet 2", "bullet 3"],
  "stat1_num": "$4.2B",
  "stat1_label": "Total Market",
  "stat2_num": "28%",
  "stat2_label": "Annual Growth",
  "stat3_num": "500K",
  "stat3_label": "Target Users"
}}

Use real numbers from context. Leave stat fields as empty string if not relevant."""

    try:
        llm = get_llm()
        from langchain.schema import HumanMessage
        response = llm.invoke([HumanMessage(content=prompt)])
        text = response.content.strip()

        # Strip markdown fences
        import re
        text = re.sub(r'```json', '', text)
        text = re.sub(r'```', '', text)
        text = text.strip()

        start = text.find('[')
        end = text.rfind(']') + 1
        if start == -1:
            return jsonify({'error': 'No JSON array in response'}), 500
        text = text[start:end]

        slides = json.loads(text)
        return jsonify({'slides': slides})
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500

if __name__ == '__main__':
    app.run(debug=True, threaded=True)
