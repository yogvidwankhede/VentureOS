from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os
import re
import random
load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# LAYOUT TEMPLATES — 8 completely different page structures & visual identities
# Each layout has its own design DNA, not just different colors
# ─────────────────────────────────────────────────────────────────────────────
LAYOUT_TEMPLATES = [
    {
        "id": "editorial",
        "name": "Editorial Split",
        "description": "Magazine-style split hero, editorial typography, large pull-quote section",
        "accent": "#1D4ED8", "accent2": "#3B82F6",
        "bg": "#FAFAF8", "surface": "#FFFFFF", "surface2": "#F4F3EF", "surface3": "#ECEAE4",
        "border": "#E5E3DC", "border2": "#D4D2CB",
        "text": "#111110", "text2": "#555551", "text3": "#999994",
        "font_display": "Playfair Display", "font_body": "Lato",
        "gf_url": "https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=Lato:wght@300;400;700&display=swap",
        "dark": False,
        "hero_style": "split",        # left text / right image
        "features_style": "grid3",    # 3-col card grid
        "testimonials_style": "quote",  # large pull quote + 2 cards
        "cta_style": "banner",        # full-width dark banner
    },
    {
        "id": "obsidian",
        "name": "Obsidian Dark",
        "description": "Premium dark canvas, emerald accents, full-bleed sections",
        "accent": "#6EE7B7", "accent2": "#34D399",
        "bg": "#0A0A0A", "surface": "#141414", "surface2": "#1C1C1C", "surface3": "#242424",
        "border": "#2A2A2A", "border2": "#333333",
        "text": "#F5F5F3", "text2": "#A3A3A0", "text3": "#666662",
        "font_display": "DM Serif Display", "font_body": "DM Sans",
        "gf_url": "https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap",
        "dark": True,
        "hero_style": "centered",     # big centered text, no sidebar
        "features_style": "bordered",  # borderless cells, left number
        "testimonials_style": "cards",  # dark glass cards
        "cta_style": "glow",          # glowing accent CTA
    },
    {
        "id": "neon-noir",
        "name": "Neon Noir",
        "description": "Bold magenta neon, ultra-dark, high-contrast kinetic layout",
        "accent": "#F000B8", "accent2": "#BF00FF",
        "bg": "#070010", "surface": "#0F0020", "surface2": "#160030", "surface3": "#1E0040",
        "border": "#2A0050", "border2": "#3A0070",
        "text": "#F0E8FF", "text2": "#A090C0", "text3": "#60507A",
        "font_display": "Bebas Neue", "font_body": "Space Grotesk",
        "gf_url": "https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Space+Grotesk:wght@300;400;500;600&display=swap",
        "dark": True,
        "hero_style": "diagonal",     # diagonal split with huge text
        "features_style": "zigzag",   # alternating left/right feature rows
        "testimonials_style": "slider",  # horizontal scrollable cards
        "cta_style": "neon",          # neon glow border CTA
    },
    {
        "id": "sand-ember",
        "name": "Sand & Ember",
        "description": "Warm terracotta, serif editorial, organic texture feel",
        "accent": "#E85D04", "accent2": "#F48C06",
        "bg": "#FBF7F0", "surface": "#FFFFFF", "surface2": "#F5EFE4", "surface3": "#EDE4D5",
        "border": "#E3D9C8", "border2": "#D4C9B5",
        "text": "#1A1208", "text2": "#6B5B45", "text3": "#A89880",
        "font_display": "Cormorant Garamond", "font_body": "Nunito",
        "gf_url": "https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=Nunito:wght@300;400;600&display=swap",
        "dark": False,
        "hero_style": "asymmetric",   # text left, stacked cards right
        "features_style": "icons",    # icon + title + text, no card border
        "testimonials_style": "minimal",  # just quote + author, no cards
        "cta_style": "warm",          # warm bg CTA with serif headline
    },
    {
        "id": "arctic",
        "name": "Arctic Pro",
        "description": "Crisp sky-blue SaaS style, clean grids, trust-forward design",
        "accent": "#0EA5E9", "accent2": "#38BDF8",
        "bg": "#F0F8FF", "surface": "#FFFFFF", "surface2": "#E8F4FE", "surface3": "#D6EDFD",
        "border": "#C4E2FC", "border2": "#A8D5FA",
        "text": "#0A2540", "text2": "#3A6080", "text3": "#7AABB0",
        "font_display": "Plus Jakarta Sans", "font_body": "Plus Jakarta Sans",
        "gf_url": "https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700&display=swap",
        "dark": False,
        "hero_style": "saas",         # centered + product mockup below
        "features_style": "grid3",
        "testimonials_style": "cards",
        "cta_style": "banner",
    },
    {
        "id": "charcoal-luxe",
        "name": "Charcoal Luxe",
        "description": "Gold accents on deep charcoal, luxury editorial, refined spacing",
        "accent": "#D4AF37", "accent2": "#F0C94A",
        "bg": "#111214", "surface": "#18191C", "surface2": "#202124", "surface3": "#28292C",
        "border": "#303235", "border2": "#3C3E42",
        "text": "#F2F0EA", "text2": "#A0A09A", "text3": "#65655F",
        "font_display": "Cormorant Garamond", "font_body": "Jost",
        "gf_url": "https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=Jost:wght@300;400;500;600&display=swap",
        "dark": True,
        "hero_style": "luxury",       # full-width hero, large serif, gold accents
        "features_style": "bordered",
        "testimonials_style": "quote",
        "cta_style": "gold",          # gold border CTA
    },
    {
        "id": "forest-sage",
        "name": "Forest Sage",
        "description": "Natural greens, Baskerville serif, clean & sustainable feel",
        "accent": "#16A34A", "accent2": "#22C55E",
        "bg": "#F7FAF5", "surface": "#FFFFFF", "surface2": "#EFF5EC", "surface3": "#E0EDD9",
        "border": "#D0E4C8", "border2": "#B8D4AD",
        "text": "#0F1F0A", "text2": "#456040", "text3": "#8AAA80",
        "font_display": "Libre Baskerville", "font_body": "Source Sans 3",
        "gf_url": "https://fonts.googleapis.com/css2?family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=Source+Sans+3:wght@300;400;600&display=swap",
        "dark": False,
        "hero_style": "split",
        "features_style": "icons",
        "testimonials_style": "minimal",
        "cta_style": "warm",
    },
    {
        "id": "rose-quartz",
        "name": "Rose Quartz",
        "description": "Elegant rose palette, Italiana display font, fashion-forward layout",
        "accent": "#E11D48", "accent2": "#FB7185",
        "bg": "#FFF5F7", "surface": "#FFFFFF", "surface2": "#FFF0F3", "surface3": "#FFE4EA",
        "border": "#FFD0DB", "border2": "#FFBBC9",
        "text": "#1A0510", "text2": "#6B3045", "text3": "#B07090",
        "font_display": "Italiana", "font_body": "Outfit",
        "gf_url": "https://fonts.googleapis.com/css2?family=Italiana&family=Outfit:wght@300;400;500;600&display=swap",
        "dark": False,
        "hero_style": "asymmetric",
        "features_style": "zigzag",
        "testimonials_style": "cards",
        "cta_style": "warm",
    },
]

# Map layout id -> index for JS
LAYOUT_IDS = [t["id"] for t in LAYOUT_TEMPLATES]


def _hex_to_rgb(hex_color: str) -> str:
    h = hex_color.lstrip('#')
    return f"{int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)}"


