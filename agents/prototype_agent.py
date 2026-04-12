from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os
import re
import random
load_dotenv()


STYLE_THEMES = [
    {"name": "Clean Light",   "accent": "#2563eb", "bg": "#fafaf8", "surface": "#ffffff",
        "surface2": "#f5f5f2", "border": "#e8e8e4", "text": "#1a1a18", "text2": "#4a4a46", "text3": "#8a8a84"},
    {"name": "Deep Dark",     "accent": "#22c55e", "bg": "#0a0a0a", "surface": "#141414",
        "surface2": "#1e1e1e", "border": "#2a2a2a", "text": "#f0f0ee", "text2": "#a0a09c", "text3": "#606060"},
    {"name": "Warm Minimal",  "accent": "#f97316", "bg": "#fffbf5", "surface": "#ffffff",
        "surface2": "#faf5ee", "border": "#ede9e0", "text": "#1c1917", "text2": "#57534e", "text3": "#a8a29e"},
    {"name": "Slate Pro",     "accent": "#6366f1", "bg": "#f8fafc", "surface": "#ffffff",
        "surface2": "#f1f5f9", "border": "#e2e8f0", "text": "#0f172a", "text2": "#475569", "text3": "#94a3b8"},
    {"name": "Carbon",        "accent": "#a855f7", "bg": "#09090b", "surface": "#18181b",
        "surface2": "#27272a", "border": "#3f3f46", "text": "#fafafa", "text2": "#a1a1aa", "text3": "#71717a"},
]

