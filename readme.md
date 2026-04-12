# VentureOS 🚀

> **Your AI co-founder. One prompt. Twelve outputs.**

VentureOS is an autonomous startup analysis platform built for the **Google Build with AI Hackathon at WashU DevFest 2026**. Describe your startup idea in one sentence — eight specialized AI agents stream back a complete go-to-market foundation in real time.

---

## 🎥 Demo

> _[Insert demo link here]_

**Live URL:** _[Insert deployment URL here]_

---

## ✨ What It Does

Paste or speak your startup idea. VentureOS runs eight AI agents in sequence and delivers twelve capabilities — all streamed live to your browser.

| # | Capability | Description |
|---|-----------|-------------|
| 01 | **Market Research** | TAM, growth rate, target customer, pain points, market trends |
| 02 | **Competitor Analysis** | Real competitors, their weaknesses, your whitespace opportunity |
| 03 | **Product Strategy** | MoSCoW features, tech stack, build timeline, revenue models |
| 04 | **Pitch Deck + Investor Emails** | 10-slide deck outline + 3 personalized cold outreach emails |
| 05 | **Domain Suggestions** | Five creative, brand-appropriate domain name options |
| 06 | **Fundability Scorecard** | VC-style scoring across 5 dimensions, score out of 100 |
| 07 | **Live App Prototype** | Interactive HTML/CSS/JS prototype rendered in 5 visual styles |
| 08 | **Idea Refinement Chat** | AI co-founder chat with full analysis context |
| 09 | **PDF Export** | One-click full report download + plain text copy |
| 10 | **Financial Model** | 3-year revenue projections, adjustable assumptions, CSV export |
| 11 | **Idea History** | Last 3 ideas auto-saved with scores — click to reload any |
| 12 | **Pivot Suggester** | 3 strategic pivots based on scorecard weaknesses |

---

## 🏗️ Architecture

```
VentureOS/
├── app.py                  # Flask server — all API routes
├── agents/
│   ├── orchestrator.py     # Runs agents in sequence, streams SSE events
│   ├── market_agent.py     # Market research agent
│   ├── competitor_agent.py # Competitor analysis agent
│   ├── product_agent.py    # Product strategy agent
│   ├── pitch_agent.py      # Pitch deck + emails + domains agent
│   ├── scorecard_agent.py  # Fundability scoring agent
│   ├── prototype_agent.py  # Live app prototype generator (5 styles)
│   └── pivot_agent.py      # Strategic pivot suggester
├── templates/
│   └── index.html          # Complete single-file frontend
├── .env                    # API keys (not committed)
├── requirements.txt
└── README.md
```

### Streaming Flow

```
Browser → POST /analyze → Flask → orchestrator.py
                                        ↓
                                market_agent runs
                                        ↓  SSE: market_research
                                competitor_agent runs
                                        ↓  SSE: competitor_analysis
                                product_agent runs
                                        ↓  SSE: product_strategy
                                pitch_agent runs
                                        ↓  SSE: pitch
                                scorecard_agent runs
                                        ↓  SSE: scorecard
                                        ↓  SSE: done
              Browser renders each card as events arrive in real time
```

---

## 🤖 Agent Details

### `orchestrator.py`
Runs all agents sequentially and yields Server-Sent Events (SSE) for each. The frontend reads the stream and renders result cards in real time as each agent completes.

### `market_agent.py`
Produces structured JSON with `market_size`, `growth_rate`, `target_customer`, `pain_point`, `market_trends[]`, and `opportunity_summary`.

### `competitor_agent.py`
Returns up to 4 real competitors each with `name`, `funding`, `description`, `weakness`, and `our_advantage`, plus a `whitespace` summary.

### `product_agent.py`
Generates a MoSCoW-prioritized feature list, suggested tech stack, a week-by-week build timeline, and 2–3 monetization models with pros and cons.

### `pitch_agent.py`
Produces a 10-slide pitch deck outline, three personalized cold investor emails (angel / seed VC / strategic), and five domain name suggestions — all in a single LLM call.

### `scorecard_agent.py`
Scores the idea across five VC dimensions (Market Size, Team Fit, Differentiation, Business Model, Timing) at 20 points each for a total out of 100. Returns a verdict, summary, biggest strength, and biggest risk.

### `prototype_agent.py`
Generates a complete, self-contained HTML/CSS/JS prototype with a landing page, feature cards, a mock app dashboard with realistic fake data, testimonials, and pricing. Supports 5 visual style themes:

| Theme | Inspiration |
|-------|------------|
| Modern SaaS | Stripe / Linear |
| Bold Dark | Vercel / Resend |
| Warm Startup | Notion / Loom |
| Premium Blue | Figma |
| Gradient Pop | Consumer apps |

Each regeneration injects a full CSS reset to guarantee style isolation from the parent page. A seed parameter controls which theme is used — random by default, ensuring every generation looks distinct.

### `pivot_agent.py`
Takes the idea, market data, competitor landscape, and scorecard weaknesses and returns 3 meaningfully different strategic pivots — each with a title, description, target customer, revenue model, difficulty rating, potential score, and a real-world example of a company that made a similar pivot.