def _build_css(t: dict) -> str:
    sc = "0,0,0" if t["dark"] else "10,20,40"
    nb = t["bg"].lstrip("#")
    nr, ng, nb2 = int(nb[0:2], 16), int(nb[2:4], 16), int(nb[4:6], 16)
    acc = _hex_to_rgb(t["accent"])
    fd, fb = t["font_display"], t["font_body"]

    return f"""  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="{t['gf_url']}" rel="stylesheet">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html {{ scroll-behavior: smooth; font-size: 16px; }}
    body {{ font-family: '{fb}', system-ui, sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; -webkit-font-smoothing: antialiased; overflow-x: hidden; }}
    a {{ text-decoration: none; color: inherit; }}
    ul, ol {{ list-style: none; }}
    img {{ display: block; max-width: 100%; }}
    button {{ cursor: pointer; font-family: inherit; border: none; background: none; }}
    input, textarea {{ font-family: inherit; }}
    :focus-visible {{ outline: 2px solid var(--accent); outline-offset: 3px; }}

    :root {{
      --bg:{t['bg']}; --surface:{t['surface']}; --surface2:{t['surface2']}; --surface3:{t['surface3']};
      --border:{t['border']}; --border2:{t['border2']};
      --text:{t['text']}; --text-2:{t['text2']}; --text-3:{t['text3']};
      --accent:{t['accent']}; --accent2:{t['accent2']};
      --accent-rgb:{acc};
      --accent-dim:rgba({acc},0.12);
      --accent-glow:rgba({acc},0.28);
      --r:14px; --r-sm:10px; --r-lg:20px; --r-xl:28px;
      --sh-sm:0 2px 8px rgba({sc},0.08);
      --sh-md:0 8px 24px rgba({sc},0.10);
      --sh-lg:0 20px 60px rgba({sc},0.14);
      --sh-xl:0 40px 100px rgba({sc},0.18);
      --ease:cubic-bezier(0.4,0,0.2,1);
    }}

    /* ── Typography ── */
    h1,h2,h3,h4 {{ font-family:'{fd}',Georgia,serif; font-weight:400; letter-spacing:-0.025em; line-height:1.1; color:var(--text); }}
    h1 {{ font-size:clamp(38px,6vw,76px); line-height:1.0; }}
    h2 {{ font-size:clamp(28px,4vw,50px); line-height:1.08; }}
    h3 {{ font-size:clamp(18px,2.4vw,24px); }}
    p {{ color:var(--text-2); font-weight:300; line-height:1.72; }}

    /* ── Layout ── */
    .wrap {{ max-width:1140px; margin:0 auto; padding:0 40px; }}
    .wrap-sm {{ max-width:780px; margin:0 auto; padding:0 40px; }}
    .sec {{ padding:100px 0; }}
    .sec-sm {{ padding:60px 0; }}
    .divider {{ height:1px; background:var(--border); }}

    /* ── Nav ── */
    nav {{ position:sticky; top:0; z-index:200; background:rgba({nr},{ng},{nb2},0.90); backdrop-filter:blur(20px); border-bottom:1px solid var(--border); height:62px; display:flex; align-items:center; transition:box-shadow 0.3s; }}
    nav.scrolled {{ box-shadow:0 1px 24px rgba({sc},0.10); }}
    .nav-inner {{ display:flex; align-items:center; justify-content:space-between; width:100%; max-width:1140px; margin:0 auto; padding:0 40px; }}
    .nav-brand {{ display:flex; align-items:center; gap:10px; font-size:15px; font-weight:700; letter-spacing:-0.4px; color:var(--text); }}
    .nav-logo {{ width:32px; height:32px; background:var(--accent); border-radius:8px; display:flex; align-items:center; justify-content:center; font-family:'{fd}',serif; font-size:15px; color:#fff; flex-shrink:0; box-shadow:0 2px 8px var(--accent-glow); }}
    .nav-links {{ display:flex; gap:32px; }}
    .nav-links a {{ font-size:14px; color:var(--text-2); transition:color 0.18s; padding:4px 0; position:relative; }}
    .nav-links a::after {{ content:''; position:absolute; bottom:-2px; left:0; right:0; height:1.5px; background:var(--accent); transform:scaleX(0); transition:transform 0.22s; }}
    .nav-links a:hover {{ color:var(--text); }}
    .nav-links a:hover::after {{ transform:scaleX(1); }}
    .nav-btns {{ display:flex; gap:10px; align-items:center; }}

    /* ── Buttons ── */
    .btn {{ display:inline-flex; align-items:center; justify-content:center; gap:8px; font-family:inherit; font-weight:500; transition:all 0.22s var(--ease); white-space:nowrap; border-radius:var(--r-sm); cursor:pointer; border:none; }}
    .btn-sm {{ font-size:13px; padding:7px 16px; }}
    .btn-md {{ font-size:14px; padding:11px 24px; }}
    .btn-lg {{ font-size:15px; padding:14px 32px; border-radius:var(--r); }}
    .btn-xl {{ font-size:16px; padding:17px 42px; border-radius:var(--r); }}
    .btn-accent {{ background:var(--accent); color:#fff; box-shadow:0 4px 20px var(--accent-glow); }}
    .btn-accent:hover {{ filter:brightness(1.08); transform:translateY(-2px); box-shadow:0 8px 32px var(--accent-glow); }}
    .btn-outline {{ background:transparent; color:var(--text); border:1.5px solid var(--border2); }}
    .btn-outline:hover {{ border-color:var(--accent); color:var(--accent); background:var(--accent-dim); }}
    .btn-ghost {{ background:var(--surface2); color:var(--text-2); border:1px solid var(--border); }}
    .btn-ghost:hover {{ background:var(--surface3); color:var(--text); }}
    .btn-primary {{ background:var(--text); color:var(--bg); }}
    .btn-primary:hover {{ opacity:0.84; transform:translateY(-1px); }}
    .btn-full {{ width:100%; }}

    /* ── Badge ── */
    .badge {{ display:inline-flex; align-items:center; gap:6px; font-size:11.5px; font-weight:600; color:var(--accent); background:var(--accent-dim); border:1px solid rgba({acc},0.22); padding:5px 13px; border-radius:999px; }}
    .badge-pulse {{ width:6px; height:6px; border-radius:50%; background:var(--accent); animation:pulse 2s infinite; flex-shrink:0; }}
    @keyframes pulse {{ 0%,100%{{box-shadow:0 0 0 0 var(--accent-glow);}} 50%{{box-shadow:0 0 0 5px transparent;}} }}

    /* ── Tags ── */
    .tag {{ display:inline-flex; align-items:center; font-size:11px; font-weight:600; padding:3px 9px; border-radius:6px; }}
    .tag-green{{background:#f0fdf4;color:#16a34a;}} .tag-amber{{background:#fffbeb;color:#d97706;}}
    .tag-blue{{background:#eff6ff;color:#2563eb;}} .tag-red{{background:#fff1f2;color:#e11d48;}}
    .tag-purple{{background:#faf5ff;color:#9333ea;}}

    /* ── Section header ── */
    .eyebrow {{ display:inline-flex; align-items:center; gap:8px; font-size:11px; font-weight:700; letter-spacing:0.14em; text-transform:uppercase; color:var(--accent); margin-bottom:18px; }}
    .eyebrow::before {{ content:''; width:22px; height:1.5px; background:var(--accent); border-radius:1px; }}
    .sec-title {{ margin-bottom:16px; }}
    .sec-desc {{ font-size:16px; color:var(--text-2); font-weight:300; max-width:520px; line-height:1.7; margin-bottom:52px; }}

    /* ────────────────────────────────────────────
       HERO STYLES (layout-specific)
    ──────────────────────────────────────────── */

    /* CENTERED hero (obsidian, saas) */
    .hero-centered {{ padding:120px 0 80px; text-align:center; background:radial-gradient(ellipse at 50% 0%, rgba({acc},0.14) 0%, transparent 65%); }}
    .hero-centered h1 {{ max-width:14ch; margin:0 auto 22px; }}
    .hero-centered h1 em {{ font-style:italic; color:var(--accent); }}
    .hero-centered .hero-desc {{ max-width:540px; margin:0 auto 40px; font-size:18px; text-align:center; }}
    .hero-centered .hero-btns {{ display:flex; gap:14px; justify-content:center; flex-wrap:wrap; margin-bottom:56px; }}
    .hero-centered .hero-trust {{ display:flex; align-items:center; justify-content:center; gap:8px; font-size:12.5px; color:var(--text-3); margin-bottom:60px; }}
    .hero-centered .trust-avatars {{ display:flex; margin-right:6px; }}
    .trust-avatar {{ width:28px; height:28px; border-radius:50%; border:2px solid var(--bg); margin-right:-9px; font-size:10px; font-weight:700; color:#fff; display:flex; align-items:center; justify-content:center; }}

    /* SPLIT hero (editorial, forest) */
    .hero-split {{ padding:0; min-height:600px; display:grid; grid-template-columns:1fr 1fr; }}
    .hero-split-left {{ padding:80px 60px 80px 40px; display:flex; flex-direction:column; justify-content:center; background:var(--surface); border-right:1px solid var(--border); }}
    .hero-split-left .badge {{ margin-bottom:28px; }}
    .hero-split-left h1 {{ margin-bottom:20px; }}
    .hero-split-left h1 em {{ font-style:italic; color:var(--accent); }}
    .hero-split-left .hero-desc {{ font-size:17px; margin-bottom:36px; max-width:38ch; }}
    .hero-split-left .hero-btns {{ display:flex; gap:12px; flex-wrap:wrap; margin-bottom:40px; }}
    .hero-split-left .hero-trust {{ display:flex; align-items:center; gap:8px; font-size:12.5px; color:var(--text-3); }}
    .hero-split-right {{ background:linear-gradient(160deg, var(--surface2) 0%, var(--surface3) 100%); display:flex; align-items:center; justify-content:center; padding:40px; position:relative; overflow:hidden; }}
    .hero-split-right::before {{ content:''; position:absolute; inset:-20% -10% -20% 20%; background:radial-gradient(circle, rgba({acc},0.16) 0%, transparent 65%); pointer-events:none; }}

    /* DIAGONAL hero (neon-noir) */
    .hero-diagonal {{ padding:100px 0 80px; position:relative; overflow:hidden; }}
    .hero-diagonal::before {{ content:''; position:absolute; top:-30%; right:-10%; width:70%; height:140%; background:linear-gradient(135deg, rgba({acc},0.10) 0%, rgba({_hex_to_rgb(t['accent2'])},0.05) 100%); transform:skewX(-12deg); pointer-events:none; }}
    .hero-diagonal-inner {{ position:relative; z-index:1; }}
    .hero-diagonal h1 {{ font-size:clamp(52px,10vw,110px); line-height:0.92; letter-spacing:-0.04em; margin-bottom:28px; }}
    .hero-diagonal h1 em {{ color:var(--accent); font-style:normal; display:block; }}
    .hero-diagonal .hero-desc {{ font-size:17px; max-width:480px; margin-bottom:36px; }}
    .hero-diagonal .hero-btns {{ display:flex; gap:12px; flex-wrap:wrap; }}

    /* ASYMMETRIC hero (sand-ember, rose) */
    .hero-asymmetric {{ padding:80px 0; }}
    .hero-asymmetric-inner {{ display:grid; grid-template-columns:1.1fr 0.9fr; gap:60px; align-items:start; }}
    .hero-asymmetric-left .badge {{ margin-bottom:24px; }}
    .hero-asymmetric-left h1 {{ margin-bottom:20px; }}
    .hero-asymmetric-left h1 em {{ font-style:italic; color:var(--accent); }}
    .hero-asymmetric-left .hero-desc {{ font-size:17px; margin-bottom:32px; max-width:36ch; }}
    .hero-asymmetric-left .hero-btns {{ display:flex; gap:12px; flex-wrap:wrap; margin-bottom:32px; }}
    .hero-asymmetric-left .hero-trust {{ display:flex; align-items:center; gap:8px; font-size:12px; color:var(--text-3); }}
    .hero-asymmetric-right {{ display:flex; flex-direction:column; gap:14px; padding-top:16px; }}
    .hero-stat-card {{ background:var(--surface); border:1px solid var(--border); border-radius:var(--r-lg); padding:24px 28px; box-shadow:var(--sh-sm); }}
    .hero-stat-card:first-child {{ border-left:3px solid var(--accent); }}
    .hsc-num {{ font-family:'{fd}',serif; font-size:clamp(32px,5vw,44px); letter-spacing:-2px; color:var(--text); line-height:1; }}
    .hsc-lbl {{ font-size:13px; color:var(--text-3); margin-top:4px; }}
    .hsc-change {{ font-size:12px; color:#16a34a; font-weight:600; margin-top:6px; }}

    /* LUXURY hero (charcoal-luxe) */
    .hero-luxury {{ padding:120px 0 100px; text-align:center; background:radial-gradient(ellipse at 50% 0%, rgba({acc},0.10) 0%, transparent 60%); border-bottom:1px solid var(--border); }}
    .hero-luxury::before {{ content:''; display:block; width:60px; height:1px; background:var(--accent); margin:0 auto 32px; }}
    .hero-luxury h1 {{ max-width:16ch; margin:0 auto 24px; font-size:clamp(40px,7vw,84px); }}
    .hero-luxury h1 em {{ font-style:italic; color:var(--accent); }}
    .hero-luxury .hero-desc {{ max-width:500px; margin:0 auto 40px; font-size:17px; text-align:center; }}
    .hero-luxury .hero-btns {{ display:flex; gap:14px; justify-content:center; flex-wrap:wrap; margin-bottom:48px; }}
    .hero-luxury .hero-trust {{ display:flex; align-items:center; justify-content:center; gap:8px; font-size:12px; color:var(--text-3); }}

    /* ────────────────────────────────────────────
       PRODUCT MOCKUP (shared, nuclear layout fix)
    ──────────────────────────────────────────── */
    .mockup-outer {{ max-width:980px; margin:0 auto; border-radius:var(--r-xl); overflow:hidden; box-shadow:var(--sh-xl),0 0 0 1px var(--border); position:relative; text-align:left; }}
    .mockup-outer, .mockup-outer * {{ text-align:left !important; }}
    .mockup-chrome {{ background:var(--surface2); border-bottom:1px solid var(--border); padding:13px 18px; display:flex !important; align-items:center; gap:12px; }}
    .mockup-dots {{ display:flex !important; gap:6px; }}
    .md {{ width:11px; height:11px; border-radius:50%; }}
    .md-r{{background:#FF5F57;}} .md-a{{background:#FEBC2E;}} .md-g{{background:#28C840;}}
    .mockup-urlbar {{ flex:1; background:var(--surface3); border:1px solid var(--border); border-radius:6px; padding:5px 14px; font-size:11.5px; color:var(--text-3); display:flex; align-items:center; gap:6px; max-width:340px; margin:0 auto; }}
    .mockup-app {{ display:flex !important; height:480px; background:var(--surface); overflow:hidden; }}
    .mockup-sb {{ width:206px; border-right:1px solid var(--border); background:var(--surface2); padding:18px 12px; flex-shrink:0; display:flex !important; flex-direction:column; gap:2px; overflow:hidden; }}
    .mockup-sb-logo {{ display:flex !important; align-items:center; gap:8px; padding:8px 10px; margin-bottom:14px; font-size:13px; font-weight:700; color:var(--text); }}
    .mockup-sb-mark {{ width:24px; height:24px; background:var(--accent); border-radius:6px; flex-shrink:0; }}
    .mockup-sb-sec {{ font-size:9.5px; font-weight:700; text-transform:uppercase; letter-spacing:0.12em; color:var(--text-3); padding:14px 10px 6px; }}
    .mockup-nav {{ display:flex !important; align-items:center; gap:9px; padding:8px 10px; border-radius:6px; font-size:12.5px; color:var(--text-2); cursor:default; }}
    .mockup-nav.active {{ background:var(--accent-dim); color:var(--accent); font-weight:600; }}
    .mockup-nav:hover {{ background:var(--surface3); }}
    .mockup-ico {{ font-size:14px; width:18px; text-align:center !important; flex-shrink:0; }}
    .mockup-main {{ flex:1; display:flex !important; flex-direction:column; overflow:hidden; min-width:0; }}
    .mockup-topbar {{ border-bottom:1px solid var(--border); padding:13px 22px; display:flex !important; align-items:center; justify-content:space-between; background:var(--surface); flex-shrink:0; }}
    .mockup-title {{ font-size:14.5px; font-weight:600; color:var(--text); }}
    .mockup-tbbtns {{ display:flex !important; gap:8px; align-items:center; }}
    .mockup-btn {{ background:var(--accent); color:#fff; padding:5px 13px; border-radius:6px; font-size:11px; font-weight:600; }}
    .mockup-btn-g {{ background:var(--surface2); color:var(--text-2); border:1px solid var(--border); padding:5px 12px; border-radius:6px; font-size:11px; }}
    .mockup-content {{ flex:1; padding:18px 22px; overflow-y:auto; text-align:left !important; }}
    .mockup-kpis {{ display:grid !important; grid-template-columns:repeat(3,1fr); gap:11px; margin-bottom:18px; }}
    .mockup-kpi {{ background:var(--surface2); border:1px solid var(--border); border-radius:var(--r-sm); padding:13px 15px; position:relative; overflow:hidden; }}
    .mockup-kpi::before {{ content:''; position:absolute; top:0; left:0; right:0; height:2px; background:var(--accent); }}
    .mockup-kpi-val {{ font-size:21px; font-weight:700; color:var(--text); letter-spacing:-0.03em; font-family:'{fd}',serif; }}
    .mockup-kpi-lbl {{ font-size:10px; color:var(--text-3); text-transform:uppercase; letter-spacing:0.08em; margin-top:2px; }}
    .mockup-kpi-ch {{ font-size:10px; color:#16a34a; font-weight:600; margin-top:3px; }}
    .mockup-sec {{ font-size:10.5px; font-weight:700; text-transform:uppercase; letter-spacing:0.1em; color:var(--text-3); margin-bottom:9px; }}
    .mockup-tbl {{ width:100%; border-collapse:collapse; font-size:11.5px; margin-bottom:14px; }}
    .mockup-tbl th {{ text-align:left !important; padding:7px 9px; font-size:9.5px; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:var(--text-3); border-bottom:1px solid var(--border); background:var(--surface2); }}
    .mockup-tbl td {{ padding:8px 9px; border-bottom:1px solid var(--border); color:var(--text-2); font-weight:300; text-align:left !important; }}
    .mockup-tbl tr:last-child td {{ border-bottom:none; }}
    .mockup-tbl tr:hover td {{ background:var(--surface2); }}
    .mockup-charts {{ display:grid !important; grid-template-columns:1.4fr 1fr; gap:11px; }}
    .mockup-chart {{ background:var(--surface2); border:1px solid var(--border); border-radius:var(--r-sm); padding:13px 15px; }}
    .mockup-chart-ttl {{ font-size:9.5px; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:var(--text-3); margin-bottom:10px; }}
    .bars {{ display:flex !important; align-items:flex-end; gap:4px; height:68px; }}
    .bar {{ flex:1; border-radius:3px 3px 0 0; background:var(--accent); opacity:0.75; min-height:5px; transition:opacity 0.2s; }}
    .bar:hover {{ opacity:1; }}
    .donut-wrap {{ display:flex !important; align-items:center; justify-content:center; height:68px; gap:14px; }}
    .donut-legend {{ display:flex !important; flex-direction:column; gap:5px; }}
    .donut-row {{ display:flex !important; align-items:center; gap:6px; font-size:10px; color:var(--text-2); }}
    .donut-dot {{ width:8px; height:8px; border-radius:50%; flex-shrink:0; }}

    /* ────────────────────────────────────────────
       STATS STRIP
    ──────────────────────────────────────────── */
    .stats-strip {{ border-top:1px solid var(--border); border-bottom:1px solid var(--border); }}
    .stats-inner {{ display:grid !important; grid-template-columns:repeat(4,1fr); max-width:1140px; margin:0 auto; }}
    .stat-cell {{ padding:38px 32px; text-align:center; border-right:1px solid var(--border); }}
    .stat-cell:last-child {{ border-right:none; }}
    .stat-num {{ font-family:'{fd}',serif; font-size:clamp(32px,4vw,54px); font-weight:400; letter-spacing:-2px; color:var(--accent); display:block; line-height:1; }}
    .stat-lbl {{ font-size:13px; color:var(--text-3); margin-top:8px; font-weight:300; }}

    /* ────────────────────────────────────────────
       FEATURES (layout-specific)
    ──────────────────────────────────────────── */
    /* Grid-3 style */
    .feat-grid {{ display:grid !important; grid-template-columns:repeat(3,1fr); gap:1px; background:var(--border); border:1px solid var(--border); border-radius:var(--r-lg); overflow:hidden; }}
    .feat-cell {{ background:var(--surface); padding:32px 28px; transition:background 0.18s; position:relative; }}
    .feat-cell:hover {{ background:var(--surface2); }}
    .feat-cell::after {{ content:''; position:absolute; top:0; left:0; right:0; height:2px; background:var(--accent); transform:scaleX(0); transition:transform 0.25s; }}
    .feat-cell:hover::after {{ transform:scaleX(1); }}
    .feat-num {{ font-family:'{fd}',serif; font-size:13px; color:var(--text-3); font-style:italic; margin-bottom:14px; }}
    .feat-icon {{ width:46px; height:46px; border-radius:var(--r-sm); background:var(--accent-dim); display:flex; align-items:center; justify-content:center; font-size:20px; margin-bottom:18px; border:1px solid rgba({acc},0.15); }}
    .feat-title {{ font-size:15px; font-weight:600; margin-bottom:9px; color:var(--text); }}
    .feat-desc {{ font-size:13.5px; color:var(--text-2); font-weight:300; line-height:1.65; }}

    /* Bordered / left-number style */
    .feat-list {{ display:flex !important; flex-direction:column; gap:0; }}
    .feat-row {{ display:grid !important; grid-template-columns:80px 1fr; gap:32px; padding:36px 0; border-bottom:1px solid var(--border); align-items:start; }}
    .feat-row:last-child {{ border-bottom:none; }}
    .feat-row-num {{ font-family:'{fd}',serif; font-size:42px; color:var(--accent); opacity:0.3; line-height:1; font-style:italic; }}
    .feat-row-body {{ padding-top:4px; }}
    .feat-row-title {{ font-size:17px; font-weight:600; color:var(--text); margin-bottom:8px; }}
    .feat-row-desc {{ font-size:14px; color:var(--text-2); font-weight:300; line-height:1.65; }}

    /* Icon-list style */
    .feat-icon-grid {{ display:grid !important; grid-template-columns:repeat(2,1fr); gap:40px 60px; }}
    .feat-icon-item {{ display:flex !important; gap:18px; align-items:flex-start; }}
    .feat-icon-circle {{ width:44px; height:44px; border-radius:50%; background:var(--accent-dim); border:1px solid rgba({acc},0.18); display:flex; align-items:center; justify-content:center; font-size:18px; flex-shrink:0; }}
    .feat-icon-text {{ }}
    .feat-icon-title {{ font-size:15px; font-weight:600; color:var(--text); margin-bottom:6px; }}
    .feat-icon-desc {{ font-size:13.5px; color:var(--text-2); font-weight:300; line-height:1.6; }}

    /* Zigzag style */
    .feat-zigzag {{ display:flex !important; flex-direction:column; gap:60px; }}
    .feat-zz {{ display:grid !important; grid-template-columns:1fr 1fr; gap:48px; align-items:center; }}
    .feat-zz:nth-child(even) {{ direction:rtl; }}
    .feat-zz:nth-child(even) > * {{ direction:ltr; }}
    .feat-zz-visual {{ background:var(--surface2); border:1px solid var(--border); border-radius:var(--r-lg); padding:32px; min-height:200px; display:flex; align-items:center; justify-content:center; position:relative; overflow:hidden; }}
    .feat-zz-visual::before {{ content:''; position:absolute; inset:-30% -20% -30% 30%; background:radial-gradient(circle, rgba({acc},0.14) 0%, transparent 65%); }}
    .feat-zz-emoji {{ font-size:48px; position:relative; z-index:1; }}
    .feat-zz-title {{ font-size:22px; font-weight:600; color:var(--text); margin-bottom:12px; font-family:'{fd}',serif; }}
    .feat-zz-desc {{ font-size:14.5px; color:var(--text-2); font-weight:300; line-height:1.7; margin-bottom:18px; }}
    .feat-zz-tag {{ display:inline-flex; align-items:center; gap:6px; font-size:12px; font-weight:600; color:var(--accent); }}

    /* ────────────────────────────────────────────
       HOW IT WORKS
    ──────────────────────────────────────────── */
    .steps-grid {{ display:grid !important; grid-template-columns:repeat(3,1fr); gap:40px; position:relative; }}
    .steps-grid::before {{ content:''; position:absolute; top:27px; left:16%; right:16%; height:1px; background:linear-gradient(90deg,transparent,var(--border),var(--border),transparent); }}
    .step {{ text-align:center; }}
    .step-num {{ width:54px; height:54px; border-radius:50%; background:var(--surface2); border:2px solid var(--border2); display:flex; align-items:center; justify-content:center; margin:0 auto 20px; font-family:'{fd}',serif; font-size:21px; color:var(--accent); position:relative; z-index:1; transition:all 0.22s; }}
    .step:hover .step-num {{ background:var(--accent); color:#fff; border-color:var(--accent); box-shadow:0 4px 20px var(--accent-glow); }}
    .step-title {{ font-size:16px; font-weight:600; margin-bottom:10px; color:var(--text); }}
    .step-desc {{ font-size:13.5px; color:var(--text-2); font-weight:300; line-height:1.65; max-width:22ch; margin:0 auto; }}

    /* ────────────────────────────────────────────
       TESTIMONIALS (style-specific)
    ──────────────────────────────────────────── */
    /* Cards style */
    .t-grid {{ display:grid !important; grid-template-columns:repeat(3,1fr); gap:20px; }}
    .t-card {{ background:var(--surface); border:1px solid var(--border); border-radius:var(--r-lg); padding:28px; box-shadow:var(--sh-sm); display:flex; flex-direction:column; transition:all 0.22s; }}
    .t-card:hover {{ border-color:rgba({acc},0.30); box-shadow:var(--sh-md); }}
    .t-stars {{ color:#F59E0B; font-size:13px; letter-spacing:1px; margin-bottom:14px; }}
    .t-text {{ font-size:14px; color:var(--text-2); font-weight:300; line-height:1.72; margin-bottom:18px; font-style:italic; flex:1; position:relative; }}
    .t-text::before {{ content:'"'; position:absolute; top:-8px; left:-4px; font-size:44px; color:var(--accent); opacity:0.15; font-family:'{fd}',serif; line-height:1; }}
    .t-author {{ display:flex !important; align-items:center; gap:11px; margin-top:auto; }}
    .t-av {{ width:38px; height:38px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:13px; font-weight:700; color:#fff; flex-shrink:0; }}
    .t-name {{ font-size:13px; font-weight:600; color:var(--text); }}
    .t-role {{ font-size:11.5px; color:var(--text-3); margin-top:1px; }}

    /* Pull-quote + 2 cards style */
    .t-pull {{ margin-bottom:40px; background:var(--surface2); border:1px solid var(--border); border-radius:var(--r-xl); padding:48px; position:relative; overflow:hidden; }}
    .t-pull::before {{ content:'"'; position:absolute; top:-20px; left:24px; font-size:160px; color:var(--accent); opacity:0.08; font-family:'{fd}',serif; line-height:1; }}
    .t-pull-text {{ font-family:'{fd}',serif; font-size:clamp(20px,2.8vw,28px); color:var(--text); line-height:1.4; margin-bottom:24px; font-style:italic; position:relative; z-index:1; max-width:60ch; }}
    .t-pull-author {{ display:flex !important; align-items:center; gap:14px; position:relative; z-index:1; }}
    .t-2grid {{ display:grid !important; grid-template-columns:1fr 1fr; gap:20px; }}

    /* Minimal style */
    .t-minimal {{ display:flex !important; flex-direction:column; gap:0; }}
    .t-min-item {{ padding:36px 0; border-bottom:1px solid var(--border); }}
    .t-min-item:last-child {{ border-bottom:none; }}
    .t-min-text {{ font-family:'{fd}',serif; font-size:clamp(17px,2.2vw,22px); color:var(--text); line-height:1.45; font-style:italic; margin-bottom:18px; }}
    .t-min-author {{ display:flex !important; align-items:center; gap:12px; }}

    /* Horizontal slider style */
    .t-slider {{ display:flex !important; gap:20px; overflow-x:auto; padding-bottom:16px; scrollbar-width:thin; scroll-snap-type:x mandatory; }}
    .t-slider-card {{ min-width:320px; max-width:320px; scroll-snap-align:start; background:var(--surface); border:1px solid var(--border); border-radius:var(--r-lg); padding:26px; flex-shrink:0; }}

    /* ────────────────────────────────────────────
       PRICING
    ──────────────────────────────────────────── */
    .pricing-grid {{ display:grid !important; grid-template-columns:repeat(3,1fr); gap:20px; align-items:start; }}
    .p-card {{ background:var(--surface); border:1px solid var(--border); border-radius:var(--r-xl); padding:36px 30px; position:relative; transition:all 0.22s; }}
    .p-card:hover {{ box-shadow:var(--sh-md); }}
    .p-card.featured {{ border-color:var(--accent); box-shadow:0 0 0 1px var(--accent),var(--sh-lg); background:linear-gradient(160deg,var(--surface) 0%,var(--accent-dim) 100%); transform:scale(1.025); }}
    .p-card.featured:hover {{ transform:scale(1.035); }}
    .p-badge {{ position:absolute; top:-12px; left:50%; transform:translateX(-50%); background:var(--accent); color:#fff; font-size:10px; font-weight:700; letter-spacing:0.08em; padding:4px 14px; border-radius:999px; white-space:nowrap; text-transform:uppercase; }}
    .p-tier {{ font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.12em; color:var(--text-3); margin-bottom:14px; }}
    .p-price-row {{ display:flex !important; align-items:baseline; gap:3px; margin-bottom:5px; }}
    .p-currency {{ font-size:20px; font-weight:600; color:var(--text); margin-top:4px; }}
    .p-price {{ font-family:'{fd}',serif; font-size:50px; font-weight:400; letter-spacing:-3px; color:var(--text); line-height:1; }}
    .p-period {{ font-size:13px; color:var(--text-3); margin-bottom:22px; font-weight:300; }}
    .p-desc {{ font-size:13px; color:var(--text-2); margin-bottom:22px; line-height:1.6; }}
    .p-divider {{ height:1px; background:var(--border); margin:18px 0; }}
    .p-features {{ display:flex !important; flex-direction:column; gap:10px; margin-bottom:26px; }}
    .p-feat {{ display:flex !important; align-items:center; gap:9px; font-size:13.5px; color:var(--text-2); font-weight:300; }}
    .p-check {{ width:17px; height:17px; border-radius:50%; background:var(--accent-dim); display:flex; align-items:center; justify-content:center; flex-shrink:0; font-size:9.5px; color:var(--accent); font-weight:700; }}

    /* ────────────────────────────────────────────
       FAQ
    ──────────────────────────────────────────── */
    .faq-list {{ max-width:720px; margin:0 auto; }}
    .faq-item {{ border-bottom:1px solid var(--border); }}
    .faq-item:first-child {{ border-top:1px solid var(--border); }}
    .faq-q {{ display:flex !important; align-items:center; justify-content:space-between; padding:22px 0; cursor:pointer; user-select:none; font-size:15px; font-weight:500; color:var(--text); transition:color 0.18s; gap:20px; }}
    .faq-q:hover {{ color:var(--accent); }}
    .faq-ico {{ width:27px; height:27px; border-radius:50%; background:var(--surface2); border:1px solid var(--border); display:flex; align-items:center; justify-content:center; flex-shrink:0; font-size:17px; color:var(--text-3); transition:transform 0.25s,background 0.2s; }}
    .faq-item.open .faq-ico {{ transform:rotate(45deg); background:var(--accent-dim); color:var(--accent); }}
    .faq-a {{ font-size:14px; color:var(--text-2); font-weight:300; line-height:1.75; max-height:0; overflow:hidden; transition:max-height 0.35s ease,padding 0.35s ease; }}
    .faq-item.open .faq-a {{ max-height:300px; padding-bottom:20px; }}

    /* ────────────────────────────────────────────
       CTA STYLES
    ──────────────────────────────────────────── */
    /* Banner (dark full-width) */
    .cta-banner {{ background:var(--text); padding:100px 0; text-align:center; position:relative; overflow:hidden; }}
    .cta-banner::before {{ content:''; position:absolute; inset:0; background:radial-gradient(ellipse at 50% 50%, rgba({acc},0.14) 0%, transparent 65%); pointer-events:none; }}
    .cta-banner h2 {{ color:var(--bg); margin-bottom:14px; position:relative; z-index:1; }}
    .cta-banner p {{ color:rgba(255,255,255,0.55); margin-bottom:36px; max-width:420px; font-size:16px; margin-left:auto; margin-right:auto; position:relative; z-index:1; }}
    /* Glow (accent bg for dark themes) */
    .cta-glow {{ background:linear-gradient(160deg,var(--surface) 0%,var(--surface2) 100%); padding:100px 0; text-align:center; position:relative; overflow:hidden; border-top:1px solid var(--border); }}
    .cta-glow::before {{ content:''; position:absolute; inset:-20% -10% -20% -10%; background:radial-gradient(ellipse at 50% 50%, rgba({acc},0.22) 0%, transparent 60%); pointer-events:none; }}
    .cta-glow h2 {{ margin-bottom:14px; position:relative; z-index:1; }}
    .cta-glow p {{ margin-bottom:36px; max-width:420px; font-size:16px; margin-left:auto; margin-right:auto; position:relative; z-index:1; }}
    /* Neon border */
    .cta-neon {{ padding:80px 0; text-align:center; }}
    .cta-neon-inner {{ max-width:720px; margin:0 auto; border:1px solid rgba({acc},0.40); border-radius:var(--r-xl); padding:64px; position:relative; background:linear-gradient(160deg,var(--surface) 0%,var(--surface2) 100%); box-shadow:0 0 60px rgba({acc},0.12), inset 0 0 60px rgba({acc},0.04); }}
    .cta-neon h2 {{ margin-bottom:14px; }}
    .cta-neon p {{ margin-bottom:36px; max-width:360px; margin-left:auto; margin-right:auto; }}
    /* Warm (light accent-tinted bg) */
    .cta-warm {{ background:var(--accent-dim); border-top:1px solid rgba({acc},0.18); border-bottom:1px solid rgba({acc},0.18); padding:100px 0; text-align:center; }}
    .cta-warm h2 {{ margin-bottom:14px; }}
    .cta-warm p {{ margin-bottom:36px; max-width:420px; font-size:16px; margin-left:auto; margin-right:auto; }}
    /* Gold */
    .cta-gold {{ background:var(--surface2); border-top:1px solid var(--border); padding:100px 0; text-align:center; }}
    .cta-gold-inner {{ border:1px solid var(--accent); border-radius:var(--r-xl); padding:64px; max-width:760px; margin:0 auto; background:linear-gradient(160deg,var(--surface) 0%,var(--surface2) 100%); }}
    .cta-gold h2 {{ margin-bottom:14px; }}
    .cta-gold p {{ margin-bottom:36px; max-width:400px; margin-left:auto; margin-right:auto; }}
    /* Shared CTA form */
    .cta-form {{ display:flex !important; gap:10px; justify-content:center; flex-wrap:wrap; max-width:500px; margin:0 auto 18px; position:relative; z-index:1; }}
    .cta-input {{ flex:1; min-width:210px; background:rgba(255,255,255,0.10); border:1px solid rgba(255,255,255,0.22); color:white; padding:13px 18px; border-radius:var(--r-sm); font-size:14px; outline:none; font-family:inherit; transition:border-color 0.2s; }}
    .cta-input:focus {{ border-color:var(--accent); }}
    .cta-input::placeholder {{ color:rgba(255,255,255,0.40); }}
    .cta-input-light {{ flex:1; min-width:210px; background:var(--surface); border:1.5px solid var(--border2); color:var(--text); padding:13px 18px; border-radius:var(--r-sm); font-size:14px; outline:none; font-family:inherit; transition:border-color 0.2s; }}
    .cta-input-light:focus {{ border-color:var(--accent); }}
    .cta-input-light::placeholder {{ color:var(--text-3); }}
    .cta-hint {{ font-size:11.5px; color:var(--text-3); position:relative; z-index:1; }}

    /* ────────────────────────────────────────────
       FOOTER
    ──────────────────────────────────────────── */
    footer {{ border-top:1px solid var(--border); padding:60px 0 28px; background:var(--surface2); }}
    .footer-grid {{ display:grid !important; grid-template-columns:2fr 1fr 1fr 1fr; gap:52px; margin-bottom:44px; }}
    .footer-brand-name {{ font-size:16px; font-weight:700; color:var(--text); margin-bottom:10px; letter-spacing:-0.3px; }}
    .footer-brand-desc {{ font-size:13px; color:var(--text-3); font-weight:300; line-height:1.65; max-width:220px; }}
    .footer-col-title {{ font-size:10.5px; font-weight:700; text-transform:uppercase; letter-spacing:0.12em; color:var(--text-3); margin-bottom:16px; }}
    .footer-link {{ display:block; font-size:13.5px; color:var(--text-2); font-weight:300; margin-bottom:10px; transition:color 0.18s; }}
    .footer-link:hover {{ color:var(--accent); }}
    .footer-bottom {{ border-top:1px solid var(--border); padding-top:22px; display:flex !important; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:12px; }}
    .footer-copy {{ font-size:12px; color:var(--text-3); }}
    .footer-legal {{ display:flex !important; gap:20px; }}
    .footer-legal a {{ font-size:12px; color:var(--text-3); transition:color 0.18s; }}
    .footer-legal a:hover {{ color:var(--text); }}

    /* ────────────────────────────────────────────
       ANIMATIONS
    ──────────────────────────────────────────── */
    @keyframes fadeUp {{ from{{opacity:0;transform:translateY(20px);}} to{{opacity:1;transform:translateY(0);}} }}
    /* reveal: always visible — no IntersectionObserver needed in iframe */
    .reveal {{ opacity:1; transform:translateY(0); }}
    .reveal.in {{ opacity:1; transform:translateY(0); }}
    /* Hero entrance animations fire immediately on load */
    .au  {{ animation:fadeUp 0.55s 0.05s cubic-bezier(0.2,0.8,0.2,1) both; }}
    .au1 {{ animation:fadeUp 0.55s 0.15s cubic-bezier(0.2,0.8,0.2,1) both; }}
    .au2 {{ animation:fadeUp 0.55s 0.25s cubic-bezier(0.2,0.8,0.2,1) both; }}
    .au3 {{ animation:fadeUp 0.55s 0.35s cubic-bezier(0.2,0.8,0.2,1) both; }}
    .d1{{}} .d2{{}} .d3{{}}

    /* ────────────────────────────────────────────
       RESPONSIVE
    ──────────────────────────────────────────── */
    @media (max-width:1024px) {{
      .wrap,.nav-inner {{ padding:0 28px; }}
      .feat-grid {{ grid-template-columns:repeat(2,1fr) !important; }}
      .stats-inner {{ grid-template-columns:repeat(2,1fr) !important; }}
      .footer-grid {{ grid-template-columns:1fr 1fr !important; gap:36px; }}
      .hero-split {{ grid-template-columns:1fr; min-height:auto; }}
      .hero-split-left {{ padding:64px 40px; }}
      .hero-split-right {{ min-height:300px; }}
    }}
    @media (max-width:768px) {{
      .wrap,.wrap-sm,.nav-inner {{ padding:0 20px; }}
      .nav-links {{ display:none !important; }}
      .sec {{ padding:64px 0; }}
      .hero-centered {{ padding:80px 0 56px; }}
      .hero-asymmetric-inner {{ grid-template-columns:1fr !important; }}
      .hero-diagonal h1 {{ font-size:clamp(44px,12vw,72px); }}
      .steps-grid {{ grid-template-columns:1fr !important; gap:32px; }}
      .steps-grid::before {{ display:none; }}
      .t-grid {{ grid-template-columns:1fr !important; }}
      .t-2grid {{ grid-template-columns:1fr !important; }}
      .pricing-grid {{ grid-template-columns:1fr !important; }}
      .p-card.featured {{ transform:none; }}
      .feat-grid {{ grid-template-columns:1fr !important; }}
      .feat-icon-grid {{ grid-template-columns:1fr !important; }}
      .feat-zigzag .feat-zz {{ grid-template-columns:1fr !important; direction:ltr; }}
      .feat-zigzag .feat-zz > * {{ direction:ltr; }}
      .mockup-sb {{ display:none !important; }}
      .mockup-app {{ height:360px; }}
      .mockup-kpis {{ grid-template-columns:repeat(2,1fr) !important; }}
      .mockup-charts {{ grid-template-columns:1fr !important; }}
      .stats-inner {{ grid-template-columns:1fr 1fr !important; }}
      .footer-grid {{ grid-template-columns:1fr !important; gap:28px; }}
      .footer-bottom {{ flex-direction:column; align-items:flex-start; }}
      .hero-split {{ grid-template-columns:1fr; }}
    }}
    @media (max-width:480px) {{
      .hero-btns {{ flex-direction:column; align-items:stretch; }}
      .btn-xl {{ width:100%; }}
      .cta-form {{ flex-direction:column; }}
      .cta-input,.cta-input-light {{ min-width:unset; width:100%; }}
      .stats-inner {{ grid-template-columns:1fr !important; }}
    }}
  </style>"""