# The exact same CSS foundation VentureOS uses — guaranteed quality output
VENTUREOS_DESIGN_SYSTEM = """
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Geist:wght@300;400;500;600&display=swap" rel="stylesheet">
  <style>
    /* === RESET === */
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html {{ scroll-behavior: smooth; font-size: 16px; }}
    body {{ font-family: 'Geist', -apple-system, BlinkMacSystemFont, sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; -webkit-font-smoothing: antialiased; font-size: 15px; }}
    a {{ text-decoration: none; color: inherit; }}
    ul, ol {{ list-style: none; }}
    img {{ display: block; max-width: 100%; }}
    button {{ cursor: pointer; font-family: inherit; }}
    input, textarea {{ font-family: inherit; }}

    /* === DESIGN TOKENS === */
    :root {{
      --bg: {bg};
      --surface: {surface};
      --surface2: {surface2};
      --border: {border};
      --text: {text};
      --text-2: {text2};
      --text-3: {text3};
      --accent: {accent};
      --accent-rgb: {accent_rgb};
      --accent-light: color-mix(in srgb, var(--accent) 10%, transparent);
      --radius: 12px;
      --radius-sm: 8px;
      --shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
      --shadow-md: 0 4px 16px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04);
      --shadow-lg: 0 16px 48px rgba(0,0,0,0.12);
    }}

    /* === TYPOGRAPHY SCALE === */
    .serif {{ font-family: 'Instrument Serif', Georgia, serif; }}
    .serif-italic {{ font-family: 'Instrument Serif', Georgia, serif; font-style: italic; }}
    h1, h2, h3 {{ font-family: 'Instrument Serif', Georgia, serif; font-weight: 400; letter-spacing: -0.02em; line-height: 1.1; }}
    h1 {{ font-size: clamp(32px, 5vw, 56px); }}
    h2 {{ font-size: clamp(24px, 3.5vw, 40px); }}
    h3 {{ font-size: clamp(18px, 2vw, 22px); }}
    p {{ color: var(--text-2); font-weight: 300; line-height: 1.7; }}

    /* === LAYOUT === */
    .container {{ max-width: 1080px; margin: 0 auto; padding: 0 32px; }}
    .section {{ padding: 80px 0; }}
    .section-sm {{ padding: 48px 0; }}
    .divider {{ height: 1px; background: var(--border); }}

    /* === NAV === */
    nav {{
      position: sticky; top: 0; z-index: 100;
      background: rgba(var(--bg-raw, 250,250,248), 0.92);
      backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border);
      height: 56px; display: flex; align-items: center;
      transition: all 0.2s;
    }}
    .nav-inner {{ display: flex; align-items: center; justify-content: space-between; width: 100%; max-width: 1080px; margin: 0 auto; padding: 0 32px; }}
    .nav-brand {{ display: flex; align-items: center; gap: 10px; font-size: 15px; font-weight: 600; letter-spacing: -0.3px; }}
    .nav-mark {{ width: 28px; height: 28px; background: var(--text); border-radius: 6px; display: flex; align-items: center; justify-content: center; color: var(--bg); font-size: 13px; font-weight: 600; font-family: 'Instrument Serif', serif; flex-shrink: 0; }}
    .nav-links {{ display: flex; align-items: center; gap: 28px; }}
    .nav-links a {{ font-size: 14px; color: var(--text-2); transition: color 0.15s; }}
    .nav-links a:hover {{ color: var(--text); }}
    .nav-actions {{ display: flex; align-items: center; gap: 8px; }}
    .btn-ghost {{ background: none; border: 1px solid var(--border); color: var(--text-2); padding: 7px 16px; border-radius: var(--radius-sm); font-size: 13px; font-weight: 500; transition: all 0.15s; }}
    .btn-ghost:hover {{ border-color: var(--text-2); color: var(--text); background: var(--surface2); }}
    .btn-primary {{ background: var(--text); color: var(--bg); border: none; padding: 8px 18px; border-radius: var(--radius-sm); font-size: 13px; font-weight: 500; transition: opacity 0.15s; }}
    .btn-primary:hover {{ opacity: 0.82; }}
    .btn-accent {{ background: var(--accent); color: white; border: none; padding: 12px 28px; border-radius: var(--radius-sm); font-size: 14px; font-weight: 500; transition: opacity 0.15s, transform 0.15s; display: inline-flex; align-items: center; gap: 8px; }}
    .btn-accent:hover {{ opacity: 0.88; transform: translateY(-1px); }}
    .btn-outline {{ background: var(--surface); color: var(--text); border: 1px solid var(--border); padding: 12px 28px; border-radius: var(--radius-sm); font-size: 14px; font-weight: 500; transition: all 0.15s; display: inline-flex; align-items: center; gap: 8px; }}
    .btn-outline:hover {{ background: var(--surface2); border-color: var(--text-2); }}

    /* === BADGE === */
    .badge {{ display: inline-flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 500; color: var(--accent); background: var(--accent-light); border: 1px solid rgba(var(--accent-rgb), 0.2); padding: 4px 12px; border-radius: 50px; margin-bottom: 20px; }}

    /* === HERO === */
    .hero {{ text-align: center; padding: 96px 0 80px; }}
    .hero h1 {{ margin-bottom: 20px; }}
    .hero h1 em {{ font-style: italic; color: var(--text-2); }}
    .hero p {{ font-size: 17px; max-width: 480px; margin: 0 auto 36px; }}
    .hero-actions {{ display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; }}

    /* === STATS ROW === */
    .stats-row {{ display: grid; grid-template-columns: repeat(3, 1fr); border-top: 1px solid var(--border); border-bottom: 1px solid var(--border); }}
    .stat-cell {{ padding: 28px 32px; border-right: 1px solid var(--border); text-align: center; }}
    .stat-cell:last-child {{ border-right: none; }}
    .stat-num {{ font-family: 'Instrument Serif', serif; font-size: 36px; font-weight: 400; letter-spacing: -1px; display: block; color: var(--text); }}
    .stat-label {{ font-size: 13px; color: var(--text-3); margin-top: 4px; }}

    /* === SECTION LABELS === */
    .sec-label {{ font-size: 11px; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: var(--text-3); margin-bottom: 12px; }}
    .sec-title {{ margin-bottom: 12px; }}
    .sec-desc {{ font-size: 15px; color: var(--text-2); font-weight: 300; max-width: 400px; line-height: 1.65; margin-bottom: 48px; }}

    /* === CARDS === */
    .card {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 28px; box-shadow: var(--shadow); transition: border-color 0.2s, transform 0.2s, box-shadow 0.2s; }}
    .card:hover {{ border-color: var(--text-3); transform: translateY(-2px); box-shadow: var(--shadow-md); }}
    .card-icon {{ font-size: 22px; margin-bottom: 16px; }}
    .card-title {{ font-size: 15px; font-weight: 600; margin-bottom: 8px; color: var(--text); letter-spacing: -0.2px; }}
    .card-desc {{ font-size: 13.5px; color: var(--text-2); font-weight: 300; line-height: 1.65; }}

    /* === GRID LAYOUTS === */
    .grid-3 {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 1px; background: var(--border); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; }}
    .grid-3 .card {{ border: none; border-radius: 0; box-shadow: none; }}
    .grid-3 .card:hover {{ transform: none; background: var(--surface2); }}
    .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}

    /* === PRODUCT MOCKUP === */
    .mockup-wrap {{ background: var(--surface2); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; box-shadow: var(--shadow-lg); }}
    .mockup-bar {{ background: var(--surface); border-bottom: 1px solid var(--border); padding: 12px 16px; display: flex; align-items: center; gap: 8px; }}
    .mockup-dot {{ width: 10px; height: 10px; border-radius: 50%; }}
    .mockup-url {{ flex: 1; background: var(--surface2); border: 1px solid var(--border); border-radius: 5px; padding: 4px 12px; font-size: 11px; color: var(--text-3); margin: 0 12px; }}
    .mockup-body {{ display: flex; min-height: 420px; }}
    .mockup-sidebar {{ width: 200px; border-right: 1px solid var(--border); background: var(--surface); padding: 16px; flex-shrink: 0; }}
    .mockup-sidebar-item {{ display: flex; align-items: center; gap: 8px; padding: 8px 10px; border-radius: 6px; font-size: 12px; color: var(--text-2); margin-bottom: 2px; font-weight: 300; }}
    .mockup-sidebar-item.active {{ background: var(--accent-light); color: var(--accent); font-weight: 500; }}
    .mockup-main {{ flex: 1; padding: 20px; }}
    .mockup-header {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }}
    .mockup-title {{ font-size: 14px; font-weight: 600; color: var(--text); }}
    .mockup-btn {{ background: var(--accent); color: white; padding: 5px 12px; border-radius: 5px; font-size: 11px; font-weight: 500; }}
    .mockup-stats {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 20px; }}
    .mockup-stat {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 12px; }}
    .mockup-stat-num {{ font-family: 'Instrument Serif', serif; font-size: 20px; color: var(--text); display: block; letter-spacing: -0.5px; }}
    .mockup-stat-lbl {{ font-size: 10px; color: var(--text-3); margin-top: 2px; text-transform: uppercase; letter-spacing: 0.06em; }}
    .mockup-table {{ width: 100%; border-collapse: collapse; }}
    .mockup-table th {{ font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-3); padding: 8px 10px; text-align: left; border-bottom: 2px solid var(--border); }}
    .mockup-table td {{ font-size: 12px; padding: 9px 10px; border-bottom: 1px solid var(--border); color: var(--text-2); font-weight: 300; }}
    .mockup-table tr:last-child td {{ border-bottom: none; }}
    .mockup-tag {{ display: inline-block; font-size: 10px; font-weight: 600; padding: 2px 8px; border-radius: 4px; }}
    .tag-green {{ background: #f0fdf4; color: #16a34a; }}
    .tag-amber {{ background: #fffbeb; color: #d97706; }}
    .tag-blue {{ background: #eff6ff; color: #2563eb; }}

    /* === CHART === */
    .chart-wrap {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 16px; margin-top: 12px; }}
    .chart-title {{ font-size: 11px; font-weight: 600; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 12px; }}
    .chart-bars {{ display: flex; align-items: flex-end; gap: 6px; height: 60px; }}
    .chart-bar {{ flex: 1; border-radius: 3px 3px 0 0; background: var(--accent); opacity: 0.8; transition: opacity 0.2s; }}
    .chart-bar:hover {{ opacity: 1; }}

    /* === TESTIMONIALS === */
    .testimonial {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 24px; box-shadow: var(--shadow); }}
    .testimonial-stars {{ color: #f59e0b; font-size: 13px; margin-bottom: 12px; letter-spacing: 2px; }}
    .testimonial-text {{ font-size: 14px; color: var(--text-2); font-weight: 300; line-height: 1.7; margin-bottom: 16px; font-style: italic; }}
    .testimonial-author {{ display: flex; align-items: center; gap: 10px; }}
    .avatar {{ width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 600; color: white; flex-shrink: 0; }}
    .author-name {{ font-size: 13px; font-weight: 600; color: var(--text); }}
    .author-role {{ font-size: 12px; color: var(--text-3); }}

    /* === PRICING === */
    .pricing-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }}
    .pricing-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 28px; position: relative; }}
    .pricing-card.featured {{ border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent), var(--shadow-md); }}
    .pricing-popular {{ position: absolute; top: -10px; left: 50%; transform: translateX(-50%); background: var(--accent); color: white; font-size: 10px; font-weight: 700; padding: 3px 12px; border-radius: 50px; white-space: nowrap; }}
    .pricing-tier {{ font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: var(--text-3); margin-bottom: 12px; }}
    .pricing-price {{ font-family: 'Instrument Serif', serif; font-size: 40px; font-weight: 400; letter-spacing: -2px; color: var(--text); line-height: 1; margin-bottom: 4px; }}
    .pricing-period {{ font-size: 13px; color: var(--text-3); margin-bottom: 20px; font-weight: 300; }}
    .pricing-features {{ display: flex; flex-direction: column; gap: 8px; margin-bottom: 24px; }}
    .pricing-feature {{ display: flex; align-items: center; gap: 8px; font-size: 13.5px; color: var(--text-2); font-weight: 300; }}
    .pricing-feature::before {{ content: '✓'; color: var(--accent); font-weight: 700; font-size: 12px; flex-shrink: 0; }}
    .pricing-divider {{ height: 1px; background: var(--border); margin: 20px 0; }}

    /* === FAQ === */
    .faq-item {{ border-bottom: 1px solid var(--border); }}
    .faq-question {{ display: flex; align-items: center; justify-content: space-between; padding: 18px 0; cursor: pointer; font-size: 14px; font-weight: 500; color: var(--text); user-select: none; }}
    .faq-question:hover {{ color: var(--accent); }}
    .faq-icon {{ font-size: 18px; color: var(--text-3); transition: transform 0.2s; flex-shrink: 0; }}
    .faq-item.open .faq-icon {{ transform: rotate(45deg); }}
    .faq-answer {{ font-size: 14px; color: var(--text-2); font-weight: 300; line-height: 1.7; max-height: 0; overflow: hidden; transition: max-height 0.3s ease, padding 0.3s ease; }}
    .faq-item.open .faq-answer {{ max-height: 200px; padding-bottom: 16px; }}

    /* === CTA SECTION === */
    .cta-section {{ background: var(--text); padding: 80px 0; text-align: center; }}
    .cta-section h2 {{ color: var(--bg); margin-bottom: 12px; }}
    .cta-section p {{ color: rgba(255,255,255,0.6); margin-bottom: 32px; max-width: 400px; margin-left: auto; margin-right: auto; }}
    .cta-input-row {{ display: flex; gap: 8px; justify-content: center; flex-wrap: wrap; max-width: 480px; margin: 0 auto; }}
    .cta-input {{ flex: 1; min-width: 220px; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: white; padding: 11px 16px; border-radius: var(--radius-sm); font-size: 14px; outline: none; font-family: inherit; }}
    .cta-input::placeholder {{ color: rgba(255,255,255,0.4); }}
    .cta-btn {{ background: var(--accent); color: white; border: none; padding: 11px 24px; border-radius: var(--radius-sm); font-size: 14px; font-weight: 500; font-family: inherit; cursor: pointer; white-space: nowrap; transition: opacity 0.15s; }}
    .cta-btn:hover {{ opacity: 0.88; }}

    /* === FOOTER === */
    footer {{ border-top: 1px solid var(--border); padding: 48px 0 24px; }}
    .footer-top {{ display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 48px; margin-bottom: 40px; }}
    .footer-brand-desc {{ font-size: 13.5px; color: var(--text-3); font-weight: 300; margin-top: 10px; line-height: 1.6; max-width: 200px; }}
    .footer-col-title {{ font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: var(--text-3); margin-bottom: 14px; }}
    .footer-link {{ display: block; font-size: 13.5px; color: var(--text-2); font-weight: 300; margin-bottom: 8px; transition: color 0.15s; }}
    .footer-link:hover {{ color: var(--text); }}
    .footer-bottom {{ border-top: 1px solid var(--border); padding-top: 20px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; }}
    .footer-copy {{ font-size: 12px; color: var(--text-3); }}
    .footer-legal {{ display: flex; gap: 20px; }}
    .footer-legal a {{ font-size: 12px; color: var(--text-3); transition: color 0.15s; }}
    .footer-legal a:hover {{ color: var(--text); }}

    /* === HOVER BAR ANIMATIONS === */
    @keyframes fadeUp {{ from {{ opacity: 0; transform: translateY(16px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    .fade-up {{ animation: fadeUp 0.5s ease both; }}
    .fade-up-2 {{ animation: fadeUp 0.5s 0.1s ease both; }}
    .fade-up-3 {{ animation: fadeUp 0.5s 0.2s ease both; }}

    /* === RESPONSIVE === */
    @media (max-width: 768px) {{
      .container {{ padding: 0 20px; }}
      .grid-3 {{ grid-template-columns: 1fr; }}
      .grid-2 {{ grid-template-columns: 1fr; }}
      .pricing-grid {{ grid-template-columns: 1fr; }}
      .footer-top {{ grid-template-columns: 1fr 1fr; gap: 32px; }}
      .stats-row {{ grid-template-columns: 1fr; }}
      .stat-cell {{ border-right: none; border-bottom: 1px solid var(--border); }}
      .stat-cell:last-child {{ border-bottom: none; }}
      nav .nav-links {{ display: none; }}
      .mockup-sidebar {{ display: none; }}
      h1 {{ font-size: 32px; }}
      h2 {{ font-size: 26px; }}
    }}
  </style>"""