---

## ⚡ Tech Stack

| Layer | Technology |
|-------|-----------|
| **LLM** | Groq API — LLaMA 3.3-70b-versatile via LangChain |
| **Agent Framework** | LangChain (`ChatPromptTemplate`, `HumanMessage`, `SystemMessage`) |
| **Backend** | Flask (Python 3.9+) with `stream_with_context` |
| **Streaming** | Server-Sent Events (`text/event-stream`) |
| **Frontend** | Vanilla HTML / CSS / JS — single file, zero build step |
| **Fonts** | Instrument Serif + Geist via Google Fonts CDN |
| **Voice Input** | Web Speech API |
| **Persistence** | `localStorage` for idea history |
| **Export** | `window.print()` for PDF, Blob API for CSV download |
| **Deployment** | Google Cloud |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- API key configured in `.env`

### Installation

```bash
# 1. Clone the repo
git clone https://github.com/yogvidwankhede/VentureOS.git
cd VentureOS

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Fill in your API key inside .env

# 5. Start the server
python app.py
```

Visit [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

---

## 📦 Dependencies

```
flask
python-dotenv
langchain
langchain-google-genai
```

Full list in `requirements.txt`.

---

## 🔌 API Routes

| Method | Route | Description |
|--------|-------|-------------|
| `GET` | `/` | Serve the frontend |
| `POST` | `/analyze` | Stream SSE analysis from all 8 agents |
| `POST` | `/prototype` | Generate a live HTML prototype |
| `POST` | `/chat` | Co-founder chat with full analysis context |
| `POST` | `/pivot` | Generate 3 strategic pivot suggestions |

### `/analyze` — Request
```json
{ "idea": "An app that helps college students find subleasers for their apartments" }
```

### `/analyze` — SSE Stream Response
```
data: {"event": "status", "message": "Running Market Research agent..."}
data: {"event": "market_research", "data": { ... }}
data: {"event": "competitor_analysis", "data": { ... }}
data: {"event": "product_strategy", "data": { ... }}
data: {"event": "pitch", "data": { ... }}
data: {"event": "scorecard", "data": { ... }}
data: {"event": "done"}
```

### `/prototype` — Request
```json
{ "idea": "...", "product_strategy": { ... }, "seed": 2 }
```
`seed` 0–4 selects a visual style. Omit for random.

### `/chat` — Request
```json
{
  "idea": "...",
  "context": { "market_research": {}, "scorecard": {}, "...": {} },
  "messages": [{ "role": "user", "content": "..." }],
  "user_message": "What is the best GTM strategy?"
}
```

### `/pivot` — Request
```json
{
  "idea": "...",
  "context": {
    "market_research": {},
    "competitor_analysis": {},
    "scorecard": {}
  }
}
```

---

## 🎨 Frontend Features

- **Live streaming** — `ReadableStream` reader renders result cards as each SSE event arrives
- **Agent status bar** — animated pills track each agent (Market → Competitors → Product → Pitch → Scorecard)
- **Voice input** — Web Speech API mic with real-time interim transcription display
- **Prototype viewer** — macOS-style browser chrome with desktop / tablet / mobile viewport switcher
- **Style selector** — 5 named themes + 🎲 Random chip; each regeneration produces a distinct design
- **Financial model** — 36-month projection table, 5 adjustable inputs, quarterly highlights, one-click CSV export
- **Idea history** — `localStorage`, max 3 entries, color-coded by fundability score, click any to reload
- **PDF export** — `@media print` stylesheet hides non-result sections and forces all result cards open
- **Co-founder chat** — full analysis context sent with every message; typing indicator; quick-prompt chips
- **Pivot suggester** — on-demand strategic analysis with difficulty ratings and real-world examples

---

## 🗑️ Unused Scaffolding

Two folders exist in the repo but are not connected to the running application:

- `data/startup_kb/` — Planned knowledge base for RAG-grounded agent responses
- `rag/` — Planned vector retrieval pipeline (ChromaDB)

These are safe to delete and have no effect on the app. They are kept as markers for a planned future enhancement.

---

## 🛣️ Roadmap

- [ ] **RAG pipeline** — ChromaDB + startup knowledge base for grounded, example-backed agent responses
- [ ] **Comparison mode** — Analyze two ideas side by side
- [ ] **Investor match** — Match idea to real investors based on thesis alignment
- [ ] **Slide deck export** — Generate a downloadable `.pptx` from the pitch deck outline
- [ ] **Team builder** — Suggest ideal co-founder profiles based on idea type and scorecard gaps
- [ ] **Vision analysis** — Analyze uploaded pitch decks or competitor screenshots

---

## 👤 Author

**Yogvid Wankhede**
M.S. Data Analytics & Statistics — Washington University in St. Louis
Research Assistant, WashU School of Medicine

- Portfolio: [yogvidwankhede.com](https://yogvidwankhede.com)
- GitHub: [@yogvidwankhede](https://github.com/yogvidwankhede)

---

## 🏆 Hackathon

Built for the **Google Build with AI Hackathon** at WashU DevFest 2026.

---

## 📄 License

MIT License — see `LICENSE` for details.