def _safety_css() -> str:
    return """<style>
  /* ── Layout safety overrides ── */
  .mockup-outer,.mockup-outer *{text-align:left!important}
  .mockup-app{display:flex!important;height:480px!important;overflow:hidden!important}
  .mockup-sb{display:flex!important;flex-direction:column!important;width:206px!important;flex-shrink:0!important;overflow:hidden!important}
  .mockup-main{display:flex!important;flex-direction:column!important;flex:1!important;overflow:hidden!important;min-width:0!important}
  .mockup-content{flex:1!important;overflow-y:auto!important;text-align:left!important;padding:18px 22px!important}
  .mockup-kpis{display:grid!important;grid-template-columns:repeat(3,1fr)!important;gap:11px!important;margin-bottom:18px!important}
  .mockup-charts{display:grid!important;grid-template-columns:1.4fr 1fr!important;gap:11px!important}
  .bars{display:flex!important;align-items:flex-end!important;height:68px!important;gap:4px!important}
  .bar{flex:1!important;border-radius:3px 3px 0 0!important;background:var(--accent)!important;opacity:0.75!important;min-height:5px!important}
  .mockup-tbl{width:100%!important;border-collapse:collapse!important}
  .mockup-tbl th,.mockup-tbl td{text-align:left!important}
  .stats-inner{display:grid!important;grid-template-columns:repeat(4,1fr)!important}
  .feat-grid{display:grid!important;grid-template-columns:repeat(3,1fr)!important}
  .steps-grid{display:grid!important;grid-template-columns:repeat(3,1fr)!important}
  .t-grid{display:grid!important;grid-template-columns:repeat(3,1fr)!important}
  .pricing-grid{display:grid!important;grid-template-columns:repeat(3,1fr)!important}
  .footer-grid{display:grid!important;grid-template-columns:2fr 1fr 1fr 1fr!important}
  .nav-inner,.nav-links,.nav-btns,.hero-btns,.hero-trust,.trust-avatars{display:flex!important}
  @media(max-width:768px){
    .steps-grid,.t-grid,.pricing-grid,.feat-grid{grid-template-columns:1fr!important}
    .stats-inner{grid-template-columns:1fr 1fr!important}
    .footer-grid{grid-template-columns:1fr!important}
    .mockup-sb{display:none!important}
    .mockup-kpis{grid-template-columns:repeat(2,1fr)!important}
    .mockup-charts{grid-template-columns:1fr!important}
  }
  @media(max-width:480px){
    .stats-inner{grid-template-columns:1fr!important}
  }
</style>"""