PROTOTYPE_PROMPT = """You are building a real, production-quality single-page website for a startup. Use the EXACT design system provided — every CSS class is already defined. Your job is to write great HTML content using these classes.

STARTUP IDEA: {idea}
THEME: {theme_name}
KEY FEATURES: {features}
TARGET CUSTOMER: {target_customer}
PAIN POINT: {pain_point}

INSTRUCTIONS:
- Use ONLY the CSS classes defined in the design system — do not add any new <style> tags or inline styles except for color variations on avatar backgrounds (e.g. style="background:#6366f1")
- All copy must be specific to this startup — no generic placeholder text
- Use realistic fake data (real-sounding names, companies, numbers)
- Every section below is REQUIRED

Write the BODY content only (everything inside <body>). Start with <nav> and end with </footer>.

REQUIRED SECTIONS IN ORDER:

1. <nav> — sticky nav with .nav-inner, .nav-brand (with .nav-mark showing first letter of product), .nav-links (3 links), .nav-actions (.btn-ghost + .btn-primary)

2. HERO — <section class="hero section"> with .container, .badge, h1 with <em> for italic word, <p>, .hero-actions with .btn-accent and .btn-outline
   Then a .mockup-wrap showing the ACTUAL PRODUCT UI:
   - .mockup-bar with 3 .mockup-dot (colors: #ff5f57 #febc2e #28c840) and .mockup-url
   - .mockup-body with .mockup-sidebar (5-6 .mockup-sidebar-item, one .active) and .mockup-main
   - .mockup-main has .mockup-header (.mockup-title + .mockup-btn), .mockup-stats (3 .mockup-stat with .mockup-stat-num + .mockup-stat-lbl), then a .mockup-table (3-4 columns, 4-5 rows of realistic data with .mockup-tag spans), then a .chart-wrap (.chart-title + .chart-bars with 8 .chart-bar at varied heights like style="height:35%", style="height:72%", etc.)
   - Use REAL data specific to the startup (e.g. if it's a food app: restaurant names, order amounts, delivery times)

3. <div class="divider"></div>

4. STATS — <section class="section-sm"> with .stats-row (3 .stat-cell, each with .stat-num + .stat-label)

5. <div class="divider"></div>

6. FEATURES — <section class="section"> with .container, .sec-label, h2.sec-title, p.sec-desc, then .grid-3 (6 feature cells, each .card with .card-icon emoji, .card-title, .card-desc)

7. HOW IT WORKS — <section class="section"> with .container, .sec-label, h2, then .grid-3 with 3 cards. Each card shows step number in large serif text, step title, step description.

8. TESTIMONIALS — <section class="section"> with .container, .sec-label, h2, then .grid-3 (3 .testimonial each with .testimonial-stars ★★★★★, .testimonial-text in quotes, .testimonial-author with .avatar + name/role)
   Avatar colors: use style="background:#6366f1" style="background:#f97316" style="background:#16a34a"

9. PRICING — <section class="section"> with .container, .sec-label, h2, then .pricing-grid (3 .pricing-card, middle has .featured + .pricing-popular "Most Popular")
   Each: .pricing-tier, .pricing-price ($X), .pricing-period (/month), .pricing-features (4 .pricing-feature), .pricing-divider, .btn-accent or .btn-outline full width

10. FAQ — <section class="section"> with .container, .sec-label, h2, then 5 .faq-item each with .faq-question (text + span.faq-icon "+") and .faq-answer

11. CTA — <section class="cta-section"> with .container, h2, p, .cta-input-row (.cta-input placeholder="Enter your email" + button.cta-btn "Get started free")

12. <footer> — .container with .footer-top (4 cols: brand+desc, Product links, Company links, Social) and .footer-bottom (.footer-copy + .footer-legal)

JAVASCRIPT (add at end of body):
- FAQ toggle: document.querySelectorAll('.faq-question').forEach(q => q.addEventListener('click', () => q.parentElement.classList.toggle('open')))
- Nav scroll effect: window.addEventListener('scroll', () => document.querySelector('nav').style.boxShadow = scrollY > 10 ? '0 1px 20px rgba(0,0,0,0.08)' : 'none')

Return ONLY the HTML body content starting with <nav>. No DOCTYPE, no <html>, no <head>, no <body> tags, no explanation."""