# ─────────────────────────────────────────────────────────────────────────────
# Per-layout prompt instructions — tells the LLM exactly what structure to build
# ─────────────────────────────────────────────────────────────────────────────
LAYOUT_PROMPTS = {
    "editorial": """
HERO STRUCTURE — copy this EXACTLY, fill in [CONTENT]:
<section class="hero-split">
  <div class="hero-split-left">
    <div class="wrap" style="height:100%;display:flex;flex-direction:column;justify-content:center;padding-top:60px;padding-bottom:60px;">
      <div class="badge au"><span class="badge-pulse"></span>[Launch claim]</div>
      <h1 class="au1">[Bold headline with <em>italic word</em>]</h1>
      <p class="hero-desc au2">[2-sentence value prop]</p>
      <div class="hero-btns au3">
        <button class="btn btn-accent btn-lg">[Primary CTA]</button>
        <button class="btn btn-outline btn-lg">[Secondary CTA]</button>
      </div>
      <div class="hero-trust au3">
        <div class="trust-avatars"><div class="trust-avatar" style="background:#6366f1">A</div><div class="trust-avatar" style="background:#f97316">M</div><div class="trust-avatar" style="background:#16a34a">S</div><div class="trust-avatar" style="background:#0ea5e9">K</div></div>
        Joined by [X,XXX] [customers] this month
      </div>
    </div>
  </div>
  <div class="hero-split-right">
    [FULL MOCKUP HERE — mockup-outer with chrome, sidebar, main, kpis, table, charts]
  </div>
</section>

FEATURES STRUCTURE — use this EXACTLY:
<div class="feat-grid">
  <div class="feat-cell"><div class="feat-num">01</div><div class="feat-icon">[emoji]</div><div class="feat-title">[title]</div><p class="feat-desc">[desc]</p></div>
  [repeat for 02-06]
</div>

TESTIMONIALS STRUCTURE — use this EXACTLY:
<div class="t-pull reveal">
  <p class="t-pull-text">"[Long impressive quote — 2-3 sentences mentioning specific results]"</p>
  <div class="t-pull-author"><div class="t-av" style="background:#6366f1">A</div><div><div class="t-name">[Name]</div><div class="t-role">[Role, Company]</div></div></div>
</div>
<div class="t-2grid reveal">
  <div class="t-card"><div class="t-stars">★★★★★</div><p class="t-text">"[specific quote]"</p><div class="t-author"><div class="t-av" style="background:#f97316">M</div><div><div class="t-name">[Name]</div><div class="t-role">[Role]</div></div></div></div>
  <div class="t-card"><div class="t-stars">★★★★★</div><p class="t-text">"[specific quote]"</p><div class="t-author"><div class="t-av" style="background:#16a34a">S</div><div><div class="t-name">[Name]</div><div class="t-role">[Role]</div></div></div></div>
</div>

CTA STRUCTURE:
<section class="cta-banner"><div class="wrap-sm"><h2>[CTA headline]</h2><p>[urgency line]</p><div class="cta-form"><input class="cta-input" type="email" placeholder="Enter your email"><button class="btn btn-accent btn-lg">Get started free</button></div><p class="cta-hint">No credit card · 5 min setup · Cancel anytime</p></div></section>
""",

    "obsidian": """
HERO STRUCTURE — copy this EXACTLY:
<section class="hero-centered">
  <div class="wrap">
    <div class="badge au"><span class="badge-pulse"></span>[launch claim]</div>
    <h1 class="au1">[Headline with <em>italic</em>]</h1>
    <p class="hero-desc au2">[2 sentences]</p>
    <div class="hero-btns au3" style="justify-content:center;">
      <button class="btn btn-accent btn-xl">[Primary]</button>
      <button class="btn btn-outline btn-xl">[Secondary]</button>
    </div>
    <div class="hero-trust au3">
      <div class="trust-avatars"><div class="trust-avatar" style="background:#6366f1">A</div><div class="trust-avatar" style="background:#f97316">M</div><div class="trust-avatar" style="background:#16a34a">S</div><div class="trust-avatar" style="background:#0ea5e9">K</div></div>
      [X,XXX] [customers] already using it
    </div>
  </div>
</section>
<section style="padding:0 0 80px;background:var(--bg);"><div class="wrap">[FULL MOCKUP]</div></section>

FEATURES STRUCTURE — numbered list, use EXACTLY:
<div class="feat-list">
  <div class="feat-row reveal"><div class="feat-row-num">01</div><div class="feat-row-body"><div class="feat-row-title">[Feature name]</div><p class="feat-row-desc">[Description]</p></div></div>
  [repeat for 02, 03, 04]
</div>

TESTIMONIALS STRUCTURE — glass cards, use EXACTLY:
<div class="t-grid">
  <div class="t-card reveal"><div class="t-stars">★★★★★</div><p class="t-text">"[quote]"</p><div class="t-author"><div class="t-av" style="background:#6366f1">A</div><div><div class="t-name">[Name]</div><div class="t-role">[Role]</div></div></div></div>
  <div class="t-card reveal d1"><div class="t-stars">★★★★★</div><p class="t-text">"[quote]"</p><div class="t-author"><div class="t-av" style="background:#f97316">M</div><div><div class="t-name">[Name]</div><div class="t-role">[Role]</div></div></div></div>
  <div class="t-card reveal d2"><div class="t-stars">★★★★★</div><p class="t-text">"[quote]"</p><div class="t-author"><div class="t-av" style="background:#16a34a">S</div><div><div class="t-name">[Name]</div><div class="t-role">[Role]</div></div></div></div>
</div>

CTA STRUCTURE:
<section class="cta-glow"><div class="wrap-sm"><h2>[CTA headline]</h2><p>[urgency]</p><div class="cta-form"><input class="cta-input-light" type="email" placeholder="Enter your email"><button class="btn btn-accent btn-lg">Get started free</button></div><p class="cta-hint">No credit card · 5 min setup · Cancel anytime</p></div></section>
""",

    "neon-noir": """
HERO STRUCTURE — diagonal kinetic, copy EXACTLY:
<section class="hero-diagonal">
  <div class="hero-diagonal-inner wrap">
    <div class="badge au"><span class="badge-pulse"></span>[LAUNCH CLAIM IN CAPS]</div>
    <h1 class="au1">[BOLD CAPS HEADLINE<em>[SECOND LINE]</em>]</h1>
    <p class="hero-desc au2">[2 sentences]</p>
    <div class="hero-btns au3">
      <button class="btn btn-accent btn-xl">[Primary]</button>
      <button class="btn btn-outline btn-xl">[Secondary]</button>
    </div>
  </div>
</section>
<section style="padding:0 0 80px;background:var(--bg);"><div class="wrap">[FULL MOCKUP]</div></section>

FEATURES STRUCTURE — zigzag alternating rows, copy EXACTLY:
<div class="feat-zigzag">
  <div class="feat-zz reveal">
    <div class="feat-zz-visual"><div class="feat-zz-emoji">[emoji]</div></div>
    <div><div class="feat-zz-title">[Feature name]</div><p class="feat-zz-desc">[Description]</p><div class="feat-zz-tag">→ [Key benefit]</div></div>
  </div>
  <div class="feat-zz reveal">
    <div class="feat-zz-visual"><div class="feat-zz-emoji">[emoji]</div></div>
    <div><div class="feat-zz-title">[Feature 2]</div><p class="feat-zz-desc">[Description]</p><div class="feat-zz-tag">→ [Key benefit]</div></div>
  </div>
  <div class="feat-zz reveal">
    <div class="feat-zz-visual"><div class="feat-zz-emoji">[emoji]</div></div>
    <div><div class="feat-zz-title">[Feature 3]</div><p class="feat-zz-desc">[Description]</p><div class="feat-zz-tag">→ [Key benefit]</div></div>
  </div>
</div>

TESTIMONIALS STRUCTURE — horizontal slider, copy EXACTLY:
<div class="t-slider reveal">
  <div class="t-slider-card"><div class="t-stars">★★★★★</div><p class="t-text">"[quote]"</p><div class="t-author"><div class="t-av" style="background:#6366f1">A</div><div><div class="t-name">[Name]</div><div class="t-role">[Role]</div></div></div></div>
  <div class="t-slider-card"><div class="t-stars">★★★★★</div><p class="t-text">"[quote]"</p><div class="t-author"><div class="t-av" style="background:#f97316">M</div><div><div class="t-name">[Name]</div><div class="t-role">[Role]</div></div></div></div>
  <div class="t-slider-card"><div class="t-stars">★★★★★</div><p class="t-text">"[quote]"</p><div class="t-author"><div class="t-av" style="background:#16a34a">S</div><div><div class="t-name">[Name]</div><div class="t-role">[Role]</div></div></div></div>
  <div class="t-slider-card"><div class="t-stars">★★★★★</div><p class="t-text">"[quote]"</p><div class="t-author"><div class="t-av" style="background:#0ea5e9">K</div><div><div class="t-name">[Name]</div><div class="t-role">[Role]</div></div></div></div>
</div>

CTA STRUCTURE:
<section class="cta-neon"><div class="cta-neon-inner"><h2>[CTA]</h2><p>[urgency]</p><div class="cta-form"><input class="cta-input-light" type="email" placeholder="Enter your email"><button class="btn btn-accent btn-lg">Get started free</button></div><p class="cta-hint">No credit card · 5 min setup · Cancel anytime</p></div></section>
""",

    "sand-ember": """
HERO STRUCTURE — asymmetric with stat cards right, copy EXACTLY:
<section class="hero-asymmetric"><div class="hero-asymmetric-inner wrap">
  <div class="hero-asymmetric-left">
    <div class="badge au"><span class="badge-pulse"></span>[launch claim]</div>
    <h1 class="au1">[Headline with <em>italic</em>]</h1>
    <p class="hero-desc au2">[2 sentences]</p>
    <div class="hero-btns au3"><button class="btn btn-accent btn-lg">[Primary]</button><button class="btn btn-outline btn-lg">[Secondary]</button></div>
    <div class="hero-trust au3"><div class="trust-avatars"><div class="trust-avatar" style="background:#6366f1">A</div><div class="trust-avatar" style="background:#f97316">M</div><div class="trust-avatar" style="background:#16a34a">S</div></div>[X,XXX] [customers] this month</div>
  </div>
  <div class="hero-asymmetric-right">
    <div class="hero-stat-card"><div class="hsc-num">[Big number]</div><div class="hsc-lbl">[Metric label]</div><div class="hsc-change">↑ [X]% this month</div></div>
    <div class="hero-stat-card"><div class="hsc-num">[Big number]</div><div class="hsc-lbl">[Metric label]</div><div class="hsc-change">↑ [X]% this month</div></div>
    <div class="hero-stat-card"><div class="hsc-num">[Big number]</div><div class="hsc-lbl">[Metric label]</div><div class="hsc-change">↑ [X]% this month</div></div>
  </div>
</div></section>
<section style="padding:40px 0 80px;background:var(--bg);"><div class="wrap">[FULL MOCKUP]</div></section>

FEATURES STRUCTURE — icon circles, copy EXACTLY:
<div class="feat-icon-grid reveal">
  <div class="feat-icon-item"><div class="feat-icon-circle">[emoji]</div><div class="feat-icon-text"><div class="feat-icon-title">[title]</div><p class="feat-icon-desc">[desc]</p></div></div>
  [repeat 5 more times]
</div>

TESTIMONIALS STRUCTURE — minimal italic quotes, copy EXACTLY:
<div class="t-minimal">
  <div class="t-min-item reveal"><p class="t-min-text">"[2-sentence specific quote]"</p><div class="t-min-author"><div class="t-av" style="background:#6366f1">A</div><div><div class="t-name">[Name]</div><div class="t-role">[Role, Company]</div></div></div></div>
  <div class="t-min-item reveal"><p class="t-min-text">"[2-sentence specific quote]"</p><div class="t-min-author"><div class="t-av" style="background:#f97316">M</div><div><div class="t-name">[Name]</div><div class="t-role">[Role, Company]</div></div></div></div>
  <div class="t-min-item reveal"><p class="t-min-text">"[2-sentence specific quote]"</p><div class="t-min-author"><div class="t-av" style="background:#16a34a">S</div><div><div class="t-name">[Name]</div><div class="t-role">[Role, Company]</div></div></div></div>
</div>

CTA STRUCTURE:
<section class="cta-warm"><div class="wrap-sm"><h2>[CTA]</h2><p>[urgency]</p><div class="cta-form"><input class="cta-input-light" type="email" placeholder="Enter your email"><button class="btn btn-accent btn-lg">Get started free</button></div><p class="cta-hint">No credit card · 5 min setup · Cancel anytime</p></div></section>
""",

    "arctic": """
HERO STRUCTURE — centered SaaS, copy EXACTLY:
<section class="hero-centered">
  <div class="wrap">
    <div class="badge au"><span class="badge-pulse"></span>[launch claim]</div>
    <h1 class="au1" style="text-align:center;">[Headline with <em>italic</em>]</h1>
    <p class="hero-desc au2">[2 sentences]</p>
    <div class="hero-btns au3"><button class="btn btn-accent btn-xl">[Primary]</button><button class="btn btn-outline btn-xl">[Secondary]</button></div>
    <div class="hero-trust au3"><div class="trust-avatars"><div class="trust-avatar" style="background:#6366f1">A</div><div class="trust-avatar" style="background:#f97316">M</div><div class="trust-avatar" style="background:#16a34a">S</div><div class="trust-avatar" style="background:#0ea5e9">K</div></div>[X,XXX] teams onboarded</div>
  </div>
</section>
<section style="padding:0 0 80px;background:var(--bg);"><div class="wrap">[FULL MOCKUP]</div></section>

FEATURES: Use feat-grid with 6 feat-cell.
TESTIMONIALS: Use t-grid with 3 t-card.
CTA: <section class="cta-banner"><div class="wrap-sm"><h2>[CTA]</h2><p>[urgency]</p><div class="cta-form"><input class="cta-input" type="email" placeholder="Enter your email"><button class="btn btn-accent btn-lg">Get started free</button></div><p class="cta-hint">No credit card · 5 min setup · Cancel anytime</p></div></section>
""",

    "charcoal-luxe": """
HERO STRUCTURE — luxury full-width, copy EXACTLY:
<section class="hero-luxury">
  <div class="wrap">
    <div class="badge au"><span class="badge-pulse"></span>[launch claim]</div>
    <h1 class="au1">[Headline with <em>italic</em>]</h1>
    <p class="hero-desc au2">[2 sentences]</p>
    <div class="hero-btns au3" style="justify-content:center;"><button class="btn btn-accent btn-xl">[Primary]</button><button class="btn btn-outline btn-xl">[Secondary]</button></div>
    <div class="hero-trust au3"><div class="trust-avatars"><div class="trust-avatar" style="background:#6366f1">A</div><div class="trust-avatar" style="background:#D4AF37">M</div><div class="trust-avatar" style="background:#F0C94A">S</div></div>[X,XXX] clients trust us</div>
  </div>
</section>
<section style="padding:0 0 80px;background:var(--bg);"><div class="wrap">[FULL MOCKUP]</div></section>

FEATURES STRUCTURE — numbered list, copy EXACTLY:
<div class="feat-list">
  <div class="feat-row reveal"><div class="feat-row-num">01</div><div class="feat-row-body"><div class="feat-row-title">[title]</div><p class="feat-row-desc">[desc]</p></div></div>
  <div class="feat-row reveal"><div class="feat-row-num">02</div><div class="feat-row-body"><div class="feat-row-title">[title]</div><p class="feat-row-desc">[desc]</p></div></div>
  <div class="feat-row reveal"><div class="feat-row-num">03</div><div class="feat-row-body"><div class="feat-row-title">[title]</div><p class="feat-row-desc">[desc]</p></div></div>
  <div class="feat-row reveal"><div class="feat-row-num">04</div><div class="feat-row-body"><div class="feat-row-title">[title]</div><p class="feat-row-desc">[desc]</p></div></div>
</div>

TESTIMONIALS STRUCTURE — pull quote + 2 cards, copy EXACTLY:
<div class="t-pull reveal">
  <p class="t-pull-text">"[Long impressive quote 2-3 sentences]"</p>
  <div class="t-pull-author"><div class="t-av" style="background:#6366f1">A</div><div><div class="t-name">[Name]</div><div class="t-role">[Role, Company]</div></div></div>
</div>
<div class="t-2grid reveal">
  <div class="t-card"><div class="t-stars">★★★★★</div><p class="t-text">"[quote]"</p><div class="t-author"><div class="t-av" style="background:#f97316">M</div><div><div class="t-name">[Name]</div><div class="t-role">[Role]</div></div></div></div>
  <div class="t-card"><div class="t-stars">★★★★★</div><p class="t-text">"[quote]"</p><div class="t-author"><div class="t-av" style="background:#16a34a">S</div><div><div class="t-name">[Name]</div><div class="t-role">[Role]</div></div></div></div>
</div>

CTA STRUCTURE:
<section class="cta-gold"><div class="cta-gold-inner"><h2>[CTA]</h2><p>[urgency]</p><div class="cta-form"><input class="cta-input-light" type="email" placeholder="Enter your email"><button class="btn btn-accent btn-lg">Get started free</button></div><p class="cta-hint">No credit card · 5 min setup · Cancel anytime</p></div></section>
""",

    "forest-sage": """
HERO STRUCTURE — split hero with mockup right, copy EXACTLY:
<section class="hero-split">
  <div class="hero-split-left">
    <div class="wrap" style="height:100%;display:flex;flex-direction:column;justify-content:center;padding-top:60px;padding-bottom:60px;">
      <div class="badge au"><span class="badge-pulse"></span>[launch claim]</div>
      <h1 class="au1">[Headline with <em>italic</em>]</h1>
      <p class="hero-desc au2">[2 sentences]</p>
      <div class="hero-btns au3"><button class="btn btn-accent btn-lg">[Primary]</button><button class="btn btn-outline btn-lg">[Secondary]</button></div>
      <div class="hero-trust au3"><div class="trust-avatars"><div class="trust-avatar" style="background:#16a34a">A</div><div class="trust-avatar" style="background:#6366f1">M</div><div class="trust-avatar" style="background:#f97316">S</div></div>[X,XXX] [customers] joined</div>
    </div>
  </div>
  <div class="hero-split-right">[FULL MOCKUP — mockup-outer]</div>
</section>

FEATURES: feat-icon-grid with 6 feat-icon-item.
TESTIMONIALS: t-minimal with 3 t-min-item.
CTA: <section class="cta-warm"><div class="wrap-sm"><h2>[CTA]</h2><p>[urgency]</p><div class="cta-form"><input class="cta-input-light" type="email" placeholder="Enter your email"><button class="btn btn-accent btn-lg">Get started free</button></div><p class="cta-hint">No credit card · 5 min setup · Cancel anytime</p></div></section>
""",

    "rose-quartz": """
HERO STRUCTURE — asymmetric with stat cards, copy EXACTLY:
<section class="hero-asymmetric"><div class="hero-asymmetric-inner wrap">
  <div class="hero-asymmetric-left">
    <div class="badge au"><span class="badge-pulse"></span>[launch claim]</div>
    <h1 class="au1">[Headline with <em>italic</em>]</h1>
    <p class="hero-desc au2">[2 sentences]</p>
    <div class="hero-btns au3"><button class="btn btn-accent btn-lg">[Primary]</button><button class="btn btn-outline btn-lg">[Secondary]</button></div>
    <div class="hero-trust au3"><div class="trust-avatars"><div class="trust-avatar" style="background:#E11D48">A</div><div class="trust-avatar" style="background:#FB7185">M</div><div class="trust-avatar" style="background:#6366f1">S</div></div>[X,XXX] [customers] this month</div>
  </div>
  <div class="hero-asymmetric-right">
    <div class="hero-stat-card"><div class="hsc-num">[Number]</div><div class="hsc-lbl">[Label]</div><div class="hsc-change">↑ [X]%</div></div>
    <div class="hero-stat-card"><div class="hsc-num">[Number]</div><div class="hsc-lbl">[Label]</div><div class="hsc-change">↑ [X]%</div></div>
    <div class="hero-stat-card"><div class="hsc-num">[Number]</div><div class="hsc-lbl">[Label]</div><div class="hsc-change">↑ [X]%</div></div>
  </div>
</div></section>
<section style="padding:40px 0 80px;background:var(--bg);"><div class="wrap">[FULL MOCKUP]</div></section>

FEATURES: feat-zigzag with 3 feat-zz items.
TESTIMONIALS: t-grid with 3 t-card.
CTA: <section class="cta-warm"><div class="wrap-sm"><h2>[CTA]</h2><p>[urgency]</p><div class="cta-form"><input class="cta-input-light" type="email" placeholder="Enter your email"><button class="btn btn-accent btn-lg">Get started free</button></div><p class="cta-hint">No credit card · 5 min setup · Cancel anytime</p></div></section>
""",
}