def _hex_to_rgb(hex_color: str) -> str:
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"{r},{g},{b}"


def run_prototype_generator(idea: str, product_strategy: dict, llm, seed: int = None) -> tuple:
    if seed is None:
        seed = random.randint(0, len(STYLE_THEMES) - 1)

    theme = STYLE_THEMES[seed % len(STYLE_THEMES)]

    # Extract product details from strategy
    features, target_customer, pain_point = [
    ], 'businesses and professionals', 'inefficient manual processes'
    if isinstance(product_strategy, dict):
        mvp = product_strategy.get('mvp_features', [])
        features = [f.get('feature', '') for f in mvp[:5]
                    if isinstance(f, dict) and f.get('feature')]
        target_customer = product_strategy.get(
            'target_customer', target_customer)
        pain_point = product_strategy.get('pain_point', pain_point)

    # Build the design system CSS with theme tokens injected
    design_system = VENTUREOS_DESIGN_SYSTEM.format(
        bg=theme['bg'],
        surface=theme['surface'],
        surface2=theme['surface2'],
        border=theme['border'],
        text=theme['text'],
        text2=theme['text2'],
        text3=theme['text3'],
        accent=theme['accent'],
        accent_rgb=_hex_to_rgb(theme['accent'])
    )

    prompt = ChatPromptTemplate.from_template(PROTOTYPE_PROMPT)
    chain = prompt | llm
    response = chain.invoke({
        "idea": idea,
        "theme_name": theme["name"],
        "features": ', '.join(features) if features else 'core product capabilities',
        "target_customer": target_customer,
        "pain_point": pain_point,
    })

    body_html = response.content.strip()

    # Strip any accidental markdown wrapping
    body_html = re.sub(r"```html\s*", "", body_html)
    body_html = re.sub(r"```\s*", "", body_html)
    body_html = body_html.strip()

    # Remove any stray DOCTYPE/html/head/body wrappers the LLM might add
    body_html = re.sub(r"(?i)<!DOCTYPE[^>]*>", "", body_html)
    body_html = re.sub(r"(?i)<html[^>]*>|</html>", "", body_html)
    body_html = re.sub(r"(?i)<body[^>]*>|</body>", "", body_html)

    # If LLM included a <head> section, strip it entirely
    head_match = re.search(r"(?i)<head>.*?</head>", body_html, re.DOTALL)
    if head_match:
        body_html = body_html[head_match.end():]

    body_html = body_html.strip()

    # Build complete isolated HTML document
    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>VentureOS Prototype — {idea[:40]}</title>
{design_system}
</head>
<body>
{body_html}
</body>
</html>"""

    return full_html, theme["name"]