MASTER_PROMPT = """You are building a production-ready startup website. Follow the HTML structure templates EXACTLY.

STARTUP: {idea}
LAYOUT: {layout_name}
KEY FEATURES: {features}
TARGET CUSTOMER: {target_customer}
PAIN POINT: {pain_point}

RULES — NEVER break these:
1. Use ONLY the CSS classes provided — NO new <style> tags whatsoever
2. ALL copy must be 100% specific to this startup — no generic text
3. ALL mockup data must be domain-specific and realistic
4. Inline style ONLY for: avatar colors (background:#hex), bar heights (height:X%), hero-stat values
5. DO NOT invent new CSS classes — only use what is defined in the design system

━━━ SECTION 1: NAV (always the same) ━━━
<nav id="nav">
  <div class="nav-inner">
    <a href="#" class="nav-brand"><div class="nav-logo">[first letter of product name]</div>[ProductName]</a>
    <div class="nav-links"><a href="#features">Features</a><a href="#how">How it works</a><a href="#pricing">Pricing</a><a href="#faq">FAQ</a></div>
    <div class="nav-btns"><button class="btn btn-ghost btn-sm">Log in</button><button class="btn btn-accent btn-sm">Start free</button></div>
  </div>
</nav>

━━━ SECTION 2 + 3: HERO + MOCKUP ━━━
USE THIS EXACT STRUCTURE — replace [CONTENT] with startup-specific content:
{layout_instructions}

MOCKUP TEMPLATE — use wherever [FULL MOCKUP] appears above:
<div class="mockup-outer">
  <div class="mockup-chrome">
    <div class="mockup-dots"><div class="md md-r"></div><div class="md md-a"></div><div class="md md-g"></div></div>
    <div class="mockup-urlbar"><span>🔒</span> app.[productdomain].com/dashboard</div>
  </div>
  <div class="mockup-app">
    <div class="mockup-sb">
      <div class="mockup-sb-logo"><div class="mockup-sb-mark"></div>[ProductName]</div>
      <div class="mockup-sb-sec">Main</div>
      <div class="mockup-nav active"><span class="mockup-ico">📊</span>[Nav item 1 — specific to product]</div>
      <div class="mockup-nav"><span class="mockup-ico">📋</span>[Nav item 2]</div>
      <div class="mockup-nav"><span class="mockup-ico">👥</span>[Nav item 3]</div>
      <div class="mockup-nav"><span class="mockup-ico">📈</span>[Nav item 4]</div>
      <div class="mockup-nav"><span class="mockup-ico">🔔</span>[Nav item 5]</div>
      <div class="mockup-sb-sec">Account</div>
      <div class="mockup-nav"><span class="mockup-ico">⚙️</span>Settings</div>
    </div>
    <div class="mockup-main">
      <div class="mockup-topbar">
        <div class="mockup-title">[Specific page/dashboard name]</div>
        <div class="mockup-tbbtns"><div class="mockup-btn-g">Export</div><div class="mockup-btn">[Primary action specific to product]</div></div>
      </div>
      <div class="mockup-content">
        <div class="mockup-kpis">
          <div class="mockup-kpi"><div class="mockup-kpi-val">[real number e.g. $84.2K]</div><div class="mockup-kpi-lbl">[domain-specific metric]</div><div class="mockup-kpi-ch">↑ 12.4%</div></div>
          <div class="mockup-kpi"><div class="mockup-kpi-val">[real number]</div><div class="mockup-kpi-lbl">[domain metric]</div><div class="mockup-kpi-ch">↑ 8.1%</div></div>
          <div class="mockup-kpi"><div class="mockup-kpi-val">[real number]</div><div class="mockup-kpi-lbl">[domain metric]</div><div class="mockup-kpi-ch">↑ 3.2%</div></div>
        </div>
        <div class="mockup-sec">[Domain-specific table name]</div>
        <table class="mockup-tbl">
          <thead><tr><th>[Col 1]</th><th>[Col 2]</th><th>[Col 3]</th><th>Status</th></tr></thead>
          <tbody>
            <tr><td>[real data]</td><td>[real data]</td><td>[real data]</td><td><span class="tag tag-green">Active</span></td></tr>
            <tr><td>[real data]</td><td>[real data]</td><td>[real data]</td><td><span class="tag tag-amber">Pending</span></td></tr>
            <tr><td>[real data]</td><td>[real data]</td><td>[real data]</td><td><span class="tag tag-green">Active</span></td></tr>
            <tr><td>[real data]</td><td>[real data]</td><td>[real data]</td><td><span class="tag tag-blue">Review</span></td></tr>
          </tbody>
        </table>
        <div class="mockup-charts">
          <div class="mockup-chart">
            <div class="mockup-chart-ttl">[Metric] — last 8 weeks</div>
            <div class="bars">
              <div class="bar" style="height:35%"></div><div class="bar" style="height:52%"></div><div class="bar" style="height:41%"></div><div class="bar" style="height:68%"></div><div class="bar" style="height:59%"></div><div class="bar" style="height:82%"></div><div class="bar" style="height:76%"></div><div class="bar" style="height:91%"></div>
            </div>
          </div>
          <div class="mockup-chart">
            <div class="mockup-chart-ttl">[Breakdown] by [category]</div>
            <div class="donut-wrap">
              <div class="donut-legend">
                <div class="donut-row"><span class="donut-dot" style="background:var(--accent)"></span>[Label] 44%</div>
                <div class="donut-row"><span class="donut-dot" style="background:var(--accent2)"></span>[Label] 33%</div>
                <div class="donut-row"><span class="donut-dot" style="background:#94a3b8"></span>[Label] 23%</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

━━━ SECTION 4: STATS ━━━
<div class="divider"></div>
<div class="stats-strip">
  <div class="stats-inner">
    <div class="stat-cell"><span class="stat-num">[impressive number]</span><div class="stat-lbl">[domain label]</div></div>
    <div class="stat-cell"><span class="stat-num">[impressive number]</span><div class="stat-lbl">[domain label]</div></div>
    <div class="stat-cell"><span class="stat-num">[impressive number]</span><div class="stat-lbl">[domain label]</div></div>
    <div class="stat-cell"><span class="stat-num">[impressive number]</span><div class="stat-lbl">[domain label]</div></div>
  </div>
</div>
<div class="divider"></div>

━━━ SECTION 5: FEATURES ━━━
<section class="sec" id="features">
  <div class="wrap">
    <div class="eyebrow reveal">Features</div>
    <h2 class="sec-title reveal">[Benefit-driven headline — specific to this startup]</h2>
    <p class="sec-desc reveal">[2 sentences — what makes this product different]</p>
    [INSERT FEATURES STRUCTURE FROM LAYOUT TEMPLATE ABOVE]
  </div>
</section>

━━━ SECTION 6: HOW IT WORKS ━━━
<section class="sec" id="how" style="background:var(--surface2);">
  <div class="wrap">
    <div class="eyebrow reveal">How it works</div>
    <h2 class="sec-title reveal">[Active verb headline e.g. "Get results in three steps"]</h2>
    <p class="sec-desc reveal">[Description]</p>
    <div class="steps-grid">
      <div class="step reveal"><div class="step-num">1</div><div class="step-title">[Specific step]</div><p class="step-desc">[Description]</p></div>
      <div class="step reveal d1"><div class="step-num">2</div><div class="step-title">[Specific step]</div><p class="step-desc">[Description]</p></div>
      <div class="step reveal d2"><div class="step-num">3</div><div class="step-title">[Specific step]</div><p class="step-desc">[Description]</p></div>
    </div>
  </div>
</section>

━━━ SECTION 7: TESTIMONIALS ━━━
<section class="sec" id="testimonials">
  <div class="wrap">
    <div class="eyebrow reveal">What customers say</div>
    <h2 class="sec-title reveal">[Credibility headline]</h2>
    [INSERT TESTIMONIALS STRUCTURE FROM LAYOUT TEMPLATE ABOVE — quotes must mention specific product features]
  </div>
</section>

━━━ SECTION 8: PRICING ━━━
<section class="sec" id="pricing" style="background:var(--surface2);">
  <div class="wrap">
    <div class="eyebrow reveal">Pricing</div>
    <h2 class="sec-title reveal">[Value-focused pricing headline]</h2>
    <p class="sec-desc reveal">[Short value statement]</p>
    <div class="pricing-grid reveal">
      <div class="p-card">
        <div class="p-tier">Starter</div>
        <div class="p-price-row"><span class="p-currency">$</span><span class="p-price">[price]</span></div>
        <div class="p-period">/month</div>
        <p class="p-desc">[Who this is for]</p>
        <div class="p-divider"></div>
        <div class="p-features">
          <div class="p-feat"><div class="p-check">✓</div>[feature]</div>
          <div class="p-feat"><div class="p-check">✓</div>[feature]</div>
          <div class="p-feat"><div class="p-check">✓</div>[feature]</div>
          <div class="p-feat"><div class="p-check">✓</div>[feature]</div>
        </div>
        <button class="btn btn-outline btn-full">Get started</button>
      </div>
      <div class="p-card featured">
        <div class="p-badge">Most Popular</div>
        <div class="p-tier">Pro</div>
        <div class="p-price-row"><span class="p-currency">$</span><span class="p-price">[price]</span></div>
        <div class="p-period">/month</div>
        <p class="p-desc">[Who this is for]</p>
        <div class="p-divider"></div>
        <div class="p-features">
          <div class="p-feat"><div class="p-check">✓</div>[feature]</div>
          <div class="p-feat"><div class="p-check">✓</div>[feature]</div>
          <div class="p-feat"><div class="p-check">✓</div>[feature]</div>
          <div class="p-feat"><div class="p-check">✓</div>[feature]</div>
          <div class="p-feat"><div class="p-check">✓</div>[feature]</div>
        </div>
        <button class="btn btn-accent btn-full">Get started free</button>
      </div>
      <div class="p-card">
        <div class="p-tier">Scale</div>
        <div class="p-price-row"><span class="p-currency">$</span><span class="p-price">[price]</span></div>
        <div class="p-period">/month</div>
        <p class="p-desc">[Who this is for]</p>
        <div class="p-divider"></div>
        <div class="p-features">
          <div class="p-feat"><div class="p-check">✓</div>[feature]</div>
          <div class="p-feat"><div class="p-check">✓</div>[feature]</div>
          <div class="p-feat"><div class="p-check">✓</div>[feature]</div>
          <div class="p-feat"><div class="p-check">✓</div>[feature]</div>
          <div class="p-feat"><div class="p-check">✓</div>[feature]</div>
          <div class="p-feat"><div class="p-check">✓</div>[feature]</div>
        </div>
        <button class="btn btn-outline btn-full">Contact sales</button>
      </div>
    </div>
  </div>
</section>

━━━ SECTION 9: FAQ ━━━
<section class="sec" id="faq">
  <div class="wrap-sm">
    <div class="eyebrow reveal" style="justify-content:center;">FAQ</div>
    <h2 class="sec-title reveal" style="text-align:center;">[FAQ headline]</h2>
    <div class="faq-list reveal">
      <div class="faq-item"><div class="faq-q">[Question 1?]<span class="faq-ico">+</span></div><div class="faq-a">[2-3 sentence answer]</div></div>
      <div class="faq-item"><div class="faq-q">[Question 2?]<span class="faq-ico">+</span></div><div class="faq-a">[answer]</div></div>
      <div class="faq-item"><div class="faq-q">[Question 3?]<span class="faq-ico">+</span></div><div class="faq-a">[answer]</div></div>
      <div class="faq-item"><div class="faq-q">[Question 4?]<span class="faq-ico">+</span></div><div class="faq-a">[answer]</div></div>
      <div class="faq-item"><div class="faq-q">[Question 5?]<span class="faq-ico">+</span></div><div class="faq-a">[answer]</div></div>
    </div>
  </div>
</section>

━━━ SECTION 10: CTA ━━━
[INSERT CTA STRUCTURE FROM LAYOUT TEMPLATE ABOVE]

━━━ SECTION 11: FOOTER ━━━
<footer>
  <div class="wrap">
    <div class="footer-grid">
      <div>
        <div class="nav-logo" style="margin-bottom:14px;">[first letter]</div>
        <div class="footer-brand-name">[ProductName]</div>
        <p class="footer-brand-desc">[2-sentence description of the product]</p>
      </div>
      <div>
        <div class="footer-col-title">Product</div>
        <a href="#" class="footer-link">Features</a><a href="#" class="footer-link">Pricing</a><a href="#" class="footer-link">Changelog</a><a href="#" class="footer-link">Roadmap</a>
      </div>
      <div>
        <div class="footer-col-title">Company</div>
        <a href="#" class="footer-link">About</a><a href="#" class="footer-link">Blog</a><a href="#" class="footer-link">Careers</a><a href="#" class="footer-link">Press</a>
      </div>
      <div>
        <div class="footer-col-title">Connect</div>
        <a href="#" class="footer-link">Twitter / X</a><a href="#" class="footer-link">LinkedIn</a><a href="#" class="footer-link">GitHub</a><a href="#" class="footer-link">Discord</a>
      </div>
    </div>
    <div class="footer-bottom">
      <div class="footer-copy">© 2025 [ProductName]. All rights reserved.</div>
      <div class="footer-legal"><a href="#">Privacy</a><a href="#">Terms</a><a href="#">Cookies</a></div>
    </div>
  </div>
</footer>

━━━ JAVASCRIPT (required at bottom) ━━━
<script>
  document.querySelectorAll('.faq-q').forEach(q=>{{
    q.addEventListener('click',()=>{{
      const item=q.parentElement,wasOpen=item.classList.contains('open');
      document.querySelectorAll('.faq-item').forEach(i=>i.classList.remove('open'));
      if(!wasOpen)item.classList.add('open');
    }});
  }});
  const nav=document.getElementById('nav');
  window.addEventListener('scroll',()=>nav.classList.toggle('scrolled',window.scrollY>12),{{passive:true}});
  document.querySelectorAll('.reveal').forEach(el=>el.classList.add('in'));
  document.querySelectorAll('a[href^="#"]').forEach(a=>{{
    a.addEventListener('click',e=>{{const t=document.querySelector(a.getAttribute('href'));if(t){{e.preventDefault();t.scrollIntoView({{behavior:'smooth',block:'start'}});}}}});
  }});
</script>

Return ONLY the HTML starting with <nav. No DOCTYPE, html, head, body tags, no markdown, no explanation."""


def run_prototype_generator(idea: str, product_strategy: dict, llm, seed: int = None) -> tuple:
    if seed is None or seed < 0:
        seed = random.randint(0, len(LAYOUT_TEMPLATES) - 1)
    else:
        seed = seed % len(LAYOUT_TEMPLATES)

    t = LAYOUT_TEMPLATES[seed]

    features, target_customer, pain_point = [
    ], 'businesses and professionals', 'inefficient manual processes'
    if isinstance(product_strategy, dict):
        mvp = product_strategy.get('mvp_features', [])
        features = [f.get('feature', '') for f in mvp[:6]
                    if isinstance(f, dict) and f.get('feature')]
        target_customer = product_strategy.get(
            'target_customer', target_customer)
        pain_point = product_strategy.get('pain_point', pain_point)

    css = _build_css(t)
    safety = _safety_css()
    layout_instructions = LAYOUT_PROMPTS.get(
        t["id"], "Use the hero-centered layout.")

    prompt = ChatPromptTemplate.from_template(MASTER_PROMPT)
    chain = prompt | llm
    response = chain.invoke({
        "idea": idea,
        "layout_name": t["name"],
        "layout_desc": t["description"],
        "features": ', '.join(features) if features else 'core product capabilities',
        "target_customer": target_customer,
        "pain_point": pain_point,
        "layout_instructions": layout_instructions,
    })

    body = response.content.strip()
    body = re.sub(r"```html\s*", "", body)
    body = re.sub(r"```\s*$", "", body, flags=re.MULTILINE)
    body = body.strip()
    body = re.sub(r"(?i)<!DOCTYPE[^>]*>", "", body)
    body = re.sub(r"(?i)<html[^>]*>|</html>", "", body)
    body = re.sub(r"(?i)<body[^>]*>|</body>", "", body)
    hm = re.search(r"(?i)<head>.*?</head>", body, re.DOTALL)
    if hm:
        body = body[hm.end():]
    body = body.strip()

    title = idea[:50].replace('"', "'")
    desc = idea[:120].replace('"', "'")

    full_html = (
        "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n"
        "  <meta charset=\"UTF-8\">\n"
        "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
        f"  <meta name=\"description\" content=\"{desc}\">\n"
        f"  <meta name=\"theme-color\" content=\"{t['accent']}\">\n"
        f"  <title>{title}</title>\n"
        f"{css}\n{safety}\n"
        "</head>\n<body>\n"
        f"{body}\n"
        "</body>\n</html>"
    )

    return full_html, t["name"]
